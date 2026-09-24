"""Validation tests for the PM-selected investigation time boundary."""

from datetime import UTC, datetime

import pytest
from app.domain.investigation_scope import InvestigationScope
from pydantic import ValidationError


def test_scope_requires_complete_primary_window() -> None:
    with pytest.raises(ValidationError, match="provided together"):
        InvestigationScope(start_time=datetime(2026, 8, 1, tzinfo=UTC))


def test_scope_describes_primary_and_comparison_windows() -> None:
    scope = InvestigationScope(
        start_time=datetime(2026, 8, 1, tzinfo=UTC),
        end_time=datetime(2026, 8, 15, tzinfo=UTC),
        comparison_start_time=datetime(2026, 7, 1, tzinfo=UTC),
        comparison_end_time=datetime(2026, 7, 15, tzinfo=UTC),
    )

    assert scope.is_bounded is True
    assert "Primary period" in scope.describe()
    assert "Compare with" in scope.describe()
