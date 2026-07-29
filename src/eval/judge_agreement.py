"""An independent model's opinion, as a fifth line of validation.

The LLM judge is deliberately kept *out* of the scored ablation. Free-tier daily token
limits made it impossible to judge all four variants under one model, and judging only
some of them would be worse than judging none: the unjudged variants could not incur
judge-derived hard fails, so they would score higher for no reason but missing scrutiny.
A comparison has to apply the same instrument to everything it compares.

What the judge is used for instead is checking the metric from the outside. It reads the
incoming email, the human's actual reply, and the draft, and answers "would the person who
wrote that reference reply send this?" on a 1-5 scale. If the rule-based composite is
measuring anything real, an independent model's answer to that question should correlate
with it — and it does so without sharing any of the composite's machinery, which is what
makes it independent evidence rather than a restatement.

It also surfaces hallucinated commitments that no rule catches, since "this promises
something the source material does not support" needs reading comprehension.
"""

from __future__ import annotations

import json
from pathlib import Path

from .judge import Judge, JudgeConfig
from .stats import correlation_report, spearman

ROOT = Path(__file__).resolve().parents[2]


def run_agreement(
    run: dict,
    judge_client,
    variant: str = "rag_fewshot",
    samples: int = 3,
    progress: bool = True,
) -> dict:
    from data.build_dataset import load_dataset

    by_id = {r["id"]: r for r in load_dataset()}
    rows = [r for r in run["responses"] if r["variant"] == variant]
    if not rows:
        raise ValueError(f"No responses for variant {variant!r} in this run.")

    judge = Judge(judge_client, JudgeConfig(samples=samples),
                  generator_model=run["generator"]["model"])

    composites: list[float] = []
    sendabilities: list[float] = []
    faithfulness: list[float] = []
    agreements: list[float] = []
    findings: list[dict] = []
    skipped = 0

    for i, row in enumerate(rows, 1):
        if progress:
            print(f"  judging {i}/{len(rows)} {row['record_id']:<10}", end="\r", flush=True)
        rec = by_id[row["record_id"]]
        verdict = judge.evaluate(row["reply_body"], rec)
        if verdict.get("sendability") is None:
            skipped += 1
            continue

        composites.append(row["composite"])
        sendabilities.append(float(verdict["sendability"]))
        if verdict.get("faithfulness") is not None:
            faithfulness.append(float(verdict["faithfulness"]))
        agreements.append(float(verdict.get("agreement", 0.0)))

        findings.append({
            "record_id": row["record_id"],
            "composite": row["composite"],
            "sendable": row["sendable"],
            "judge_sendability": verdict["sendability"],
            "judge_faithfulness": verdict.get("faithfulness"),
            "hallucinated_commitments": verdict.get("hallucinated_commitments", []),
            "reason": verdict.get("reason", ""),
            "self_consistency": verdict.get("agreement"),
            "samples": verdict.get("sendability_samples"),
        })

    if progress:
        print(" " * 60, end="\r")

    out: dict = {
        "variant": variant,
        "judge_model": judge_client.model,
        "generator_model": run["generator"]["model"],
        "same_family_as_generator": judge.same_family_as_generator,
        "samples_per_response": samples,
        "n_judged": len(composites),
        "n_failed": skipped,
        "mean_judge_sendability": (round(sum(sendabilities) / len(sendabilities), 3)
                                   if sendabilities else None),
        "mean_judge_faithfulness": (round(sum(faithfulness) / len(faithfulness), 3)
                                    if faithfulness else None),
        "mean_self_consistency": (round(sum(agreements) / len(agreements), 3)
                                  if agreements else None),
        "responses_with_hallucinations": sum(
            1 for f in findings if f["hallucinated_commitments"]),
        "findings": findings,
        "judge_stats": judge_client.stats(),
    }

    if len(composites) >= 4:
        out["correlation_with_composite"] = correlation_report(composites, sendabilities)
        # Does the composite agree with the judge specifically about *safety*?
        out["sendable_flag_vs_judge"] = round(
            spearman([1.0 if f["sendable"] else 0.0 for f in findings], sendabilities), 4)

    return out


def save(agreement: dict, directory: Path | None = None) -> Path:
    directory = directory or (ROOT / "reports")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "judge_agreement.json"
    path.write_text(json.dumps(agreement, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load(directory: Path | None = None) -> dict | None:
    path = (directory or (ROOT / "reports")) / "judge_agreement.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
