"""Gmail integration: mine your own replies as the corpus, draft new ones back into it.

The interesting half of this is not reading and writing mail — it is that **your sent
mail becomes the dataset**. Every thread where someone wrote to you and you replied is
exactly the (incoming, reply) pair this system retrieves over, so a real mailbox fixes the
single biggest weakness in the shipped project: that its corpus is synthetic.

Three deliberate constraints:

**It never sends.** It creates *drafts*, in the right thread, for a human to read and
send. The OAuth scope requested is ``gmail.compose``, which cannot send on your behalf
even if the code tried — the permission simply is not granted. That is enforcement, not
etiquette.

**The full metric cannot run online.** Scoring a reply against `must_include` /
`must_not_include` needs a known-correct answer, and for new mail there isn't one. What
survives at inference time is the reference-free half — placeholders, over-promising,
fabricated identifiers, deferral behaviour, and the judge's faithfulness check against
the incoming message. Those are reported per draft. The reference-based components
(grounding, intent, similarity against gold) are for offline evaluation on history, where
your past reply *is* the gold answer.

**Your mail is sent to a third-party model.** Whichever provider is configured receives
the incoming message and the retrieved examples from your mailbox. That is a real
disclosure, not a footnote — see ``--dry-run``, which does everything except call the LLM.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_PATH = ROOT / "credentials.json"
TOKEN_PATH = ROOT / ".gmail_token.json"

#: readonly to mine history and read new mail; compose to create drafts.
#: gmail.send is deliberately NOT requested — this tool must not be able to send.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

QUOTE_MARKERS = (
    re.compile(r"^On .{0,120}wrote:$", re.MULTILINE),
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^_{10,}$", re.MULTILINE),
    re.compile(r"^From:.*$", re.MULTILINE),
)
SIGNATURE_CUT = re.compile(r"^--\s*$", re.MULTILINE)


# --------------------------------------------------------------------------- auth


def get_service(credentials_path: Path = CREDENTIALS_PATH, token_path: Path = TOKEN_PATH):
    """Authorise and return a Gmail API client, caching the token locally.

    Setup, once:
      1. console.cloud.google.com -> new project -> enable the Gmail API
      2. Credentials -> Create -> OAuth client ID -> Desktop app
      3. Download the JSON to ``credentials.json`` in the repo root (gitignored)
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"{credentials_path.name} not found. Create an OAuth 'Desktop app' "
                    f"client at console.cloud.google.com (Gmail API enabled) and save the "
                    f"JSON there. See src/integrations/gmail.py for the steps."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# --------------------------------------------------------------------------- parsing


@dataclass
class Message:
    id: str
    thread_id: str
    sender: str
    to: str
    subject: str
    body: str
    date: str
    message_id_header: str = ""
    label_ids: list[str] = field(default_factory=list)

    @property
    def from_me(self) -> bool:
        return "SENT" in self.label_ids


def _header(payload: dict, name: str) -> str:
    for h in payload.get("headers", []):
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")


def _extract_body(payload: dict) -> str:
    """Prefer text/plain; fall back to stripping tags from text/html."""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime == "text/plain" and body.get("data"):
        return _decode(body["data"])

    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return _decode(part["body"]["data"])
    for part in payload.get("parts", []) or []:
        nested = _extract_body(part)
        if nested:
            return nested

    if mime == "text/html" and body.get("data"):
        html = _decode(body["data"])
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL)
        return re.sub(r"<[^>]+>", " ", html)
    return ""


def clean_body(text: str) -> str:
    """Drop quoted history and signature blocks.

    Real mail is mostly quotation. Feeding the whole chain to the model buries the actual
    question and blows the context budget, and quoted text of *previous* replies makes the
    retrieval corpus look artificially self-similar.
    """
    if not text:
        return ""
    text = text.replace("\r\n", "\n")
    cut = len(text)
    for pat in QUOTE_MARKERS:
        m = pat.search(text)
        if m:
            cut = min(cut, m.start())
    text = text[:cut]
    sig = SIGNATURE_CUT.search(text)
    if sig:
        text = text[: sig.start()]
    text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def to_message(raw: dict) -> Message:
    payload = raw.get("payload", {})
    return Message(
        id=raw.get("id", ""),
        thread_id=raw.get("threadId", ""),
        sender=_header(payload, "From"),
        to=_header(payload, "To"),
        subject=_header(payload, "Subject"),
        body=clean_body(_extract_body(payload)),
        date=_header(payload, "Date"),
        message_id_header=_header(payload, "Message-ID"),
        label_ids=raw.get("labelIds", []) or [],
    )


# --------------------------------------------------------------------------- mining


