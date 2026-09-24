"""Unit tests for evaluation ground truth definitions."""

from evaluations.scenarios import (
    ALL_GROUND_TRUTH_SCENARIOS,
    BILL_PAYMENT_GROUND_TRUTH,
    KYC_ABANDONMENT_GROUND_TRUTH,
    TRANSFER_DELAYS_GROUND_TRUTH,
    WALLET_FUNDING_GROUND_TRUTH,
    ScenarioGroundTruth,
)


def test_ground_truth_scenarios_registered() -> None:
    """Verify all 4 ground truth scenarios are validated and registered."""
    assert len(ALL_GROUND_TRUTH_SCENARIOS) == 4
    for scenario in ALL_GROUND_TRUTH_SCENARIOS:
        assert isinstance(scenario, ScenarioGroundTruth)
        assert len(scenario.expected_findings) >= 1
        assert len(scenario.acceptable_conclusions) >= 1
        assert len(scenario.unacceptable_conclusions) >= 1
        assert set(scenario.required_evidence_sources) == {
            "zendesk",
            "posthog",
            "jira",
        }


def test_transfer_delays_ground_truth() -> None:
    """Verify Scenario A ground truth properties."""
    gt = TRANSFER_DELAYS_GROUND_TRUTH
    assert gt.scenario_id == "scenario_a_transfer_delays"
    assert gt.expected_recommendation_type == "prioritise"
    assert any("PAY-117" in f for f in gt.expected_findings)
    assert any("flat" in c or "stable" in c for c in gt.contradictory_evidence)
    assert any("failed" in t for t in gt.known_traps)


def test_kyc_abandonment_ground_truth() -> None:
    """Verify Scenario B ground truth properties."""
    gt = KYC_ABANDONMENT_GROUND_TRUTH
    assert gt.scenario_id == "scenario_b_kyc_abandonment"
    assert gt.expected_recommendation_type == "experiment"
    assert any("CORE-82" in f for f in gt.expected_findings)
    assert any("sole or primary" in u for u in gt.unacceptable_conclusions)


def test_wallet_funding_ground_truth() -> None:
    """Verify Scenario C ground truth properties."""
    gt = WALLET_FUNDING_GROUND_TRUTH
    assert gt.scenario_id == "scenario_c_wallet_funding"
    assert gt.expected_recommendation_type == "investigate_further"
    assert any("zero open issues" in f for f in gt.expected_findings)


def test_bill_payment_ground_truth() -> None:
    """Verify Scenario D ground truth properties."""
    gt = BILL_PAYMENT_GROUND_TRUTH
    assert gt.scenario_id == "scenario_d_bill_payment"
    assert gt.expected_recommendation_type == "technical_remediation"
    assert any("PAY-134" in f for f in gt.expected_findings)
