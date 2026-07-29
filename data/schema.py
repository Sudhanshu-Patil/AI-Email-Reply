"""Dataset schema: the taxonomies every record is validated against.

The two design decisions that matter here:

1. ``intent_label`` — a small, closed speech-act taxonomy. "Did the suggested reply *do*
   the same thing the human's reply did?" is the single most important question for a
   suggested reply, and it is only answerable if the gold reply carries an action label.

2. ``must_include`` / ``must_not_include`` — the facts a correct reply has to state, and
   the claims it must never make. These turn factual grounding from a vague judge call
   into something checkable, and they are what the hard-fail gate keys off.
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------- taxonomies

INTENTS: dict[str, str] = {
    "confirm_and_commit": "Agrees to the request and states a concrete commitment (date, number, action).",
    "decline_politely": "Says no to the request, with or without a reason.",
    "request_information": "Withholds action and asks for missing information first.",
    "provide_information": "Answers a factual question without committing to new work.",
    "resolve_with_action": "States a fix or action already taken or now underway.",
    "negotiate_alternative": "Rejects the specific ask but counter-proposes something else.",
    "acknowledge_and_defer": "Acknowledges receipt and promises a substantive answer later.",
    "escalate_or_handoff": "Routes the request to another person or team.",
    "apologize_and_remediate": "Apologises for a failure and offers a concrete remedy.",
}

CATEGORIES = (
    "support", "escalation", "outreach",       # -> cs_rep
    "scheduling", "internal", "vendor",        # -> ops_mgr
    "billing", "sales", "recruiting",          # -> business_mgr
)

DIFFICULTIES = ("normal", "hard")


@dataclass(frozen=True)
class Persona:
    key: str
    name: str
    role: str
    company: str
    style_card: str
    signoff: str


PERSONAS: dict[str, Persona] = {
    "cs_rep": Persona(
        key="cs_rep",
        name="Priya Raman",
        role="Support Lead",
        company="Northwind Systems",
        style_card=(
            "Warm and personable. Opens by thanking the sender or acknowledging their "
            "frustration by name. Uses full sentences and contractions. Explains the "
            "reasoning behind an answer rather than just stating it. Medium length "
            "(60-130 words). Greets with 'Hi <FirstName>,'. Never uses bullet points "
            "unless listing steps the customer must take."
        ),
        signoff="Warmly,\nPriya\nSupport Lead, Northwind Systems",
    ),
    "ops_mgr": Persona(
        key="ops_mgr",
        name="Dan Whitfield",
        role="Operations Manager",
        company="Northwind Systems",
        style_card=(
            "Terse and operational. Front-loads the decision in the first sentence. "
            "Uses short bullet points for anything with more than two moving parts. "
            "Rarely uses pleasantries beyond a one-word acknowledgement. Short "
            "(25-70 words). Greets with '<FirstName> -'. Signs off with just his name."
        ),
        signoff="- Dan",
    ),
    "business_mgr": Persona(
        key="business_mgr",
        name="Margaret Osei",
        role="Business Manager",
        company="Northwind Systems",
        style_card=(
            "Formal and precise; handles billing, quotes and hiring administration. "
            "Complete sentences, no contractions, no exclamation marks. States figures, "
            "dates and reference numbers explicitly. Medium length (55-120 words). "
            "Greets with 'Dear <Name>,' or 'Hello <Name>,'. Always closes with her full "
            "signature block."
        ),
        signoff="Kind regards,\nMargaret Osei\nBusiness Manager, Northwind Systems",
    ),
}

CATEGORY_PERSONA: dict[str, str] = {
    "support": "cs_rep", "escalation": "cs_rep", "outreach": "cs_rep",
    "scheduling": "ops_mgr", "internal": "ops_mgr", "vendor": "ops_mgr",
    "billing": "business_mgr", "sales": "business_mgr", "recruiting": "business_mgr",
}

REQUIRED_FIELDS = (
    "id", "category", "persona", "incoming", "gold_reply", "intent_label",
    "must_include", "must_not_include", "difficulty", "requires_human_review",
)


def validate_record(rec: dict) -> list[str]:
    """Return a list of human-readable problems with ``rec``. Empty list means valid."""
    problems: list[str] = []
    rid = rec.get("id", "<no id>")

    for field in REQUIRED_FIELDS:
        if field not in rec:
            problems.append(f"{rid}: missing field '{field}'")
    if problems:
        return problems

    if rec["category"] not in CATEGORIES:
        problems.append(f"{rid}: unknown category '{rec['category']}'")
    if rec["persona"] not in PERSONAS:
        problems.append(f"{rid}: unknown persona '{rec['persona']}'")
    if rec["intent_label"] not in INTENTS:
        problems.append(f"{rid}: unknown intent_label '{rec['intent_label']}'")
    if rec["difficulty"] not in DIFFICULTIES:
        problems.append(f"{rid}: unknown difficulty '{rec['difficulty']}'")

    expected_persona = CATEGORY_PERSONA.get(rec["category"])
    if expected_persona and rec["persona"] != expected_persona:
        problems.append(
            f"{rid}: category '{rec['category']}' should be answered by "
            f"'{expected_persona}', not '{rec['persona']}'"
        )

    for side in ("incoming", "gold_reply"):
        block = rec.get(side)
        if not isinstance(block, dict):
            problems.append(f"{rid}: '{side}' must be an object")
            continue
        for sub in ("subject", "body"):
            if not block.get(sub, "").strip():
                problems.append(f"{rid}: '{side}.{sub}' is empty")
    if isinstance(rec.get("incoming"), dict) and not rec["incoming"].get("from", "").strip():
        problems.append(f"{rid}: 'incoming.from' is empty")

    for key in ("must_include", "must_not_include"):
        if not isinstance(rec[key], list):
            problems.append(f"{rid}: '{key}' must be a list")
        elif any(not isinstance(x, str) or not x.strip() for x in rec[key]):
            problems.append(f"{rid}: '{key}' contains an empty entry")

    if not rec["must_include"]:
        problems.append(f"{rid}: 'must_include' is empty — every reply owes at least one fact")

    # A constraint is only meaningful if the human's own reply satisfies it. We check with
    # the *same* matcher used for scoring, so the dataset cannot contain a constraint that
    # the evaluator would mark the gold reply as failing.
    from src.eval.constraints import check_constraint, check_forbidden

    body = rec.get("gold_reply", {}).get("body", "")
    for phrase in rec.get("must_include", []):
        if not check_constraint(phrase, body).satisfied:
            problems.append(
                f"{rid}: gold reply does not satisfy its own must_include {phrase!r} "
                f"— fix the constraint or the gold reply"
            )
    for phrase in rec.get("must_not_include", []):
        if check_forbidden(phrase, body).satisfied:
            problems.append(f"{rid}: gold reply asserts its own must_not_include {phrase!r}")

    if not isinstance(rec["requires_human_review"], bool):
        problems.append(f"{rid}: 'requires_human_review' must be a boolean")

    return problems
