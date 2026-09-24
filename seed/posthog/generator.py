"""Deterministic synthetic product analytics event generator.

Generates 10,000–20,000 events matching the 18-event taxonomy and reflecting
Scenarios A, B, C, and D with high fidelity to the authoritative specifications,
while strictly omitting all evaluation ground-truth and root-cause labels.
"""

import random
from datetime import UTC, datetime, timedelta

from app.domain.analytics import AnalyticsEvent

# Fixed deterministic seed and dataset version
DEFAULT_SEED = 20260914
DATASET_VERSION = "2.0"

# Controlled dimensions from DATA_API_SPECIFICATION
USER_TYPES = ["student", "freelancer", "young_professional", "small_business"]
BANKS = ["Bank A", "Bank B", "Bank C", "Bank D", "Bank E"]
APP_VERSIONS = ["2.3.0", "2.3.1", "2.4.0", "2.4.1"]
BILL_CATEGORIES = ["airtime", "electricity", "cable_tv", "internet"]
KYC_DOCUMENT_TYPES = ["national_id", "passport", "voters_card", "student_id"]

# Forbidden keys that must NEVER leak into event properties
FORBIDDEN_GROUND_TRUTH_KEYS = {
    "scenario_id",
    "root_cause",
    "is_anomaly",
    "ground_truth",
    "expected_verdict",
    "trap",
    "label",
    "is_failure",
    "is_bug",
    "jira_key",
}


class SyntheticUser:
    """Fictional user profile used to generate correlated event streams."""

    def __init__(
        self,
        user_id: str,
        user_type: str,
        primary_bank: str,
        app_version: str,
        signup_date: datetime,
    ) -> None:
        self.user_id = user_id
        self.user_type = user_type
        self.primary_bank = primary_bank
        self.app_version = app_version
        self.signup_date = signup_date


