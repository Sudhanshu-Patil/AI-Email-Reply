"""End-to-end: generate replies for the test split, score them, write a run file.

One run covers every variant so the ablation comparison is apples-to-apples — same items,
same scorer, same judge, same session.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ..generate import ReplyGenerator, Suggestion
from ..llm.base import BaseClient
from .harness import build_scorer, load_all
from .metrics import ResponseScore, Scorer, aggregate
from .stats import bootstrap_ci

ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = ROOT / "reports"


def run_variant(
    generator: ReplyGenerator,
    scorer: Scorer,
    records: list[dict],
    variant: str,
    progress: bool = True,
) -> tuple[list[ResponseScore], list[Suggestion]]:
    scores: list[ResponseScore] = []
    suggestions: list[Suggestion] = []

    for i, rec in enumerate(records, 1):
        if progress:
            print(f"  [{variant}] {i}/{len(records)} {rec['id']:<10}", end="\r", flush=True)
        sug = generator.generate_for_record(rec, variant=variant)

        # The retrieved exemplars are legitimate sources for identifiers, so the
        # fabrication check must see them or it flags correct references as invented.
        sources = []
        for ex_id in sug.exemplar_ids:
            ex = next((r for r in generator.retriever.pool if r["id"] == ex_id), None)
            if ex:
                sources += [ex["incoming"]["body"], ex["gold_reply"]["body"]]

        scores.append(scorer.score(sug.body, rec, variant=variant, sources=sources,
                                   generation_error=sug.error))
        suggestions.append(sug)

    if progress:
        print(" " * 70, end="\r")
    return scores, suggestions


def gold_baseline(scorer: Scorer, records: list[dict]) -> dict:
    """Score the human replies under our own metric — the practical ceiling.

    It will not be 100, and the gap is informative rather than embarrassing: it is the
    portion of the metric that penalises legitimate variation. Reporting a system score
    without it invites the reader to compare against an unreachable 100.
    """
    scores = [scorer.score(r["gold_reply"]["body"], r, variant="gold") for r in records]
    agg = aggregate(scores)
    agg["ci"] = bootstrap_ci([s.composite for s in scores]).to_dict()
    return agg


def run_all(
    client: BaseClient,
    judge_client: BaseClient | None = None,
    variants: tuple[str, ...] = ("zero_shot", "static_fewshot", "rag_fewshot",
                                 "rag_plus_stylecard"),
    limit: int | None = None,
    use_llm_intent: bool = True,
    judge_samples: int = 3,
    progress: bool = True,
    intent_client: BaseClient | None = None,
) -> dict:
    from ..retrieval import Retriever
    from .judge import Judge, JudgeConfig

    records, train, test = load_all()
    if limit:
        test = test[:limit]

    retriever = Retriever(train)
    generator = ReplyGenerator(client, retriever)

    judge = None
    if judge_client is not None:
        judge = Judge(judge_client, JudgeConfig(samples=judge_samples),
                      generator_model=client.model)
        if judge.same_family_as_generator:
            print(f"  [warn] judge model ({judge_client.model}) is the same family as the "
                  f"generator ({client.model}). Self-preference bias is likely; the report "
                  f"records this.")

    intent_client = intent_client or judge_client or client
    scorer = build_scorer(train, judge=judge, intent_client=intent_client,
                          use_llm_intent=use_llm_intent)

    started = time.time()
    run: dict = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "generator": {"provider": client.name, "model": client.model},
        "judge": ({"provider": judge_client.name, "model": judge_client.model,
                   "samples": judge_samples,
                   "same_family_as_generator": judge.same_family_as_generator}
                  if judge_client else None),
        "intent_classifier": ({"provider": intent_client.name, "model": intent_client.model}
                              if use_llm_intent and intent_client else
                              {"provider": "offline", "model": "cue-phrases + centroid"}),
        "embedding_backend": scorer.embedder.backend,
        "n_test": len(test),
        "variants": {},
        "responses": [],
    }

    for variant in variants:
        print(f"Generating + scoring: {variant}")
        scores, suggestions = run_variant(generator, scorer, test, variant, progress)
        agg = aggregate(scores)
        agg["ci"] = bootstrap_ci([s.composite for s in scores]).to_dict()
        agg["component_ci"] = {
            k: bootstrap_ci([s.components[k] * 100 for s in scores]).to_dict()
            for k in scores[0].components
        } if scores else {}
        run["variants"][variant] = agg

        for s, sug in zip(scores, suggestions):
            row = s.to_dict()
            row["suggestion"] = sug.to_dict()
            run["responses"].append(row)

        print(f"  {variant}: composite {agg['ci']['mean']:.1f} "
              f"[{agg['ci']['lo']:.1f}, {agg['ci']['hi']:.1f}]  "
              f"sendable {agg['sendable_rate']:.0%}  edit-free {agg['edit_free_rate']:.0%}")

    print("Scoring the human replies (ceiling)")
    run["gold_ceiling"] = gold_baseline(scorer, test)
    print(f"  gold: composite {run['gold_ceiling']['ci']['mean']:.1f}  "
          f"sendable {run['gold_ceiling']['sendable_rate']:.0%}")

    # Report the classifier that actually ran, not the one that was requested. A model
    # that fails every call would otherwise leave the run claiming it was used.
    from collections import Counter

    methods = Counter(r["intent_detail"]["method"] for r in run["responses"])
    run["intent_classifier"]["methods_used"] = dict(methods)
    run["intent_classifier"].update(scorer.intent_classifier.stats())
    if use_llm_intent and not methods.get("llm"):
        run["intent_classifier"]["warning"] = (
            "No reply was classified by the LLM — every call failed and the offline "
            "classifier was used instead. Intent scores are correspondingly weaker."
        )
        print(f"  [warn] intent: 0/{sum(methods.values())} classified by "
              f"{intent_client.model}; fell back to offline cues. "
              f"{scorer.intent_classifier.failure_reasons[:1]}")

    run["elapsed_s"] = round(time.time() - started, 1)
    run["client_stats"] = client.stats()
    if judge_client is not None:
        run["judge_stats"] = judge_client.stats()
    return run


def save_run(run: dict, directory: Path = REPORTS_DIR) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"run_{run['run_id']}.json"
    path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    latest = directory / "latest_run.json"
    latest.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_run(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
