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
| `gold` | 92.2 | the human's reply — practical ceiling |
| `gold_slang` | 81.4 | facts intact, register wrecked — style drops, grounding holds |
| `gold_fact_corrupted` | 40.0 | one required figure altered — must hard-fail |
| `gold_forbidden` | 40.0 | asserts a forbidden claim — must hard-fail |
| `gold_placeholder` | 40.0 | unfilled placeholder — must hard-fail |
| `wrong_email` | 33.1 | a good reply to a different email — floor |
| `gold_intent_inverted` | 27.2 | opposite action, same voice — intent collapses |
| `generic` | 26.9 | fluent, polite, says nothing |

**Agreement with human ratings** (n=24 replies rated 1–5 for sendability):

- Spearman ρ = **0.298** (95% CI -0.12 to 0.63)
- Kendall τ-b = **0.241**
- Pearson r = 0.273

Per component — this is where a weak component gives itself away:

| Component | Spearman ρ vs human |
|---|---:|
| grounding | 0.509 |
| style | 0.296 |
| similarity | 0.169 |
| intent | 0.165 |
| sendability | -0.177 |

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
| `zero_shot` | 36.5 [33.1–40.4] | 93% | 0% | 0.03 | 0.28 | 0.48 | 0.64 | 0.77 |
| `static_fewshot` | 35.4 [32.6–38.3] | 86% | 0% | 0.06 | 0.22 | 0.50 | 0.69 | 0.74 |
| `rag_fewshot` | 41.2 [37.3–45.6] | 93% | 0% | 0.10 | 0.32 | 0.50 | 0.70 | 0.86 |
| `rag_plus_stylecard` | 40.1 [34.2–45.9] | 83% | 0% | 0.12 | 0.30 | 0.47 | 0.68 | 0.78 |
| **human reply (ceiling)** | **92.2 [88.7–95.2]** | 100% | 83% | 1.00 | 0.82 | 1.00 | 0.83 | 0.95 |

The best variant (`rag_fewshot`) reaches **45% of the human ceiling**. The ceiling is 92.2 rather than 100 because the metric charges the human's own replies for legitimate variation — quoting that gap is the only way the system score means anything.

### Are the gaps real?

- `rag_fewshot` (41.2) vs `rag_plus_stylecard` (40.1): intervals overlap — **not** a demonstrated difference
- `rag_plus_stylecard` (40.1) vs `zero_shot` (36.5): intervals overlap — **not** a demonstrated difference
- `zero_shot` (36.5) vs `static_fewshot` (35.4): intervals overlap — **not** a demonstrated difference

### Where it struggles

| Difficulty | n | Mean composite |
|---|---:|---:|
| hard | 9 | 43.6 |
| normal | 20 | 40.1 |

| Category | n | Mean composite |
|---|---:|---:|
| internal | 3 | 30.3 |
| outreach | 3 | 34.1 |
| vendor | 3 | 36.7 |
| support | 5 | 38.6 |
| sales | 3 | 39.8 |
| scheduling | 3 | 43.3 |
| recruiting | 3 | 46.0 |
| escalation | 3 | 49.0 |
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

#### `int-007` — 27.0 (sendable)

*Missing required fact(s): ops should own the facts not the wording; ops posts a raw factual line; comms rewrites within 15 minutes. Acted as 'provide_information' where the human 'negotiate_alternative' (15% credit). Style drifts from ops_mgr (greeting 'hi' vs expected 'none'). Asked for information or promised follow-up where the human answered, decided, or acted.*


```
Hi Rhea,

I’m open to having Ops handle the status‑page updates during incidents – we’re the ones monitoring the systems in real time. To make it work smoothly we’ll need a clear template and a quick review step (e.g., product sign‑off) before publishing, especially for any non‑technical wording.

Could you share the expected format, any branding guidelines, and who should give the final approval? Once we have that, we can set up a simple process and get started.

Thanks,
- Dan
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

#### `rec-002` — 30.8 (sendable)

*Missing required fact(s): we will not be progressing your application; more hands on experience with industrial network hardware; keep your details on file for twelve months. Acted as 'escalate_or_handoff' where the human 'decline_politely' (15% credit). Asked for information or promised follow-up where the human answered, decided, or acted.*


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
