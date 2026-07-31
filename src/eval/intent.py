"""Did the suggested reply *do* the same thing the human's reply did?

This is the question a similarity score cannot answer. A warm, fluent, well-written reply
that commits to a refund where the human escalated to legal is not 80% correct — it is
wrong in the only way that matters. Scoring the action separately from the prose is what
makes that visible.

Partial credit is graded by *family*, because the confusions are not equally bad.
Mistaking "ask for more detail" for "acknowledge and come back later" is a near miss: both
withhold action, and a human editing the draft fixes it in one line. Mistaking "decline"
for "commit" inverts the meaning and cannot be edited into correctness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from ..llm.base import BaseClient, LLMError

INTENT_FAMILIES: dict[str, str] = {
    "confirm_and_commit": "acts",
    "resolve_with_action": "acts",
    "apologize_and_remediate": "acts",
    "request_information": "withholds",
    "acknowledge_and_defer": "withholds",
    "escalate_or_handoff": "withholds",
    "decline_politely": "refuses",
    "negotiate_alternative": "refuses",
    "provide_information": "informs",
}

EXACT = 1.0
SAME_FAMILY = 0.6
CROSS_FAMILY = 0.15
INVERSION = 0.0

#: Family pairs where being wrong reverses the message rather than merely missing it.
INVERSIONS = {("acts", "refuses"), ("refuses", "acts")}


def intent_credit(predicted: str, gold: str) -> float:
    if not predicted:
        return 0.0
    if predicted == gold:
        return EXACT
    fp, fg = INTENT_FAMILIES.get(predicted), INTENT_FAMILIES.get(gold)
    if fp is None or fg is None:
        return 0.0
    if fp == fg:
        return SAME_FAMILY
    if (fp, fg) in INVERSIONS:
        return INVERSION
    return CROSS_FAMILY


@dataclass
class IntentResult:
    predicted: str
    gold: str
    credit: float
    method: str          # "llm" | "cues" | "centroid" | "none"
    confidence: float = 0.0
    reason: str = ""


# --------------------------------------------------------------------------- offline cues

# Embedding centroids over whole replies were tried first and reached only 21% on held-out
# gold replies (chance is 11%): sentence embeddings encode what an email is *about*, and
# every reply in a category is about the same thing. The action lives in a handful of
# verb phrases, so the offline classifier matches those directly.
#
# These patterns were written against the training split only. Held-out accuracy is
# reported in the evaluation output and in the README — treat it as the real number.

import re as _re

CUES: dict[str, list[tuple[str, float]]] = {
    "confirm_and_commit": [
        (r"\bconfirmed (?:for|as)\b", 3.0), (r"\bi confirm\b", 2.5),
        (r"\binvite sent\b", 3.0), (r"\bi have scheduled\b", 3.0),
        (r"\bbook both\b", 3.0), (r"^\s*yes[,.]", 2.0), (r"\bagreed\b", 1.5),
        (r"\bi will (?:issue|send|have|be your|review)\b", 1.5),
        (r"\bi(?:'ll| will) be your named contact\b", 3.0),
        (r"\backnowledged\b", 1.5), (r"\bi would be glad to\b", 2.0),
    ],
    "resolve_with_action": [
        (r"\bi(?:'ve| have) (?:re-?run|fixed|reverted|removed|swapped|shifted|changed|"
         r"applied|refunded|reissued|paused|revoked|re-?authorised|taken ownership|"
         r"added|generated|recorded|corrected)\b", 3.0),
        (r"\bhas been (?:reissued|updated|reverted|refunded|corrected)\b", 3.0),
        (r"\bsorted\b", 2.5), (r"\bwe'?ll move\b", 2.0),
        (r"\bis running now\b", 2.0), (r"\bnothing further needed\b", 2.0),
        (r"\bremoving them today\b", 2.0),
    ],
    "apologize_and_remediate": [
        (r"\bi (?:am|'m) (?:very |really )?sorry\b", 2.5),
        (r"\bi apologi[sz]e\b", 2.5), (r"\bour fault\b", 3.0),
        (r"\bthat'?s on me\b", 3.0), (r"\bit was our fault\b", 3.0),
        (r"\byou are (?:right|correct)\b", 2.0), (r"\bfair, that\b", 2.5),
        (r"\bshould not have happened\b", 2.0),
    ],
    "request_information": [
        (r"\bbefore i (?:can|answer|confirm)\b", 3.0),
        (r"\bcould you (?:tell|send|confirm)\b", 2.5),
        (r"\bi need (?:two|three|to know|the following)\b", 3.0),
        (r"\bplease send\b", 2.0), (r"\bi don'?t have enough\b", 3.0),
        (r"\bin order to (?:trace|pin|give)\b", 2.5),
        (r"\bwhat (?:the topic|he wants|you'?re seeing)\b", 2.0),
        (r"\bmissing three things\b", 3.0), (r"\bi need\b", 1.0),
    ],
    "escalate_or_handoff": [
        (r"\bpassed (?:it |your |the )?(?:straight )?to\b", 3.0),
        (r"\bi(?:'ve| have) (?:referred|forwarded)\b", 3.0),
        (r"\bnot (?:the right person|mine|my signature)\b", 3.0),
        (r"\bwrong person\b", 3.0), (r"\b(?:goes|sits) (?:to|with)\b", 2.5),
        (r"\bwill (?:contact|respond to) you directly\b", 2.0),
        (r"\blooping her in\b", 3.0), (r"\bwill be your point of contact\b", 2.0),
    ],
    "decline_politely": [
        (r"\bi(?:'m| am) not able to\b", 2.0), (r"\bi can'?(?:no)?t\b", 1.5),
        (r"\bno thanks\b", 3.0), (r"\bthanks,? but no\b", 3.0),
        (r"\bno from us\b", 3.0), (r"\bi'?m afraid i can'?t\b", 2.5),
        (r"\bwe will not\b", 2.0), (r"^\s*no\.", 3.0),
        (r"\bi won'?t be\b", 2.0), (r"\bnot looking to\b", 2.5),
        (r"\bunable to pay\b", 2.5), (r"\bi am unable to\b", 2.0),
    ],
    "negotiate_alternative": [
        (r"\bwhat i can (?:do|offer|support|put on the table)\b", 4.0),
        (r"\bwhat can i offer\b", 3.0), (r"\bi can offer\b", 3.0),
        (r"\boptions:\b", 3.5), (r"\bwould you consider\b", 3.0),
        (r"\binstead\b", 1.5), (r"\bwhat i can do instead\b", 4.0),
        (r"\bhalf agree\b", 3.0), (r"\bproposal:\b", 3.0),
        (r"\bi'?ll sign at\b", 3.0), (r"\byour call\b", 2.0),
    ],
    "acknowledge_and_defer": [
        (r"\bi(?:'ll| will) come back to you\b", 3.5),
        (r"\bcome back to you (?:by|with|next|personally)\b", 3.0),
        (r"\bi don'?t want to speculate\b", 3.5),
        (r"\bnot yet able\b", 3.0), (r"\bi can'?t tell you yet\b", 3.5),
        (r"\bi'?m not going to give you\b", 3.5),
        (r"\bi have(?:n'?t| not) (?:heard|read)\b", 3.0),
        (r"\bi(?:'ve| have) (?:asked|requested|pulled|referred)\b.{0,80}\bi'?ll\b", 2.0),
        (r"\bfirm answer\b", 2.5), (r"\bcan'?t commit\b", 3.0),
        (r"\byou'?ll have (?:the|it|a)\b", 2.0),
    ],
    "provide_information": [
        (r"\byou'?ll find it under\b", 3.0), (r"\bis retained for\b", 3.0),
        (r"\bthe limit applies\b", 2.5), (r"\bare supported\b", 2.0),
        (r"\bthere are \d+\b", 2.0), (r"\bwe (?:take|track|hold|provide)\b", 1.5),
        (r"\bthe role (?:does |is )\b", 2.5), (r"\boperates one week\b", 3.0),
        (r"\btwo approvers\b", 2.5), (r"\bgoing into q\d\b", 2.5),
        (r"\bevery other tuesday\b", 3.0), (r"\bworth knowing\b", 1.5),
    ],
}

_COMPILED = {k: [(_re.compile(p, _re.IGNORECASE | _re.MULTILINE), w) for p, w in v]
             for k, v in CUES.items()}


def cue_scores(body: str) -> dict[str, float]:
    scores = {k: 0.0 for k in CUES}
    for label, patterns in _COMPILED.items():
        for pat, weight in patterns:
            if pat.search(body):
                scores[label] += weight
    return scores


def classify_by_cues(body: str) -> tuple[str, float]:
    """Argmax over cue weights, with the two precedence rules that matter.

    A reply that refuses *and* counter-proposes is a negotiation, not a refusal — the
    counter-proposal is the substance. And an apology attached to a fix is remediation
    rather than a bare fix. Both distinctions are lost without an explicit rule because
    the losing label's cues are genuinely present.
    """
    if not (body or "").strip():
        return "", 0.0
    scores = cue_scores(body)

    if scores["negotiate_alternative"] >= 3.0 and scores["decline_politely"] >= 1.5:
        scores["negotiate_alternative"] += 2.0
    if scores["apologize_and_remediate"] >= 2.5 and scores["resolve_with_action"] >= 2.0:
        scores["apologize_and_remediate"] += 1.5

    best = max(scores, key=lambda k: scores[k])
    if scores[best] <= 0.0:
        return "", 0.0
    total = sum(scores.values()) or 1.0
    return best, round(scores[best] / total, 3)


CLASSIFY_SYSTEM = """You label the communicative act of a business email reply.

