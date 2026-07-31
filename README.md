# Suggested email replies, and a way to tell whether they're any good

Given an incoming email, this system drafts a reply grounded in a corpus of past
email/reply pairs — and then measures how good that draft actually is, on five dimensions,
with evidence that the measurement tracks real quality.

The evaluation is the substance here. A generator is easy; knowing whether its output is
worth sending is the hard part, so most of this README is about the metric and how it was
validated.

```bash
pip install -r requirements.txt
python cli.py setup --provider groq      # paste a key; verifies it and lists live models
python cli.py run-all --provider groq    # generate, score, validate, write reports
```

No API key? Everything runs offline:

```bash
python -m pytest                         # 61 tests, no key needed
python cli.py validate-metric            # the metric's own validation suite
python cli.py run-all --provider mock
```

---

## 1. What "accurate" means for a suggested reply

Exact match is the wrong target. Ask five competent people to answer the same email and
you get five different replies, all correct. Any metric that rewards reproducing one
specific wording is measuring conformity, not quality.

The operational definition used throughout:

> **A suggested reply is accurate to the degree that the person it was drafted for would
> send it with at most minor edits.**

"Minor edits" is the load-bearing phrase. It makes the target *editability*, not identity,
and it decomposes into five things that can be measured separately:

| # | Dimension | Weight | The question it answers |
|---|-----------|-------:|-------------------------|
| 1 | **Factual grounding** | 30 | Does it state every fact it owes, and assert no forbidden claim? |
| 2 | **Intent match** | 25 | Does it *do* what the human's reply did? |
| 3 | **Semantic similarity** | 15 | Does it say roughly what the human said? |
| 4 | **Style fit** | 15 | Does it sound like *this specific person*? |
| 5 | **Sendability** | 15 | Placeholders, fabricated references, over-promises, correct deferral |

### Why these weights

Grounding and intent carry 55% between them because they are the two failures a human
editor *cannot* fix cheaply. Wrong tone is a twenty-second edit. A fabricated commitment is
a phone call to a customer.

Similarity to the gold reply is deliberately only 15%, even though it is the most obvious
thing to measure. A different-but-equally-good reply scores badly on it, so weighting it
heavily would punish exactly the diversity that makes this problem interesting. It earns
its place by catching replies that are on a completely different topic — a failure the
other four can miss.

### The hard-fail gate

Weighted averaging has a specific pathology: a reply that is fluent, on-topic, perfectly
styled, and states one catastrophic falsehood scores about 85. That number is a lie.

So any of these caps the composite at 40 and marks the response **not sendable**:

- asserting a `must_not_include` claim ("I've processed your full refund")
- **contradicting** a required figure — stating `RMA-7788` where the truth is `RMA-2291`
- an unfilled placeholder (`[CUSTOMER NAME]`)
- a fabricated reference number that appears in no source the model could have seen
- an empty or failed generation

Note the distinction between *contradicting* a figure and *omitting* one. Omission costs
coverage points — an editor adds the number in seconds. Contradiction is confidently wrong,
reads as authoritative, and sends the customer chasing something that does not exist. Only
the second is a hard fail. Getting this distinction right required separating the two cases
in the matcher; the probe suite caught that it was missing.

### Three headline numbers, never one

- **Composite mean** — how good replies are on average
- **Sendable rate** — how often the system is *safe* (no hard fail)
- **Edit-free rate** — how often it is actually *useful* (≥85 and sendable)

They move independently. A system that hedges everything scores well on sendable and
terribly on edit-free; that's a real and important failure mode, and one number would hide
it.

---

## 2. How I know the metric measures anything

This is the part that matters most, so it gets four independent lines of evidence. Each can
fail in a way the others cannot see.

### (a) Discriminant probes — the metric has a test suite

Take the human's own reply and damage it in exactly one known way. Assert the metric
notices that damage **and only that damage**.

| Probe | What it should show |
|---|---|
| `gold` | the human's own reply — the practical ceiling |
| `gold_slang` | identical facts, wrecked register — style must drop, grounding must *not* |
| `gold_fact_corrupted` | one required figure altered — must hard-fail |
| `gold_forbidden` | asserts a forbidden claim — must hard-fail |
| `gold_placeholder` | `[CUSTOMER NAME]` inserted — must hard-fail |
| `gold_intent_inverted` | opposite action, same voice — intent must collapse |
| `wrong_email` | a real, well-written reply to a *different* email — the floor |
| `generic` | "Thanks, I'll get back to you" — fluent and contentless |

