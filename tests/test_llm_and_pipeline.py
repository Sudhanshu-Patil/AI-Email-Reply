"""Provider plumbing, retry policy, dataset integrity, and an end-to-end run on mock."""

import json

import pytest

from src.eval.constraints import check_constraint, check_forbidden
from src.llm.base import (AuthError, BadRequestError, RateLimitError, TokenBucket,
                          TransientError, extract_json, with_retry)
from src.llm.keys import mask, redact
from src.llm.providers import get_client, model_family, pick_judge_model


class TestRetryPolicy:
    def test_auth_errors_are_never_retried(self):
        """A bad key must fail immediately — retrying only delays a clear message."""
        calls = {"n": 0}

        def bad():
            calls["n"] += 1
            raise Exception("Error code: 401 - Invalid API Key")

        with pytest.raises(AuthError):
            with_retry(bad, max_attempts=4, base_delay=0.001)
        assert calls["n"] == 1

    def test_bad_request_is_never_retried(self):
        calls = {"n": 0}

        def bad():
            calls["n"] += 1
            raise Exception("Error code: 404 - model_not_found")

        with pytest.raises(BadRequestError):
            with_retry(bad, max_attempts=4, base_delay=0.001)
        assert calls["n"] == 1

    def test_transient_errors_retry_then_succeed(self):
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise Exception("Error code: 503 - service temporarily unavailable")
            return "ok"

        result, attempts = with_retry(flaky, max_attempts=4, base_delay=0.001)
        assert result == "ok" and attempts == 3

    def test_rate_limit_is_retried_then_raised(self):
        calls = {"n": 0}

        def limited():
            calls["n"] += 1
            raise Exception("Rate limit reached, please try again in 0.01s")

        with pytest.raises(RateLimitError):
            with_retry(limited, max_attempts=3, base_delay=0.001)
        assert calls["n"] == 3

    def test_retry_after_is_parsed_from_the_message(self):
        try:
            with_retry(lambda: (_ for _ in ()).throw(
                Exception("Rate limit reached, please try again in 2.5s")),
                max_attempts=1, base_delay=0.001)
        except RateLimitError as exc:
            assert exc.retry_after == 2.5


class TestJsonExtraction:
    def test_plain_object(self):
        assert extract_json('{"a": 1}') == {"a": 1}

    def test_fenced_block(self):
        assert extract_json('sure:\n```json\n{"a": 1}\n```\n') == {"a": 1}

    def test_braces_inside_strings(self):
        assert extract_json('noise {"x": {"y": "}"}} tail') == {"x": {"y": "}"}}

    def test_empty_raises(self):
        from src.llm.base import OutputParseError

        with pytest.raises(OutputParseError):
            extract_json("   ")


class TestKeyHandling:
    def test_mask_hides_the_middle(self):
        m = mask("gsk_abcdefghijklmnopqrstuvwxyz")
        assert "abcdefghijklmnop" not in m and m.endswith("wxyz")

    def test_redact_scrubs_keys_from_text(self):
        text = "failed with key sk-abcdefghijklmnopqrstuvwxyz012345 while calling"
        out = redact(text)
        assert "abcdefghijklmnopqrstuvwxyz012345" not in out

    def test_redact_handles_groq_and_google_prefixes(self):
        assert "1234567890abcdefghij" not in redact("gsk_1234567890abcdefghij")
        assert "SyAbcdefghijklmnop123" not in redact("AIzaSyAbcdefghijklmnop123")


class TestProviderSelection:
    def test_families_are_distinguished(self):
        assert model_family("openai/gpt-oss-120b") == "gpt-oss"
        assert model_family("llama-3.3-70b-versatile") == "llama"
        assert model_family("gemini-2.0-flash") == "gemini"

    def test_judge_prefers_a_different_family(self):
        client = get_client("mock", interactive=False, cache=False)
        client.preferred_models = ("llama-3.3-70b", "openai/gpt-oss-120b")
        assert model_family(pick_judge_model(client, "llama-3.3-70b")) != "llama"

    def test_mock_needs_no_key(self):
        c = get_client("mock", interactive=False, cache=False)
        assert c.complete("sys", "user").text


