"""Evidence and provenance domain models for specialist agents."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceConfidence(StrEnum):
    """Confidence calibration for specialist evidence and findings."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    """Atomic piece of attributable evidence anchored to an Evidence Ledger entry."""

    model_config = ConfigDict(frozen=True)

    ledger_entry_id: str = Field(
        ...,
        description="Unique identifier of the verified Evidence Ledger entry (e.g. 'led_001')",
    )
    source_type: Literal["zendesk", "posthog", "jira"] = Field(
        ...,
        description="External source system from which evidence was retrieved",
    )
    source_reference: str = Field(
        ...,
        description="Human-readable citation (e.g. 'ticket_id:101', 'issue_key:PAY-117')",
    )
    finding: str = Field(
        ...,
        min_length=3,
        description="Specific observation or extracted fact supported by this evidence",
    )
    support: str = Field(
        ...,
        min_length=1,
        description="Direct excerpt, metric value, or field value from the ledger entry",
    )
    confidence: EvidenceConfidence = Field(
        ...,
        description="Confidence assessment for this piece of evidence",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Known constraints, sample size limits, or ambiguities in this evidence",
    )


class BaseSpecialistFinding(BaseModel):
    """Base schema for all specialist agent findings enforcing epistemic separation."""

    model_config = ConfigDict(frozen=True)

    finding: str = Field(
        ...,
        min_length=3,
        description="Summary statement of the finding",
    )
    facts: list[str] = Field(
        ...,
        min_length=1,
        description="Directly observed data points without extrapolation",
    )
    interpretations: list[str] = Field(
        ...,
        min_length=1,
        description="Domain inferences drawn directly from observed facts",
    )
    hypotheses: list[str] = Field(
        default_factory=list,
        description="Plausible explanatory working propositions requiring cross-domain corroboration",
    )
    evidence: list[Evidence] = Field(
        ...,
        min_length=1,
        description="Attributable evidence items grounding this finding",
    )
    confidence: EvidenceConfidence = Field(
        ...,
        description="Overall confidence in this finding",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Known limitations or caveats of this finding",
    )