The slang probe is the discriminant one. If wrecking the tone also moves the factual score,
the metric is measuring one blurred thing rather than five separable ones. To make that
assertion meaningful the probe *verifies* it preserved every required fact before applying
each substitution — an earlier version silently corrupted facts (`I have` → `ive` broke a
constraint) and reported a metric bug that was its own.

**Result: 270/270 assertions hold (100%)**, and the ordering comes out as constructed:

```
gold 92.0  >  gold_slang 80.7  >  fact_corrupted / forbidden / placeholder 40.0
           >  wrong_email 33.6  >  intent_inverted 28.8  ≈  generic 28.3
```

These run with no API key, in `pytest`, so "the evaluation works" is a checkable claim.

### (b) Agreement with human ratings

Hand-assigned 1–5 sendability labels on generated replies, correlated against the
composite with **Spearman ρ and Kendall τ-b** — rank statistics, because the claim being
tested is an ordering claim and the 1–5 scale is not linear.

The sample is stratified across variants and difficulty and shuffled with a fixed seed, and
the rating template deliberately **omits the metric's score** so a label cannot be anchored
by the number it is meant to validate (`python cli.py export-ratings`).

**The result, on 24 rated replies:**

| | Spearman ρ vs human rating |
|---|---:|
| **Composite** | **0.257** (95% CI −0.16 to 0.60) |
| grounding | **+0.509** |
| style | +0.296 |
| similarity | +0.169 |
| intent | +0.073 |
| sendability | −0.177 |

**This is a weak result and I am not going to dress it up.** The composite's confidence
interval crosses zero: at n=24 this does not demonstrate that the composite tracks human
judgement. Four things are worth saying about it.

**The component structure behaves as designed — in one respect.** Grounding, the
heaviest-weighted component and the one I argued matters most, is comfortably the best
predictor of whether I would send a draft. That is the metric's central design claim, and
it survives.

**Intent is a much weaker predictor than its 25% weight assumes** (ρ = +0.073). Notably it
got *weaker* when I fixed the classifier: an earlier run scored +0.165 while silently
falling back to a 20.7%-accurate offline classifier, and replacing that with a real LLM
classifier (116/116, zero fallbacks) dropped it to +0.073. So the earlier, higher number
was partly noise. The substantive reading is that drafts frequently get the *action* right
— they decline when the human declined — and still fail on what they actually say. Knowing
a reply declined is not much evidence that it declined *well*. On this data the weighting
looks wrong, but see the note below on why I have not rebalanced it.

**`sendability` anti-correlates, and chasing that was a mistake worth recording.** I made
three attempts to fix it against these same 24 labels — removing a nonsensical
length gate, broadening deferral detection for the subject-dropping terse persona, and
replacing `requires_human_review` with the gold intent family as the trigger. All three
were structurally justified and I kept them. **None moved the correlation** (−0.139 →
−0.194 → −0.177). That pattern is the signature of fitting noise, and it is why the
guidance against tuning on your validation labels exists.

The actual explanation is that **rank correlation is the wrong instrument for this
component.** Sendability is a rare-event *safety* detector — placeholders, fabricated
references, forbidden claims. Across the 24 rated drafts it fired on 3, with **zero
placeholders and zero fabricated references**; 14 of 24 sit at exactly 1.00. A near-constant
cannot correlate with anything, and the residual variance is noise whose sign means
nothing. Its correct validation is the probe suite — detection rate on inputs that *do*
contain those failures — where it catches **100%** of forbidden-claim, placeholder and
fabricated-reference probes.

That distinction generalises: a component that measures how *good* a reply is should be
validated by correlation; a component that measures whether a reply is *dangerous* should
be validated by detection rate on known-bad inputs. Applying one test to both was my error,
not the component's.

**Honest limitation: one annotator, no inter-annotator agreement**, and the sendability
rules were revised three times while looking at these labels — so its numbers here are no
longer independent evidence. A second rater and a fresh label set are the single
highest-value addition to this project.

### (e) An independent model's opinion

