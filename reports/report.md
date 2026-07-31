# Evaluation report

- **Run** `20260731T032857Z` · 29 held-out emails · 272.1s
- **Generator** `groq` / `openai/gpt-oss-120b`
- **Judge** not used — rule-based components only
- **Embeddings** `sentence-transformers`

## Does the metric measure anything? (read this first)

**Discriminant probes:** 270/270 assertions passed (**100.0%**) across 29 records.

Each probe damages the human's own reply in exactly one known way. The metric must notice that damage and only that damage.

| Probe | Mean composite | What it should show |
|---|---:|---|
| `gold` | 92.2 | the human's reply — practical ceiling |
| `gold_slang` | 81.4 | facts intact, register wrecked — style drops, grounding holds |
| `gold_fact_corrupted` | 40.0 | one required figure altered — must hard-fail |
| `gold_forbidden` | 40.0 | asserts a forbidden claim — must hard-fail |
| `gold_placeholder` | 40.0 | unfilled placeholder — must hard-fail |
| `wrong_email` | 33.1 | a good reply to a different email — floor |
| `gold_intent_inverted` | 27.2 | opposite action, same voice — intent collapses |
| `generic` | 26.9 | fluent, polite, says nothing |

**Agreement with human ratings** (n=24 replies rated 1–5 for sendability):

- Spearman ρ = **0.257** (95% CI -0.16 to 0.60)
- Kendall τ-b = **0.204**
- Pearson r = 0.196

Per component — this is where a weak component gives itself away:

| Component | Spearman ρ vs human |
|---|---:|
| grounding | 0.509 |
| style | 0.296 |
| similarity | 0.169 |
| intent | 0.073 |
| sendability | -0.177 |

**An independent model's opinion** — `llama-3.1-8b-instant` judging `openai/gpt-oss-120b`, 29 responses of `rag_fewshot`:

- Spearman ρ vs composite = **0.339** (95% CI -0.03 to 0.63)
- Judge mean sendability 3.241/5, faithfulness 3.621/5
- Responses where the judge flagged an unsupported commitment: 12/29

The judge is kept out of the scored ablation: free-tier daily token limits made it impossible to judge all four variants under one model, and judging only some of them would let the unjudged ones score higher purely for escaping scrutiny.

**Offline intent classifier** (used when no API key is available): 75.9% exact on held-out human replies, mean credit 0.82. Chance is 11.1%.

## System results

Three headline numbers, not one. The mean says how good replies are; the sendable rate says how often the system is *safe*; the edit-free rate says how often it is actually *useful*. They move independently.

| Variant | Composite (95% CI) | Sendable | Edit-free | Grounding | Intent | Similarity | Style | Sendability |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `zero_shot` | 37.5 [34.0–41.1] | 93% | 0% | 0.03 | 0.33 | 0.48 | 0.64 | 0.77 |
| `static_fewshot` | 40.3 [36.6–44.2] | 86% | 0% | 0.06 | 0.41 | 0.50 | 0.69 | 0.74 |
| `rag_fewshot` | 42.8 [38.6–47.0] | 93% | 0% | 0.10 | 0.36 | 0.50 | 0.70 | 0.86 |
| `rag_plus_stylecard` | 43.5 [39.8–47.3] | 90% | 0% | 0.12 | 0.36 | 0.52 | 0.73 | 0.84 |
| **human reply (ceiling)** | **92.0 [89.0–94.8]** | 100% | 86% | 1.00 | 0.81 | 1.00 | 0.83 | 0.95 |

The best variant (`rag_plus_stylecard`) reaches **47% of the human ceiling**. The ceiling is 92.0 rather than 100 because the metric charges the human's own replies for legitimate variation — quoting that gap is the only way the system score means anything.

### Are the gaps real?

- `rag_plus_stylecard` (43.5) vs `rag_fewshot` (42.8): intervals overlap — **not** a demonstrated difference
- `rag_fewshot` (42.8) vs `static_fewshot` (40.3): intervals overlap — **not** a demonstrated difference
- `static_fewshot` (40.3) vs `zero_shot` (37.5): intervals overlap — **not** a demonstrated difference

### Where it struggles

