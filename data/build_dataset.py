"""Assemble, validate and split the dataset.

The source of truth is the three ``corpus_*.py`` files, which are plain readable Python
rather than a blob of JSON — a dataset you cannot review is a dataset you cannot trust.
This script turns them into ``emails.jsonl`` plus a stratified split, and refuses to write
anything if a record fails validation.

Usage:
    python data/build_dataset.py            # build + validate + split + report
    python data/build_dataset.py --verify   # validate the committed files, write nothing
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from data.schema import CATEGORY_PERSONA, INTENTS, PERSONAS, validate_record  # noqa: E402

EMAILS_PATH = HERE / "emails.jsonl"
SPLITS_PATH = HERE / "splits.json"
SEED = 20250329
TEST_FRACTION = 0.27
#: Above this train/test cosine similarity a test item is effectively memorisable.
LEAKAGE_THRESHOLD = 0.92


def load_source_records() -> list[dict]:
    from data import corpus_business_mgr, corpus_cs_rep, corpus_ops_mgr

    records: list[dict] = []
    for module in (corpus_cs_rep, corpus_ops_mgr, corpus_business_mgr):
        for rec in module.RECORDS:
            rec = dict(rec)
            # Persona is derived, never hand-written, so it cannot contradict the category.
            rec["persona"] = CATEGORY_PERSONA[rec["category"]]
            rec.setdefault("thread_context", "")
            records.append(rec)
    return records


def validate_all(records: list[dict]) -> list[str]:
    problems: list[str] = []
    seen_ids: set[str] = set()
    for rec in records:
        rid = rec.get("id", "<no id>")
        if rid in seen_ids:
            problems.append(f"{rid}: duplicate id")
        seen_ids.add(rid)
        problems.extend(validate_record(rec))
    return problems


def stratified_split(records: list[dict]) -> dict[str, list[str]]:
    """Split by (category, difficulty) so the test set keeps the hard cases proportional.

    Hard cases are the ones that actually discriminate between a good and a lazy reply, so
    a split that quietly dropped them into train would make the headline score meaningless.
    """
    rng = random.Random(SEED)
    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    for rec in records:
        buckets[(rec["category"], rec["difficulty"])].append(rec["id"])

    train, test = [], []
    for key in sorted(buckets):
        ids = sorted(buckets[key])
        rng.shuffle(ids)
        n_test = max(1, round(len(ids) * TEST_FRACTION)) if len(ids) > 2 else 1
        test.extend(ids[:n_test])
        train.extend(ids[n_test:])
    return {"train": sorted(train), "test": sorted(test)}


def leakage_report(records: list[dict], splits: dict[str, list[str]]) -> dict:
    """How close is the nearest training email to each test email?

    If a test item has a near-identical twin in the retrieval pool, a high score proves
    nothing except that copying works. We measure this rather than asserting it doesn't
    happen, and the number goes in the README.
    """
    from src.embeddings import get_embedder

    by_id = {r["id"]: r for r in records}
    train_ids, test_ids = splits["train"], splits["test"]

    def text(rid: str) -> str:
        r = by_id[rid]
        return f"{r['incoming']['subject']}\n{r['incoming']['body']}"

    embedder = get_embedder()
    embedder.fit_background([text(r["id"]) for r in records])
    sims = embedder.similarity_matrix([text(i) for i in test_ids], [text(i) for i in train_ids])

    rows = []
    for i, tid in enumerate(test_ids):
        j = int(sims[i].argmax())
        rows.append({"test_id": tid, "nearest_train_id": train_ids[j], "similarity": round(float(sims[i][j]), 4)})
    rows.sort(key=lambda r: -r["similarity"])

    over = [r for r in rows if r["similarity"] >= LEAKAGE_THRESHOLD]
    return {
        "backend": embedder.backend,
        "max_similarity": rows[0]["similarity"] if rows else 0.0,
        "mean_max_similarity": round(sum(r["similarity"] for r in rows) / max(len(rows), 1), 4),
        "threshold": LEAKAGE_THRESHOLD,
        "n_over_threshold": len(over),
        "over_threshold": over,
        "top_5": rows[:5],
    }


def describe(records: list[dict], splits: dict[str, list[str]] | None = None) -> str:
    cats = Counter(r["category"] for r in records)
    pers = Counter(r["persona"] for r in records)
    diff = Counter(r["difficulty"] for r in records)
    ints = Counter(r["intent_label"] for r in records)
    review = Counter(r["requires_human_review"] for r in records)
    n_con = sum(len(r["must_include"]) for r in records)
    n_forb = sum(len(r["must_not_include"]) for r in records)

    lines = [f"Records: {len(records)}", ""]
    lines.append("By category:")
    for k, v in sorted(cats.items()):
        lines.append(f"  {k:<12} {v:>4}")
    lines.append("\nBy persona:")
    for k, v in sorted(pers.items()):
        lines.append(f"  {k:<14} {v:>4}  ({PERSONAS[k].name}, {PERSONAS[k].role})")
    lines.append("\nBy difficulty:")
    for k, v in sorted(diff.items()):
        lines.append(f"  {k:<12} {v:>4}")
    lines.append("\nBy intent label:")
    for k, v in sorted(ints.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {k:<24} {v:>4}")
    lines.append(f"\nrequires_human_review: True={review[True]}  False={review[False]}")
    lines.append(f"must_include constraints:     {n_con} (mean {n_con/len(records):.2f} per record)")
    lines.append(f"must_not_include constraints: {n_forb} (mean {n_forb/len(records):.2f} per record)")

    if splits:
        lines.append(f"\nSplit: train={len(splits['train'])}  test={len(splits['test'])}")
        by_id = {r["id"]: r for r in records}
        for name in ("train", "test"):
            c = Counter(by_id[i]["category"] for i in splits[name])
            d = Counter(by_id[i]["difficulty"] for i in splits[name])
            lines.append(f"  {name}: " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())))
            lines.append(f"         hard={d['hard']} normal={d['normal']}")
    return "\n".join(lines)


def write_outputs(records: list[dict], splits: dict[str, list[str]]) -> None:
    with EMAILS_PATH.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    SPLITS_PATH.write_text(json.dumps(splits, indent=2), encoding="utf-8")


def load_dataset(path: Path = EMAILS_PATH) -> list[dict]:
    """Read the built dataset.

    This is the seam to replace if you want to run the system on real mail: return records
    in the same shape from wherever they live (mbox, Gmail API, a warehouse table) and
    everything downstream works unchanged.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run: python data/build_dataset.py")
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_splits(path: Path = SPLITS_PATH) -> dict[str, list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run: python data/build_dataset.py")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Build and validate the email dataset.")
    ap.add_argument("--verify", action="store_true",
                    help="Validate the committed dataset without rewriting it.")
    ap.add_argument("--no-leakage", action="store_true",
                    help="Skip the embedding-based leakage check (faster).")
    args = ap.parse_args()

    if args.verify:
        records = load_dataset()
        splits = load_splits()
        print(f"Verifying committed dataset ({EMAILS_PATH.name})\n")
    else:
        records = load_source_records()
        splits = stratified_split(records)
        print("Building dataset from corpus_*.py\n")

    problems = validate_all(records)
    if problems:
        print(f"VALIDATION FAILED — {len(problems)} problem(s):\n")
        for p in problems[:60]:
            print(f"  - {p}")
        if len(problems) > 60:
            print(f"  ... and {len(problems) - 60} more")
        return 1

    print(f"Validation passed: {len(records)} records, {len(INTENTS)} intent labels.\n")
    print(describe(records, splits))

    if not args.no_leakage:
        print("\nTrain/test leakage check")
        rep = leakage_report(records, splits)
        print(f"  embedding backend : {rep['backend']}")
        print(f"  max similarity    : {rep['max_similarity']:.3f}  (threshold {rep['threshold']})")
        print(f"  mean nearest      : {rep['mean_max_similarity']:.3f}")
        print(f"  over threshold    : {rep['n_over_threshold']}")
        for row in rep["top_5"]:
            print(f"    {row['test_id']:<10} <- {row['nearest_train_id']:<10} {row['similarity']:.3f}")
        if rep["n_over_threshold"]:
            print("  WARNING: near-duplicate test items found; scores on them are not informative.")

    if not args.verify:
        write_outputs(records, splits)
        print(f"\nWrote {EMAILS_PATH.relative_to(ROOT)} and {SPLITS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
