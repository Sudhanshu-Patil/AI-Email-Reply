"""Confidence intervals and rank correlations.

Two ideas do most of the work here.

**Never report a bare mean.** With 29 test items, the difference between 71 and 74 is
noise. Every headline number carries a bootstrap interval so a reader can see whether a
gap between two variants is real. A comparison whose intervals overlap heavily has not
demonstrated anything, and saying so is more useful than a leaderboard.

**Rank correlation, not Pearson.** The claim being tested is "when the metric says one
reply is better than another, a human agrees" — an ordering claim. Spearman and Kendall
test exactly that and do not assume the 1–5 human scale is linear, which it is not: the
gap between "send as-is" and "one small edit" is not the same size as the gap between
"several edits" and "discard".
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Interval:
    mean: float
    lo: float
    hi: float
    n: int

    def __str__(self) -> str:
        return f"{self.mean:.1f} [{self.lo:.1f}, {self.hi:.1f}]"

    def overlaps(self, other: "Interval") -> bool:
        return not (self.hi < other.lo or other.hi < self.lo)

    def to_dict(self) -> dict:
        return {"mean": round(self.mean, 2), "lo": round(self.lo, 2),
                "hi": round(self.hi, 2), "n": self.n}


def bootstrap_ci(values: list[float], iterations: int = 2000, alpha: float = 0.05,
                 seed: int = 20250329) -> Interval:
    """Percentile bootstrap over the items. Deterministic given ``seed``."""
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return Interval(0.0, 0.0, 0.0, 0)
    mean = sum(vals) / n
    if n == 1:
        return Interval(mean, mean, mean, 1)

    rng = random.Random(seed)
    means = []
    for _ in range(iterations):
        means.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int((alpha / 2) * iterations)]
    hi = means[min(int((1 - alpha / 2) * iterations), iterations - 1)]
    return Interval(mean, lo, hi, n)


# --------------------------------------------------------------------------- ranks


def _ranks(values: list[float]) -> list[float]:
    """Average ranks, ties shared — required for Spearman to be correct with ties."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx < 1e-12 or dy < 1e-12:
        return 0.0
    return num / (dx * dy)


def spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    return pearson(_ranks(xs), _ranks(ys))


def kendall_tau_b(xs: list[float], ys: list[float]) -> float:
    """Tau-b — handles the heavy tie structure of a 1–5 human scale correctly."""
    n = len(xs)
    if n < 2:
        return 0.0
    conc = disc = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = xs[i] - xs[j], ys[i] - ys[j]
            p = dx * dy
            if p > 0:
                conc += 1
            elif p < 0:
                disc += 1
            else:
                if dx == 0 and dy != 0:
                    tx += 1
                elif dy == 0 and dx != 0:
                    ty += 1
                else:
                    tx += 1
                    ty += 1
    denom = math.sqrt((conc + disc + tx) * (conc + disc + ty))
    return (conc - disc) / denom if denom > 0 else 0.0


def correlation_report(metric_scores: list[float], human_scores: list[float]) -> dict:
    n = len(metric_scores)
    rho = spearman(metric_scores, human_scores)
    return {
        "n": n,
        "spearman_rho": round(rho, 4),
        "kendall_tau_b": round(kendall_tau_b(metric_scores, human_scores), 4),
        "pearson_r": round(pearson(metric_scores, human_scores), 4),
        # Fisher z approximation; with n around 40 the interval is wide and should be
        # reported as such rather than quoted as a point estimate.
        "spearman_95ci": _fisher_ci(rho, n),
    }


def _fisher_ci(rho: float, n: int) -> list[float]:
    if n < 5 or abs(rho) >= 0.999:
        return [-1.0, 1.0]
    z = 0.5 * math.log((1 + rho) / (1 - rho))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se
    return [round(math.tanh(lo), 4), round(math.tanh(hi), 4)]