A reference-aware LLM judge reads the incoming email, the human's reply, and the draft, and
answers "would the person who wrote that reference reply send this?" on a 1–5 scale. If the
rule-based composite measures anything real, that should correlate with it — and the judge
shares none of the composite's machinery, which is what makes it independent evidence
rather than a restatement.

**The judge is deliberately kept out of the scored ablation.** Groq's free tier caps daily
tokens per model, and three self-consistency samples over four variants exceeds it. Judging
only *some* variants would be worse than judging none: the unjudged ones could not incur
judge-derived hard fails, so they would score higher purely for escaping scrutiny. A
comparison has to apply the same instrument to everything it compares. So the ablation is
scored by the rule-based metric alone, and the judge runs separately on the main variant:

```bash
python cli.py judge-agreement --variant rag_fewshot
```

**Result** (`llama-3.1-8b-instant` judging `openai/gpt-oss-120b`, 29 responses, 3 samples
each): Spearman ρ vs composite = **0.339**, judge mean sendability **2.76/5**, unsupported
commitments flagged in 12/29 responses, mean self-consistency **0.724**.

The judge's ρ (0.339) and my own (0.257) land in a similar place from two raters sharing no
machinery, and the judge's mean rating (2.76/5) is close to mine (2.33/5). Two independent
assessors agreeing both about the *level* and about how loosely it tracks the composite is
more informative than either number alone: it says the weak correlation is a property of
the metric, not of one idiosyncratic rater.

Self-consistency of 0.724 is itself a finding — the judge disagrees with itself across
samples often enough that single-sample judging would be noticeably noisy, which is exactly
why the median of three is taken and the spread is reported per item.

Judge biases are handled structurally rather than assumed away:

- **Self-preference** — the judge defaults to a different model *family* than the generator
  (`pick_judge_model`), and the report records the pair and warns when they coincide.
  Cross-*provider* judging is stronger and available with a second key.
- **Verbosity bias** — length is scored by a deterministic style feature the judge never
  sees, and the judge is instructed to ignore length. It cannot inflate what it doesn't
  compute.
- **Position bias** — avoided entirely by scoring each reply alone against a rubric rather
  than pairwise.
- **Reference-free unreliability** — the judge always sees the human's actual reply. "Does
  this do what that one did" is a far more constrained question than "is this good".
- **Run-to-run variance** — 3 samples, median taken, spread reported per item. A judge that
  disagrees with itself is telling you its score is unreliable, and that belongs in the
  output.
- **Single alarmist sample** — a hallucination is only recorded if the majority of samples
  independently flag it, so one sample crying wolf cannot trip the hard-fail gate.

### What the system actually scored

29 held-out emails, generated with `openai/gpt-oss-120b` on Groq:

29 held-out emails, generated with `openai/gpt-oss-120b`, intent classified by
`llama-3.3-70b-versatile` (116/116, zero fallbacks):

| Variant | Composite (95% CI) | Sendable | Edit-free | Grounding |
|---|---:|---:|---:|---:|
| `zero_shot` | 37.5 [34.0–41.1] | 93% | 0% | 0.03 |
| `static_fewshot` | 40.3 [36.6–44.2] | 86% | 0% | 0.06 |
| `rag_fewshot` | 42.8 [38.6–47.0] | 93% | 0% | 0.10 |
| **`rag_plus_stylecard`** | **43.5 [39.8–47.3]** | 90% | 0% | 0.12 |
| **human reply (ceiling)** | **92.0 [88.5–94.9]** | 100% | 100% | 1.00 |

The two retrieval variants rank top, as predicted. **But every interval overlaps its
neighbour, so the ablation has not demonstrated a real difference** — 29 items is too few
to separate 37 from 44. The report states this per adjacent pair rather than presenting a
leaderboard.

The honest headline: the best variant reaches **47% of the human ceiling**, and
**0% of drafts were sendable without edits**. Grounding at 0.10 means the drafts state
roughly one in ten of the facts they owe. Reading them (the worst-five section of
`reports/report.md`) shows why: they are fluent and plausible, and they systematically ask
for information or promise follow-up where the human answered, decided, or refused. Two
drafts accepted an 18% price increase the human explicitly rejected; another confirmed a
legal preservation the human deliberately refused to confirm.

That is a genuinely poor result for the generator, and the metric surfacing it clearly is
the point. A system that reported "82% accurate" on this output would be broken.

