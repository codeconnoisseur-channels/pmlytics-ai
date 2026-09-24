"""Unit tests for minimal Zendesk ticket seeding."""

from seed.zendesk.minimal_loader import get_minimal_tickets_payload


def test_minimal_tickets_payload_structure() -> None:
    """Verify minimal ticket payload structure, noise ratio, and absence of ground truth."""
    tickets = get_minimal_tickets_payload()
    assert len(tickets) == 25

    # Check Scenario A tickets (pending transfers on Bank A and Bank B): 10 tickets
    transfer_tickets = [t for t in tickets if "transfer" in t.get("tags", [])]
    assert len(transfer_tickets) == 11
    assert any("bank_a" in t.get("tags", []) for t in transfer_tickets)
    assert any("bank_b" in t.get("tags", []) for t in transfer_tickets)

    # Check normal support tickets: 5 tickets
    normal_tickets = [
        t for t in tickets if "account" in t.get("tags", []) or "statement" in t.get("tags", [])
    ]
    assert len(normal_tickets) == 5

    # Check noise/general tickets: 4 tickets
    noise_tickets = [
        t
        for t in tickets
        if "general" in t.get("tags", [])
        or "card" in t.get("tags", [])
        or "feedback" in t.get("tags", [])
    ]
    assert len(noise_tickets) == 6

    # Verify no evaluation ground truth fields leak into tickets
    forbidden_keys = {
        "underlying_reality",
        "known_traps",
        "acceptable_conclusions",
        "unacceptable_conclusions",
        "expected_findings",
        "scenario_id",
    }
    for t in tickets:
        for key in forbidden_keys:
            assert key not in t
            assert key not in t.get("comment", {})
