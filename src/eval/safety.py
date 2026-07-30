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

# Subject-dropped forms matter: the terse persona writes "Cannot commit", "Will evaluate",
# "Confirming attendance" with no leading pronoun. Requiring "I cannot" made the detector
# blind to exactly the replies that persona produces.
DEFERRAL_MARKERS = (
    "come back to you", "referred", "passed it to", "passed to", "forwarded", "escalat",
    "not able", "cannot", "can't", "not the right person", "not mine",
    "before i can", "before i answer", "could you tell me", "can you tell me",
    "i need", "please send", "please confirm", "would you", "which ", "what ",
    "do not have", "don't have", "not going to", "not yet able", "will evaluate",
    "will review", "will look into", "will get back", "respond by", "revert by",
    "let me know", "once i have", "in order to", "need to know", "hold the",
)

#: Gold intents whose defining move is to withhold action. If the human's reply belongs
#: here, a draft that answers confidently is under-delivering.
WITHHOLDING_INTENTS = frozenset(
    {"request_information", "acknowledge_and_defer", "escalate_or_handoff"})

QUESTION_RE = re.compile(r"\?")

# Language that signals the reply actually *did* something or committed to doing it.
# Used to tell "asked a clarifying question on the way to an answer" apart from "asked a
# question instead of answering", which is the difference that matters.
ACTION_MARKERS = (
    re.compile(r"\b(?:i|we)(?:'ve| have) (?:re-?run|fixed|reverted|removed|swapped|"
               r"shifted|changed|applied|refunded|reissued|paused|revoked|re-?authorised|"
               r"added|scheduled|arranged|booked|processed|updated|raised|issued|"
               r"credited|taken|moved|recorded|corrected|approved|shipped)\b",
               re.IGNORECASE),
    re.compile(r"\bhas been (?:reissued|updated|reverted|refunded|corrected|applied|"
               r"scheduled|arranged|raised|added|approved|processed)\b", re.IGNORECASE),
    # Subject optional throughout — "Will issue the order form" is a commitment.
    re.compile(r"\b(?:i |we )?(?:will|'ll) (?:issue|send|arrange|reissue|apply|process|"
               r"refund|book|schedule|sign|pay|move|be your|make the change|keep|"
               r"confirm|have (?:it|them|a)|proceed)\b", re.IGNORECASE),
    re.compile(r"\b(?:i |we )?can (?:agree|offer|confirm|arrange|support|put)\b",
               re.IGNORECASE),
    re.compile(r"\b(?:confirming|confirmed for|acknowledged|agreed)\b", re.IGNORECASE),
    re.compile(r"\b(?:invite sent|sorted|ships today|book both|rota updated|no charge|"
               r"send the paperwork|go ahead)\b", re.IGNORECASE),
)


def has_action_or_commitment(text: str) -> bool:
    """Does the reply state something done, or commit to a specific thing?"""
    return any(p.search(text or "") for p in ACTION_MARKERS)


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
    acts = has_action_or_commitment(body)

    # The trigger is the *gold intent*, not `requires_human_review`. Those are different
    # propositions and conflating them was a design error: "a human should review this"
    # does not mean "the reply must withhold". Several records are flagged for review and
    # answered by a confirmation — penalising a draft for confirming them was backwards,
    # and it was hitting the two best drafts in the rated sample.
    gold_withholds = record.get("intent_label") in WITHHOLDING_INTENTS

    if gold_withholds and not deferring:
        res.deferral = "under"
        res.score -= 0.45
        res.warnings.append(
            "answered confidently on a case the human escalated, deferred, or refused"
        )
    elif not gold_withholds and deferring and not acts:
        # Over-deferral used to be gated on the reply being <= 3 sentences, which was
        # simply wrong: length has nothing to do with whether deferring was appropriate,
        # and a draft that hedged at *length* — asking for detail the sender already gave,
        # promising to look into something the human had already fixed — collected full
        # marks. Validation against human ratings caught it: this component was the only
        # one that anti-correlated with whether a person would send the draft.
        #
        # The test is now whether the reply does anything at all. Asking a question on the
        # way to an answer is fine; asking one *instead* of the answer is the failure.
        res.deferral = "over"
        res.score -= 0.35
        res.warnings.append(
            "asked for information or promised follow-up where the human answered, "
            "decided, or acted"
        )

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