### (c) Sensitivity against the metric's own noise

Every headline number carries a bootstrap 95% CI over test items. With 29 held-out emails
the intervals are wide, and the report states explicitly, for each adjacent pair of
variants, whether the gap survives:

> `rag_fewshot` (X) vs `static_fewshot` (Y): intervals overlap — **not** a demonstrated
> difference

A leaderboard without this invites readers to believe in differences that are noise.

### (d) Ceiling and floor, so the scale means something

The human replies score **92.0**, not 100, under this metric. That gap is the portion that
penalises legitimate variation, and quoting it is the only way a system score is
interpretable. The floor — a well-written reply to a *different* email — is **33.6**. A
metric that scored that highly would be measuring fluency, not accuracy.

So the real scale is roughly 34 → 92, not 0 → 100.

### Where the metric is weak — stated plainly

- **Lexical polarity has a blind spot.** Negation scope is decided by clause, plus a
  seven-token window. "I'm not the right person to name a custodian of records" negates
  across a clause boundary and 15 tokens; the rule misses it. The optional LLM verifier
  tier is the backstop, and every constraint records which tier decided it.
- **The offline intent classifier is cue-based** and was written against the training
  split. Held-out accuracy is **75.9%** on *human* gold replies (chance 11.1%). It replaced
  embedding centroids, which managed only 20.7% — sentence embeddings encode what an email
  is *about*, and every reply in a category is about the same thing.

  **That 75.9% does not transfer to generated replies.** The cue patterns were written
  against terse human prose; on verbose LLM drafts they fire only ~28% of the time and the
  rest fall through to the 20.7% centroid. Any run made with `--no-llm-intent` has a
  correspondingly noisy intent component, and the committed run therefore uses a real LLM
  classifier (`llama-3.3-70b-versatile`, 116/116 classified, zero fallbacks).

- **A silent fallback once made a report assert something false.** An earlier run was
  configured to classify intent with `qwen/qwen3.6-27b`; every call failed (that model
  400s on `response_format`, and as a reasoning model it emits a `<think>` block that
  exhausted the token budget before any JSON). The classifier caught the exception, fell
  back to offline cues, and the run metadata still recorded "classified by qwen". The run
  looked completely normal. Three things changed as a result: the JSON-mode fallback now
  recognises Groq's actual error text, `extract_json` strips or explicitly rejects
  reasoning blocks, and **every run now reports the method distribution that actually
  occurred** (`intent_classifier.methods_used`) plus a loud warning when zero replies were
  classified by the model that was requested. A metric that cannot be trusted to say what
  it did is worse than one that scores badly.
- **Judge and generator share a provider.** With only a Groq key available, the judge
  defaults to a different model *family* (`llama-3.3-70b-versatile` judging
  `openai/gpt-oss-120b`). That is weaker than cross-provider judging. The report records
  the pair and warns when they coincide.
- **The dataset is synthetic** (see below).

---

## 3. The dataset

**106 email/reply pairs, 77 train / 29 held out.** Full provenance and limitations in
[`data/DATA_CARD.md`](data/DATA_CARD.md).

- 9 categories, **3 deliberately different responder personas** — a warm support lead, a
  terse operations manager, a formal business manager. One house style would let a
  generator that answers everything in the same agreeable register pass unnoticed.
- **26 hard cases** where the correct reply withholds, asks, or routes elsewhere: a
  phishing email requesting credentials, a litigation hold, a press enquiry about an
  alleged breach, a bank-detail change request, a reference request without consent.
  Without these, any fluent and polite model scores well.
- **335 `must_include` and 234 `must_not_include` constraints**, hand-written per record.

**It is synthetic, and that is the weakest part of this project.** No real email was used.
Scenarios were hand-specified (category, intent, persona, required facts), expanded to
prose with AI assistance, then reviewed and corrected.

Enron was considered and rejected: reply pairing must be reconstructed heuristically and is
unreliable, it carries real personal data, and — decisively — it has no ground truth about
*what a reply owed*. The constraint fields are what make this more than a similarity score,
and no public corpus has them.

The honest cost: real inboxes are messier, and absolute scores here are optimistic.
*Relative* comparisons between variants are the defensible use of this dataset.

**Two integrity properties are enforced, not asserted:**

