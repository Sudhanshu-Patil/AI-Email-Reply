"""Human rating workflow — the ground truth the metric is validated against.

The metric claims to predict whether a person would send a draft. The only way to check
that claim is to ask a person. This module exports a stratified sample of generated
replies for rating and reads the ratings back.

The rating scale is the same one the judge uses, deliberately, so the two are comparable:

    5  send as-is
    4  one small edit
    3  several edits
    2  substantial rewrite
    1  discard, or actively harmful to send

**The sample is stratified across variants and difficulty, and shuffled with a fixed
seed.** Rating a convenience sample of whatever is at the top of the file would correlate
with position rather than quality, and rating only the good variant would compress the
range and inflate the correlation.

Ratings are written *without* the metric's score visible, so the label cannot be anchored
by the number it is supposed to validate.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RATINGS_PATH = ROOT / "data" / "human_ratings.jsonl"

SCALE = {
    5: "send as-is",
    4: "one small edit",
    3: "several edits",
    2: "substantial rewrite",
    1: "discard or harmful to send",
}


def sample_for_rating(run: dict, n: int = 40, seed: int = 20250329) -> list[dict]:
    """Stratified, shuffled sample of responses to rate."""
    by_bucket: dict[tuple[str, str], list[dict]] = {}
    for r in run["responses"]:
        by_bucket.setdefault((r["variant"], r["difficulty"]), []).append(r)

    rng = random.Random(seed)
    for rows in by_bucket.values():
        rng.shuffle(rows)

    picked: list[dict] = []
    buckets = sorted(by_bucket)
    i = 0
    # Round-robin across buckets so no variant or difficulty dominates the sample.
    while len(picked) < n and any(by_bucket[b] for b in buckets):
        bucket = buckets[i % len(buckets)]
        if by_bucket[bucket]:
            picked.append(by_bucket[bucket].pop())
        i += 1

    rng.shuffle(picked)
    return picked


def export_template(run: dict, path: Path, n: int = 40, seed: int = 20250329) -> int:
    """Write a rating template. Metric scores are omitted on purpose."""
    from data.build_dataset import load_dataset

    by_id = {r["id"]: r for r in load_dataset()}
    rows = sample_for_rating(run, n=n, seed=seed)

    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            rec = by_id[row["record_id"]]
            fh.write(json.dumps({
                "record_id": row["record_id"],
                "variant": row["variant"],
                "sendability": None,          # <- fill in 1-5
                "note": "",
                "_incoming_subject": rec["incoming"]["subject"],
                "_incoming_body": rec["incoming"]["body"],
                "_human_reply": rec["gold_reply"]["body"],
                "_draft": row["reply_body"],
            }, ensure_ascii=False) + "\n")
    return len(rows)


def load_ratings(path: Path = RATINGS_PATH) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("sendability") is not None:
                out.append(row)
    return out


def strip_context(rows: list[dict]) -> list[dict]:
    """Drop the `_`-prefixed helper fields before committing the ratings."""
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
