# Data card — Northwind Systems reply corpus

## What this is

106 incoming business emails, each paired with the reply that was "sent", plus the
metadata the evaluator needs to score a *new* reply against that gold one.

| | |
|---|---|
| Records | 106 |
| Split | 77 train (retrieval pool) / 29 test |
| Categories | 9 (support, escalation, outreach, scheduling, internal, vendor, billing, sales, recruiting) |
| Responder personas | 3 |
| Difficulty | 80 normal / 26 hard |
| `must_include` constraints | 335 (mean 3.16 per record) |
| `must_not_include` constraints | 234 (mean 2.21 per record) |
| Language | English only |
| Max train↔test similarity | 0.692 (threshold 0.92, 0 items over) |

## Where it came from — honestly

**It is synthetic. No real email was used, and no real person's mail appears in it.**

The scenarios were hand-specified first: for each record a category, a speech-act intent,
a responder persona, and the list of facts the reply owes. Those skeletons were then
written up into full prose with the help of an AI assistant, and every record was reviewed
and edited afterwards — several were rewritten when the automated validator showed that
the gold reply did not actually satisfy a constraint attached to it.

**Why not a public corpus?** Enron is the obvious candidate and was considered. It was
rejected for three reasons: reply pairing has to be reconstructed heuristically from quoted
text and is unreliable; it contains real people's personal information that would need
scrubbing before redistribution; and — decisively — it carries no ground truth about *what
a reply owed*. The `must_include` / `must_not_include` fields are what make this evaluation
more than a similarity score, and no public corpus has them. Building them by hand for 106
scenarios was a better use of the effort than mining 106 noisy pairs and then annotating
those by hand anyway.

**The honest cost of that choice** is set out under Limitations. Synthetic data is the
weakest part of this project and it should be read that way.

## Schema

```json
{
  "id": "sup-014",
  "category": "support",
  "persona": "cs_rep",
  "thread_context": "",
  "incoming":   {"from": "...", "subject": "...", "received_at": "...", "body": "..."},
  "gold_reply": {"subject": "...", "body": "..."},
  "intent_label": "confirm_and_commit",
  "must_include":     ["advance replacement is covered", "RMA-2291", "5 to 7 business days"],
  "must_not_include": ["you will be invoiced for the replacement", "next day delivery"],
  "difficulty": "normal",
  "requires_human_review": false
}
```

`persona` is **derived** from `category` at build time rather than hand-written, so a
record can never disagree with itself about who wrote the reply.

### The two fields that do the real work

`must_include` is the set of facts a correct reply has to convey — an RMA number, a
turnaround, a named person, a refusal. `must_not_include` is the set of claims it must
never make: commitments nobody authorised, refunds nobody approved, reassurances that
aren't true yet.

Without these, "accuracy" collapses into similarity-to-gold, which rewards a reply that
sounds right and says something false. With them, factual grounding is checkable per fact,
and a reply that invents a refund policy can be failed outright rather than averaged into
a respectable-looking 85.

Every constraint is validated against its own gold reply at build time using the *same
matcher the evaluator uses*. The build fails if a gold reply does not satisfy a constraint
attached to it. So the dataset cannot contain a constraint the scorer would mark the human
answer as failing.

### Intent taxonomy

Nine closed labels: `confirm_and_commit`, `decline_politely`, `request_information`,
`provide_information`, `resolve_with_action`, `negotiate_alternative`,
`acknowledge_and_defer`, `escalate_or_handoff`, `apologize_and_remediate`.

The point is to make "did the suggested reply *do* the same thing?" answerable. A fluent,
friendly reply that commits to a refund where the human escalated to legal is not 80%
right — it is wrong in the way that matters, and only an action label catches that.

## The three personas

| Key | Who | Categories | Voice |
|---|---|---|---|
| `cs_rep` | Priya Raman, Support Lead | support, escalation, outreach | Warm, explains reasoning, 60–130 words, "Hi *First*," → "Warmly, Priya" |
| `ops_mgr` | Dan Whitfield, Operations Manager | scheduling, internal, vendor | Terse, decision first, bullets, 25–70 words, "*First* -" → "- Dan" |
| `business_mgr` | Margaret Osei, Business Manager | billing, sales, recruiting | Formal, no contractions, explicit figures and references, "Dear *Name*," → full signature block |