Choose exactly one label:
- confirm_and_commit: agrees and states a concrete commitment (a date, figure, or action)
- decline_politely: says no to what was asked
- request_information: withholds action and asks for missing information first
- provide_information: answers a factual question without committing to new work
- resolve_with_action: states a fix or action already taken or now underway
- negotiate_alternative: rejects the specific ask but counter-proposes something else
- acknowledge_and_defer: acknowledges and promises a substantive answer later
- escalate_or_handoff: routes the matter to another person or team
- apologize_and_remediate: apologises for a failure and offers a concrete remedy

Judge only what the reply DOES. Ignore tone, length, and quality.
If it does several things, pick the one the sender would consider the main outcome.

Return JSON only: {"intent": "<label>", "confidence": 0.0-1.0, "reason": "<8 words>"}"""


class IntentClassifier:
    """LLM classifier with an embedding nearest-centroid fallback.

    The fallback is not decoration: it keeps the whole evaluation runnable with no API key,
    and it gives a second opinion that is independent of the judge model, which matters
    when the generator and judge come from the same provider.
    """

    def __init__(self, client: BaseClient | None = None, train_records: list[dict] | None = None,
                 embedder=None):
        self.client = client
        self.embedder = embedder
        self._centroids: dict[str, list[float]] = {}
        self.llm_ok = 0
        self.llm_failures = 0
        self.failure_reasons: list[str] = []
        if train_records and embedder is not None:
            self._fit_centroids(train_records)

    def _record_failure(self, reason: str) -> None:
        from ..llm.keys import redact

        reason = redact(reason)[:200]
        if reason not in self.failure_reasons and len(self.failure_reasons) < 5:
            self.failure_reasons.append(reason)

    def stats(self) -> dict:
        total = self.llm_ok + self.llm_failures
        return {
            "llm_classified": self.llm_ok,
            "llm_failed": self.llm_failures,
            "llm_success_rate": round(self.llm_ok / total, 4) if total else None,
            "failure_reasons": self.failure_reasons,
        }

    def _fit_centroids(self, train_records: list[dict]) -> None:
        import numpy as np

        by_intent: dict[str, list[str]] = {}
        for rec in train_records:
            by_intent.setdefault(rec["intent_label"], []).append(rec["gold_reply"]["body"])
        for label, bodies in by_intent.items():
            vecs = self.embedder.encode(bodies)
            centroid = vecs.mean(axis=0)
            norm = float(np.linalg.norm(centroid))
            if norm > 1e-9:
                self._centroids[label] = (centroid / norm).tolist()

    def _centroid_predict(self, body: str) -> tuple[str, float]:
        import numpy as np

        if not self._centroids or not body.strip():
            return "", 0.0
        vec = self.embedder.encode([body])[0]
        labels = list(self._centroids)
        mat = np.array([self._centroids[l] for l in labels], dtype=np.float32)
        sims = mat @ vec
        best = int(sims.argmax())
        return labels[best], float(sims[best])

    def classify(self, reply_body: str, use_llm: bool = True) -> tuple[str, str, float, str]:
        """Return ``(label, method, confidence, reason)``."""
        if not (reply_body or "").strip():
            return "", "none", 0.0, "empty reply"

        if use_llm and self.client is not None:
            try:
                payload, _ = self.client.complete_json(
                    CLASSIFY_SYSTEM,
                    f"Reply to classify:\n\n{reply_body}\n\nReturn the JSON object only.",
                    temperature=0.0, max_tokens=200,
                )
                label = str(payload.get("intent", "")).strip()
                if label in INTENT_FAMILIES:
                    self.llm_ok += 1
                    return (label, "llm", float(payload.get("confidence", 0.5) or 0.5),
                            str(payload.get("reason", ""))[:120])
                self.llm_failures += 1
                self._record_failure(f"model returned unknown label {label!r}")
            except (LLMError, ValueError, json.JSONDecodeError) as exc:
                # Falling back silently once hid a total failure: a model that 400s on
                # every call left the run reporting "classified by <model>" while nothing
                # had actually been classified by it. Failures are counted and surfaced so
                # the report can state what was really used.
                self.llm_failures += 1
                self._record_failure(f"{type(exc).__name__}: {exc}")

        label, conf = classify_by_cues(reply_body)
        if label:
            return label, "cues", conf, "offline cue-phrase classifier"

        label, sim = self._centroid_predict(reply_body)
        return label, "centroid", sim, "nearest centroid over training replies"

    def score(self, reply_body: str, gold_intent: str, use_llm: bool = True) -> IntentResult:
        label, method, conf, reason = self.classify(reply_body, use_llm=use_llm)
        return IntentResult(label, gold_intent, intent_credit(label, gold_intent),
                            method, conf, reason)
