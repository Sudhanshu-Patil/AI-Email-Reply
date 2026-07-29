"""The constraint matcher — the component the whole grounding score rests on."""

import pytest

from src.eval.constraints import (check_constraint, check_forbidden, hard_tokens,
                                  sentence_polarity, stem)


class TestStemming:
    @pytest.mark.parametrize("a,b", [
        ("save", "saving"), ("cover", "covers"), ("cover", "covered"),
        ("notice", "notices"), ("provide", "provided"), ("change", "changed"),
        ("apply", "applying"),
    ])
    def test_symmetric(self, a, b):
        """Asymmetric stemming silently breaks matching in one direction only."""
        assert stem(a) == stem(b), f"{a!r} and {b!r} must stem alike"

    def test_short_tokens_untouched(self):
        assert stem("did") == "did"
        assert stem("not") == "not"


class TestRequiredFacts:
    def test_exact_phrase(self):
        r = check_constraint("ticket #4821", "I've reopened ticket #4821 for you.")
        assert r.satisfied and r.method == "exact"

    def test_paraphrase_by_tokens(self):
        r = check_constraint("escalated to the platform team",
                             "I have escalated this to our platform team.")
        assert r.satisfied

    def test_wrong_identifier_fails(self):
        r = check_constraint("ticket #4821", "I've reopened ticket #4822 for you.")
        assert not r.satisfied
        assert "#4821" in r.missing_hard_tokens

    def test_wrong_amount_fails(self):
        r = check_constraint("$1,250 credit", "I applied a $1,150 credit to your account.")
        assert not r.satisfied

    def test_missing_percentage_fails(self):
        r = check_constraint("20% discount", "We can extend a discount for the first year.")
        assert not r.satisfied

    def test_negative_constraint_met_by_negative_reply(self):
        """A required fact can itself be a refusal — polarity must MATCH, not be absent."""
        r = check_constraint("cannot authorise a full refund",
                             "I'm not able to authorise a full refund.")
        assert r.satisfied

    def test_negative_constraint_not_met_by_positive_reply(self):
        r = check_constraint("cannot authorise a full refund",
                             "I have authorised a full refund.")
        assert not r.satisfied


class TestForbiddenClaims:
    def test_asserted_claim_is_a_violation(self):
        assert check_forbidden("full refund", "I've processed a full refund.").satisfied

    def test_denied_claim_is_not_a_violation(self):
        """The single most important false positive to avoid."""
        r = check_forbidden("full refund",
                            "I'm not able to offer a full refund, but I can offer credit.")
        assert not r.satisfied and r.negated

    def test_cannot_phrasing_is_not_a_violation(self):
        assert not check_forbidden(
            "full refund", "We cannot provide a full refund under the policy.").satisfied

    def test_partial_overlap_is_not_a_violation(self):
        """Forbidden checks demand every token — 4-of-5 must not trip a hard fail."""
        r = check_forbidden("pricing has increased on the reissued quote",
                            "Quote Q-3391 has been reissued with the same pricing.")
        assert not r.satisfied

    def test_scattered_tokens_are_not_a_violation(self):
        r = check_forbidden("your start date is confirmed as",
                            "I will confirm the formal start date once you have given notice.")
        assert not r.satisfied

    def test_unrelated_text_is_not_a_violation(self):
        assert not check_forbidden("full refund", "I've issued a 20% credit.").satisfied


class TestPolarityScoping:
    def test_negator_inside_the_constraint_span(self):
        assert sentence_polarity("this message did not come from Northwind",
                                 {"message", "come", "northwind", "not"})

    def test_negation_in_a_different_clause_does_not_leak(self):
        """'Not mine either - scope questions sit with Nadia' is not a denial of the fact."""
        assert not sentence_polarity(
            "Not mine either - scope questions sit with Nadia in Compliance",
            {"scope", "questions", "sit", "nadia", "compliance"})

    def test_negation_later_in_sentence_does_not_flip_earlier_claim(self):
        assert not sentence_polarity(
            "a full refund is not something I can reverse later", {"full", "refund"})


class TestHardTokens:
    def test_extracts_money_ids_and_percentages(self):
        toks = hard_tokens("Invoice INV-20412 for $1,250 at 20% by 30 June")
        assert "20412" in " ".join(toks) or "inv-20412" in " ".join(toks).lower()
        assert any("1250" in t for t in toks)
        assert any("20%" in t for t in toks)

    def test_contradiction_detected_not_mere_omission(self):
        omitted = check_constraint("$1,250 credit",
                                   "I have applied a credit to your account.")
        contradicted = check_constraint("$1,250 credit",
                                        "I have applied a $1,150 credit to your account.")
        assert not omitted.satisfied and not omitted.contradicted
        assert not contradicted.satisfied and contradicted.contradicted

    @pytest.mark.parametrize("constraint,reply,expect", [
        ("RMA-2291", "Your RMA-8891 is raised.", True),
        ("RMA-2291", "Your RMA-2291 is raised.", False),
        ("RMA-2291", "A replacement is on its way.", False),
        ("INV-20455", "I will reissue INV-20456 for you.", True),
    ])
    def test_wrong_identifier_is_a_contradiction(self, constraint, reply, expect):
        """A bare identifier shares no words with the wrong one, so topic overlap is 0.

        Without a prefix-aware check this whole class — the one retrieval actually
        produces, by echoing a reference number from a similar past email — is scored as a
        mere omission.
        """
        assert check_constraint(constraint, reply).contradicted is expect
