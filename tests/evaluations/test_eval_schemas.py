"""Unit tests for evaluation schemas and scenario quota enforcement."""

import pytest
from evaluations.dataset.loader import (
    ALL_SCENARIOS,
    DatasetQuotaError,
    get_scenario_by_id,
    get_scenarios,
    validate_scenario_quotas,
)


def test_scenario_dataset_count_and_uniqueness() -> None:
    """Verify exactly 45 unique scenarios exist."""
    assert len(ALL_SCENARIOS) == 45
    scenario_ids = [s.scenario_id for s in ALL_SCENARIOS]
    assert len(set(scenario_ids)) == 45


def test_scenario_splits_distribution() -> None:
    """Verify exact 25 dev, 10 val, 10 holdout split distribution."""
    dev = get_scenarios("dev")
    val = get_scenarios("val")
    holdout = get_scenarios("holdout")

    assert len(dev) == 25
    assert len(val) == 10
    assert len(holdout) == 10


def test_scenario_quotas_all_satisfied() -> None:
    """Verify all 11 coverage quotas meet or exceed minimum requirements."""
    quotas = validate_scenario_quotas(ALL_SCENARIOS)

    assert quotas["contradictions"] >= 8
    assert quotas["causal_traps"] >= 6
    assert quotas["critic_true_positives"] >= 8
    assert quotas["critic_true_negatives"] >= 10
    assert quotas["segmentation_traps"] >= 5
    assert quotas["magnitude_traps"] >= 5
    assert quotas["source_outages"] >= 4
    assert quotas["adversarial_injections"] >= 4
    assert quotas["single_source"] >= 6
    assert quotas["multi_source"] >= 25
    assert quotas["missing_evidence"] >= 6


def test_get_scenario_by_id() -> None:
    """Verify scenario lookup by ID."""
    scn = get_scenario_by_id("scn_001")
    assert scn.scenario_id == "scn_001"
    assert scn.product_area == "Transfers"

    with pytest.raises(KeyError):
        get_scenario_by_id("nonexistent_id")


def test_quota_validation_fails_on_truncated_dataset() -> None:
    """Verify quota validator raises DatasetQuotaError if scenario count is wrong."""
    with pytest.raises(DatasetQuotaError, match="Expected exactly 45"):
        validate_scenario_quotas(ALL_SCENARIOS[:40])