1. Every constraint is validated against its own gold reply **using the same matcher the
   evaluator uses**. The build fails if a gold reply doesn't satisfy a constraint attached
   to it, so the dataset cannot demand something the scorer would fail the human for. This
   caught 21 authoring errors and two genuine matcher bugs.
2. Leakage is **measured**: max train↔test cosine similarity is **0.692** (threshold 0.92,
   0 items over), mean nearest 0.463. Nothing in test has a memorisable twin in train.

---

## 4. The generator

**Retrieval-augmented few-shot prompting.** A hybrid retriever (MiniLM embeddings +
TF-IDF word and character n-grams, with a same-category bonus) pulls the 3 most similar
past email/reply pairs; those become exemplars in the prompt.

The two channels fail differently, which is why both are used: embeddings catch "our sync
stopped overnight" ≈ "the connector hasn't run since 2am" with no shared words; TF-IDF
catches the exact identifiers — `EG-400`, `reverse charge` — that embeddings smooth away
precisely because they're rare.

Output is structured JSON including `needs_human_review` and `unresolved_questions`, which
makes correct deferral a *measurable* behaviour rather than something inferred from prose.

### Why not fine-tuning

With 77 training examples, fine-tuning memorises rather than generalises, and it welds the
system to one vendor's tuning API. Retrieval adapts the moment a new reply is filed, stays
portable across all three providers, and — most important for this brief — is **auditable**:
every generated reply records which past emails shaped it, so a bad output can be traced to
the exemplars that produced it.

Fine-tuning wins on style-matching and per-call cost at a few thousand examples. That's the
point where the choice flips, and it isn't this dataset.

### Four variants, all evaluated

`zero_shot` · `static_fewshot` (3 fixed exemplars) · `rag_fewshot` (the system) ·
`rag_plus_stylecard` (+ explicit persona card).

The ablation isn't padding. It's the evidence that grounding in the dataset does anything,
and it doubles as a sensitivity test: a metric that can't separate zero-shot from
retrieval-grounded output isn't measuring what it claims.

---

## 5. Providers, keys, and retry

Three providers plus an offline mock:

| Provider | Notes |
|---|---|
| **Groq** | Default. Uses the `openai` SDK against Groq's compatible endpoint — no extra dependency. |
| **Gemini** | `google-generativeai`. |
| **OpenAI** | `openai`. |
| **`mock`** | Deterministic, no key. Backs the "runs end-to-end" claim in CI. |

**Model IDs are discovered at runtime**, never hardcoded — Groq deprecated
`llama-3.3-70b-versatile` and `llama-3.1-8b-instant` in June 2026, which is exactly the
breakage a compiled-in constant causes. `cli.py setup` queries the provider and prints what
your account can actually see, then resolves generator and judge models from it.

**Key handling.** Resolution order: `--api-key` → environment variable → `.env` →
interactive `getpass` prompt (never echoed). Optional save to `.env` only after explicit
confirmation. `.env` is gitignored from the first commit, and every key-shaped string is
scrubbed from logs, reports, and exception traces by `redact()`.

**Retry.** Exponential backoff with jitter, 4 attempts, honouring `Retry-After` (parsed
from the header *or* the message body, since Groq puts it there). Retries 429/5xx/timeouts.
**Never retries 401/403/400** — a bad key should fail loudly and immediately rather than
after four pointless round trips. A separate loop re-asks the model when it returns
malformed JSON, feeding the parse error back rather than backing off, because the transport
succeeded and only the content was wrong.

Responses are cached on disk keyed by a hash of everything that determines them, so an eval
run that dies at item 180 doesn't re-spend quota on the first 179.

---

## 6. Running it

```bash
python cli.py setup --provider groq        # verify a key, list live models
python cli.py build-data --verify          # validate the dataset + leakage report
python cli.py reply --email email.txt      # suggest a reply to one email
python cli.py evaluate --provider groq     # generate + score the held-out split
python cli.py validate-metric              # probes, ceiling/floor, correlations
python cli.py run-all --provider groq      # everything, then write reports/
streamlit run app.py                       # UI with a masked key box + live scoring
```

Useful flags: `--limit N` (first N test emails), `--variants rag_fewshot`,
`--judge-provider gemini` (cross-provider judging if you have a second key), `--no-judge`,
`--rpm 20` (throttle for free tiers), `--no-cache`.

