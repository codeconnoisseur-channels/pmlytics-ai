"""Unit tests for seed generation configurations."""

from datetime import datetime

from seed.scenarios import (
    ALL_SEED_CONFIGS,
    BILL_PAYMENT_SEED_CONFIG,
    KYC_ABANDONMENT_SEED_CONFIG,
    TRANSFER_DELAYS_SEED_CONFIG,
    WALLET_FUNDING_SEED_CONFIG,
    ScenarioSeedConfig,
)
from seed.zendesk.minimal_loader import get_demo_tickets_payload


def test_seed_configs_registered() -> None:
    """Verify all 4 scenario seed configs are present and validated."""
    assert len(ALL_SEED_CONFIGS) == 4
    for config in ALL_SEED_CONFIGS:
        assert isinstance(config, ScenarioSeedConfig)
        assert config.target_tickets_count > 0
        assert config.target_events_count > 0
        assert 0.0 <= config.noise_ratio <= 1.0


def test_transfer_delays_seed_config() -> None:
    """Verify Scenario A seed generation parameters."""
    cfg = TRANSFER_DELAYS_SEED_CONFIG
    assert cfg.scenario_id == "scenario_a_transfer_delays"
    assert len(cfg.jira_issues) == 1
    assert cfg.jira_issues[0].key == "PAY-117"
    assert cfg.target_segment.destination_bank == "Bank A"
    assert (
        cfg.injection_timeline.jira_logged_offset_hours
        <= cfg.injection_timeline.ticket_spike_offset_hours
    )


def test_kyc_abandonment_seed_config() -> None:
    """Verify Scenario B seed generation parameters."""
    cfg = KYC_ABANDONMENT_SEED_CONFIG
    assert cfg.scenario_id == "scenario_b_kyc_abandonment"
    assert len(cfg.jira_issues) == 1
    assert cfg.jira_issues[0].key == "CORE-82"
    assert cfg.target_segment.user_type == "student"


def test_wallet_funding_seed_config() -> None:
    """Verify Scenario C seed generation parameters has zero engineering issues."""
    cfg = WALLET_FUNDING_SEED_CONFIG
    assert cfg.scenario_id == "scenario_c_wallet_funding"
    assert len(cfg.jira_issues) == 0  # Confirms no engineering bug exists
    assert "50k-200k" in cfg.target_segment.amount_brackets
    assert ">=200k" in cfg.target_segment.amount_brackets


def test_bill_payment_seed_config() -> None:
    """Verify Scenario D seed generation parameters."""
    cfg = BILL_PAYMENT_SEED_CONFIG
    assert cfg.scenario_id == "scenario_d_bill_payment"
    assert len(cfg.jira_issues) == 1
    assert cfg.jira_issues[0].key == "PAY-134"
    assert cfg.target_segment.category == "electricity"


def test_demo_support_tickets_fall_inside_reference_periods() -> None:
    """The selected report period must not filter out its own support evidence."""
    tickets = get_demo_tickets_payload()
    windows = [
        ("2026-08-10T08:00:00+00:00", "2026-08-15T20:00:00+00:00"),
        ("2026-08-01T00:00:00+00:00", "2026-08-20T23:59:59+00:00"),
        ("2026-08-05T00:00:00+00:00", "2026-08-18T23:59:59+00:00"),
        ("2026-08-28T08:00:00+00:00", "2026-08-31T23:00:00+00:00"),
    ]
    for scenario_index, (start_text, end_text) in enumerate(windows):
        start = datetime.fromisoformat(start_text)
        end = datetime.fromisoformat(end_text)
        scenario_tickets = tickets[scenario_index * 12 : (scenario_index + 1) * 12]
        assert len(scenario_tickets) == 12
        assert all(
            start <= datetime.fromisoformat(ticket["created_at"].replace("Z", "+00:00")) <= end
            for ticket in scenario_tickets
        )