Three deliberately different voices, not one house style with cosmetic variation. This is
what makes the tone/style component of the metric testable: a generator that answers every
email in the same agreeable register will match one persona and visibly miss the other two.
A single-voice corpus would have let that failure pass unnoticed.

## Hard cases (26 of 106)

Roughly a quarter of the corpus is cases where the *correct* reply withholds, asks, or
routes elsewhere rather than answering:

- a phishing email requesting admin credentials (`sup-016`)
- a litigation hold notice that support must not answer (`sup-018`)
- a press enquiry about an alleged breach (`out-004`)
- a bank-detail change request — a standard payment-fraud pattern (`bil-009`)
- a reference request without candidate consent (`rec-006`)
- an interview-discrimination complaint the recipient cannot investigate herself (`rec-010`)
- a supplier gift that exceeds the policy cap, from a supplier the recipient approves orders for (`ven-006`)
- an "it's broken, same as before" email with no recoverable context (`sup-017`)

These exist because without them the metric is trivially gameable. A model that is fluent,
polite, and confident scores well on easy tickets; these are where it either defers
correctly or invents a commitment, and that difference is most of what a suggested-reply
system's real-world value turns on.

## Splits and leakage

Stratified by `(category, difficulty)` with a fixed seed (`20250329`), so hard cases stay
proportionally represented in test rather than drifting into train.

Leakage is **measured, not asserted**. `build_dataset.py` embeds every test email, finds
its nearest neighbour in the training pool, and reports the distribution:

```
max similarity  : 0.692   (threshold 0.92, 0 items over)
mean nearest    : 0.463
```

The closest pair is `rec-002` ← `rec-001` at 0.692 — two emails to the same recruiting
candidate about the same role, which is realistic rather than duplicated. Nothing in test
has a near-twin in train, so retrieval scores cannot be explained by copying.

## Limitations — read these before trusting any number

1. **It is synthetic.** Real inboxes are messier: typos, top-posting, broken quoting,
   forwarded chains, half-sentences, attachments carrying the actual content. Absolute
   scores here will be optimistic relative to production. *Relative* comparisons between
   generator variants are the defensible use of this dataset.
2. **One author.** All 106 records come from a single authoring process, so the emails
   share latent stylistic habits. A model that learns "how this corpus phrases things" gets
   credit it would not get on real mail.
3. **The gold reply is *a* good reply, not *the* one.** Several incoming emails admit
   multiple legitimate responses. This is precisely why the metric does not use exact match
   and weights similarity-to-gold at only 15% — but it still means a genuinely good reply
   taking a different valid line will be under-scored on that component.
4. **Constraints were written by the same process that wrote the gold replies.** They are
   internally consistent by construction. An independent annotator would likely have
   written some of them differently.
5. **English only, UK/EU business context**, one fictional company, B2B software and
   hardware. Nothing here tests other languages, consumer email, or other domains.
6. **No thread history in practice.** `thread_context` exists in the schema but is empty
   for every record. Multi-turn threads are a real and unaddressed part of the problem.
7. **106 records is small.** Enough to compare generator variants and to validate the
   metric's behaviour; not enough to fine-tune, and not enough for narrow confidence
   intervals. Reported intervals are wide and shown as such.

## Using real data instead

`data/build_dataset.py::load_dataset()` is the seam. Return records in the schema above
from anywhere — mbox, the Gmail API, a warehouse table — and retrieval, generation and
evaluation all work unchanged. The only genuinely manual part is `must_include` /
`must_not_include`; for real mail these can be bootstrapped by having a model propose them
from the human reply and then reviewing, which is much faster than authoring from scratch.

## Rebuilding

```bash
python data/build_dataset.py            # rebuild emails.jsonl + splits.json from corpus_*.py
python data/build_dataset.py --verify   # validate the committed files, write nothing
```

The source of truth is the three `corpus_*.py` files, which are readable Python rather than
a JSON blob — a dataset you cannot review is a dataset you cannot trust. The build refuses
to write anything if a single record fails validation.
