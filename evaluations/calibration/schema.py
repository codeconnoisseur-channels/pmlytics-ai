"""Typed contracts for product-owned cases and audited judge calibration."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaseLifecycle(StrEnum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    ACTIVE = "active"
    RETIRED = "retired"
    INVALIDATED = "invalidated"


class AtomicVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCLEAR = "UNCLEAR"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FindingSeverity(StrEnum):
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class CaseDefinition(BaseModel):
    """Product-owned case metadata loaded from the editable catalog."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    criterion_id: str = Field(min_length=1)
    split: Literal["development", "held_out"]
    lifecycle: CaseLifecycle
    expected_verdict: AtomicVerdict
    expected_severity: FindingSeverity
    rationale: str = Field(min_length=1)
    packet_source: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    rubric_version: str = Field(min_length=1)
    provenance_status: Literal[
        "predeclared_system_fixture",
        "independent_human_adjudicated",
    ]
    last_reviewed_utc: datetime | None = None

    @model_validator(mode="after")
    def validate_reference_claims(self) -> "CaseDefinition":
        if self.split == "held_out":
            if self.provenance_status != "independent_human_adjudicated":
                raise ValueError("Held-out cases require independent human adjudication")
            if self.lifecycle not in {CaseLifecycle.REVIEWED, CaseLifecycle.ACTIVE}:
                raise ValueError("Held-out cases must be reviewed or active")
            if self.last_reviewed_utc is None:
                raise ValueError("Held-out cases require a review timestamp")
        if self.expected_verdict == AtomicVerdict.PASS:
            if self.expected_severity != FindingSeverity.NONE:
                raise ValueError("Passing expectations must use severity 'none'")
        elif self.expected_severity == FindingSeverity.NONE:
            raise ValueError("Non-passing expectations require a material severity")
        return self


class AtomicRubricCriterion(BaseModel):
    """One observable semantic quality question."""

    model_config = ConfigDict(frozen=True)

    criterion_id: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    question: str = Field(min_length=1)
    critical_when_failed: bool
    pass_definition: str = Field(min_length=1)
    fail_definition: str = Field(min_length=1)
    not_applicable_definition: str | None = None


class RubricDefinition(BaseModel):
    model_config = ConfigDict(frozen=True)

    rubric_version: str
    title: str
    owner: str
    status: Literal["draft", "active", "retired"]
    severity_scale: dict[FindingSeverity, str]
    criteria: list[AtomicRubricCriterion]

    @model_validator(mode="after")
    def validate_unique_criteria(self) -> "RubricDefinition":
        ids = [criterion.criterion_id for criterion in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("Rubric criterion IDs must be unique")
        return self


class ReferenceSet(BaseModel):
    model_config = ConfigDict(frozen=True)

    set_id: str
    purpose: str
    status: Literal["active", "not_qualified", "retired"]
    case_ids: list[str]
    qualification_note: str | None = None

    @model_validator(mode="after")
    def validate_qualification(self) -> "ReferenceSet":
        if self.status == "not_qualified" and self.case_ids:
            raise ValueError("A not-qualified reference set cannot contain cases")
        if self.status == "not_qualified" and not self.qualification_note:
            raise ValueError("A not-qualified reference set requires an explanation")
        if len(self.case_ids) != len(set(self.case_ids)):
            raise ValueError("Reference set case IDs must be unique")
        return self


class EvaluationPacket(BaseModel):
    """Identical candidate and evidence content supplied to every reviewer."""

    model_config = ConfigDict(frozen=True)

    packet_version: str = "1"
    case_id: str
    user_query: str
    evidence: list[dict[str, object]]
    candidate_recommendation: dict[str, object]
    source_failures: list[dict[str, object]] = Field(default_factory=list)
    content_sha256: str


class AtomicJudgment(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str
    criterion_id: str
    verdict: AtomicVerdict
    severity: FindingSeverity
    reason: str = Field(min_length=1)
    claim_reference: str | None = None
    evidence_references: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_severity(self) -> "AtomicJudgment":
        if self.verdict != AtomicVerdict.FAIL and self.severity != FindingSeverity.NONE:
            raise ValueError("Only failing judgments can carry a material severity")
        if self.verdict == AtomicVerdict.FAIL and self.severity == FindingSeverity.NONE:
            raise ValueError("Failing judgments require a material severity")
        return self


class AuditRecord(BaseModel):
    """Auditable human or automated judgments over one immutable packet."""

    model_config = ConfigDict(frozen=True)

    audit_id: str
    reviewer_type: Literal["human", "llm_judge"]
    reviewer_id: str
    reviewer_attestation: (
        Literal[
            "author_human_review",
            "independent_human_review",
        ]
        | None
    ) = None
    packet_sha256: str
    rubric_version: str
    created_at_utc: datetime
    judge_model: str | None = None
    judge_prompt_version: str | None = None
    judgments: list[AtomicJudgment]

    @model_validator(mode="after")
    def validate_provenance(self) -> "AuditRecord":
        if self.reviewer_type == "human":
            if self.reviewer_attestation not in {
                "author_human_review",
                "independent_human_review",
            }:
                raise ValueError("Human records require a truthful reviewer attestation")
            if self.judge_model or self.judge_prompt_version:
                raise ValueError("Human records cannot declare an automated judge")
        else:
            if self.reviewer_attestation is not None:
                raise ValueError("LLM judge records cannot carry human attestation")
            if not self.judge_model or not self.judge_prompt_version:
                raise ValueError("LLM judge records require model and prompt versions")
        keys = [(judgment.case_id, judgment.criterion_id) for judgment in self.judgments]
        if len(keys) != len(set(keys)):
            raise ValueError("An audit cannot contain duplicate case and criterion judgments")
        return self


class DimensionAgreement(BaseModel):
    model_config = ConfigDict(frozen=True)

    dimension: str
    comparable_count: int
    exact_agreement_count: int
    exact_agreement_rate: float | None
    false_pass_count: int
    false_fail_count: int


class Disagreement(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: str
    criterion_id: str
    dimension: str
    reference_verdict: AtomicVerdict
    judge_verdict: AtomicVerdict
    reference_severity: FindingSeverity
    judge_severity: FindingSeverity
    critical_false_pass: bool


class AgreementReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    comparable_count: int
    exact_agreement_count: int
    exact_agreement_rate: float | None
    critical_reference_count: int
    critical_agreement_count: int
    critical_agreement_rate: float | None
    false_pass_count: int
    critical_false_pass_count: int
    false_fail_count: int
    unresolved_disagreements: list[Disagreement]
    by_dimension: list[DimensionAgreement]
