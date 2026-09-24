"""Unit tests for ToolResult structural invariants and error normalization."""

import pytest
from app.tools.base import ToolError, ToolProvenance, ToolResult
from pydantic import ValidationError


def test_tool_result_valid_success() -> None:
    """Verify that a successful ToolResult with data and provenance passes validation."""
    result = ToolResult[str](
        success=True,
        data="valid_payload",
        error=None,
        provenance=ToolProvenance(source_type="zendesk", source_reference="ticket_id:1"),
        execution_duration_ms=12.5,
    )
    assert result.success is True
    assert result.data == "valid_payload"
    assert result.error is None
    assert result.provenance is not None
    assert result.provenance.source_type == "zendesk"


def test_tool_result_valid_failure_with_attempted_source() -> None:
    """Verify that an upstream failure ToolResult with error and no provenance passes validation."""
    result = ToolResult[str](
        success=False,
        data=None,
        error=ToolError(
            error_type="timeout",
            message="Upstream timed out",
            attempted_source="posthog",
        ),
        provenance=None,
        execution_duration_ms=5000.0,
    )
    assert result.success is False
    assert result.data is None
    assert result.error is not None
    assert result.error.attempted_source == "posthog"
    assert result.provenance is None


def test_tool_result_permission_denied_attempted_source_none() -> None:
    """Regression test: verify permission_denied error can be represented with attempted_source=None."""
    err = ToolError(
        error_type="permission_denied",
        message="Role 'research' cannot access 'query_analytics'.",
        attempted_source=None,
        details={"role": "research", "requested_tool": "query_analytics"},
    )
    assert err.attempted_source is None

    result = ToolResult[str](
        success=False,
        data=None,
        error=err,
        provenance=None,
        execution_duration_ms=0.0,
    )
    assert result.success is False
    assert result.error is not None
    assert result.error.attempted_source is None
    assert result.provenance is None


def test_tool_result_invariant_success_missing_data() -> None:
    """Assert success=True with data=None is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult[str](
            success=True,
            data=None,
            error=None,
            provenance=ToolProvenance(source_type="jira", source_reference="PAY-1"),
            execution_duration_ms=5.0,
        )
    assert "Successful ToolResult must have 'data' populated" in str(exc_info.value)


def test_tool_result_invariant_success_with_error() -> None:
    """Assert success=True with error populated is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult[str](
            success=True,
            data="payload",
            error=ToolError(error_type="upstream_error", message="err", attempted_source="jira"),
            provenance=ToolProvenance(source_type="jira", source_reference="PAY-1"),
            execution_duration_ms=5.0,
        )
    assert "Successful ToolResult cannot have 'error' populated" in str(exc_info.value)


def test_tool_result_invariant_success_missing_provenance() -> None:
    """Assert success=True with provenance=None is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult[str](
            success=True,
            data="payload",
            error=None,
            provenance=None,
            execution_duration_ms=5.0,
        )
    assert "Successful ToolResult must have 'provenance' populated" in str(exc_info.value)


def test_tool_result_invariant_failure_missing_error() -> None:
    """Assert success=False with error=None is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult[str](
            success=False,
            data=None,
            error=None,
            provenance=None,
            execution_duration_ms=5.0,
        )
    assert "Failed ToolResult must have 'error' populated" in str(exc_info.value)


def test_tool_result_invariant_failure_with_data() -> None:
    """Assert success=False with data populated is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult[str](
            success=False,
            data="leaked_data",
            error=ToolError(error_type="upstream_error", message="err", attempted_source="jira"),
            provenance=None,
            execution_duration_ms=5.0,
        )
    assert "Failed ToolResult cannot have 'data' populated" in str(exc_info.value)


def test_tool_result_invariant_failure_with_provenance() -> None:
    """Assert failed ToolResult claiming evidence provenance is strictly rejected."""
    with pytest.raises(ValidationError) as exc_info:
        ToolResult[str](
            success=False,
            data=None,
            error=ToolError(error_type="timeout", message="timed out", attempted_source="jira"),
            provenance=ToolProvenance(source_type="jira", source_reference="PAY-1"),
            execution_duration_ms=5.0,
        )
    assert "Failed ToolResult cannot claim evidence 'provenance'" in str(exc_info.value)
