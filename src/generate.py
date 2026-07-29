"""Turning an incoming email into a suggested reply.

Four variants ship, and all four are evaluated. That is not padding — the ablation *is*
the evidence that grounding in the dataset does anything, and it doubles as a sensitivity
test for the metric. A metric that cannot separate a zero-shot reply from a retrieval-
grounded one is not measuring what it claims to.

    zero_shot          no dataset at all
    static_fewshot     three fixed exemplars, same for every email
    rag_fewshot        three exemplars retrieved per email          <- the system
    rag_plus_stylecard rag_fewshot + an explicit persona style card

**Why prompting + retrieval rather than fine-tuning.** With 77 training examples,
fine-tuning memorises rather than generalises, and it welds the system to one vendor's
tuning API. Retrieval adapts the moment a new reply is filed, stays portable across the
three providers here, and — the part that matters most for this brief — is *auditable*:
every generated reply records which past emails shaped it, so a bad output can be traced
to the exemplars that produced it. Fine-tuning wins on style-matching and per-call cost at
a few thousand examples; that is the point where the choice flips, and it is not this
dataset.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from .llm.base import BaseClient, LLMError, OutputParseError
from .retrieval import Retriever

VARIANTS = ("zero_shot", "static_fewshot", "rag_fewshot", "rag_plus_stylecard")
DEFAULT_VARIANT = "rag_fewshot"


@dataclass
class Suggestion:
    subject: str
    body: str
    confidence: float = 0.5
    needs_human_review: bool = False
    unresolved_questions: list[str] = field(default_factory=list)

    # provenance — what produced this, so a score can be traced back
    variant: str = DEFAULT_VARIANT
    exemplar_ids: list[str] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


SYSTEM_BASE = """You are drafting a reply on behalf of {name}, {role} at {company}.

The reply will be shown to {first} as a suggestion. They will send it, edit it, or discard
it. Write what they would actually send.

Rules:
- Only state facts supported by the incoming email or the past examples. If a detail is not
  available, ask for it rather than inventing it.
- Never invent reference numbers, dates, prices, names, or policy. A confident wrong number
  is far worse than an admission that you need to check.
- Do not commit to anything the sender has no authority to commit to. Refunds, contractual
  terms, legal positions and disciplinary outcomes are escalations, not answers.
- Never leave placeholders such as [NAME] or TODO. If you would need one, you do not have
  enough information — set needs_human_review and say what is missing.
- Match the voice of the past examples, including greeting and sign-off.