class TestTokenBucket:
    def test_permits_burst_up_to_capacity(self):
        import time

        b = TokenBucket(rpm=6000)
        t0 = time.monotonic()
        for _ in range(10):
            b.acquire()
        assert time.monotonic() - t0 < 1.0


class TestDataset:
    def test_every_record_validates(self):
        from data.build_dataset import load_dataset, validate_all

        problems = validate_all(load_dataset())
        assert not problems, f"{len(problems)} invalid record(s): {problems[:5]}"

    def test_gold_replies_satisfy_their_own_constraints(self):
        """The dataset cannot demand something the scorer would fail the human for."""
        from data.build_dataset import load_dataset

        for rec in load_dataset():
            body = rec["gold_reply"]["body"]
            for phrase in rec["must_include"]:
                assert check_constraint(phrase, body).satisfied, (
                    f"{rec['id']}: gold fails required {phrase!r}")
            for phrase in rec["must_not_include"]:
                assert not check_forbidden(phrase, body).satisfied, (
                    f"{rec['id']}: gold asserts forbidden {phrase!r}")

    def test_splits_are_disjoint_and_complete(self):
        from data.build_dataset import load_dataset, load_splits

        ids = {r["id"] for r in load_dataset()}
        s = load_splits()
        assert not set(s["train"]) & set(s["test"])
        assert set(s["train"]) | set(s["test"]) == ids

    def test_hard_cases_are_present_in_the_test_split(self):
        from data.build_dataset import load_dataset, load_splits

        by_id = {r["id"]: r for r in load_dataset()}
        hard = [i for i in load_splits()["test"] if by_id[i]["difficulty"] == "hard"]
        assert len(hard) >= 5, "the test split must retain the discriminating cases"


class TestEndToEndOnMock:
    def test_generate_and_score_without_any_api_key(self):
        from src.eval.harness import build_scorer, load_all
        from src.generate import ReplyGenerator
        from src.retrieval import Retriever

        _, train, test = load_all()
        gen = ReplyGenerator(get_client("mock", interactive=False, cache=False),
                             Retriever(train))
        scorer = build_scorer(train)

        rec = test[0]
        s = gen.generate_for_record(rec, variant="rag_fewshot")
        assert s.exemplar_ids and s.body
        assert rec["id"] not in s.exemplar_ids, "a record must never retrieve itself"

        score = scorer.score(s.body, rec, variant="rag_fewshot")
        assert 0.0 <= score.composite <= 100.0
        assert set(score.components) == {"grounding", "intent", "similarity", "style",
                                         "sendability"}
        assert json.dumps(score.to_dict())  # the run file must be serialisable

    def test_all_variants_run(self):
        from src.generate import VARIANTS, ReplyGenerator
        from src.eval.harness import load_all
        from src.retrieval import Retriever

        _, train, test = load_all()
        gen = ReplyGenerator(get_client("mock", interactive=False, cache=False),
                             Retriever(train))
        for variant in VARIANTS:
            s = gen.generate_for_record(test[0], variant=variant)
            assert s.body, variant
            if variant == "zero_shot":
                assert not s.exemplar_ids


class TestStats:
    def test_bootstrap_is_deterministic(self):
        from src.eval.stats import bootstrap_ci

        vals = [10, 20, 30, 40, 50, 60]
        assert bootstrap_ci(vals).to_dict() == bootstrap_ci(vals).to_dict()

    def test_spearman_detects_monotone_relationships(self):
        from src.eval.stats import spearman

        assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
        assert spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)

    def test_kendall_handles_ties(self):
        from src.eval.stats import kendall_tau_b

        assert -1.0 <= kendall_tau_b([1, 1, 2, 2], [1, 2, 2, 3]) <= 1.0
