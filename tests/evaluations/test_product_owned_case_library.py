"""Offline tests for product-owned evaluation cases and judge auditing."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from app.integrations.llm.client import LLMClient, LLMMessage
from evaluations.calibration import atomic_judge_pilot
from evaluations.calibration.agreement import compare_audits
from evaluations.calibration.atomic_judge import AtomicJudgeEvaluator, AtomicJudgeResponse
from evaluations.calibration.human_review import (
    compare_human_review_to_catalog,
    create_human_review_working_copy,
    export_human_review_bundle,
    export_human_review_subset,
    validate_human_review_form,
)
from evaluations.calibration.live_gate import (
    PAID_EVALUATION_ENV,
    calculate_preflight,
    require_paid_evaluation_opt_in,
)
from evaluations.calibration.loader import load_case_library
from evaluations.calibration.packets import build_evaluation_packet
from evaluations.calibration.schema import (
    AtomicJudgment,
    AtomicVerdict,
    AuditRecord,
    CaseDefinition,
    CaseLifecycle,
    FindingSeverity,
)
from pydantic import ValidationError


def test_case_library_is_product_owned_and_honest_about_holdout() -> None:
    library = load_case_library()

    assert len(library.cases) == 15
    assert len(library.development.case_ids) == 15
    assert library.held_out.status == "not_qualified"
    assert library.held_out.case_ids == []
    assert {case.lifecycle.value for case in library.cases} == {"proposed"}
    assert {case.provenance_status for case in library.cases} == {"predeclared_system_fixture"}
    assert library.rubric.rubric_version == "atomic_semantic_v2"
    assert library.rubric.status == "active"


def test_held_out_case_requires_human_adjudication() -> None:
    with pytest.raises(ValidationError, match="independent human adjudication"):
        CaseDefinition(
            case_id="case_held_out",
            title="Invalid held-out case",
            dimension="groundedness",
            criterion_id="grounding.material_claim_supported",
            split="held_out",
            lifecycle=CaseLifecycle.ACTIVE,
            expected_verdict=AtomicVerdict.FAIL,
            expected_severity=FindingSeverity.CRITICAL,
            rationale="A held-out case cannot be self-qualified.",
            packet_source="legacy_stress_fixture:stress_02_fabricated_metric",
            owner="AI Product Manager",
            rubric_version="atomic_semantic_v1",
            provenance_status="predeclared_system_fixture",
        )


def test_packet_is_stable_and_excludes_expected_behavior() -> None:
    library = load_case_library()
    packet_a = build_evaluation_packet(library, "stress_02_fabricated_metric")
    packet_b = build_evaluation_packet(library, "stress_02_fabricated_metric")

    assert packet_a.content_sha256 == packet_b.content_sha256
    serialized = packet_a.model_dump_json()
    assert "expected_verdict" not in serialized
    assert "predeclared_expected_behavior" not in serialized
    assert "human_ground_truth" not in serialized


def test_missing_source_case_contains_structured_failure() -> None:
    library = load_case_library()
    packet = build_evaluation_packet(library, "stress_13_source_outage_insufficient")

    assert packet.source_failures == [
        {
            "error_type": "timeout",
            "message": "Telco adapter telemetry was unavailable for the selected period.",
            "attempted_source": "posthog",
            "details": {"missing_signal": "telco adapter logs and partner telemetry"},
        }
    ]


def test_human_review_bundle_is_fillable_and_blind(tmp_path: Path) -> None:
    packets_path, form_path = export_human_review_bundle(tmp_path)
    packets = json.loads(packets_path.read_text(encoding="utf-8"))
    with form_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(packets) == len(rows) == 15
    assert rows[0]["review_case_id"] == "review_case_001"
    assert rows[0]["verdict"] == ""
    assert rows[0]["reason"] == ""
    serialized = packets_path.read_text(encoding="utf-8")
    assert "expected_verdict" not in serialized
    assert "predeclared_expected_behavior" not in serialized
    assert "stress_02_fabricated_metric" not in serialized


def test_completed_human_review_form_validates_offline(tmp_path: Path) -> None:
    packets_path, form_path = export_human_review_bundle(tmp_path)
    with form_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames is not None

    for row in rows:
        row["reviewer_id"] = "independent_reviewer_1"
        row["reviewer_attestation"] = "independent_human_review"
        row["reviewed_at_utc"] = "2026-09-29T14:30:00Z"
        row["verdict"] = "PASS"
        row["severity"] = "none"
        row["reason"] = "The supplied evidence supports the assessed behavior."

    with form_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    records = validate_human_review_form(form_path, packet_bundle_path=packets_path)
    assert len(records) == 15
    assert {record.reviewer_id for record in records} == {"independent_reviewer_1"}


def test_independent_review_subset_preserves_packets_and_validates(tmp_path: Path) -> None:
    selected_ids = ["review_case_002", "review_case_013", "review_case_014"]
    packets_path, form_path = export_human_review_subset(
        output_dir=tmp_path,
        review_case_ids=selected_ids,
    )
    packets = json.loads(packets_path.read_text(encoding="utf-8"))
    with form_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames is not None
    assert [packet["review_case_id"] for packet in packets] == selected_ids
    assert [row["review_case_id"] for row in rows] == selected_ids

    for row in rows:
        row["reviewer_id"] = "independent_reviewer_2"
        row["reviewer_attestation"] = "independent_human_review"
        row["reviewed_at_utc"] = "2026-09-29T15:00:00Z"
        row["verdict"] = "PASS"
        row["severity"] = "none"
        row["reason"] = "Reviewed against only the supplied packet."
    with form_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    records = validate_human_review_form(form_path, packet_bundle_path=packets_path)
    assert len(records) == 3
    assert {record.reviewer_id for record in records} == {"independent_reviewer_2"}


def test_author_can_submit_review_without_claiming_independence(tmp_path: Path) -> None:
    packets_path, form_path = export_human_review_bundle(tmp_path)
    with form_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames is not None

    for row in rows:
        row["reviewer_id"] = "project_author"
        row["reviewer_attestation"] = "author_human_review"
        row["reviewed_at_utc"] = "2026-09-29T14:30:00Z"
        row["verdict"] = "PASS"
        row["severity"] = "none"
        row["reason"] = "The supplied evidence supports the assessed behavior."

    with form_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    records = validate_human_review_form(form_path, packet_bundle_path=packets_path)
    assert {record.reviewer_attestation for record in records} == {"author_human_review"}


def test_personal_working_copy_preserves_blank_template(tmp_path: Path) -> None:
    _, template_path = export_human_review_bundle(tmp_path / "template")
    original_template = template_path.read_text(encoding="utf-8")
    working_path = tmp_path / "workspace" / "human_review_project_author.csv"

    create_human_review_working_copy(
        template_path=template_path,
        output_path=working_path,
        reviewer_id="project_author",
        reviewer_attestation="author_human_review",
    )

    assert template_path.read_text(encoding="utf-8") == original_template
    assert working_path.exists()
    with working_path.open("r", encoding="utf-8", newline="") as handle:
        first_row = next(csv.DictReader(handle))
    assert first_row["reviewer_id"] == "project_author"
    assert first_row["reviewer_attestation"] == "author_human_review"
    assert first_row["reviewed_at_utc"]


def test_human_catalog_comparison_runs_without_provider_calls(tmp_path: Path) -> None:
    packets_path, form_path = export_human_review_bundle(tmp_path)
    with form_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    assert fieldnames is not None

    library = load_case_library()
    expected = {case.case_id: case for case in library.cases}
    for index, row in enumerate(rows):
        case = library.get_case(library.development.case_ids[index])
        row["reviewer_id"] = "project_author"
        row["reviewer_attestation"] = "author_human_review"
        row["reviewed_at_utc"] = "2026-09-29T14:30:00Z"
        row["verdict"] = expected[case.case_id].expected_verdict.value
        row["severity"] = expected[case.case_id].expected_severity.value
        row["reason"] = "Reviewed against the supplied packet."
    with form_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    comparison = compare_human_review_to_catalog(
        form_path,
        packet_bundle_path=packets_path,
    )
    assert comparison["case_count"] == 15
    assert comparison["disagreement_count"] == 0
    assert comparison["provider_calls"] == 0


@pytest.mark.asyncio
async def test_atomic_judge_receives_no_expected_answer() -> None:
    class FakeLLM:
        messages: list[LLMMessage] = []

        async def complete_structured(self, **kwargs: object) -> AtomicJudgeResponse:
            self.messages = cast(list[LLMMessage], kwargs["messages"])
            return AtomicJudgeResponse(
                verdict=AtomicVerdict.FAIL,
                severity=FindingSeverity.CRITICAL,
                reason="The material claim is not supported by the supplied evidence packet.",
                evidence_references=["led_001"],
            )

    library = load_case_library()
    packet = json.loads(
        Path("evaluations/reviews/human_review/review_packets.json").read_text(encoding="utf-8")
    )[1]
    case = library.get_case("stress_02_fabricated_metric")
    criterion = next(
        item for item in library.rubric.criteria if item.criterion_id == case.criterion_id
    )
    fake = FakeLLM()
    evaluator = AtomicJudgeEvaluator(cast(LLMClient, fake), "test/model")

    response = await evaluator.evaluate(
        packet=packet,
        criterion=criterion,
        rubric=library.rubric,
    )

    prompt = "\n".join(message.content or "" for message in fake.messages)
    assert response.verdict.value == "FAIL"
    assert "expected_verdict" not in prompt
    assert "predeclared_expected_behavior" not in prompt
    assert "42.8%" in prompt


def test_atomic_judge_pilot_preflight_is_offline_and_bounded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(atomic_judge_pilot, "CACHE_PATH", tmp_path / "missing-cache.json")
    preflight = atomic_judge_pilot.build_preflight("openai/gpt-5.4")

    assert preflight.case_count == 5
    assert preflight.provider_calls_required == 5
    assert preflight.estimated_input_tokens == 30_000
    assert preflight.maximum_output_tokens == 5_000
    assert preflight.estimated_maximum_cost_usd == 0.15


def test_human_audit_requires_independent_attestation() -> None:
    judgment = AtomicJudgment(
        case_id="stress_02_fabricated_metric",
        criterion_id="grounding.material_claim_supported",
        verdict=AtomicVerdict.FAIL,
        severity=FindingSeverity.CRITICAL,
        reason="The metric is absent from the supplied evidence.",
    )

    with pytest.raises(ValidationError, match="truthful reviewer attestation"):
        AuditRecord(
            audit_id="human_invalid",
            reviewer_type="human",
            reviewer_id="reviewer_1",
            packet_sha256="abc",
            rubric_version="atomic_semantic_v1",
            created_at_utc=datetime.now(UTC),
            judgments=[judgment],
        )


@pytest.mark.parametrize(
    "verdict",
    [AtomicVerdict.PASS, AtomicVerdict.UNCLEAR, AtomicVerdict.NOT_APPLICABLE],
)
def test_non_failing_atomic_verdicts_use_no_severity(verdict: AtomicVerdict) -> None:
    judgment = AtomicJudgment(
        case_id="stress_test",
        criterion_id="grounding.material_claim_supported",
        verdict=verdict,
        severity=FindingSeverity.NONE,
        reason="The reviewer recorded a non-failing outcome.",
    )

    assert judgment.severity == FindingSeverity.NONE


def test_agreement_report_surfaces_critical_false_pass() -> None:
    library = load_case_library()
    packet = build_evaluation_packet(library, "stress_02_fabricated_metric")
    reference_judgment = AtomicJudgment(
        case_id="stress_02_fabricated_metric",
        criterion_id="grounding.material_claim_supported",
        verdict=AtomicVerdict.FAIL,
        severity=FindingSeverity.CRITICAL,
        reason="The churn metric is not present in the packet.",
    )
    judge_judgment = AtomicJudgment(
        case_id="stress_02_fabricated_metric",
        criterion_id="grounding.material_claim_supported",
        verdict=AtomicVerdict.PASS,
        severity=FindingSeverity.NONE,
        reason="The judge incorrectly accepted the metric.",
    )
    reference = AuditRecord(
        audit_id="human_1",
        reviewer_type="human",
        reviewer_id="reviewer_1",
        reviewer_attestation="independent_human_review",
        packet_sha256=packet.content_sha256,
        rubric_version="atomic_semantic_v1",
        created_at_utc=datetime.now(UTC),
        judgments=[reference_judgment],
    )
    judge = AuditRecord(
        audit_id="judge_1",
        reviewer_type="llm_judge",
        reviewer_id="judge_runner",
        packet_sha256=packet.content_sha256,
        rubric_version="atomic_semantic_v1",
        created_at_utc=datetime.now(UTC),
        judge_model="test/model",
        judge_prompt_version="judge_v1",
        judgments=[judge_judgment],
    )

    report = compare_audits(reference=reference, judge=judge, library=library)

    assert report.comparable_count == 1
    assert report.exact_agreement_rate == 0.0
    assert report.false_pass_count == 1
    assert report.critical_false_pass_count == 1
    assert len(report.unresolved_disagreements) == 1


def test_paid_evaluation_gate_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PAID_EVALUATION_ENV, raising=False)
    preflight = calculate_preflight(
        case_count=3,
        cache_hits=1,
        model_name="test/model",
        estimated_input_tokens_per_case=1000,
        maximum_output_tokens_per_case=500,
        input_cost_per_million=1.0,
        output_cost_per_million=2.0,
        approved_maximum_cost_usd=0.01,
    )

    assert preflight.provider_calls_required == 2
    with pytest.raises(PermissionError, match="explicit live opt-in"):
        require_paid_evaluation_opt_in(live=False, preflight=preflight)
    with pytest.raises(PermissionError, match=PAID_EVALUATION_ENV):
        require_paid_evaluation_opt_in(live=True, preflight=preflight)


def test_paid_evaluation_gate_accepts_only_approved_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PAID_EVALUATION_ENV, "true")
    too_expensive = calculate_preflight(
        case_count=10,
        cache_hits=0,
        model_name="test/model",
        estimated_input_tokens_per_case=10000,
        maximum_output_tokens_per_case=5000,
        input_cost_per_million=10.0,
        output_cost_per_million=20.0,
        approved_maximum_cost_usd=0.10,
    )
    with pytest.raises(PermissionError, match="exceeds"):
        require_paid_evaluation_opt_in(live=True, preflight=too_expensive)

    approved = calculate_preflight(
        case_count=1,
        cache_hits=0,
        model_name="test/model",
        estimated_input_tokens_per_case=1000,
        maximum_output_tokens_per_case=500,
        input_cost_per_million=1.0,
        output_cost_per_million=2.0,
        approved_maximum_cost_usd=0.01,
    )
    require_paid_evaluation_opt_in(live=True, preflight=approved)
