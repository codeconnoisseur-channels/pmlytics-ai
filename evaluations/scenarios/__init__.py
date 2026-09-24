"""Registry of evaluation ground truth scenarios."""

from evaluations.scenarios.bill_payment import BILL_PAYMENT_GROUND_TRUTH
from evaluations.scenarios.kyc_abandonment import KYC_ABANDONMENT_GROUND_TRUTH
from evaluations.scenarios.schema import RecommendationType, ScenarioGroundTruth
from evaluations.scenarios.transfer_delays import TRANSFER_DELAYS_GROUND_TRUTH
from evaluations.scenarios.wallet_funding import WALLET_FUNDING_GROUND_TRUTH

ALL_GROUND_TRUTH_SCENARIOS: list[ScenarioGroundTruth] = [
    TRANSFER_DELAYS_GROUND_TRUTH,
    KYC_ABANDONMENT_GROUND_TRUTH,
    WALLET_FUNDING_GROUND_TRUTH,
    BILL_PAYMENT_GROUND_TRUTH,
]

__all__ = [
    "ScenarioGroundTruth",
    "RecommendationType",
    "TRANSFER_DELAYS_GROUND_TRUTH",
    "KYC_ABANDONMENT_GROUND_TRUTH",
    "WALLET_FUNDING_GROUND_TRUTH",
    "BILL_PAYMENT_GROUND_TRUTH",
    "ALL_GROUND_TRUTH_SCENARIOS",
]
