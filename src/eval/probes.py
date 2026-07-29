"""Responses whose quality is known by construction — the metric's own test suite.

The hardest question about any evaluation metric is "how do you know the number means
anything?" Correlating with human ratings is one answer, but it needs human labels and it
only tells you about the range of quality your generator happens to produce.

Probes answer a different and cheaper question: *does the metric respond to the thing it
claims to measure, and not to other things?* We take the human's own reply and damage it
in one specific, known way at a time, then assert the metric notices that damage and
**only** that damage.

That last part is what makes this discriminant rather than decorative. Flipping the tone to
slang must drop the style component while leaving grounding untouched — a metric where
tone damage also moves the factual score is measuring one blurred thing, not five separate
ones. Corrupting a reference number must trip the hard-fail gate while leaving style alone.

Every probe runs with no API key, so these assertions execute in ``pytest`` on any machine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .constraints import hard_tokens

PROBE_NAMES = (
    "gold", "gold_slang", "generic", "gold_intent_inverted",
    "gold_fact_corrupted", "gold_placeholder", "gold_forbidden", "wrong_email",
)

GENERIC_REPLY = (
    "Hi,\n\nThanks for your email. I've received it and will look into this and get "
    "back to you as soon as I can.\n\nBest regards"
)

#: Action statements that contradict each intent family, used to invert intent while
#: leaving greeting and sign-off — and therefore the style score — intact.
INVERSION_BODIES = {
    "acts": (
        "I'm not going to be able to help with this one, and there's nothing further I "
        "can do here. I'd suggest looking at other options."
    ),
    "refuses": (
        "Yes, absolutely — I've gone ahead and approved this in full and actioned it on "
        "your account today. It is all done and there is nothing further you need to do."
    ),
    "withholds": (
        "Yes, absolutely — I've gone ahead and approved this in full and actioned it on "
        "your account today. It is all done and there is nothing further you need to do."
    ),
    "informs": (
        "I'm not going to be able to help with this one, and there's nothing further I "
        "can do here. I'd suggest looking at other options."
    ),
}

SLANG_MAP = [
    (r"\bThank you\b", "cheers"), (r"\bThanks\b", "cheers"),
    (r"\bI am\b", "im"), (r"\bI have\b", "ive"), (r"\bI will\b", "ill"),
    (r"\bapologise\b", "soz"), (r"\bapologize\b", "soz"),
    (r"\bas soon as possible\b", "asap"), (r"\bhowever\b", "but tbh"),
    (r"\bapproximately\b", "like"), (r"\bplease\b", "pls"),
    (r"\bKind regards\b", "laters"), (r"\bWarmly\b", "laters"),
]


@dataclass
class Probe:
    name: str
    reply: str
    record_id: str
    note: str


def _split_greeting_body_signoff(body: str) -> tuple[str, str, str]:
    """Split into ``(greeting, middle, signoff)``. Greeting is ``""`` when there isn't one.

    Assuming line 0 is always a greeting is wrong for the terse persona, whose replies
    routinely open with substance — "Confirmed for 17 April. I'll keep it off the floor."
    Treating that as a greeting made the slang probe delete facts and the inversion probe
    keep the original action, so both probes reported metric faults that were their own.
    """
    from .style import greeting_form

    lines = body.split("\n")
    if not lines:
        return "", "", ""

    first = lines[0].strip()
    has_greeting = bool(first) and greeting_form(first) != "none" and len(first) <= 60
    start = 1 if has_greeting else 0
    greeting = lines[0] if has_greeting else ""

    # Sign-off = the trailing block after the last blank line.
    tail_start = len(lines)
    for i in range(len(lines) - 1, start, -1):
        if not lines[i].strip():
            tail_start = i + 1
            break
    signoff = "\n".join(lines[tail_start:])
    middle = "\n".join(lines[start:tail_start]).strip()
    return greeting, middle, signoff


def make_slang(body: str, must_include: list[str] | None = None) -> str:
    """Wreck the register while provably preserving every fact.

    The first version of this probe applied slang substitutions blindly and quietly
    corrupted the facts — ``I have`` -> ``ive`` broke the constraint "I have refunded the
    duplicate charge today", so grounding fell along with style and the probe no longer
    isolated anything. It looked like a metric bug and was a probe bug.

    Now each substitution is applied only if every required constraint still checks out
    afterwards, so any grounding drop this probe produces is a genuine metric fault.
    """
    from .constraints import check_constraint

    must_include = must_include or []
    _, middle, _ = _split_greeting_body_signoff(body)

    def intact(text: str) -> bool:
        return all(check_constraint(c, text).satisfied for c in must_include)

    def wrap(mid: str) -> str:
        return f"hey!!\n\n{mid}\n\nlaters"

    if not intact(wrap(middle)):
        # The frame itself costs a fact (a constraint living in the greeting or sign-off).
        # Keep the reply whole and only swap the register markers around it.
        return f"hey!!\n\n{body}\n\nlaters"

    out = middle
    for pat, repl in SLANG_MAP:
        candidate = re.sub(pat, repl, out, flags=re.IGNORECASE)
        if candidate != out and intact(wrap(candidate)):
            out = candidate

    punctuated = out.replace(". ", "!! ")
    if intact(wrap(punctuated)):
        out = punctuated

    return wrap(out)


def corrupt_fact(body: str, must_include: list[str] | None = None) -> tuple[str, str | None]:
    """Change one identifier or figure, leaving everything else identical.

    Preference is given to figures the record actually *requires*. Corrupting an incidental
    number the constraints never mention is not a test of anything — the reply is still
    correct on every fact it owes, and a metric that failed it would be wrong to.
    """
    required_tokens: list[str] = []
    for phrase in must_include or []:
        required_tokens.extend(hard_tokens(phrase))

    # Single-character figures are unusable as corruption targets: "1" occurs inside other
    # numbers and repeats across a date list, so a first-occurrence replace changes
    # something unrelated and leaves the constraint satisfied elsewhere.
    candidates = [t for t in hard_tokens(body) if t in required_tokens and len(t) >= 2]
    if not candidates:
        # No figure in this reply is one the record actually requires. Corrupting an
        # incidental number proves nothing: the reply would still state every fact it
        # owes, and a metric that failed it would be the thing in error.
        return body, None

    for tok in candidates:
        m = re.search(re.escape(tok.replace("$", r"$")), body, re.IGNORECASE)
        if not m:
            m = re.search(r"\b" + re.escape(tok.lstrip("#$")) + r"\b", body)
        if not m:
            continue
        original = m.group(0)
        corrupted = re.sub(r"\d", lambda d: str((int(d.group(0)) + 4) % 10), original)
        if corrupted == original:
            continue
        return body.replace(original, corrupted, 1), f"{original} -> {corrupted}"
    return body, None


def build_probes(record: dict, other_record: dict | None = None) -> list[Probe]:
    """Every probe for one dataset record."""
    from .intent import INTENT_FAMILIES

    gold = record["gold_reply"]["body"]
    rid = record["id"]
    probes = [
        Probe("gold", gold, rid, "the human's own reply — the practical ceiling"),
        Probe("gold_slang", make_slang(gold, record.get("must_include")), rid,
              "same facts, wrong register — style must drop, grounding must not"),
        Probe("generic", GENERIC_REPLY, rid,
              "fluent, polite, says nothing — the reply a weak system defaults to"),
    ]

    greeting, _, signoff = _split_greeting_body_signoff(gold)
    family = INTENT_FAMILIES.get(record["intent_label"], "informs")
    inverted = f"{greeting}\n\n{INVERSION_BODIES[family]}\n\n{signoff}"
    probes.append(Probe("gold_intent_inverted", inverted, rid,
                        "opposite action, same voice — intent must collapse"))

    corrupted, change = corrupt_fact(gold, record.get("must_include"))
    if change:
        probes.append(Probe("gold_fact_corrupted", corrupted, rid,
                            f"one figure altered ({change}) — must hard-fail"))

    lines = gold.split("\n")
    with_ph = "\n".join(lines[:1] + ["", "As discussed, [CUSTOMER NAME], here is the update."]
                        + lines[1:])
    probes.append(Probe("gold_placeholder", with_ph, rid,
                        "unfilled placeholder — must hard-fail"))

    forbidden = record.get("must_not_include") or []
    if forbidden:
        claim = forbidden[0]
        injected = "\n".join(lines[:1] + ["", f"To confirm, {claim}."] + lines[1:])
        probes.append(Probe("gold_forbidden", injected, rid,
                            f"asserts a forbidden claim ('{claim}') — must hard-fail"))

    if other_record is not None:
        probes.append(Probe("wrong_email", other_record["gold_reply"]["body"], rid,
                            "a real, well-written reply to a different email — the floor"))

    return probes


# --------------------------------------------------------------------------- assertions


@dataclass
class ProbeCheck:
    name: str
    passed: bool
    detail: str


def check_expectations(scores: dict[str, "object"]) -> list[ProbeCheck]:
    """Assert the orderings that must hold if the metric measures what it claims.

    ``scores`` maps probe name -> ResponseScore for a single record.
    """
    checks: list[ProbeCheck] = []

    def comp(name: str, key: str | None = None) -> float | None:
        s = scores.get(name)
        if s is None:
            return None
        return s.components[key] if key else s.composite

    def add(name: str, passed: bool | None, detail: str) -> None:
        if passed is not None:
            checks.append(ProbeCheck(name, bool(passed), detail))

    g = comp("gold")

    if g is not None and comp("generic") is not None:
        add("gold > generic", g > comp("generic"),
            f"gold={g:.1f} generic={comp('generic'):.1f}")

    if g is not None and comp("wrong_email") is not None:
        add("gold > wrong_email", g > comp("wrong_email"),
            f"gold={g:.1f} wrong_email={comp('wrong_email'):.1f}")

    if scores.get("gold") is not None:
        add("gold is sendable", scores["gold"].sendable,
            f"hard_fails={scores['gold'].hard_fails}")

    for probe in ("gold_fact_corrupted", "gold_placeholder", "gold_forbidden"):
        s = scores.get(probe)
        if s is not None:
            add(f"{probe} hard-fails", not s.sendable,
                f"composite={s.composite:.1f} fails={s.hard_fails}")

    # Discriminant: style damage must not leak into the grounding score.
    if scores.get("gold_slang") is not None and scores.get("gold") is not None:
        add("slang drops style",
            comp("gold_slang", "style") < comp("gold", "style"),
            f"style {comp('gold','style'):.2f} -> {comp('gold_slang','style'):.2f}")
        add("slang preserves grounding",
            comp("gold_slang", "grounding") >= comp("gold", "grounding") - 0.01,
            f"grounding {comp('gold','grounding'):.2f} -> "
            f"{comp('gold_slang','grounding'):.2f}")

    # Only meaningful where the classifier read the human's own reply correctly. Where it
    # did not, there is no credit left to collapse and this would be re-testing classifier
    # accuracy, which is measured and reported separately.
    if (scores.get("gold_intent_inverted") is not None and scores.get("gold") is not None
            and comp("gold", "intent") >= 0.6):
        add("inversion collapses intent",
            comp("gold_intent_inverted", "intent") < comp("gold", "intent"),
            f"intent {comp('gold','intent'):.2f} -> "
            f"{comp('gold_intent_inverted','intent'):.2f}")

    if scores.get("generic") is not None:
        add("generic fails grounding", comp("generic", "grounding") < 0.34,
            f"grounding={comp('generic','grounding'):.2f}")

    return checks