| Difficulty | n | Mean composite |
|---|---:|---:|
| hard | 9 | 44.8 |
| normal | 20 | 41.8 |

| Category | n | Mean composite |
|---|---:|---:|
| outreach | 3 | 34.1 |
| scheduling | 3 | 36.2 |
| vendor | 3 | 36.7 |
| internal | 3 | 37.4 |
| sales | 3 | 42.3 |
| support | 5 | 42.8 |
| escalation | 3 | 49.0 |
| recruiting | 3 | 49.4 |
| billing | 3 | 56.8 |

### Five worst responses (`rag_fewshot`)

Printed in full because an evaluation you cannot audit by reading the failures is a number, not a measurement.

#### `ven-001` — 26.8 (sendable)

*Missing required fact(s): 18% does not work; I will sign at 6% for a 24 month term; let me know by 25 April. Acted as 'confirm_and_commit' where the human 'negotiate_alternative' (0% credit).*


```
Hi Gavin,

Yes, please go ahead and send the renewal paperwork.

Thanks,
Dan Whitfield
Operations Manager, Northwind Systems
```

#### `int-007` — 27.0 (sendable)

*Missing required fact(s): ops should own the facts not the wording; ops posts a raw factual line; comms rewrites within 15 minutes. Acted as 'request_information' where the human 'negotiate_alternative' (15% credit). Style drifts from ops_mgr (greeting 'hi' vs expected 'none'). Asked for information or promised follow-up where the human answered, decided, or acted.*


```
Hi Rhea,

I’m open to having Ops handle the status‑page updates during incidents – we’re the ones monitoring the systems in real time. To make it work smoothly we’ll need a clear template and a quick review step (e.g., product sign‑off) before publishing, especially for any non‑technical wording.

Could you share the expected format, any branding guidelines, and who should give the final approval? Once we have that, we can set up a simple process and get started.

Thanks,
- Dan
```

#### `sch-011` — 27.1 (sendable)

*Missing required fact(s): we will move; your session has external attendees; shifted us to the small meeting room. Acted as 'request_information' where the human 'resolve_with_action' (15% credit). Style drifts from ops_mgr (greeting 'hi' vs expected 'none'). Asked for information or promised follow-up where the human answered, decided, or acted.*


```
Hi Carla,

Thanks for flagging the clash. I’ll check our schedule and see if we have an alternate room or a different slot that could work for my team. Could you let me know if your team has any flexibility on that Thursday, or if there’s a preferred alternative time?

Happy to coordinate a solution that works for both of us.

- Dan
```

#### `rec-002` — 30.8 (sendable)

*Missing required fact(s): we will not be progressing your application; more hands on experience with industrial network hardware; keep your details on file for twelve months. Acted as 'acknowledge_and_defer' where the human 'decline_politely' (15% credit). Asked for information or promised follow-up where the human answered, decided, or acted.*


```
Dear Patience,

Thank you for your email and for taking the time to interview for the Field Engineer role on 6 May. I understand how important it is to receive timely feedback.

I have forwarded your enquiry to the recruitment team and will let you know the outcome as soon as possible. You can expect an update from me by the end of next week (within five business days).

Thank you for your patience.

Kind regards,
Margaret Osei
Business Manager, Northwind Systems
```

#### `out-003` — 31.8 (sendable)

*Missing required fact(s): yes I would be glad to; 900 words by 18 April; send over any style guide. Acted as 'request_information' where the human 'confirm_and_commit' (15% credit). Asked for information or promised follow-up where the human answered, decided, or acted.*


```
Hi Raj,

Thank you for the kind words about my talk on incident communications – I’m glad it resonated with you. I’m flattered by the invitation to contribute a guest post.

Before I can commit, could you share a few details?
- The specific angle or topic you’d like the piece to cover.
- Any editorial guidelines or style requirements for the newsletter.
- Whether there is any compensation or credit arrangement for contributors.
- Confirmation that the 18 April deadline aligns with your publishing schedule.

Once I have that information I’ll be able to check my calendar and let you know if I can deliver the 900‑word article within the timeframe.

Looking forward to hearing more.

Warmly,
Priy
```
