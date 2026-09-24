"""Unit tests for ProductRecommendation domain schemas and immutability."""

import pytest
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from pydantic import ValidationError


def _make_sample_evidence() -> Evidence:
    return Evidence(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket:101",
        finding="Customers reported delayed transfer status.",
        support="Ticket 101",
        confidence=EvidenceConfidence.HIGH,
        limitations=["Small sample size"],
    )


def test_product_recommendation_valid() -> None:
    rec = ProductRecommendation(
        problem_statement="Customers experience transaction delays during peak hours.",
        why_it_matters="Degrades customer satisfaction and trust.",
        affected_users="Mobile wallet checkout users",
        factual_observations=[
            "17 Zendesk tickets mention transfer delays between 10:00 and 12:00 UTC.",
            "Jira incident PAY-117 confirms webhook processing delay.",
        ],
        inferences=[
            "Users perceive transactions as pending indefinitely when webhook callbacks lag."
        ],
        hypotheses=["Client-side polling fallback would alleviate perceived transfer latency."],
        evidence=[_make_sample_evidence()],
        likely_causes=["Associated with core banking callback latency"],
        conflicting_evidence=[],
        recommendation="Implement client-side polling fallback within 24 hours.",
        recommendation_type="prioritise",
        success_metrics=["Transfer support ticket volume decreases by 50%."],
        risks=["Increased polling frequency may increase server traffic."],
        confidence="high",
        open_questions=["What is the maximum acceptable polling interval?"],
    )
    assert rec.recommendation_type == "prioritise"
    assert len(rec.factual_observations) == 2
    assert len(rec.evidence) == 1
    assert rec.confidence == "high"


def test_product_recommendation_is_frozen_immutable() -> None:
    """ProductRecommendation MUST be immutable and raise error on in-place mutation."""
    ev = _make_sample_evidence()
    rec = ProductRecommendation(
        problem_statement="Problem statement describing the issue in full.",
        why_it_matters="Why it matters to users and product business metrics.",
        affected_users="All mobile users",
        factual_observations=["Fact 1 observed"],
        inferences=["Interp 1 inferred"],
        hypotheses=["Hypo 1 plausible"],
        evidence=[ev],
        recommendation="Take this concrete recommendation action.",
        recommendation_type="monitor",
        success_metrics=["Metric 1"],
        risks=["Risk 1"],
        confidence="low",
        open_questions=["Question 1"],
    )

    with pytest.raises(ValidationError):
        rec.problem_statement = "Mutated statement"

    # Verify model_copy(update=...) produces an immutable replacement without mutating original
    new_questions = ["[Unresolved Critic Issue - causal_overreach] Address causal overreach"]
    updated_rec = rec.model_copy(update={"open_questions": [*rec.open_questions, *new_questions]})
    assert rec.open_questions == ["Question 1"]
    assert updated_rec.open_questions == [
        "Question 1",
        "[Unresolved Critic Issue - causal_overreach] Address causal overreach",
    ]
    assert rec is not updated_rec


def test_product_recommendation_validation_failures() -> None:
    """Verify schema bounds on empty fields and minimum lengths."""
    with pytest.raises(ValidationError):
        ProductRecommendation(
            problem_statement="Too short",  # < 10 chars
            why_it_matters="Matters",  # < 10 chars
            affected_users="US",  # < 5 chars
            factual_observations=[],  # min_length=1
            inferences=[],  # min_length=1
            evidence=[],  # min_length=1
            recommendation="Short",  # < 10 chars
            recommendation_type="prioritise",
            success_metrics=[],  # min_length=1
            risks=[],  # min_length=1
            confidence="high",
        )