Outputs land in `reports/`: `report.md`, a self-contained `report.html`, and
`run_<id>.json` with every per-response sub-score, judge reason, and hard-fail flag.

### Setup notes

A plain `pip install -r requirements.txt` into a fresh virtualenv is the supported path.
On a machine with a pre-existing `transformers`/`tokenizers` version conflict, a venv
created with `--system-site-packages` plus `pip install "tokenizers>=0.21,<0.22"` fixes
`sentence-transformers` without disturbing the global environment. If embeddings can't
load at all, the system falls back to TF-IDF and says so loudly in the report — semantic
scores are materially weaker that way and any report produced should be read accordingly.

---

## 7. Repository layout

```
cli.py                     entry point for every command
app.py                     Streamlit UI
data/
  corpus_*.py              the dataset as readable Python (source of truth)
  build_dataset.py         build, validate, split, leakage report
  schema.py                taxonomies + per-record validation
  DATA_CARD.md             provenance and limitations
  emails.jsonl             built dataset
src/
  llm/                     providers, key resolution, retry, cache
  retrieval.py             hybrid retriever
  generate.py              prompt assembly, 4 variants
  embeddings.py            MiniLM with an explicit TF-IDF fallback
  eval/
    constraints.py         fact matching with polarity + contradiction detection
    metrics.py             the composite score and hard-fail gate
    intent.py              speech-act classification (LLM + offline cues)
    style.py               per-persona style profiles
    safety.py              placeholders, fabrications, deferral checks
    judge.py               reference-aware LLM judge
    probes.py              known-quality responses — the metric's test suite
    stats.py               bootstrap CIs, Spearman, Kendall
    validate_metric.py     the four validation lines
  report.py                markdown + HTML + console reporting
tests/                     61 tests, no API key required
```

---

## 8. How AI tools were used

An AI coding assistant was used throughout, and it did substantial work here:

- **Dataset.** I specified the schema, taxonomies, personas, and the requirement that every
  record carry explicit required/forbidden facts. The assistant drafted the 106 scenarios
  and replies against those specifications; I reviewed them and the automated validator
  forced corrections to 21 records where a gold reply didn't satisfy its own constraint.
- **Code.** Written collaboratively. The parts I directed most closely were the metric
  decomposition, the hard-fail gate, and the probe design — the evaluation decisions the
  brief weights heaviest.
- **Debugging.** Several genuine bugs surfaced from the probe and test suites rather than
  from reading code: an asymmetric stemmer (`saving`→`sav` but `save`→`save`, so they never
  matched), negation scope leaking across clauses, forbidden-claim matching firing on 4-of-5
  token overlap, and the missing omission/contradiction distinction. Each is documented at
  the fix site.
- **Not used for:** the evaluation design itself, the weighting rationale, or the decision
  about which limitations to disclose.

The dataset being AI-drafted is a real limitation and is stated as such in the data card
rather than glossed.

---

## 9. What I'd do next, in priority order

1. **A second annotator and a fresh label set.** Single-rater correlation with a CI
   crossing zero is the weakest link in the whole project, and the sendability rules have
   now been revised three times while looking at the existing 24 labels. More labels from
   someone else would either confirm the composite tracks quality or show it doesn't;
   right now neither is established.
2. **Validate sendability by detection rate, not correlation** — and build an adversarial
   set that actually contains placeholders, fabricated references and forbidden claims at
   a realistic rate. It scores 100% on the synthetic probes and fires on 3 of 24 real
   drafts, which is too few real positives to say anything about its precision.
3. **Improve the generator.** 0% edit-free and 0.10 grounding is poor. The drafts defer
   where humans act. Worth trying: stronger instruction to commit when the exemplars
   commit, and retrieving on *reply* similarity rather than only incoming-email similarity.
4. **Real email data.** `load_dataset()` is the seam; constraint fields could be
   bootstrapped by having a model propose them from human replies, then reviewing.
5. **Cross-provider judging by default** — generate on one vendor, judge on another, and a
   paid tier so the judge can cover every variant in the scored comparison.
6. **Multi-turn threads.** `thread_context` exists in the schema and is empty everywhere.
7. **Calibration.** `confidence` is self-reported and unvalidated; whether it predicts the
   composite is measurable and isn't measured yet.