def mine_history(service, max_threads: int = 300, min_reply_words: int = 15,
                 progress: bool = True) -> list[dict]:
    """Build a retrieval corpus of (incoming, your reply) pairs from real threads.

    This is the point of the integration. Each pair is emitted in the same schema the
    synthetic dataset uses, so retrieval, generation and offline evaluation all work
    unchanged — with the exception of `must_include` / `must_not_include`, which cannot be
    derived automatically and are left empty. Offline scoring on mined data therefore runs
    on intent, similarity, style and sendability; grounding needs annotation.
    """
    records: list[dict] = []
    page_token = None
    seen = 0

    while seen < max_threads:
        resp = service.users().threads().list(
            userId="me", q="in:inbox has:userlabels OR in:anywhere",
            maxResults=min(100, max_threads - seen), pageToken=page_token,
        ).execute()
        threads = resp.get("threads", [])
        if not threads:
            break

        for t in threads:
            seen += 1
            if progress and seen % 25 == 0:
                print(f"  mined {seen} threads, {len(records)} pairs", end="\r", flush=True)
            full = service.users().threads().get(userId="me", id=t["id"], format="full").execute()
            msgs = [to_message(m) for m in full.get("messages", [])]

            # Pair each of your replies with the message immediately before it.
            for i in range(1, len(msgs)):
                reply, incoming = msgs[i], msgs[i - 1]
                if not reply.from_me or incoming.from_me:
                    continue
                if len(reply.body.split()) < min_reply_words or not incoming.body.strip():
                    continue
                records.append({
                    "id": f"gmail-{reply.id[:12]}",
                    "category": "gmail",
                    "persona": "self",
                    "thread_context": "",
                    "incoming": {
                        "from": incoming.sender, "subject": incoming.subject,
                        "received_at": incoming.date, "body": incoming.body,
                    },
                    "gold_reply": {
                        "subject": reply.subject or f"Re: {incoming.subject}",
                        "body": reply.body,
                    },
                    "intent_label": "provide_information",  # unlabelled; see docstring
                    "must_include": [],
                    "must_not_include": [],
                    "difficulty": "normal",
                    "requires_human_review": False,
                    "_gmail": {"thread_id": t["id"], "reply_id": reply.id},
                })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    if progress:
        print(" " * 60, end="\r")
    return records


def fetch_needing_reply(service, query: str = "in:inbox is:unread -from:me",
                        limit: int = 10) -> list[Message]:
    """Messages that plausibly want a reply. The query is a plain Gmail search string."""
    resp = service.users().messages().list(userId="me", q=query, maxResults=limit).execute()
    out = []
    for ref in resp.get("messages", []) or []:
        raw = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        msg = to_message(raw)
        if msg.body.strip():
            out.append(msg)
    return out


# --------------------------------------------------------------------------- drafting


def create_draft(service, original: Message, subject: str, body: str,
                 me: str = "me") -> dict:
    """Create a reply draft inside the original thread.

    ``threadId`` alone is not enough for Gmail to thread it correctly — ``In-Reply-To`` and
    ``References`` must carry the original ``Message-ID`` or the draft shows up as a
    detached message.
    """
    mime = MIMEText(body, "plain", "utf-8")
    mime["To"] = original.sender
    mime["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    if original.message_id_header:
        mime["In-Reply-To"] = original.message_id_header
        mime["References"] = original.message_id_header

    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode("utf-8")
    return service.users().drafts().create(
        userId=me, body={"message": {"raw": raw, "threadId": original.thread_id}}
    ).execute()


def profile_email(service) -> str:
    return service.users().getProfile(userId="me").execute().get("emailAddress", "")


# --------------------------------------------------------------------------- scoring


def inference_time_checks(reply_body: str, incoming: Message,
                          exemplars: list[dict] | None = None) -> dict:
    """The subset of the metric that works without a known-correct answer.

    Grounding, intent-match and similarity all compare against a gold reply that does not
    exist for new mail. These do not, so they are what a live integration can report.
    """
    from ..eval.safety import (find_invented_identifiers, find_overpromises,
                               find_placeholders, has_action_or_commitment,
                               looks_deferring)

    sources = [incoming.subject, incoming.body]
    for ex in exemplars or []:
        sources += [ex["incoming"]["body"], ex["gold_reply"]["body"]]

    placeholders = find_placeholders(reply_body)
    invented = find_invented_identifiers(reply_body, sources)
    overpromises = find_overpromises(reply_body)

    return {
        "placeholders": placeholders,
        "invented_identifiers": invented,
        "overpromises": overpromises,
        "defers": looks_deferring(reply_body),
        "commits": has_action_or_commitment(reply_body),
        "blocking": bool(placeholders or invented),
        "note": ("Reference-free checks only — grounding, intent and similarity need a "
                 "known-correct reply and cannot be computed for new mail."),
    }
