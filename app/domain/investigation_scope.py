"""Typed user-selected boundaries for a single investigation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvestigationScope(BaseModel):
    """A bounded analysis window, with an optional comparison period.

    A missing scope preserves the existing all-available-data behaviour.  When a
    window is supplied, it is carried through planning and specialist tasks so
    agents can state and respect the PM's period of interest.
    """

    model_config = ConfigDict(frozen=True)

    start_time: datetime | None = None
    end_time: datetime | None = None
    comparison_start_time: datetime | None = None
    comparison_end_time: datetime | None = None
    timezone: str = Field(default="UTC", min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_windows(self) -> "InvestigationScope":
        if (self.start_time is None) != (self.end_time is None):
            raise ValueError("start_time and end_time must be provided together.")
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValueError("end_time must be after start_time.")
        if (self.comparison_start_time is None) != (self.comparison_end_time is None):
            raise ValueError(
                "comparison_start_time and comparison_end_time must be provided together."
            )
        if (
            self.comparison_start_time
            and self.comparison_end_time
            and self.comparison_start_time >= self.comparison_end_time
        ):
            raise ValueError("comparison_end_time must be after comparison_start_time.")
        return self

    @property
    def is_bounded(self) -> bool:
        return self.start_time is not None

    def describe(self) -> str:
        start_time = self.start_time
        end_time = self.end_time
        if start_time is None or end_time is None:
            return "No date window was selected; use all available evidence and state that clearly."
        primary = f"{start_time.isoformat()} to {end_time.isoformat()} ({self.timezone})"
        comparison_start = self.comparison_start_time
        comparison_end = self.comparison_end_time
        if comparison_start is not None and comparison_end is not None:
            return (
                f"Primary period: {primary}. Compare with: "
                f"{comparison_start.isoformat()} to {comparison_end.isoformat()} "
                f"({self.timezone})."
            )
        return f"Primary period: {primary}."
