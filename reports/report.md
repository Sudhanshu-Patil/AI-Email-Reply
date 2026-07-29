# Evaluation report

- **Run** `20260729T113219Z` · 29 held-out emails · 225.3s
- **Generator** `groq` / `openai/gpt-oss-120b`
- **Judge** not used — rule-based components only
- **Embeddings** `sentence-transformers`

## Does the metric measure anything? (read this first)

**Discriminant probes:** 270/270 assertions passed (**100.0%**) across 29 records.

Each probe damages the human's own reply in exactly one known way. The metric must notice that damage and only that damage.

| Probe | Mean composite | What it should show |
|---|---:|---|
| `gold` | 92.0 | the human's reply — practical ceiling |
| `gold_slang` | 80.7 | facts intact, register wrecked — style drops, grounding holds |
| `gold_fact_corrupted` | 40.0 | one required figure altered — must hard-fail |
| `gold_forbidden` | 40.0 | asserts a forbidden claim — must hard-fail |
| `gold_placeholder` | 40.0 | unfilled placeholder — must hard-fail |
| `wrong_email` | 33.6 | a good reply to a different email — floor |
| `gold_intent_inverted` | 28.8 | opposite action, same voice — intent collapses |
| `generic` | 28.3 | fluent, polite, says nothing |

**Agreement with human ratings** (n=24 replies rated 1–5 for sendability):

- Spearman ρ = **0.265** (95% CI -0.16 to 0.60)
- Kendall τ-b = **0.204**
- Pearson r = 0.261

Per component — this is where a weak component gives itself away:

| Component | Spearman ρ vs human |
|---|---:|
| grounding | 0.509 |
| style | 0.296 |
| similarity | 0.169 |
| intent | 0.165 |
| sendability | -0.139 |

**An independent model's opinion** — `llama-3.1-8b-instant` judging `openai/gpt-oss-120b`, 29 responses of `rag_fewshot`:

- Spearman ρ vs composite = **0.281** (95% CI -0.09 to 0.59)
- Judge mean sendability 2.759/5, faithfulness 3.552/5
- Responses where the judge flagged an unsupported commitment: 18/29

The judge is kept out of the scored ablation: free-tier daily token limits made it impossible to judge all four variants under one model, and judging only some of them would let the unjudged ones score higher purely for escaping scrutiny.

**Offline intent classifier** (used when no API key is available): 75.9% exact on held-out human replies, mean credit 0.82. Chance is 11.1%.

## System results

Three headline numbers, not one. The mean says how good replies are; the sendable rate says how often the system is *safe*; the edit-free rate says how often it is actually *useful*. They move independently.

| Variant | Composite (95% CI) | Sendable | Edit-free | Grounding | Intent | Similarity | Style | Sendability |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `zero_shot` | 38.2 [34.9–41.9] | 93% | 0% | 0.03 | 0.28 | 0.48 | 0.64 | 0.88 |
| `static_fewshot` | 38.6 [36.1–41.4] | 86% | 0% | 0.06 | 0.22 | 0.50 | 0.69 | 0.96 |
| `rag_fewshot` | 42.7 [39.2–46.8] | 93% | 0% | 0.10 | 0.32 | 0.50 | 0.70 | 0.97 |
| `rag_plus_stylecard` | 40.8 [34.7–46.5] | 83% | 0% | 0.12 | 0.30 | 0.47 | 0.68 | 0.84 |
| **human reply (ceiling)** | **92.0 [88.5–94.9]** | 100% | 83% | 1.00 | 0.82 | 1.00 | 0.83 | 0.93 |

The best variant (`rag_fewshot`) reaches **46% of the human ceiling**. The ceiling is 92.0 rather than 100 because the metric charges the human's own replies for legitimate variation — quoting that gap is the only way the system score means anything.

### Are the gaps real?

- `rag_fewshot` (42.7) vs `rag_plus_stylecard` (40.8): intervals overlap — **not** a demonstrated difference
- `rag_plus_stylecard` (40.8) vs `static_fewshot` (38.6): intervals overlap — **not** a demonstrated difference
- `static_fewshot` (38.6) vs `zero_shot` (38.2): intervals overlap — **not** a demonstrated difference

### Where it struggles

| Difficulty | n | Mean composite |
|---|---:|---:|
| hard | 9 | 44.0 |
| normal | 20 | 42.1 |

| Category | n | Mean composite |
|---|---:|---:|
| internal | 3 | 32.1 |
| outreach | 3 | 37.6 |
| vendor | 3 | 38.5 |
| sales | 3 | 39.8 |
| support | 5 | 41.7 |
| scheduling | 3 | 42.8 |
| escalation | 3 | 48.5 |
| recruiting | 3 | 49.5 |
| billing | 3 | 54.3 |

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

#### `int-005` — 28.9 (sendable)

*Missing required fact(s): what is the budget per machine; is the serial console adapter still supported. Acted as 'provide_information' where the human 'request_information' (15% credit). Style drifts from ops_mgr (greeting 'hi' vs expected 'none').*


```
Hi,

Thanks for the heads‑up on the laptop refresh. To make sure we’re set up for a smooth transition, could you let me know:

- The planned rollout timeline for the ops team
- Preferred operating system and any baseline image you’ll be using
- Whether the laptops will include admin rights or if we need to request them
- Any pre‑installed tools or configurations (e.g., monitoring agents, VPN client, disk encryption) that you plan to provide

Once I have those details I can confirm any special requirements on our end.

Thanks,

- Dan
```

#### `int-007` — 32.3 (sendable)

*Missing required fact(s): ops should own the facts not the wording; ops posts a raw factual line; comms rewrites within 15 minutes. Acted as 'provide_information' where the human 'negotiate_alternative' (15% credit). Style drifts from ops_mgr (greeting 'hi' vs expected 'none').*


```
Hi Rhea,

I’m open to having Ops handle the status‑page updates during incidents – we’re the ones monitoring the systems in real time. To make it work smoothly we’ll need a clear template and a quick review step (e.g., product sign‑off) before publishing, especially for any non‑technical wording.

Could you share the expected format, any branding guidelines, and who should give the final approval? Once we have that, we can set up a simple process and get started.

Thanks,
- Dan
```

#### `sch-009` — 32.8 (sendable)

*Missing required fact(s): every other Tuesday at 14:00; next one is 15 April; no prep needed. Acted as 'confirm_and_commit' where the human 'provide_information' (15% credit). Style drifts from ops_mgr (greeting 'hi' vs expected 'none').*


```
Hi Jonas,

The ops onboarding sessions are run on a regular cadence, but the exact date and time depend on the cohort you’re assigned to. Could you let me know which onboarding group you’re in (or the start date you were given) so I can confirm the schedule for you?

In the meantime, the usual prep includes reviewing the onboarding packet we sent earlier, having a laptop with VPN access ready, and familiarising yourself with the basic ops handbook.

Thanks,
- Dan
```

#### `int-009` — 35.1 (sendable)

*Missing required fact(s): we cannot sign up to a number we do not hit today; 99.9% contractually; review at 99.99% once the multi-region work lands in Q4. Acted as 'provide_information' where the human 'decline_politely' (15% credit).*


```
Joe,

Thanks for flagging this. I’m not able to confirm a 99.99 % SLA at this stage – moving from our current 99.9 % commitment to 99.99 % requires a review by both operations and legal to understand the impact on capacity, reporting and liability.

I’ll pull the relevant performance data and run it by the ops team and our counsel today. I’ll get back to you with a clear answer and any alternative wording we can offer by end of day tomorrow so you have something to work with before the Friday deadline.

- Dan
```
