"""Checking whether a reply states a required fact — or asserts a forbidden one.

Naive substring matching gets this badly wrong in both directions:

* **False negative.** The constraint is ``"48-hour turnaround"`` and the reply says
  "we'll have it back to you within two business days". Same fact, no shared substring.
* **False positive.** The forbidden claim is ``"full refund"`` and the reply says
  "I'm not able to offer a full refund". The phrase is present; the claim is *denied*.
  Counting that as a violation would punish exactly the reply we want.

The fix for the second case is **polarity matching** rather than blanket negation
rejection, because plenty of required facts are themselves negative. When the constraint
is ``"cannot authorise a full refund"``, a reply saying "I'm not able to authorise a full
refund" *satisfies* it — both are negative, so the polarities agree. A reply saying "I've
authorised a full refund" does not. So we compare the polarity of the constraint against
the polarity of the sentence we matched it to, and require them to agree.

Numbers and identifiers are treated as non-negotiable: if a constraint contains ``#4821``
or ``$1,250``, a reply that omits or alters it has not satisfied the constraint no matter
how similar the surrounding prose is. This is what stops a fluent, confident,
factually-wrong reply from scoring well.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Words that flip an assertion. Checked in a window *before* the matched span.
# Contractions are expanded before this is consulted, so "can't" arrives as "can not".
# Kept deliberately tight. "instead" and "rather" were tried here and removed: they signal
# contrast, not negation, so "what I can do instead is run the export" was being read as a
# refusal to run the export.
NEGATORS = {
    "not", "no", "never", "cannot", "unable", "without",
    "neither", "nor", "none", "unwilling", "decline", "declined",
}

# Expanded before tokenising so "can't" and "cannot" compare equal to "can not".
CONTRACTIONS = [
    ("cannot", "can not"), ("can't", "can not"), ("won't", "will not"),
    ("shan't", "shall not"), ("n't", " not"),
    ("'ve", " have"), ("'ll", " will"), ("'re", " are"), ("'m", " am"),
    ("'d", " would"),
    ("'s", ""),  # possessive or "is" — either way the token carries no signal
]

STOPWORDS = {
    "the", "a", "an", "of", "to", "for", "in", "on", "at", "and", "or", "is", "are",
    "be", "will", "with", "that", "this", "we", "you", "your", "our", "it", "as", "by",
}

# Tokens that must survive verbatim: ids, money, percentages, dates, versions, counts.
_HARD_TOKEN = re.compile(r"(?:#\w+|\$[\d,.]+|\d[\d,.:/-]*%?|v\d[\w.]*)", re.IGNORECASE)
_WORD = re.compile(r"[a-z0-9#$%.'/-]+")

NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11",
    "twelve": "12", "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50",
    "hundred": "100",
}


@dataclass
class ConstraintResult:
    constraint: str
    satisfied: bool
    method: str          # how we decided: "exact" | "tokens" | "embedding" | "llm" | "absent"
    score: float         # best evidence strength in [0, 1]
    evidence: str = ""   # the sentence we matched against, for the report
    negated: bool = False
    missing_hard_tokens: list[str] = field(default_factory=list)
    #: True when the reply discusses this fact but states a *different* figure or
    #: identifier. Distinct from simply omitting it, and far more damaging — see
    #: :func:`detect_contradiction`.
    contradicted: bool = False
    contradicting_tokens: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- helpers


def normalise(text: str) -> str:
    text = text.lower().replace("’", "'").replace("–", "-").replace("—", "-")
    for src, dst in CONTRACTIONS:
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> list[str]:
    return [t.strip(".'") for t in _WORD.findall(normalise(text)) if t.strip(".'")]


def stem(token: str) -> str:
    """Deliberately crude suffix stripping.

    A full Porter stemmer would be marginally better, but this metric has to be auditable
    by whoever reads the report — a handful of visible rules beat an opaque dependency.

    The trailing-``e`` rule is what makes it *symmetric*, which matters more than being
    linguistically right: without it "saving" stems to "sav" while "save" stays "save",
    and the two never match. Both must land on the same string or the overlap score is
    silently wrong in one direction.
    """
    if len(token) <= 3 or not token.isalpha():
        return token

    # "-ies" plurals first: "replies" must become "reply", not "repli", or it never meets
    # the singular. Same for "supplies", "policies", "queries".
    if token.endswith("ies") and len(token) >= 5:
        token = token[:-3] + "y"

    # Two passes, so "payments" -> "payment" -> "pay" lands where "payment" does. A single
    # pass leaves the plural one suffix behind and the two never match.
    for _ in range(2):
        for suffix in ("ing", "ed", "es", "s", "ly", "ment"):
            if not token.endswith(suffix) or len(token) - len(suffix) < 3:
                continue
            # "address"/"addresses" must not become "addre" — stripping into a doubled
            # consonant is where this kind of stemmer starts inventing collisions.
            if suffix in ("s", "es") and token.endswith("ss"):
                continue
            base = token[: -len(suffix)]
            # "-ly" is an adverb ending, except when it is not: "apply", "reply",
            # "supply", "family". Requiring a longer base keeps those verbs intact.
            if suffix == "ly" and len(base) < 5:
                continue
            token = base
            if len(token) > 3 and token[-1] == token[-2] and token[-1] not in "sl":
                token = token[:-1]  # "stopping" -> "stopp" -> "stop"
            break
        else:
            break

    if len(token) > 3 and token.endswith("e"):
        token = token[:-1]
    return token


def content_tokens(text: str, stemmed: bool = False) -> list[str]:
    out = [t for t in tokens(text) if t not in STOPWORDS and len(t) > 1]
    return [stem(t) for t in out] if stemmed else out


def hard_tokens(text: str) -> list[str]:
    """Identifiers, money, percentages and bare numbers — these must be preserved exactly."""
    out = []
    for tok in _HARD_TOKEN.findall(normalise(text)):
        tok = tok.strip(".,")
        if tok and tok not in {"-", "."}:
            out.append(tok.replace(",", ""))
    return out


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _expand_numbers(toks: list[str]) -> set[str]:
    out = set(toks)
    for t in toks:
        if t in NUMBER_WORDS:
            out.add(NUMBER_WORDS[t])
    return out


def phrase_polarity(text: str) -> bool:
    """True when the phrase as a whole reads as a negation."""
    return any(t in NEGATORS for t in tokens(text))


#: Clause boundaries. A negation rarely reaches across one.
_CLAUSE_SPLIT = re.compile(r"\s*[-–—,;:]\s+|\s+[-–—]\s*")
#: Clauses opening with these inherit a negation from the clause before ("not X, Y or Z").
_CONTINUATIONS = {"or", "nor", "and"}


def clauses(sentence: str) -> list[str]:
    return [c for c in _CLAUSE_SPLIT.split(sentence) if c and c.strip()]


def sentence_polarity(sentence: str, target_tokens: set[str], window: int = 7) -> bool:
    """True when the target content is negated where it appears in ``sentence``.

    Scoping is *clause-level*, which matters more than it sounds. The terse persona in this
    dataset writes "Not mine either - scope questions sit with Nadia in Compliance": a
    refusal and a positive fact welded together. A sentence-level scan reads the whole
    thing as negative and marks a correct reply wrong. Splitting on clause boundaries keeps
    the "Not" attached to the clause it actually governs.

    Within the matched clause we scan the span the target occupies plus a short left
    window, so both "I am **not** able to offer a full refund" (negator before) and "this
    message did **not** come from Northwind" (negator inside the constraint) read as
    negative, while "a full refund is **not** something I can reverse later" does not.

    Known limitation: a negator scoping across a clause boundary other than the
    list-continuation case handled below — "I'm not the right person to name a custodian of
    records" is 15 tokens and a clause away. The optional LLM verifier tier is the backstop
    for those, and every report records which tier decided each constraint.
    """
    stems = {stem(t) for t in target_tokens}

    def matched(toks: list[str]) -> list[int]:
        return [i for i, t in enumerate(toks) if t in target_tokens or stem(t) in stems]

    parts = clauses(sentence)
    found_any = False

    for idx, clause in enumerate(parts):
        toks = tokens(clause)
        positions = matched(toks)
        if not positions:
            continue
        found_any = True

        # A constraint can straddle clauses — "Ops should own the facts, not the wording"
        # is one claim split across two. Checking every clause the constraint touches, and
        # treating the whole thing as negative if any of them is, keeps that claim's
        # polarity intact. Returning on the first clause with a partial match instead reads
        # "I can see the change, but I can't see who authorised it" as positive.
        lo = max(0, min(positions) - window)
        hi = max(positions) + 1
        if any(t in NEGATORS for t in toks[lo:hi]):
            return True

        # "we will not ship Friday, or approve the substitution" — a short trailing clause
        # is still governed by the previous clause's negator. Length-capped on purpose: a
        # long clause carries its own verb phrase and stands alone.
        if idx > 0 and toks and toks[0] in _CONTINUATIONS and len(toks) <= 6:
            if any(t in NEGATORS for t in tokens(parts[idx - 1])):
                return True

    return False if found_any else phrase_polarity(sentence)


# --------------------------------------------------------------------------- core check


def check_constraint(
    constraint: str,
    reply_body: str,
    embedder=None,
    token_threshold: float = 0.7,
    embed_threshold: float = 0.62,
) -> ConstraintResult:
    """Decide whether ``reply_body`` states ``constraint``.

    Tier 1 exact/near-exact phrase, tier 2 content-token overlap per sentence, tier 3
    embedding similarity per sentence. Any tier can only succeed if every hard token
    (id, amount, percentage, date) in the constraint is also present in the reply.
    """
    body_norm = normalise(reply_body)
    c_norm = normalise(constraint)
    c_negative = phrase_polarity(constraint)

    required_hard = hard_tokens(constraint)
    body_hard = set(_expand_numbers(hard_tokens(reply_body) + tokens(reply_body)))
    missing_hard = [h for h in required_hard if h not in body_hard]

    c_raw = set(content_tokens(constraint))
    c_stem = {stem(t) for t in _expand_numbers(list(c_raw))}
    if not c_stem:
        return ConstraintResult(constraint, False, "absent", 0.0, "", False, missing_hard)

    # Tier 1: the phrase is there verbatim (after contraction/whitespace normalisation).
    if c_norm in body_norm and not missing_hard:
        sent = _containing_sentence(reply_body, c_norm)
        s_negative = sentence_polarity(sent, c_raw)
        agree = s_negative == c_negative
        return ConstraintResult(constraint, agree, "exact", 1.0, sent, not agree, missing_hard)

    best = ConstraintResult(constraint, False, "absent", 0.0, "", False, missing_hard)

    # Tier 2: stemmed content-token overlap, sentence by sentence.
    for sent in sentences(reply_body):
        sent_stems = {stem(t) for t in _expand_numbers(content_tokens(sent))}
        overlap = len(c_stem & sent_stems) / len(c_stem)
        if overlap > best.score:
            s_negative = sentence_polarity(sent, c_raw)
            agree = s_negative == c_negative
            best = ConstraintResult(
                constraint,
                overlap >= token_threshold and not missing_hard and agree,
                "tokens", overlap, sent, not agree, missing_hard,
            )

    if best.satisfied:
        return best

    # Tier 3: paraphrase. "within two business days" == "48-hour turnaround".
    if embedder is not None and not missing_hard:
        try:
            sents = sentences(reply_body) or [reply_body]
            sims = embedder.similarity_matrix([constraint], sents)[0]
            top = int(max(range(len(sims)), key=lambda i: sims[i]))
            sim = float(sims[top])
            if sim > best.score:
                s_negative = sentence_polarity(sents[top], c_raw)
                agree = s_negative == c_negative
                best = ConstraintResult(
                    constraint, sim >= embed_threshold and agree,
                    "embedding", sim, sents[top], not agree, missing_hard,
                )
        except Exception:  # noqa: BLE001 - embeddings are an optimisation, never required
            pass

    if not best.satisfied and best.missing_hard_tokens:
        detect_contradiction(best, reply_body)
    return best


def detect_contradiction(res: ConstraintResult, reply_body: str = "",
                         min_topic_score: float = 0.5) -> ConstraintResult:
    """Separate "did not mention the figure" from "stated a different figure".

    Both leave a required constraint unsatisfied, and they are not remotely equally bad.
    A reply that says "I have applied a credit to your account" has merely omitted the
    amount — a human editor adds it in five seconds. A reply that says "$1,150" where the
    truth is "$1,250", or cites ``RMA-7788`` when the real reference is ``RMA-2291``, is
    confidently wrong: it reads as authoritative and sends the customer chasing something
    that does not exist.

    The test is that the reply addresses the topic (``min_topic_score``) *and* the matched
    sentence carries a figure or identifier that the constraint does not. Omission leaves
    the sentence with no competing value; contradiction supplies one.

    Contradictions are escalated to a hard fail by the scorer; omissions only cost
    coverage.
    """
    # A bare identifier constraint ("RMA-2291") shares no words with a reply that cites the
    # wrong one ("RMA-8891"), so there is no topic overlap to trigger the check below. Match
    # on the identifier's alphabetic prefix instead: same prefix, different number, is a
    # contradiction regardless of how the surrounding prose scored. This is the failure
    # retrieval actually produces — echoing a reference number from a similar past email.
    want = identifier_map(res.constraint)
    if want:
        got = identifier_map(reply_body or res.evidence)
        competing = sorted(
            f"{prefix.upper()}-{v}"
            for prefix, values in want.items()
            for v in got.get(prefix, set()) - values
        )
        if competing:
            res.contradicted = True
            res.contradicting_tokens = competing
            return res

    if res.score < min_topic_score or not res.evidence:
        return res

    expected = set(hard_tokens(res.constraint))
    present = set(hard_tokens(res.evidence))
    competing = sorted(present - expected)
    if competing:
        res.contradicted = True
        res.contradicting_tokens = competing
    return res


_IDENTIFIER = re.compile(r"\b([A-Za-z]{1,6})-?(\d{2,8})\b")


def identifier_map(text: str) -> dict[str, set[str]]:
    """``"RMA-2291 and INV-20455"`` -> ``{"rma": {"2291"}, "inv": {"20455"}}``."""
    out: dict[str, set[str]] = {}
    for prefix, value in _IDENTIFIER.findall(text or ""):
        out.setdefault(prefix.lower(), set()).add(value)
    return out


def _containing_sentence(text: str, needle_norm: str) -> str:
    for sent in sentences(text):
        if needle_norm in normalise(sent):
            return sent
    return text[:200]


def check_forbidden(phrase: str, reply_body: str, embedder=None) -> ConstraintResult:
    """Does the reply *assert* a forbidden claim?  ``satisfied=True`` means violated.

    Deliberately far stricter than :func:`check_constraint`, because the two error types
    are not symmetric. Missing a required fact costs one component point. A false
    violation trips the hard-fail gate and caps the entire response score at 40 — so this
    side is tuned for precision and the other for recall:

    * **Every** content token must be present, not 70% of them. "Pricing has increased on
      the reissued quote" must not fire on "reissued with the same pricing" merely because
      four words out of five line up.
    * The match must be **contiguous**. Scattering the tokens across an unrelated sentence
      ("I will confirm the formal start date once you have given notice") is not an
      assertion of "your start date is confirmed as".
    * The **embedding tier is off**. Paraphrase detection is exactly where a similarity
      score is least trustworthy, and a hard fail is too expensive to hang on 0.82 cosine.

    The cost of this is recall: a forbidden claim made entirely in paraphrase slips
    through. That is what the optional LLM verifier tier is for, and the report records
    which tier decided each constraint so a reader can tell the difference.
    """
    res = check_constraint(phrase, reply_body, embedder=None, token_threshold=1.0)

    if res.satisfied and res.method == "tokens":
        n_tokens = max(len(set(content_tokens(phrase))), 1)
        for sent in sentences(reply_body):
            toks = tokens(sent)
            stems = {stem(t) for t in content_tokens(phrase)}
            pos = [i for i, t in enumerate(toks) if stem(t) in stems]
            if len(pos) >= n_tokens and (max(pos) - min(pos) + 1) > n_tokens + 1:
                return ConstraintResult(phrase, False, "not-contiguous", res.score,
                                        res.evidence, res.negated, res.missing_hard_tokens)
    return res