Return a single JSON object and nothing else:
{{
  "subject": "Re: ...",
  "body": "the full reply including greeting and sign-off",
  "confidence": 0.0-1.0,
  "needs_human_review": true|false,
  "unresolved_questions": ["anything you had to guess at"]
}}"""

STYLE_CARD = """
Voice of {name} ({role}) — follow this closely:
{style_card}
Sign off exactly like this:
{signoff}
"""

#: Fixed exemplars for the static_fewshot baseline. Generic on purpose: this variant exists
#: to isolate the value of *retrieving* exemplars from the value of having exemplars at all.
STATIC_EXEMPLAR_IDS = ("sup-002", "sch-001", "bil-001")


def format_email(record: dict) -> str:
    inc = record["incoming"]
    return (f"From: {inc['from']}\nSubject: {inc['subject']}\n\n{inc['body']}")


def format_exemplar(record: dict, n: int) -> str:
    return (
        f"--- Past example {n} ---\n"
        f"INCOMING:\n{format_email(record)}\n\n"
        f"REPLY THAT WAS SENT:\nSubject: {record['gold_reply']['subject']}\n\n"
        f"{record['gold_reply']['body']}\n"
    )


class ReplyGenerator:
    """Builds the prompt, calls the model, parses and repairs the result."""

    def __init__(
        self,
        client: BaseClient,
        retriever: Retriever | None = None,
        personas: dict | None = None,
        k: int = 3,
    ):
        self.client = client
        self.retriever = retriever
        self.k = k
        if personas is None:
            from data.schema import PERSONAS

            personas = PERSONAS
        self.personas = personas
        self._by_id = {r["id"]: r for r in (retriever.pool if retriever else [])}

    # -- prompt assembly ----------------------------------------------------------

    def _system(self, persona_key: str, variant: str) -> str:
        p = self.personas[persona_key]
        system = SYSTEM_BASE.format(
            name=p.name, role=p.role, company=p.company, first=p.name.split()[0]
        )
        if variant == "rag_plus_stylecard":
            system += "\n" + STYLE_CARD.format(
                name=p.name, role=p.role, style_card=p.style_card, signoff=p.signoff
            )
        return system

    def _exemplars(self, incoming: dict, variant: str, category: str | None,
                   exclude_ids: set[str]) -> list[dict]:
        if variant == "zero_shot" or self.retriever is None:
            return []
        if variant == "static_fewshot":
            return [self._by_id[i] for i in STATIC_EXEMPLAR_IDS
                    if i in self._by_id and i not in exclude_ids]
        hits = self.retriever.retrieve(incoming, k=self.k, category=category,
                                       exclude_ids=exclude_ids)
        return [h.record for h in hits]

    def _user(self, incoming: dict, exemplars: list[dict]) -> str:
        parts: list[str] = []
        if exemplars:
            parts.append(
                "Here are past emails of this kind and the replies that were actually "
                "sent. Use them for tone, structure, and house policy — not as text to "
                "copy.\n"
            )
            parts.extend(format_exemplar(r, i + 1) for i, r in enumerate(exemplars))
        parts.append(
            "--- Now reply to this new email ---\n"
            f"{format_email({'incoming': incoming})}\n\n"
            "Return the JSON object only."
        )
        return "\n".join(parts)

    # -- generation ---------------------------------------------------------------

    def generate(
        self,
        incoming: dict,
        persona_key: str,
        variant: str = DEFAULT_VARIANT,
        category: str | None = None,
        exclude_ids: set[str] | None = None,
        temperature: float = 0.3,
    ) -> Suggestion:
        if variant not in VARIANTS:
            raise ValueError(f"Unknown variant {variant!r}. Choose from {VARIANTS}.")

        exemplars = self._exemplars(incoming, variant, category, exclude_ids or set())
        system = self._system(persona_key, variant)
        user = self._user(incoming, exemplars)

        try:
            payload, resp = self.client.complete_json(
                system, user, temperature=temperature, max_tokens=900
            )
        except (LLMError, OutputParseError) as exc:
            from .llm.keys import redact

            # A failed generation is a real, reportable outcome — it scores zero rather
            # than vanishing from the denominator and quietly flattering the average.
            return Suggestion(
                subject="", body="", confidence=0.0, needs_human_review=True,
                variant=variant, exemplar_ids=[r["id"] for r in exemplars],
                model=getattr(self.client, "_model", "") or "",
                provider=self.client.name, error=redact(str(exc))[:300],
            )

        return Suggestion(
            subject=str(payload.get("subject") or "").strip(),
            body=str(payload.get("body") or "").strip(),
            confidence=_as_float(payload.get("confidence"), 0.5),
            needs_human_review=bool(payload.get("needs_human_review", False)),
            unresolved_questions=[str(q) for q in (payload.get("unresolved_questions") or [])
                                  if str(q).strip()],
            variant=variant,
            exemplar_ids=[r["id"] for r in exemplars],
            model=resp.model,
            provider=resp.provider,
        )

    def generate_for_record(self, record: dict, variant: str = DEFAULT_VARIANT,
                            temperature: float = 0.3) -> Suggestion:
        """Generate for a dataset record, never letting it retrieve itself."""
        return self.generate(
            record["incoming"],
            persona_key=record["persona"],
            variant=variant,
            category=record.get("category"),
            exclude_ids={record["id"]},
            temperature=temperature,
        )


def _as_float(value: Any, default: float) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, f))
