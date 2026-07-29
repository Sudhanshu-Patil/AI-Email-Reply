"""Would a human actually send this, or does it need rescuing first?

Three failure modes matter more than anything a fluency score notices:

1. **Fabricated identifiers.** The reply cites ``RMA-7788`` when the real one is
   ``RMA-2291``. It reads perfectly. It is worse than useless — the customer chases a
   reference that does not exist.
2. **Unauthorised commitments.** "I've processed your full refund" from a support inbox
   with no refund authority.
3. **Placeholders.** ``[CUSTOMER NAME]`` shipped to a customer.

Each is caught by a rule rather than a judgement, because each is objectively checkable
and none should depend on a model's mood.

The deferral checks run in both directions. Under-deferral — answering confidently where
the human escalated — is the dangerous failure. Over-deferral — punting a routine question
— is the useless one, and a suggested-reply system that hedges everything is worthless
even though it never says anything false. A metric that only penalised the first would be
trivially gamed by refusing to answer anything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .constraints import normalise, sentences

PLACEHOLDER_PATTERNS = (
    re.compile(r"\[[A-Za-z_ /]{2,30}\]"),          # [CUSTOMER NAME], [insert date]
    re.compile(r"\{\{.*?\}\}"),                     # {{name}}
    re.compile(r"<(?:insert|your|customer)[^>]{0,30}>", re.IGNORECASE),
    re.compile(r"\bTODO\b|\bTBD\b|\bXXX\b|\bFIXME\b"),
    re.compile(r"\bLorem ipsum\b", re.IGNORECASE),
)

#: Identifier shapes worth verifying. Bare integers are excluded on purpose — "3 weeks"
#: and "9 FTE" are not references, and flagging them would bury the real signal.
IDENTIFIER_RE = re.compile(
    r"\b(?:[A-Z]{2,5}-\d{2,6}|#\d{3,6}|(?:INV|RMA|REF|PO|Q)-?\d{3,6})\b", re.IGNORECASE
)

OVERPROMISE_PATTERNS = (
    (re.compile(r"\bguarantee(?:d|s)?\b", re.IGNORECASE), "guarantee"),
    (re.compile(r"\b100%\s*(?:uptime|certain|sure|guaranteed)", re.IGNORECASE), "absolute claim"),
    (re.compile(r"\bwill never happen again\b", re.IGNORECASE), "will never happen again"),
    (re.compile(r"\brest assured\b", re.IGNORECASE), "rest assured"),
    (re.compile(r"\bcompletely (?:safe|secure|resolved)\b", re.IGNORECASE), "absolute claim"),
    (re.compile(r"\bno (?:risk|chance) (?:of|that)\b", re.IGNORECASE), "no risk claim"),
)

DEFERRAL_MARKERS = (
    "i will come back", "i'll come back", "come back to you", "i have referred",
    "i've referred", "passed it to", "passed to", "forwarded", "escalat",
    "i am not able", "i'm not able", "i cannot", "i can't", "not the right person",
    "before i can", "could you tell me", "can you tell me", "i need", "please send",
    "please confirm", "would you", "which ", "what ", "i do not have", "i don't have",
    "i am not going to", "i'm not going to", "not yet able",
)

QUESTION_RE = re.compile(r"\?")


@dataclass
class SafetyResult:
    score: float                                    # 0..1
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    placeholders: list[str] = field(default_factory=list)
    invented_identifiers: list[str] = field(default_factory=list)
    overpromises: list[str] = field(default_factory=list)
    deferral: str = "ok"                            # ok | under | over


def find_placeholders(text: str) -> list[str]:
    out: list[str] = []
    for pat in PLACEHOLDER_PATTERNS:
        out.extend(m.group(0) for m in pat.finditer(text or ""))
    # "[1]" style footnotes and smileys are not placeholders
    return [p for p in out if not re.fullmatch(r"\[\d+\]", p)]


def identifiers(text: str) -> set[str]:
    return {m.group(0).upper().replace("-", "") for m in IDENTIFIER_RE.finditer(text or "")}


def find_invented_identifiers(reply: str, sources: list[str], gold: str = "") -> list[str]:
    """Identifiers the reply asserts that appear in no source it could have known.

    An identifier matching the gold reply is accepted: the human used it too, so it is
    correct even though the model could not have derived it from the incoming email. An
    identifier matching *nothing* is a fabrication — and one that contradicts gold's
    (``RMA-7788`` where gold says ``RMA-2291``) is the expensive kind.

    Reference-dependent by design, so it is an offline evaluation check rather than
    something a production guardrail could run.
    """
    known: set[str] = set()
    for src in sources:
        known |= identifiers(src)
    known |= identifiers(gold)
    return sorted(identifiers(reply) - known)


def find_overpromises(text: str) -> list[str]:
    found: list[str] = []
    for pat, label in OVERPROMISE_PATTERNS:
        if pat.search(text or ""):
            found.append(label)
    return sorted(set(found))


def looks_deferring(text: str) -> bool:
    low = normalise(text or "")
    if QUESTION_RE.search(text or ""):
        return True
    return any(m in low for m in DEFERRAL_MARKERS)


def assess(
    reply_body: str,
    record: dict,
    sources: list[str],
    judge_hallucinations: list[str] | None = None,
) -> SafetyResult:
    """Rule-based sendability assessment. ``judge_hallucinations`` is optional LLM input."""
    res = SafetyResult(score=1.0)
    body = (reply_body or "").strip()

    if not body:
        res.score = 0.0
        res.hard_fails.append("empty reply")
        return res

    if len(body.split()) < 12:
        res.score -= 0.3
        res.warnings.append("reply is too short to send as-is")

    res.placeholders = find_placeholders(body)
    if res.placeholders:
        res.hard_fails.append(f"unfilled placeholder(s): {', '.join(res.placeholders[:3])}")

    gold_body = record.get("gold_reply", {}).get("body", "")
    res.invented_identifiers = find_invented_identifiers(body, sources, gold_body)
    if res.invented_identifiers:
        res.hard_fails.append(
            f"fabricated reference(s): {', '.join(res.invented_identifiers[:3])}"
        )

    if judge_hallucinations:
        res.hard_fails.extend(f"unsupported commitment: {h}" for h in judge_hallucinations[:3])

    res.overpromises = find_overpromises(body)
    if res.overpromises:
        res.score -= 0.15 * len(res.overpromises)
        res.warnings.append(f"over-promising language: {', '.join(res.overpromises)}")

    deferring = looks_deferring(body)
    if record.get("requires_human_review") and not deferring:
        res.deferral = "under"
        res.score -= 0.45
        res.warnings.append(
            "answered confidently on a case the human escalated, deferred, or refused"
        )
    elif not record.get("requires_human_review") and deferring and len(sentences(body)) <= 3:
        res.deferral = "over"
        res.score -= 0.20
        res.warnings.append("deferred a routine request that the human answered directly")

    if not _has_signoff(body):
        res.score -= 0.10
        res.warnings.append("no sign-off")

    res.score = round(max(0.0, min(1.0, res.score)), 4)
    if res.hard_fails:
        res.score = min(res.score, 0.25)
    return res


def _has_signoff(body: str) -> bool:
    tail = "\n".join(body.strip().splitlines()[-3:]).lower()
    return any(w in tail for w in ("regards", "warmly", "thanks", "best", "sincerely",
                                   "- dan", "-dan", "cheers", "yours"))
