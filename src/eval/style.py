"""Does this reply sound like the person it is being written for?

Style is scored against the *persona's own distribution in the training set*, not against
a global notion of good writing. A 30-word bulleted reply is excellent from the operations
manager and wrong from the business manager, and a metric with one prose standard would
score the same text differently depending on nothing at all.

Every feature is a plain countable quantity. That is deliberate: style is the component
most tempting to hand to an LLM judge, and also the one where a judge's own preferences
(longer, warmer, more hedged) contaminate the result most badly.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass

CONTRACTION_RE = re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE)
BULLET_RE = re.compile(r"^\s*[-*•]\s+", re.MULTILINE)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

FORMAL_MARKERS = (
    "kind regards", "dear ", "i am not able", "i would be grateful", "please note",
    "further to", "with regard to", "i am unable", "kindly", "should you",
    "i would like to", "in order to", "please find",
)
CASUAL_MARKERS = (
    "thanks", "happy to", "no worries", "cheers", "let me know", "sorry", "i'd",
    "we'll", "that's", "worth knowing", "fair point", "good luck",
)

GREETING_PATTERNS = {
    "hi": re.compile(r"^\s*hi\b", re.IGNORECASE),
    "dear": re.compile(r"^\s*dear\b", re.IGNORECASE),
    "hello": re.compile(r"^\s*hello\b", re.IGNORECASE),
    "dash": re.compile(r"^\s*[A-Z][a-z]+\s*[-–—]\s*$", re.MULTILINE),
    "none": re.compile(r"^(?!\s*(hi|dear|hello)\b)", re.IGNORECASE),
}

#: Which numeric features are compared as z-scores against the persona distribution.
NUMERIC_FEATURES = (
    "word_count", "mean_sentence_words", "contraction_rate", "bullet_lines",
    "exclamations", "formal_markers", "casual_markers", "second_person_rate",
    "paragraphs",
)


def greeting_form(text: str) -> str:
    head = text.strip().split("\n", 1)[0]
    for name, pat in GREETING_PATTERNS.items():
        if name == "none":
            continue
        if pat.search(head):
            return name
    if re.match(r"^\s*[A-Z][a-z]+\s*[-–—]", head):
        return "dash"
    return "none"


def features(text: str) -> dict[str, float]:
    """Countable style properties of a reply body."""
    body = (text or "").strip()
    words = re.findall(r"[A-Za-z']+", body)
    n_words = len(words)
    sents = [s for s in SENT_SPLIT.split(body) if s.strip()]
    lower = body.lower()

    return {
        "word_count": float(n_words),
        "mean_sentence_words": float(n_words / len(sents)) if sents else 0.0,
        "contraction_rate": float(len(CONTRACTION_RE.findall(body)) / max(n_words, 1) * 100),
        "bullet_lines": float(len(BULLET_RE.findall(body))),
        "exclamations": float(body.count("!")),
        "formal_markers": float(sum(lower.count(m) for m in FORMAL_MARKERS)),
        "casual_markers": float(sum(lower.count(m) for m in CASUAL_MARKERS)),
        "second_person_rate": float(
            len(re.findall(r"\b(you|your|you're|yours)\b", lower)) / max(n_words, 1) * 100
        ),
        "paragraphs": float(len([p for p in body.split("\n\n") if p.strip()])),
    }


@dataclass
class StyleProfile:
    """Mean/stdev of each feature for one persona, plus its habitual greeting and sign-off."""

    persona: str
    means: dict[str, float]
    stdevs: dict[str, float]
    modal_greeting: str
    signoff_tokens: set[str]
    n: int

    @classmethod
    def fit(cls, persona: str, replies: list[str], signoff: str) -> "StyleProfile":
        feats = [features(r) for r in replies]
        means, stdevs = {}, {}
        for key in NUMERIC_FEATURES:
            vals = [f[key] for f in feats]
            means[key] = statistics.fmean(vals) if vals else 0.0
            # Floor the spread: a feature with near-zero variance in a small sample would
            # otherwise turn any deviation at all into an enormous z-score.
            sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
            stdevs[key] = max(sd, max(abs(means[key]) * 0.15, 0.5))

        greetings = [greeting_form(r) for r in replies]
        modal = max(set(greetings), key=greetings.count) if greetings else "none"
        tokens = {t.lower() for t in re.findall(r"[A-Za-z]+", signoff) if len(t) > 2}
        return cls(persona, means, stdevs, modal, tokens, len(replies))

    # -- scoring ------------------------------------------------------------------

    def score(self, text: str) -> tuple[float, dict]:
        """Return ``(score in [0,1], detail)`` for how well ``text`` fits this persona."""
        if not (text or "").strip():
            return 0.0, {"reason": "empty reply"}

        f = features(text)
        zs = {}
        for key in NUMERIC_FEATURES:
            zs[key] = abs(f[key] - self.means[key]) / self.stdevs[key]

        # Mean |z| mapped through a soft curve: |z|=0 -> 1.0, |z|=1 -> 0.67, |z|=3 -> 0.25.
        mean_z = statistics.fmean(zs.values())
        numeric = 1.0 / (1.0 + mean_z / 2.0)

        greet = greeting_form(text)
        greeting_match = 1.0 if greet == self.modal_greeting else 0.0

        tail = "\n".join(text.strip().splitlines()[-4:]).lower()
        tail_tokens = {t for t in re.findall(r"[a-z]+", tail) if len(t) > 2}
        overlap = len(self.signoff_tokens & tail_tokens) / max(len(self.signoff_tokens), 1)
        signoff_match = min(overlap * 1.5, 1.0)

        # 60% distributional fit, 40% the two discrete tells a reader notices immediately.
        score = 0.60 * numeric + 0.20 * greeting_match + 0.20 * signoff_match
        detail = {
            "mean_abs_z": round(mean_z, 3),
            "numeric_fit": round(numeric, 3),
            "greeting_expected": self.modal_greeting,
            "greeting_found": greet,
            "signoff_overlap": round(overlap, 3),
            "worst_features": sorted(
                ((k, round(v, 2)) for k, v in zs.items()), key=lambda kv: -kv[1]
            )[:3],
        }
        return round(min(max(score, 0.0), 1.0), 4), detail


def fit_profiles(train_records: list[dict], personas: dict) -> dict[str, StyleProfile]:
    """One profile per persona, fitted on that persona's training replies only."""
    by_persona: dict[str, list[str]] = {}
    for rec in train_records:
        by_persona.setdefault(rec["persona"], []).append(rec["gold_reply"]["body"])
    return {
        key: StyleProfile.fit(key, replies, personas[key].signoff)
        for key, replies in by_persona.items()
    }
