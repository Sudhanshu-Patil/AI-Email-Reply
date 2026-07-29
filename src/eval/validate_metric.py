"""Evidence that the composite score tracks real quality.

Four independent lines, because each can fail in a way the others cannot see:

1. **Discriminant probes** — damage the human's reply in one known way; assert the metric
   notices that and only that. Needs no API key and no human labels, so it runs in CI.
2. **Agreement with human ratings** — Spearman/Kendall against hand-assigned 1–5
   sendability labels, reported *per component* so a weak component cannot hide inside a
   respectable composite.
3. **Sensitivity vs. its own noise** — bootstrap intervals on the ablation ordering. A gap
   smaller than the interval is not a finding.
4. **Ceiling and floor** — score the human replies and a mismatched reply, so the headline
   number sits on an interpretable scale instead of an implied 0–100.
"""

from __future__ import annotations

import json
from pathlib import Path

from .harness import build_scorer, load_all, run_probes
from .intent import IntentClassifier, intent_credit
from .stats import bootstrap_ci, correlation_report, spearman

ROOT = Path(__file__).resolve().parents[2]
HUMAN_RATINGS = ROOT / "data" / "human_ratings.jsonl"


def load_human_ratings(path: Path = HUMAN_RATINGS) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def intent_accuracy(test: list[dict], train: list[dict]) -> dict:
    """How good is the *offline* intent classifier on held-out human replies?

    Reported because the keyless path depends on it, and because a component's own
    accuracy bounds how much signal the component can contribute.
    """
    from ..embeddings import get_embedder

    ic = IntentClassifier(None, train, get_embedder())
    exact = 0
    credit = 0.0
    for rec in test:
        label, _, _, _ = ic.classify(rec["gold_reply"]["body"], use_llm=False)
        exact += int(label == rec["intent_label"])
        credit += intent_credit(label, rec["intent_label"])
    n = max(len(test), 1)
    return {"n": len(test), "exact": round(exact / n, 4),
            "mean_credit": round(credit / n, 4), "chance": round(1 / 9, 4)}


def correlate_with_humans(run: dict, ratings: list[dict]) -> tuple[dict, dict]:
    """Match rated (record_id, variant) pairs to their metric scores."""
    if not ratings:
        return {}, {}

    index = {(r["record_id"], r["variant"]): r for r in run["responses"]}
    metric, human = [], []
    per_component: dict[str, list[float]] = {}

    for rating in ratings:
        key = (rating["record_id"], rating["variant"])
        row = index.get(key)
        if row is None:
            continue
        metric.append(row["composite"])
        human.append(float(rating["sendability"]))
        for comp, val in row["components"].items():
            per_component.setdefault(comp, []).append(val)

    if len(metric) < 3:
        return {}, {}

    overall = correlation_report(metric, human)
    components = {
        comp: {"spearman_rho": round(spearman(vals, human), 4), "n": len(vals)}
        for comp, vals in per_component.items()
    }
    return overall, components


def validate(run: dict | None = None, probe_limit: int | None = None) -> dict:
    records, train, test = load_all()
    scorer = build_scorer(train)

    _, probe_summary = run_probes(test, scorer, limit=probe_limit)

    out: dict = {
        "probes": probe_summary,
        "intent_accuracy": intent_accuracy(test, train),
    }

    # Floor: a real, well-written reply to a *different* email. A metric that scores this
    # highly is measuring fluency, not accuracy.
    floor = [scorer.score(test[(i + 1) % len(test)]["gold_reply"]["body"], rec,
                          variant="floor").composite
             for i, rec in enumerate(test)]
    ceiling = [scorer.score(rec["gold_reply"]["body"], rec, variant="gold").composite
               for rec in test]
    out["scale"] = {
        "floor_mismatched_reply": bootstrap_ci(floor).to_dict(),
        "ceiling_human_reply": bootstrap_ci(ceiling).to_dict(),
    }

    from .judge_agreement import load as load_judge_agreement

    agreement = load_judge_agreement()
    if agreement and agreement.get("n_judged"):
        out["judge_agreement"] = agreement

    ratings = load_human_ratings()
    out["human_ratings_available"] = len(ratings)
    if run is not None and ratings:
        overall, components = correlate_with_humans(run, ratings)
        if overall:
            out["correlation"] = overall
            out["component_correlation"] = components

    return out


def print_validation(v: dict) -> None:
    p = v["probes"]
    print(f"\nDiscriminant probes: {p['n_passed']}/{p['n_checks']} "
          f"({p['pass_rate']:.1%}) over {p['n_records']} records")
    for name, mean in sorted(p["mean_composite_by_probe"].items(), key=lambda kv: -kv[1]):
        print(f"    {name:<22} {mean:6.1f}")
    if p.get("failures_by_check"):
        print("  assertions that did not hold:")
        for k, val in p["failures_by_check"].items():
            print(f"    {k}: {val['count']} — e.g. {val['examples'][0]}")

    s = v["scale"]
    print(f"\nScale: floor {s['floor_mismatched_reply']['mean']:.1f} → "
          f"ceiling {s['ceiling_human_reply']['mean']:.1f} "
          f"[{s['ceiling_human_reply']['lo']:.1f}–{s['ceiling_human_reply']['hi']:.1f}]")

    ia = v["intent_accuracy"]
    print(f"Offline intent classifier: {ia['exact']:.1%} exact on held-out "
          f"(chance {ia['chance']:.1%}), mean credit {ia['mean_credit']:.2f}")

    if v.get("correlation"):
        c = v["correlation"]
        print(f"\nHuman agreement (n={c['n']}): Spearman ρ={c['spearman_rho']:.3f} "
              f"[{c['spearman_95ci'][0]:.2f}, {c['spearman_95ci'][1]:.2f}], "
              f"Kendall τ={c['kendall_tau_b']:.3f}")
        for comp, val in sorted(v.get("component_correlation", {}).items(),
                                key=lambda kv: -kv[1]["spearman_rho"]):
            print(f"    {comp:<14} ρ={val['spearman_rho']:+.3f}")
    else:
        print(f"\nHuman ratings on file: {v['human_ratings_available']} "
              f"(need a scored run to correlate)")
