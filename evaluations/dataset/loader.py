"""Dataset loader, validation, and quota enforcement for Phase 9 evaluations."""

from typing import Literal

from evaluations.dataset.scenarios.bill_payment_scenarios import BILL_PAYMENT_SCENARIOS
from evaluations.dataset.scenarios.funding_scenarios import FUNDING_SCENARIOS
from evaluations.dataset.scenarios.kyc_scenarios import KYC_SCENARIOS
from evaluations.dataset.scenarios.transfer_scenarios import TRANSFER_SCENARIOS
from evaluations.ground_truth.schema import EvaluationScenario, ScenarioSplit

ALL_SCENARIOS: list[EvaluationScenario] = [
    *TRANSFER_SCENARIOS,
    *KYC_SCENARIOS,
    *FUNDING_SCENARIOS,
    *BILL_PAYMENT_SCENARIOS,
]


class DatasetQuotaError(ValueError):
    """Raised when the evaluation dataset violates coverage quota requirements."""


def validate_scenario_quotas(scenarios: list[EvaluationScenario]) -> dict[str, int]:
    """Verify that the evaluation scenario corpus satisfies all approved coverage quotas."""
    if len(scenarios) != 45:
        raise DatasetQuotaError(f"Expected exactly 45 evaluation scenarios, found {len(scenarios)}")

    # Check ID uniqueness
    scenario_ids = [s.scenario_id for s in scenarios]
    if len(set(scenario_ids)) != len(scenario_ids):
        raise DatasetQuotaError("Duplicate scenario_id detected in dataset")

    # Split counts
    dev_count = sum(1 for s in scenarios if s.split == "dev")
    val_count = sum(1 for s in scenarios if s.split == "val")
    holdout_count = sum(1 for s in scenarios if s.split == "holdout")

    if dev_count != 25 or val_count != 10 or holdout_count != 10:
        raise DatasetQuotaError(
            f"Invalid split distribution: dev={dev_count} (expected 25), "
            f"val={val_count} (expected 10), holdout={holdout_count} (expected 10)"
        )

    # Coverage quota checks
    quotas = {
        "contradictions": sum(1 for s in scenarios if s.has_contradiction),
        "causal_traps": sum(1 for s in scenarios if s.is_causal_trap),
        "critic_true_positives": sum(1 for s in scenarios if s.is_critic_true_positive),
        "critic_true_negatives": sum(1 for s in scenarios if s.is_critic_true_negative),
        "segmentation_traps": sum(1 for s in scenarios if s.is_segmentation_trap),
        "magnitude_traps": sum(1 for s in scenarios if s.is_magnitude_trap),
        "source_outages": sum(1 for s in scenarios if s.is_source_outage),
        "adversarial_injections": sum(1 for s in scenarios if s.is_adversarial_injection),
        "single_source": sum(1 for s in scenarios if s.is_single_source),
        "multi_source": sum(1 for s in scenarios if s.is_multi_source),
        "missing_evidence": sum(1 for s in scenarios if s.is_missing_evidence),
    }

    min_requirements = {
        "contradictions": 8,
        "causal_traps": 6,
        "critic_true_positives": 8,
        "critic_true_negatives": 10,
        "segmentation_traps": 5,
        "magnitude_traps": 5,
        "source_outages": 4,
        "adversarial_injections": 4,
        "single_source": 6,
        "multi_source": 25,
        "missing_evidence": 6,
    }

    for key, min_val in min_requirements.items():
        actual_val = quotas[key]
        if actual_val < min_val:
            raise DatasetQuotaError(
                f"Coverage quota violation for '{key}': found {actual_val}, required >= {min_val}"
            )

    return quotas


def get_scenarios(split: ScenarioSplit | Literal["all"] = "all") -> list[EvaluationScenario]:
    """Retrieve validated evaluation scenarios filtered by split."""
    validate_scenario_quotas(ALL_SCENARIOS)
    if split == "all":
        return list(ALL_SCENARIOS)
    return [s for s in ALL_SCENARIOS if s.split == split]


def get_scenario_by_id(scenario_id: str) -> EvaluationScenario:
    """Find scenario by unique scenario_id."""
    for s in ALL_SCENARIOS:
        if s.scenario_id == scenario_id:
            return s
    raise KeyError(f"Scenario '{scenario_id}' not found in evaluation dataset")
