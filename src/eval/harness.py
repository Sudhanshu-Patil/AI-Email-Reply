"""Assembly: build a Scorer wired to the dataset, and run probes over it.

Kept separate from ``metrics.py`` so the scorer stays a pure function of its inputs and
this module owns the "where does the data come from" wiring.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.embeddings import get_embedder  # noqa: E402
from src.eval.intent import IntentClassifier  # noqa: E402
from src.eval.metrics import Scorer  # noqa: E402
from src.eval.probes import ProbeCheck, build_probes, check_expectations  # noqa: E402
from src.eval.style import fit_profiles  # noqa: E402


def load_all() -> tuple[list[dict], list[dict], list[dict]]:
    """Return ``(all_records, train, test)``."""
    from data.build_dataset import load_dataset, load_splits

    records = load_dataset()
    splits = load_splits()
    by_id = {r["id"]: r for r in records}
    return records, [by_id[i] for i in splits["train"]], [by_id[i] for i in splits["test"]]


def build_scorer(train: list[dict], judge=None, intent_client=None,
                 use_llm_intent: bool = False) -> Scorer:
    from data.schema import PERSONAS

    embedder = get_embedder()
    return Scorer(
        style_profiles=fit_profiles(train, PERSONAS),
        intent_classifier=IntentClassifier(intent_client, train, embedder),
        embedder=embedder,
        judge=judge,
        use_llm_intent=use_llm_intent,
    )


def run_probes(records: list[dict], scorer: Scorer,
               limit: int | None = None) -> tuple[list[ProbeCheck], dict]:
    """Score every probe for every record and collect the assertion results."""
    subset = records[:limit] if limit else records
    all_checks: list[ProbeCheck] = []
    per_probe: dict[str, list[float]] = {}

    for i, rec in enumerate(subset):
        other = subset[(i + 1) % len(subset)] if len(subset) > 1 else None
        scores = {}
        for probe in build_probes(rec, other):
            s = scorer.score(probe.reply, rec, variant=f"probe:{probe.name}")
            scores[probe.name] = s
            per_probe.setdefault(probe.name, []).append(s.composite)
        all_checks.extend(check_expectations(scores))

    summary = {
        "n_records": len(subset),
        "n_checks": len(all_checks),
        "n_passed": sum(c.passed for c in all_checks),
        "pass_rate": round(sum(c.passed for c in all_checks) / max(len(all_checks), 1), 4),
        "mean_composite_by_probe": {
            k: round(sum(v) / len(v), 2) for k, v in sorted(per_probe.items())
        },
        "failures_by_check": {},
    }
    fails: dict[str, list[str]] = {}
    for c in all_checks:
        if not c.passed:
            fails.setdefault(c.name, []).append(c.detail)
    summary["failures_by_check"] = {k: {"count": len(v), "examples": v[:3]}
                                    for k, v in sorted(fails.items())}
    return all_checks, summary
