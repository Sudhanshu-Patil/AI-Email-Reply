# Suggested email replies, and a way to tell whether they're any good

Given an incoming email, this system drafts a reply grounded in a corpus of past
email/reply pairs — and then measures how good that draft actually is, on five dimensions,
with evidence that the measurement tracks real quality.

The evaluation is the substance here. A generator is easy; knowing whether its output is
worth sending is the hard part, so the metric and how it was validated get their own
write-up in [docs/EVALUATION.md](docs/EVALUATION.md).

https://github.com/user-attachments/assets/39f17bca-201d-4d4b-8dc9-f51cb03d5ba0

```bash
pip install -r requirements.txt
python cli.py setup --provider groq      # paste a key; verifies it and lists live models
python cli.py run-all --provider groq    # generate, score, validate, write reports
```

No API key? Everything runs offline:

```bash
python -m pytest                         # 96 tests, no key needed
python cli.py validate-metric            # the metric's own validation suite
python cli.py run-all --provider mock
```

---

## What it found

29 held-out emails, generated with `openai/gpt-oss-120b`:

| Variant | Composite (95% CI) | Sendable | Edit-free | Grounding |
|---|---:|---:|---:|---:|
| `zero_shot` | 37.5 [34.0–41.1] | 93% | 0% | 0.03 |
| `static_fewshot` | 40.3 [36.6–44.2] | 86% | 0% | 0.06 |
| `rag_fewshot` | 42.8 [38.6–47.0] | 93% | 0% | 0.10 |
| **`rag_plus_stylecard`** | **43.5 [39.8–47.3]** | 90% | 0% | 0.12 |
| **human reply (ceiling)** | **92.0 [88.5–94.9]** | 100% | 100% | 1.00 |

The best variant reaches **47% of the human ceiling**, and **0% of drafts were sendable
without edits**. That is a poor result for the generator, and the metric surfacing it
clearly is the point.

A reply is scored on five dimensions — factual grounding (30), intent match (25), semantic
similarity (15), style fit (15) and sendability (15) — with a hard-fail gate that caps the
composite at 40 for a forbidden claim, a contradicted figure, an unfilled placeholder or a
fabricated reference. The metric has its own test suite: **270/270 probe assertions hold**.

**[docs/EVALUATION.md](docs/EVALUATION.md)** has the full write-up: the definition of
"accurate", the validation evidence, the dataset, the generator design, where the metric is
weak, how AI tools were used, and what comes next.

---

## Running it

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

## Gmail

```bash
python cli.py gmail-mine                    # your sent replies -> retrieval corpus
python cli.py gmail-draft --dry-run         # see what it would draft, no LLM call
python cli.py gmail-draft --provider groq   # create reply drafts in Gmail
```

It can create drafts but cannot send: the OAuth scopes are `gmail.readonly` and
`gmail.compose` only. Setup, privacy and what the metric can tell you on live mail are in
[docs/GMAIL.md](docs/GMAIL.md).

---

## Repository layout

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
  integrations/gmail.py    mine sent mail as corpus; draft replies back into Gmail
  report.py                markdown + HTML + console reporting
docs/
  EVALUATION.md            the metric, its validation, results and limitations
  GMAIL.md                 Gmail setup, scopes and privacy
tests/                     96 tests, no API key required
```
