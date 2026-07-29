"""The composite accuracy metric.

## What "accurate" means here

Exact match is the wrong target. Ask five competent people to answer the same email and
you get five different replies, all correct. So the operational definition throughout is:

> **A suggested reply is accurate to the degree that the person it was drafted for would
> send it with at most minor edits.**

That decomposes into five things that can be measured separately, and separating them is
the point — a single number tells you a reply is mediocre; these five tell you *why*, and
they fail in different enough ways that averaging them alone would hide the failures that
matter.

| # | Dimension | Weight | Question |
|---|-----------|--------|----------|
| 1 | Factual grounding | 30 | Does it state every fact it owes, and no forbidden claim? |
| 2 | Intent match | 25 | Does it *do* what the human's reply did? |
| 3 | Semantic similarity | 15 | Does it say roughly what the human said? |
| 4 | Style fit | 15 | Does it sound like this specific person? |
| 5 | Sendability | 15 | Placeholders, fabricated references, over-promises, deferral |

### Why these weights

Grounding and intent carry 55% between them because they are the two things a human editor
cannot fix cheaply. Wrong tone is a 20-second edit. A fabricated commitment is a phone call
to a customer. Similarity to the gold reply is deliberately *only* 15%: it is the most
obvious metric and the most misleading one, since a different-but-equally-good reply scores
badly on it. It is included because it catches replies that are on a completely different
topic, which the other components can miss.

### The hard-fail gate

Weighted averaging has a specific pathology: a reply that is fluent, on-topic, perfectly
styled and states one catastrophic falsehood scores about 85. That number is a lie. So any
of

* asserting a `must_not_include` claim,
* an unfilled placeholder,
* a fabricated reference number,
* an empty or failed generation,

caps the composite at 40 and marks the response **not sendable**. This is why the headline
is three numbers rather than one: the mean says how good replies are on average, the
sendable rate says how often the system is safe, and the edit-free rate says how often it
is actually useful. A system can move any one of them without moving the others.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from ..embeddings import Embedder, get_embedder
from .constraints import ConstraintResult, check_constraint, check_forbidden, content_tokens
from .intent import IntentClassifier, IntentResult
from .safety import SafetyResult, assess

WEIGHTS = {
    "grounding": 30.0,
    "intent": 25.0,
    "similarity": 15.0,
    "style": 15.0,
    "sendability": 15.0,
}

#: Composite ceiling applied when a hard fail fires.
HARD_FAIL_CAP = 40.0
#: At or above this, a reply is treated as sendable without edits.
EDIT_FREE_THRESHOLD = 85.0


# --------------------------------------------------------------------------- ROUGE-L


def lcs_length(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(cur[j], prev[j + 1]))
        prev = cur
    return prev[-1]


def rouge_l(candidate: str, reference: str) -> float:
    """F1 over the longest common subsequence of content tokens."""
    c, r = content_tokens(candidate, stemmed=True), content_tokens(reference, stemmed=True)
    if not c or not r:
        return 0.0
    lcs = lcs_length(c, r)
    if lcs == 0:
        return 0.0
    prec, rec = lcs / len(c), lcs / len(r)
    return 2 * prec * rec / (prec + rec)


# --------------------------------------------------------------------------- result


@dataclass
class ResponseScore:
    record_id: str
    variant: str
    composite: float
    components: dict[str, float]            # each 0..1
    weighted: dict[str, float]              # each 0..weight
    sendable: bool
    hard_fails: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    grounding_detail: list[dict] = field(default_factory=list)
    intent_detail: dict = field(default_factory=dict)
    similarity_detail: dict = field(default_factory=dict)
    style_detail: dict = field(default_factory=dict)
    safety_detail: dict = field(default_factory=dict)
    judge_detail: dict = field(default_factory=dict)

    reply_body: str = ""
    category: str = ""
    difficulty: str = ""
    persona: str = ""

    @property
    def edit_free(self) -> bool:
        return self.sendable and self.composite >= EDIT_FREE_THRESHOLD

    def explain(self) -> str:
        """One-paragraph plain-English account of why this response scored as it did."""
        bits: list[str] = []
        if self.hard_fails:
            bits.append("NOT SENDABLE — " + "; ".join(self.hard_fails))
        miss = [d["constraint"] for d in self.grounding_detail
                if not d["satisfied"] and d["kind"] == "required"]
        if miss:
            bits.append(f"missing required fact(s): {'; '.join(miss[:3])}")
        i = self.intent_detail
        if i and i.get("credit", 1.0) < 1.0:
            bits.append(f"acted as '{i.get('predicted') or 'unclear'}' where the human "
                        f"'{i.get('gold')}' ({int(i.get('credit', 0) * 100)}% credit)")
        if self.components.get("style", 1.0) < 0.6:
            sd = self.style_detail
            bits.append(f"style drifts from {self.persona} "
                        f"(greeting '{sd.get('greeting_found')}' vs expected "
                        f"'{sd.get('greeting_expected')}')")
        for w in self.warnings[:2]:
            bits.append(w)
        if not bits:
            bits.append("matches the human reply on facts, action, tone and sendability")
        return ". ".join(b[0].upper() + b[1:] for b in bits) + "."

    def to_dict(self) -> dict:
        d = asdict(self)
        d["edit_free"] = self.edit_free
        d["explanation"] = self.explain()
        return d


# --------------------------------------------------------------------------- scorer


class Scorer:
    """Scores one generated reply against one dataset record."""

    def __init__(
        self,
        style_profiles: dict,
        intent_classifier: IntentClassifier,
        embedder: Embedder | None = None,
        judge=None,
        use_llm_intent: bool = True,
    ):
        self.style_profiles = style_profiles
        self.intent_classifier = intent_classifier
        self.embedder = embedder or get_embedder()
        self.judge = judge
        self.use_llm_intent = use_llm_intent

    # -- components ---------------------------------------------------------------

    def _grounding(self, reply: str, record: dict) -> tuple[float, list[dict], list[str]]:
        details: list[dict] = []
        hard_fails: list[str] = []

        required = record.get("must_include", [])
        satisfied = 0
        for phrase in required:
            res: ConstraintResult = check_constraint(phrase, reply, embedder=self.embedder)
            satisfied += int(res.satisfied)
            details.append(_constraint_dict(res, "required"))
            # Omitting a figure costs coverage. Stating a *different* one is a hard fail:
            # a confidently wrong reference number is worse than an obvious gap, because
            # nothing about the reply signals that it needs checking.
            if res.contradicted:
                hard_fails.append(
                    f"contradicts required fact '{phrase}' "
                    f"(reply states {', '.join(res.contradicting_tokens[:3])})"
                )

        for phrase in record.get("must_not_include", []):
            res = check_forbidden(phrase, reply)
            details.append(_constraint_dict(res, "forbidden"))
            if res.satisfied:
                hard_fails.append(f"asserts forbidden claim: '{phrase}'")

        coverage = satisfied / len(required) if required else 1.0
        return coverage, details, hard_fails

    def _similarity(self, reply: str, gold: str) -> tuple[float, dict]:
        if not reply.strip():
            return 0.0, {"embedding": 0.0, "rouge_l": 0.0}
        emb = float(self.embedder.similarity(reply, gold))
        emb = max(0.0, min(1.0, emb))
        rl = rouge_l(reply, gold)
        # Embeddings carry the weight; ROUGE-L is retained as an independent, lexical
        # cross-check whose correlation with human ratings is reported honestly.
        blended = 0.75 * emb + 0.25 * rl
        return blended, {"embedding": round(emb, 4), "rouge_l": round(rl, 4)}

    # -- main ---------------------------------------------------------------------

    def score(
        self,
        reply_body: str,
        record: dict,
        variant: str = "rag_fewshot",
        sources: list[str] | None = None,
        generation_error: str | None = None,
    ) -> ResponseScore:
        gold = record["gold_reply"]["body"]
        reply = (reply_body or "").strip()

        sources = sources or []
        sources = sources + [record["incoming"]["subject"], record["incoming"]["body"],
                             record.get("thread_context", "")]

        # 1. grounding
        coverage, grounding_detail, ground_fails = self._grounding(reply, record)

        # optional LLM judge — hallucination detection and a holistic read
        judge_detail: dict = {}
        judge_halluc: list[str] = []
        if self.judge is not None and reply:
            judge_detail = self.judge.evaluate(reply, record)
            judge_halluc = judge_detail.get("hallucinated_commitments", []) or []

        # 5. sendability (needs judge output, so computed before the composite)
        safety: SafetyResult = assess(reply, record, sources, judge_halluc)

        # 2. intent
        intent: IntentResult = self.intent_classifier.score(
            reply, record["intent_label"], use_llm=self.use_llm_intent
        )

        # 3. similarity
        sim, sim_detail = self._similarity(reply, gold)

        # 4. style
        profile = self.style_profiles.get(record["persona"])
        style, style_detail = profile.score(reply) if profile else (0.0, {})

        components = {
            "grounding": round(coverage, 4),
            "intent": round(intent.credit, 4),
            "similarity": round(sim, 4),
            "style": round(style, 4),
            "sendability": round(safety.score, 4),
        }
        weighted = {k: round(v * WEIGHTS[k], 3) for k, v in components.items()}
        composite = round(sum(weighted.values()), 2)

        hard_fails = list(ground_fails) + list(safety.hard_fails)
        if generation_error:
            hard_fails.append(f"generation failed: {generation_error}")
        sendable = not hard_fails
        if hard_fails:
            composite = min(composite, HARD_FAIL_CAP)

        return ResponseScore(
            record_id=record["id"],
            variant=variant,
            composite=composite,
            components=components,
            weighted=weighted,
            sendable=sendable,
            hard_fails=hard_fails,
            warnings=safety.warnings,
            grounding_detail=grounding_detail,
            intent_detail={
                "predicted": intent.predicted, "gold": intent.gold,
                "credit": intent.credit, "method": intent.method,
                "confidence": round(intent.confidence, 3), "reason": intent.reason,
            },
            similarity_detail=sim_detail,
            style_detail=style_detail,
            safety_detail={
                "deferral": safety.deferral,
                "placeholders": safety.placeholders,
                "invented_identifiers": safety.invented_identifiers,
                "overpromises": safety.overpromises,
            },
            judge_detail=judge_detail,
            reply_body=reply,
            category=record.get("category", ""),
            difficulty=record.get("difficulty", ""),
            persona=record.get("persona", ""),
        )


def _constraint_dict(res: ConstraintResult, kind: str) -> dict:
    return {
        "kind": kind,
        "constraint": res.constraint,
        "satisfied": bool(res.satisfied),
        "method": res.method,
        "score": round(res.score, 3),
        "negated": res.negated,
        "missing_hard_tokens": res.missing_hard_tokens,
        "contradicted": res.contradicted,
        "contradicting_tokens": res.contradicting_tokens,
        "evidence": (res.evidence or "")[:160],
    }


# --------------------------------------------------------------------------- aggregate


def aggregate(scores: list[ResponseScore]) -> dict:
    """System-level numbers. Never a single figure — see the module docstring."""
    if not scores:
        return {}
    n = len(scores)
    comp = [s.composite for s in scores]
    out = {
        "n": n,
        "composite_mean": round(sum(comp) / n, 2),
        "composite_median": round(sorted(comp)[n // 2], 2),
        "sendable_rate": round(sum(s.sendable for s in scores) / n, 4),
        "edit_free_rate": round(sum(s.edit_free for s in scores) / n, 4),
        "hard_fail_count": sum(len(s.hard_fails) > 0 for s in scores),
        "components": {
            k: round(sum(s.components[k] for s in scores) / n, 4) for k in WEIGHTS
        },
    }
    for field_name in ("category", "difficulty", "persona"):
        buckets: dict[str, list[float]] = {}
        for s in scores:
            buckets.setdefault(getattr(s, field_name), []).append(s.composite)
        out[f"by_{field_name}"] = {
            k: {"n": len(v), "mean": round(sum(v) / len(v), 2)}
            for k, v in sorted(buckets.items())
        }
    return out
