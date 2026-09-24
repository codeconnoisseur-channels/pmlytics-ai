from app.domain.provenance import source_references_match


def test_jira_display_aliases_resolve_to_the_same_issue_key() -> None:
    assert source_references_match("jira", "PAY-134 (+3 issues)", "issue_key:PAY-134")


def test_non_jira_references_remain_exact() -> None:
    assert not source_references_match("zendesk", "ticket_id:101", "ticket_id:102")
    assert not source_references_match("posthog", "query:event_count:a", "query:event_count:b")
