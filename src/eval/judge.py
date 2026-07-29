"""LLM-as-judge for the parts no rule can decide.

The rule-based components cover everything objectively checkable. What is left needs
reading comprehension: has this reply promised something the incoming email and the past
examples do not support? That is what the judge is for — plus one holistic "would you send
this?" read used for *validating the metric*, not for computing it.

## The biases, and what is done about each

**Self-preference.** A model scores its own output higher. Mitigated by defaulting the
judge to a different model family than the generator (`pick_judge_model`), and by printing
a warning and recording it in the report when they end up the same. Cross-*provider*
judging is stronger and available whenever a second API key exists; with a single provider
this is the best available, and the report says so rather than implying the result is
clean.

**Verbosity bias.** Judges reward longer answers. Neutralised structurally: length is
scored by a deterministic style feature the judge never sees, and the judge is told
explicitly to ignore length. It cannot inflate a component it does not compute.

**Position bias.** Avoided by not doing pairwise comparison at all — each reply is scored
alone against a rubric.

**Reference-free unreliability.** The judge always sees the human's actual reply. Asking
"is this good?" invites the model's own taste; asking "does this do what that one did"
is a far more constrained question.

**Run-to-run variance.** Three samples at temperature 0.3, median taken, and the spread is
reported per item. A judge that disagrees with itself is saying its score is unreliable,
and that belongs in the output rather than being averaged away.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from ..llm.base import BaseClient, LLMError, OutputParseError

JUDGE_SYSTEM = """You are auditing a draft email reply that an assistant produced for a
human to send. You can see the reply that the human actually sent for the same email.

Your job is NOT to decide which is better written. It is to answer three questions.

1. faithfulness (1-5): does the draft stay within what the incoming email and the human's
   reply support? 5 = every claim is supported. 1 = it invents facts, figures or policy.

2. hallucinated_commitments: list any promise, figure, date, reference number, policy or
   authority the draft asserts that is NOT supported by the incoming email or the human
   reply. Quote the exact phrase. This is the most important field. An empty list is the
   right answer when the draft invents nothing — do not pad it.

3. sendability (1-5): would the human who sent the reference reply send this draft?
   5 = send as-is. 4 = one small edit. 3 = several edits. 2 = substantial rewrite.
   1 = discard, or actively harmful to send.

Rules you must follow:
- IGNORE LENGTH. A shorter or longer draft is not better or worse for that reason. Length
  is measured separately.
- IGNORE writing polish. Judge substance and accuracy.
- A draft that correctly refuses, defers, or asks for missing information is CORRECT when
  the human reply did the same. Do not mark it down for not answering.
- Disagreeing with the human's wording is fine. Disagreeing with the human's decision is
  not.

Return JSON only:
{"faithfulness": 1-5, "hallucinated_commitments": ["exact quote", ...],
 "sendability": 1-5, "reason": "<one sentence, max 25 words>",
 "evidence": "<the single most telling quote from the draft, or empty>"}"""


@dataclass
class JudgeConfig:
    samples: int = 3
    temperature: float = 0.3
    max_tokens: int = 500


class Judge:
    """Reference-aware rubric judge with self-consistency sampling."""

    def __init__(self, client: BaseClient, config: JudgeConfig | None = None,
                 generator_model: str | None = None):
        self.client = client
        self.config = config or JudgeConfig()
        self.generator_model = generator_model
        self.calls = 0
        self.failures = 0

    @property
    def same_family_as_generator(self) -> bool:
        """True when judge and generator share a model family — a bias risk worth flagging."""
        if not self.generator_model:
            return False
        from ..llm.providers import model_family

        return model_family(self.client.model) == model_family(self.generator_model)

    def _prompt(self, reply: str, record: dict) -> str:
        inc = record["incoming"]
        return (
            f"INCOMING EMAIL\nFrom: {inc['from']}\nSubject: {inc['subject']}\n\n"
            f"{inc['body']}\n\n"
            f"=== REPLY THE HUMAN ACTUALLY SENT ===\n{record['gold_reply']['body']}\n\n"
            f"=== DRAFT TO AUDIT ===\n{reply}\n\n"
            "Return the JSON object only."
        )

    def evaluate(self, reply: str, record: dict) -> dict:
        """Median of ``samples`` judgements, with the spread reported."""
        if not (reply or "").strip():
            return {"faithfulness": 1, "sendability": 1, "hallucinated_commitments": [],
                    "reason": "empty reply", "evidence": "", "n_samples": 0,
                    "agreement": 1.0, "error": None}

        prompt = self._prompt(reply, record)
        faiths: list[int] = []
        sends: list[int] = []
        halluc: list[list[str]] = []
        reasons: list[str] = []
        evidences: list[str] = []
        error: str | None = None

        for i in range(self.config.samples):
            try:
                payload, _ = self.client.complete_json(
                    JUDGE_SYSTEM, prompt,
                    # Vary temperature slightly per sample so self-consistency measures
                    # real uncertainty rather than re-reading one cached response.
                    temperature=self.config.temperature + i * 0.05,
                    max_tokens=self.config.max_tokens,
                )
                self.calls += 1
            except (LLMError, OutputParseError) as exc:
                from ..llm.keys import redact

                self.failures += 1
                error = redact(str(exc))[:200]
                continue

            faiths.append(_clamp_1_5(payload.get("faithfulness")))
            sends.append(_clamp_1_5(payload.get("sendability")))
            halluc.append([str(h)[:160] for h in (payload.get("hallucinated_commitments") or [])])
            reasons.append(str(payload.get("reason", ""))[:200])
            evidences.append(str(payload.get("evidence", ""))[:200])

        if not sends:
            return {"faithfulness": None, "sendability": None,
                    "hallucinated_commitments": [], "reason": "judge unavailable",
                    "evidence": "", "n_samples": 0, "agreement": 0.0, "error": error}

        # Only report a hallucination the majority of samples independently saw. A single
        # sample crying wolf would otherwise trip the hard-fail gate on its own.
        threshold = max(1, len(halluc) // 2 + 1)
        counts: dict[str, int] = {}
        for sample in halluc:
            for item in set(sample):
                counts[item] = counts.get(item, 0) + 1
        agreed = sorted([h for h, c in counts.items() if c >= threshold])

        spread = (statistics.pstdev(sends) if len(sends) > 1 else 0.0)
        return {
            "faithfulness": int(statistics.median(faiths)) if faiths else None,
            "sendability": int(statistics.median(sends)),
            "hallucinated_commitments": agreed,
            "reason": reasons[0] if reasons else "",
            "evidence": evidences[0] if evidences else "",
            "n_samples": len(sends),
            "sendability_samples": sends,
            "agreement": round(1.0 - min(spread / 2.0, 1.0), 3),
            "judge_model": self.client.model,
            "same_family_as_generator": self.same_family_as_generator,
            "error": error,
        }


def _clamp_1_5(value) -> int:
    try:
        v = int(round(float(value)))
    except (TypeError, ValueError):
        return 3
    return max(1, min(5, v))
