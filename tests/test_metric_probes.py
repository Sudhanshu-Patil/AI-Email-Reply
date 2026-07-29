"""The metric's own test suite.

These are discriminant-validity assertions: damage a known-good reply in one specific way
and require the metric to notice that and only that. They run with no API key, which is
what makes "the evaluation system works" a checkable claim rather than a promise.
"""

import pytest

from src.eval.harness import build_scorer, load_all, run_probes
from src.eval.metrics import HARD_FAIL_CAP
from src.eval.probes import build_probes


@pytest.fixture(scope="module")
def data():
    return load_all()


@pytest.fixture(scope="module")
def scorer(data):
    _, train, _ = data
    return build_scorer(train)


@pytest.fixture(scope="module")
def probe_run(data, scorer):
    _, _, test = data
    return run_probes(test, scorer)


def test_all_probe_assertions_hold(probe_run):
    checks, summary = probe_run
    failures = [f"{c.name}: {c.detail}" for c in checks if not c.passed]
    assert not failures, (
        f"{len(failures)}/{summary['n_checks']} metric assertions failed:\n"
        + "\n".join(failures[:10])
    )


def test_probe_ordering_is_sane(probe_run):
    """The overall ranking of probe classes must match their construction."""
    _, summary = probe_run
    m = summary["mean_composite_by_probe"]
    assert m["gold"] > m["gold_slang"], "style damage should cost less than being wrong"
    assert m["gold_slang"] > m["generic"]
    assert m["gold"] > m["wrong_email"]
    assert m["generic"] < 45, "a contentless reply must not score respectably"


def test_human_replies_score_near_the_ceiling(probe_run):
    _, summary = probe_run
    assert summary["mean_composite_by_probe"]["gold"] > 80


def test_hard_fail_classes_are_capped(probe_run):
    _, summary = probe_run
    for probe in ("gold_forbidden", "gold_placeholder"):
        assert summary["mean_composite_by_probe"][probe] <= HARD_FAIL_CAP


class TestDiscriminance:
    """Damage to one dimension must not leak into the others."""

    def test_style_damage_leaves_facts_alone(self, data, scorer):
        _, _, test = data
        for rec in test[:12]:
            probes = {p.name: p for p in build_probes(rec)}
            gold = scorer.score(probes["gold"].reply, rec)
            slang = scorer.score(probes["gold_slang"].reply, rec)
            assert slang.components["style"] < gold.components["style"], rec["id"]
            assert slang.components["grounding"] >= gold.components["grounding"] - 1e-6, (
                f"{rec['id']}: register change must not move the factual score")

    def test_fact_corruption_hard_fails(self, data, scorer):
        _, _, test = data
        checked = 0
        for rec in test:
            probes = {p.name: p for p in build_probes(rec)}
            if "gold_fact_corrupted" not in probes:
                continue
            checked += 1
            s = scorer.score(probes["gold_fact_corrupted"].reply, rec)
            assert not s.sendable, f"{rec['id']}: a wrong figure must not be sendable"
            assert s.composite <= HARD_FAIL_CAP
        assert checked >= 10, "too few records exercised this probe to be meaningful"

    def test_forbidden_claim_hard_fails(self, data, scorer):
        _, _, test = data
        for rec in test:
            probes = {p.name: p for p in build_probes(rec)}
            if "gold_forbidden" not in probes:
                continue
            s = scorer.score(probes["gold_forbidden"].reply, rec)
            assert not s.sendable, f"{rec['id']}: forbidden claim must hard-fail"


class TestGate:
    def test_empty_reply_scores_zero_and_fails(self, data, scorer):
        _, _, test = data
        s = scorer.score("", test[0])
        assert not s.sendable and s.composite == 0.0

    def test_generation_error_is_scored_not_dropped(self, data, scorer):
        """A failed call must land in the denominator, not vanish and flatter the mean."""
        _, _, test = data
        s = scorer.score("", test[0], generation_error="429 rate limited")
        assert not s.sendable
        assert any("generation failed" in h for h in s.hard_fails)

    def test_explanation_is_produced(self, data, scorer):
        _, _, test = data
        rec = test[0]
        s = scorer.score(rec["gold_reply"]["body"], rec)
        assert len(s.explain()) > 20
