"""Utilities for comparing display-safe evidence provenance."""

import re

_JIRA_KEY = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")


def source_references_match(
    source_type: str,
    actual: str,
    cited: str,
) -> bool:
    """Compare evidence references without weakening provenance identity.

    Jira responses are frequently cited by their stable issue key, while older
    search display labels could add a presentation suffix such as ``(+3
    issues)`` or ``issue_key:``.  Those labels describe the same retrieved Jira
    record; non-Jira provenance remains exact.
    """
    if actual == cited:
        return True
    if source_type != "jira":
        return False
    actual_key = _JIRA_KEY.search(actual)
    cited_key = _JIRA_KEY.search(cited)
    return bool(actual_key and cited_key and actual_key.group(0) == cited_key.group(0))
