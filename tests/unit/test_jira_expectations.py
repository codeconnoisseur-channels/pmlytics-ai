"""Unit tests for Jira expectation structures and scenario coverage."""

from mocks.jira.expectations import get_jira_mock_expectations, make_adf_body


def test_make_adf_body_structure() -> None:
    """Verify ADF document generation structure."""
    adf = make_adf_body(["First paragraph", "Second paragraph"])
    assert adf["version"] == 1
    assert adf["type"] == "doc"
    assert len(adf["content"]) == 2
    assert adf["content"][0]["type"] == "paragraph"
    assert adf["content"][0]["content"][0]["text"] == "First paragraph"


def test_jira_mock_expectations_scenarios() -> None:
    """Verify expectation definitions cover PAY-117, CORE-82, PAY-134 and no wallet issues."""
    expectations = get_jira_mock_expectations()
    assert len(expectations) >= 8

    # Extract issue paths
    issue_paths = [
        exp["httpRequest"]["path"]
        for exp in expectations
        if exp["httpRequest"].get("method") == "GET"
        and "/issue/" in exp["httpRequest"]["path"]
        and "/comment" not in exp["httpRequest"]["path"]
    ]
    assert "/rest/api/3/issue/PAY-117" in issue_paths
    assert "/rest/api/3/issue/CORE-82" in issue_paths
    assert "/rest/api/3/issue/PAY-134" in issue_paths

    # Confirm zero wallet funding issues in expectations
    for path in issue_paths:
        assert "WAL-" not in path

    # Check search/jql expectation is present
    search_exp = [
        exp for exp in expectations if exp["httpRequest"]["path"] == "/rest/api/3/search/jql"
    ]
    assert len(search_exp) == 5
    assert all(exp["httpRequest"]["method"] == "POST" for exp in search_exp)
    wallet_search = next(
        exp for exp in search_exp if "wallet" in exp["httpRequest"].get("body", {}).get("regex", "")
    )
    assert wallet_search["httpResponse"]["body"]["issues"] == []
    assert wallet_search["priority"] > 0
    catch_all = min(search_exp, key=lambda exp: exp.get("priority", 0))
    assert catch_all["priority"] < 0
    assert catch_all["httpResponse"]["body"]["issues"] == []
    kyc_search = next(
        exp
        for exp in search_exp
        if "identity" in exp["httpRequest"].get("body", {}).get("regex", "")
    )
    assert [issue["key"] for issue in kyc_search["httpResponse"]["body"]["issues"]] == ["CORE-82"]
    bill_search = next(
        exp
        for exp in search_exp
        if "electricity" in exp["httpRequest"].get("body", {}).get("regex", "")
    )
    assert [issue["key"] for issue in bill_search["httpResponse"]["body"]["issues"]] == ["PAY-134"]

    # Confirm all comments use ADF body format
    comment_exps = [exp for exp in expectations if "/comment" in exp["httpRequest"]["path"]]
    for c_exp in comment_exps:
        comments_list = c_exp["httpResponse"]["body"].get("comments", [])
        for comm in comments_list:
            assert isinstance(comm["body"], dict)
            assert comm["body"]["type"] == "doc"

    # Confirm zero evaluation ground truth fields leak
    forbidden_keys = {
        "underlying_reality",
        "known_traps",
        "acceptable_conclusions",
        "unacceptable_conclusions",
        "expected_findings",
        "scenario_id",
    }
    for exp in expectations:
        body_str = str(exp["httpResponse"]["body"])
        for key in forbidden_keys:
            assert key not in body_str
