"""Tests verifying strict isolation across dev, validation, and holdout scenario partitions."""

import pytest
from evaluations.dataset.loader import get_scenarios


def test_scenario_partition_counts_and_isolation() -> None:
    """Verify exactly 25 dev, 10 val, and 10 holdout scenarios exist with zero overlap."""
    dev_scenarios = get_scenarios("dev")
    val_scenarios = get_scenarios("val")
    holdout_scenarios = get_scenarios("holdout")

    assert len(dev_scenarios) == 25
    assert len(val_scenarios) == 10
    assert len(holdout_scenarios) == 10

    dev_ids = {s.scenario_id for s in dev_scenarios}
    val_ids = {s.scenario_id for s in val_scenarios}
    holdout_ids = {s.scenario_id for s in holdout_scenarios}

    # Zero overlap across partitions
    assert len(dev_ids & val_ids) == 0, "Leakage between dev and val partitions"
    assert len(dev_ids & holdout_ids) == 0, "Leakage between dev and holdout partitions"
    assert len(val_ids & holdout_ids) == 0, "Leakage between val and holdout partitions"


def test_scenario_lifecycle_isolation_rules() -> None:
    """Verify explicit evaluation lifecycle partitioning:
    - dev -> development / prompt tuning
    - val -> qualification / selection / model choice
    - holdout -> final locked evaluation only
    """
    holdout_scenarios = get_scenarios("holdout")
    for s in holdout_scenarios:
        # Holdout scenarios must be fully specified ground truth, but must not be used for tuning
        assert s.split == "holdout"
        assert len(s.acceptable_conclusions) > 0
        assert len(s.unacceptable_conclusions) > 0
        assert s.version == "1.0"


def test_holdout_immutability() -> None:
    """Verify that scenarios are frozen Pydantic models preventing in-memory tampering."""
    from pydantic import ValidationError

    holdout_scenario = get_scenarios("holdout")[0]
    with pytest.raises(ValidationError):
        holdout_scenario.split = "dev"
