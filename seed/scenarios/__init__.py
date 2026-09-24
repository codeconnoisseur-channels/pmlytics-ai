"""Registry of seed generation configurations."""

from seed.scenarios.bill_payment import BILL_PAYMENT_SEED_CONFIG
from seed.scenarios.kyc_abandonment import KYC_ABANDONMENT_SEED_CONFIG
from seed.scenarios.schema import (
    InjectionTimeline,
    JiraSeedIssue,
    ScenarioSeedConfig,
    SegmentConstraint,
)
from seed.scenarios.transfer_delays import TRANSFER_DELAYS_SEED_CONFIG
from seed.scenarios.wallet_funding import WALLET_FUNDING_SEED_CONFIG

ALL_SEED_CONFIGS: list[ScenarioSeedConfig] = [
    TRANSFER_DELAYS_SEED_CONFIG,
    KYC_ABANDONMENT_SEED_CONFIG,
    WALLET_FUNDING_SEED_CONFIG,
    BILL_PAYMENT_SEED_CONFIG,
]

__all__ = [
    "ScenarioSeedConfig",
    "JiraSeedIssue",
    "InjectionTimeline",
    "SegmentConstraint",
    "TRANSFER_DELAYS_SEED_CONFIG",
    "KYC_ABANDONMENT_SEED_CONFIG",
    "WALLET_FUNDING_SEED_CONFIG",
    "BILL_PAYMENT_SEED_CONFIG",
    "ALL_SEED_CONFIGS",
]