class PostHogEventGenerator:
    """Generates a coherent synthetic analytics dataset for Pocket."""

    def __init__(self, seed: int = DEFAULT_SEED, num_users: int = 2000) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.num_users = num_users
        self.users: list[SyntheticUser] = []
        self._init_users()

    def _init_users(self) -> None:
        """Initialize deterministic user population."""
        base_date = datetime(2026, 7, 1, 0, 0, 0, tzinfo=UTC)
        for i in range(1, self.num_users + 1):
            user_id = f"usr_{i:06d}"
            # Distribution: 35% students, 25% freelancers, 30% young professionals, 10% small business
            rand_val = self.rng.random()
            if rand_val < 0.35:
                user_type = "student"
            elif rand_val < 0.60:
                user_type = "freelancer"
            elif rand_val < 0.90:
                user_type = "young_professional"
            else:
                user_type = "small_business"

            bank = self.rng.choice(BANKS)
            app_version = self.rng.choices(APP_VERSIONS, weights=[0.10, 0.15, 0.35, 0.40], k=1)[0]
            signup_offset = timedelta(
                days=self.rng.randint(0, 40), seconds=self.rng.randint(0, 86400)
            )
            self.users.append(
                SyntheticUser(
                    user_id=user_id,
                    user_type=user_type,
                    primary_bank=bank,
                    app_version=app_version,
                    signup_date=base_date + signup_offset,
                )
            )

    def generate_events(self) -> list[AnalyticsEvent]:
        """Generate all synthetic events across background and scenarios."""
        events: list[AnalyticsEvent] = []
        txn_counter = 1

        # 1. Background account activity: signups and logins
        for user in self.users:
            # signup
            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="signup_completed",
                    timestamp=user.signup_date,
                    properties={
                        "app_version": user.app_version,
                        "user_type": user.user_type,
                        "primary_bank": user.primary_bank,
                    },
                )
            )

        # Active sample of logins (~800 events)
        active_login_users = self.rng.sample(self.users, k=600)
        for user in active_login_users:
            num_logins = self.rng.randint(1, 2)
            for _ in range(num_logins):
                login_time = user.signup_date + timedelta(
                    days=self.rng.randint(1, 35),
                    seconds=self.rng.randint(0, 86400),
                )
                if login_time < datetime(2026, 8, 25, 0, 0, 0, tzinfo=UTC):
                    events.append(
                        AnalyticsEvent(
                            distinct_id=user.user_id,
                            event="login_completed",
                            timestamp=login_time,
                            properties={
                                "app_version": user.app_version,
                                "user_type": user.user_type,
                            },
                        )
                    )

        # 2. Scenario A & Background Transfers (~1,500 transactions, ~9,000 events)
        # August 10 to 15 is the active Scenario A window
        scenario_a_start = datetime(2026, 8, 10, 8, 0, 0, tzinfo=UTC)
        scenario_a_end = datetime(2026, 8, 15, 20, 0, 0, tzinfo=UTC)

        total_transfers = 1500
        for _ in range(total_transfers):
            user = self.rng.choice(self.users)
            dest_bank = self.rng.choice(BANKS)
            txn_id = f"txn_{txn_counter:06d}"
            txn_counter += 1

            # Amount distribution
            amt_rand = self.rng.random()
            if amt_rand < 0.40:
                amount = self.rng.randint(1000, 9999)
            elif amt_rand < 0.75:
                amount = self.rng.randint(10000, 49999)
            elif amt_rand < 0.95:
                amount = self.rng.randint(50000, 199999)
            else:
                amount = self.rng.randint(200000, 500000)

            # Random timestamp between Aug 1 and Aug 22, 2026
            txn_time = datetime(2026, 8, 1, 8, 0, 0, tzinfo=UTC) + timedelta(
                days=self.rng.randint(0, 21),
                seconds=self.rng.randint(0, 86400),
            )

            is_scenario_a = scenario_a_start <= txn_time <= scenario_a_end and dest_bank in (
                "Bank A",
                "Bank B",
            )

            # Funnel steps
            t0 = txn_time
            t1 = t0 + timedelta(seconds=self.rng.randint(4, 12))
            t2 = t1 + timedelta(seconds=self.rng.randint(3, 8))
            t3 = t2 + timedelta(seconds=self.rng.randint(2, 6))
            t4 = t3 + timedelta(milliseconds=self.rng.randint(300, 800))

            base_props = {
                "transaction_id": txn_id,
                "amount_ngn": amount,
                "destination_bank": dest_bank,
                "source_bank": user.primary_bank,
                "app_version": user.app_version,
                "user_type": user.user_type,
            }

            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="transfer_started",
                    timestamp=t0,
                    properties=base_props,
                )
            )
            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="transfer_recipient_selected",
                    timestamp=t1,
                    properties=base_props,
                )
            )
            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="transfer_reviewed",
                    timestamp=t2,
                    properties=base_props,
                )
            )
            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="transfer_submitted",
                    timestamp=t3,
                    properties=base_props,
                )
            )
            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="transfer_processing",
                    timestamp=t4,
                    properties=base_props,
                )
            )

            # Outcome
            # Stable baseline failure rate: ~1.2% across all transfers
            if self.rng.random() < 0.012:
                fail_time = t4 + timedelta(seconds=self.rng.randint(2, 10))
                events.append(
                    AnalyticsEvent(
                        distinct_id=user.user_id,
                        event="transfer_failed",
                        timestamp=fail_time,
                        properties={
                            **base_props,
                            "failure_code": "INSUFFICIENT_FUNDS",
                            "duration_ms": int((fail_time - t3).total_seconds() * 1000),
                        },
                    )
                )
            else:
                # Success
                if is_scenario_a:
                    # Webhook callback delay on Bank A / Bank B:
                    # In-session immediate completion (<60s) happens only ~8% of the time.
                    # 92% hang in processing and only complete 45s to 4 hours later!
                    if self.rng.random() < 0.08:
                        delay_sec = self.rng.randint(5, 45)
                    else:
                        delay_sec = self.rng.randint(1800, 14400)  # 30m to 4h
                else:
                    # Normal banks (Bank C, D, E or outside window): 2-5s completion
                    delay_sec = self.rng.randint(2, 5)

                comp_time = t4 + timedelta(seconds=delay_sec)
                events.append(
                    AnalyticsEvent(
                        distinct_id=user.user_id,
                        event="transfer_completed",
                        timestamp=comp_time,
                        properties={**base_props, "duration_ms": delay_sec * 1000},
                    )
                )

        # 3. Scenario B: KYC Abandonment (~500 user journeys, ~1,100 events)
        kyc_users = self.rng.sample(self.users, k=500)
        for user in kyc_users:
            kyc_time = datetime(2026, 8, 2, 9, 0, 0, tzinfo=UTC) + timedelta(
                days=self.rng.randint(0, 18),
                seconds=self.rng.randint(0, 86400),
            )
            doc_type = (
                "student_id" if user.user_type == "student" else self.rng.choice(KYC_DOCUMENT_TYPES)
            )
            base_props = {
                "app_version": user.app_version,
                "user_type": user.user_type,
                "document_type": doc_type,
            }

            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="kyc_started",
                    timestamp=kyc_time,
                    properties=base_props,
                )
            )

            # Drop-off occurs BEFORE document submission:
            # Students & Freelancers drop heavily due to document confusion (only ~35% proceed to submit)
            # Young professionals & Small business proceed ~82%
            # Secondary CORE-82 signal: Android 2.4.0 has an extra ~1.8% drop
            proceed_chance = 0.35 if user.user_type in ("student", "freelancer") else 0.82
            if user.app_version == "2.4.0":
                proceed_chance -= 0.018

            if self.rng.random() < proceed_chance:
                t_sub = kyc_time + timedelta(seconds=self.rng.randint(30, 180))
                events.append(
                    AnalyticsEvent(
                        distinct_id=user.user_id,
                        event="kyc_document_submitted",
                        timestamp=t_sub,
                        properties=base_props,
                    )
                )

                # Post-submission: High and stable completion (>92%)
                if self.rng.random() < 0.92:
                    t_comp = t_sub + timedelta(minutes=self.rng.randint(5, 60))
                    events.append(
                        AnalyticsEvent(
                            distinct_id=user.user_id,
                            event="kyc_completed",
                            timestamp=t_comp,
                            properties=base_props,
                        )
                    )
                else:
                    t_fail = t_sub + timedelta(minutes=self.rng.randint(5, 30))
                    events.append(
                        AnalyticsEvent(
                            distinct_id=user.user_id,
                            event="kyc_failed",
                            timestamp=t_fail,
                            properties={**base_props, "failure_code": "DOC_UNREADABLE"},
                        )
                    )

        # 4. Scenario C: Wallet Funding Abandonment (>= ₦50,000 fee surprise) (~500 attempts, ~1,100 events)
        for _ in range(500):
            user = self.rng.choice(self.users)
            txn_id = f"txn_{txn_counter:06d}"
            txn_counter += 1

            # Amount distribution: 50% < 50k, 50% >= 50k
            is_high_value = self.rng.random() < 0.50
            if is_high_value:
                amount = self.rng.randint(50000, 300000)
            else:
                amount = self.rng.randint(2000, 49999)

            fund_time = datetime(2026, 8, 5, 10, 0, 0, tzinfo=UTC) + timedelta(
                days=self.rng.randint(0, 13),
                seconds=self.rng.randint(0, 86400),
            )

            base_props = {
                "transaction_id": txn_id,
                "amount_ngn": amount,
                "primary_bank": user.primary_bank,
                "app_version": user.app_version,
                "user_type": user.user_type,
            }

            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="wallet_funding_started",
                    timestamp=fund_time,
                    properties=base_props,
                )
            )

            # Abandonment behavior:
            # If amount >= 50,000: fee surprise causes ~80% abandonment BEFORE submission (only 20% submit)
            # If amount < 50,000: normal conversion (>95% submit)
            # ZERO wallet_funding_failed events!
            submit_chance = 0.20 if is_high_value else 0.96

            if self.rng.random() < submit_chance:
                t_sub = fund_time + timedelta(seconds=self.rng.randint(8, 25))
                events.append(
                    AnalyticsEvent(
                        distinct_id=user.user_id,
                        event="wallet_funding_submitted",
                        timestamp=t_sub,
                        properties=base_props,
                    )
                )

                # Post-submission completes smoothly
                t_comp = t_sub + timedelta(seconds=self.rng.randint(2, 6))
                events.append(
                    AnalyticsEvent(
                        distinct_id=user.user_id,
                        event="wallet_funding_completed",
                        timestamp=t_comp,
                        properties=base_props,
                    )
                )

        # 5. Scenario D: Bill Payments (~450 attempts, ~1,100 events with electricity failure spike)
        # Month-end settlement window: Aug 28-31.  The question and all three
        # sources now refer to the same customer-visible period.
        incident_start = datetime(2026, 8, 28, 14, 0, 0, tzinfo=UTC)
        incident_end = datetime(2026, 8, 31, 2, 0, 0, tzinfo=UTC)

        for _ in range(450):
            user = self.rng.choice(self.users)
            category = self.rng.choice(BILL_CATEGORIES)
            txn_id = f"txn_{txn_counter:06d}"
            txn_counter += 1

            bill_time = datetime(2026, 8, 20, 8, 0, 0, tzinfo=UTC) + timedelta(
                days=self.rng.randint(0, 11),
                seconds=self.rng.randint(0, 86400),
            )

            # Concentration during incident window for realism
            if self.rng.random() < 0.32:
                bill_time = incident_start + timedelta(
                    seconds=self.rng.randint(
                        0, int((incident_end - incident_start).total_seconds())
                    )
                )

            amount = self.rng.randint(1500, 25000)
            base_props = {
                "transaction_id": txn_id,
                "amount_ngn": amount,
                "category": category,
                "app_version": user.app_version,
                "user_type": user.user_type,
            }

            t0 = bill_time
            t1 = t0 + timedelta(seconds=self.rng.randint(5, 15))

            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="bill_payment_started",
                    timestamp=t0,
                    properties=base_props,
                )
            )
            events.append(
                AnalyticsEvent(
                    distinct_id=user.user_id,
                    event="bill_payment_submitted",
                    timestamp=t1,
                    properties=base_props,
                )
            )

            # Incident failure logic:
            # During incident window, electricity has ~80% failure rate with BAD_GATEWAY / PROVIDER_UNAVAILABLE
            # Other categories maintain normal ~1% failure rate
            in_incident = incident_start <= t1 <= incident_end
            if in_incident and category == "electricity":
                is_failure = self.rng.random() < 0.80
            else:
                is_failure = self.rng.random() < 0.012

            t2 = t1 + timedelta(seconds=self.rng.randint(2, 6))
            if is_failure:
                fail_code = (
                    "BAD_GATEWAY" if (in_incident and category == "electricity") else "TIMEOUT"
                )
                events.append(
                    AnalyticsEvent(
                        distinct_id=user.user_id,
                        event="bill_payment_failed",
                        timestamp=t2,
                        properties={**base_props, "failure_code": fail_code},
                    )
                )
            else:
                events.append(
                    AnalyticsEvent(
                        distinct_id=user.user_id,
                        event="bill_payment_completed",
                        timestamp=t2,
                        properties=base_props,
                    )
                )

        # Sort all events chronologically
        events.sort(key=lambda e: e.timestamp)

        # Tag every event with the reproducible dataset version. Runtime reads
        # are constrained to this property, so a reseed cannot blend evidence
        # from different synthetic populations.
        for event in events:
            event.properties["dataset_version"] = DATASET_VERSION

        # Sanity check: Ensure zero ground-truth keys leaked into properties
        for event in events:
            leaked = set(event.properties.keys()) & FORBIDDEN_GROUND_TRUTH_KEYS
            if leaked:
                raise ValueError(f"Ground-truth leakage detected in event properties: {leaked}")

        return events
