"""Export and validate blind, offline human-review worksheets."""

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from evaluations.calibration.loader import CaseLibrary, load_case_library
from evaluations.calibration.packets import build_evaluation_packet
from evaluations.calibration.schema import (
    AtomicJudgment,
    AtomicVerdict,
    AuditRecord,
    FindingSeverity,
)

REVIEW_COLUMNS = [
    "reviewer_id",
    "reviewer_attestation",
    "reviewed_at_utc",
    "review_case_id",
    "packet_sha256",
    "criterion_id",
    "dimension",
    "rubric_question",
    "pass_definition",
    "fail_definition",
    "verdict",
    "severity",
    "reason",
    "claim_reference",
    "evidence_references",
]
DEFAULT_REVIEW_PACKETS_PATH = (
    Path(__file__).resolve().parents[1] / "reviews" / "human_review" / "review_packets.json"
)


def _stable_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _review_cases(library: CaseLibrary) -> list[tuple[str, str]]:
    return [
        (f"review_case_{index:03d}", case_id)
        for index, case_id in enumerate(library.development.case_ids, 1)
    ]


def build_blind_review_packet(
    library: CaseLibrary,
    *,
    review_case_id: str,
    internal_case_id: str,
) -> dict[str, object]:
    """Remove descriptive internal IDs and all expected answers from a review packet."""
    packet = build_evaluation_packet(library, internal_case_id)
    content: dict[str, object] = {
        "packet_version": packet.packet_version,
        "review_case_id": review_case_id,
        "user_query": packet.user_query,
        "evidence": packet.evidence,
        "candidate_recommendation": packet.candidate_recommendation,
        "source_failures": packet.source_failures,
    }
    content["packet_sha256"] = _stable_hash(content)
    return content


def export_human_review_bundle(output_dir: Path) -> tuple[Path, Path]:
    """Create a blind packet file and a spreadsheet-friendly blank review form."""
    library = load_case_library()
    criteria = {criterion.criterion_id: criterion for criterion in library.rubric.criteria}
    output_dir.mkdir(parents=True, exist_ok=True)
    packets_path = output_dir / "review_packets.json"
    form_path = output_dir / "human_review_form.csv"

    packets: list[dict[str, object]] = []
    rows: list[dict[str, str]] = []
    for review_case_id, internal_case_id in _review_cases(library):
        case = library.get_case(internal_case_id)
        criterion = criteria[case.criterion_id]
        packet = build_blind_review_packet(
            library,
            review_case_id=review_case_id,
            internal_case_id=internal_case_id,
        )
        packets.append(packet)
        rows.append(
            {
                "reviewer_id": "",
                "reviewer_attestation": "",
                "reviewed_at_utc": "",
                "review_case_id": review_case_id,
                "packet_sha256": str(packet["packet_sha256"]),
                "criterion_id": criterion.criterion_id,
                "dimension": criterion.dimension,
                "rubric_question": criterion.question,
                "pass_definition": criterion.pass_definition,
                "fail_definition": criterion.fail_definition,
                "verdict": "",
                "severity": "",
                "reason": "",
                "claim_reference": "",
                "evidence_references": "",
            }
        )

    packets_path.write_text(json.dumps(packets, indent=2), encoding="utf-8")
    with form_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return packets_path, form_path


def export_human_review_subset(
    *,
    output_dir: Path,
    review_case_ids: list[str],
    source_packets_path: Path = DEFAULT_REVIEW_PACKETS_PATH,
    source_form_path: Path | None = None,
) -> tuple[Path, Path]:
    """Export a blind subset while preserving the packets already judged."""
    if not review_case_ids or len(review_case_ids) != len(set(review_case_ids)):
        raise ValueError("Review case IDs must be a non-empty unique list")

    source_form_path = source_form_path or source_packets_path.with_name("human_review_form.csv")
    packet_data = json.loads(source_packets_path.read_text(encoding="utf-8"))
    if not isinstance(packet_data, list):
        raise ValueError("Human-review packet bundle must contain a JSON list")
    packet_map = {
        str(packet["review_case_id"]): packet
        for packet in packet_data
        if isinstance(packet, dict) and "review_case_id" in packet
    }
    with source_form_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        form_rows = list(reader)
        fieldnames = reader.fieldnames
    if fieldnames != REVIEW_COLUMNS:
        raise ValueError("Human-review template columns do not match the expected schema")
    row_map = {row["review_case_id"]: row for row in form_rows}

    missing = [
        case_id
        for case_id in review_case_ids
        if case_id not in packet_map or case_id not in row_map
    ]
    if missing:
        raise ValueError(f"Unknown review case IDs: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    packets_path = output_dir / "review_packets.json"
    form_path = output_dir / "independent_review_form.csv"
    packets_path.write_text(
        json.dumps([packet_map[case_id] for case_id in review_case_ids], indent=2) + "\n",
        encoding="utf-8",
    )
    with form_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(row_map[case_id] for case_id in review_case_ids)
    return packets_path, form_path


def create_human_review_working_copy(
    *,
    template_path: Path,
    output_path: Path,
    reviewer_id: str,
    reviewer_attestation: Literal["author_human_review", "independent_human_review"],
) -> Path:
    """Create a personalized, untracked worksheet without changing the template."""
    if output_path.exists():
        raise FileExistsError(
            f"Review file already exists: {output_path}. Rename it or choose another output path."
        )
    with template_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if fieldnames != REVIEW_COLUMNS:
        raise ValueError("Human-review template columns do not match the expected schema")

    started_at = datetime.now(UTC).isoformat()
    for row in rows:
        row["reviewer_id"] = reviewer_id
        row["reviewer_attestation"] = reviewer_attestation
        row["reviewed_at_utc"] = started_at

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def validate_human_review_form(
    form_path: Path,
    *,
    packet_bundle_path: Path = DEFAULT_REVIEW_PACKETS_PATH,
) -> list[AuditRecord]:
    """Validate a completed form and convert blind IDs back to internal audit records."""
    library = load_case_library()
    criteria = {criterion.criterion_id: criterion for criterion in library.rubric.criteria}
    mappings = dict(_review_cases(library))
    packet_data = json.loads(packet_bundle_path.read_text(encoding="utf-8"))
    if not isinstance(packet_data, list):
        raise ValueError("Human-review packet bundle must contain a JSON list")
    review_packets = {
        str(packet["review_case_id"]): packet
        for packet in packet_data
        if isinstance(packet, dict) and "review_case_id" in packet
    }
    if not review_packets or not set(review_packets) <= set(mappings):
        raise ValueError("Human-review packet bundle contains unknown review cases")
    with form_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != len(review_packets):
        raise ValueError(f"Expected {len(review_packets)} review rows, found {len(rows)}")
    row_case_ids = {row.get("review_case_id", "") for row in rows}
    if row_case_ids != set(review_packets):
        raise ValueError("Human-review rows do not match the supplied packet bundle")

    records: list[AuditRecord] = []
    seen: set[str] = set()
    for row in rows:
        review_case_id = row.get("review_case_id", "")
        if review_case_id in seen or review_case_id not in mappings:
            raise ValueError(f"Unknown or duplicate review case: {review_case_id}")
        seen.add(review_case_id)
        internal_case_id = mappings[review_case_id]
        case = library.get_case(internal_case_id)
        criterion = criteria[case.criterion_id]
        packet = review_packets[review_case_id]

        protected_values = {
            "packet_sha256": str(packet["packet_sha256"]),
            "criterion_id": criterion.criterion_id,
            "dimension": criterion.dimension,
            "rubric_question": criterion.question,
            "pass_definition": criterion.pass_definition,
            "fail_definition": criterion.fail_definition,
        }
        for field, expected in protected_values.items():
            if row.get(field) != expected:
                raise ValueError(f"Protected field {field} changed for {review_case_id}")

        reviewer_id = row.get("reviewer_id", "").strip()
        reviewed_at = row.get("reviewed_at_utc", "").strip()
        reason = row.get("reason", "").strip()
        if not reviewer_id or not reviewed_at or not reason:
            raise ValueError(
                f"Reviewer ID, review time, and reason are required for {review_case_id}"
            )
        attestation = row.get("reviewer_attestation")
        if attestation not in {"author_human_review", "independent_human_review"}:
            raise ValueError(
                f"A truthful human-review attestation is required for {review_case_id}"
            )
        validated_attestation = cast(
            Literal["author_human_review", "independent_human_review"],
            attestation,
        )

        judgment = AtomicJudgment(
            case_id=internal_case_id,
            criterion_id=criterion.criterion_id,
            verdict=AtomicVerdict(row.get("verdict", "")),
            severity=FindingSeverity(row.get("severity", "")),
            reason=reason,
            claim_reference=row.get("claim_reference", "").strip() or None,
            evidence_references=[
                reference.strip()
                for reference in row.get("evidence_references", "").split(";")
                if reference.strip()
            ],
        )
        records.append(
            AuditRecord(
                audit_id=f"human_{reviewer_id}_{review_case_id}",
                reviewer_type="human",
                reviewer_id=reviewer_id,
                reviewer_attestation=validated_attestation,
                packet_sha256=str(packet["packet_sha256"]),
                rubric_version=library.rubric.rubric_version,
                created_at_utc=datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")),
                judgments=[judgment],
            )
        )
    return records


def save_human_review_submission(
    *,
    submission_path: Path,
    output_path: Path,
    packet_bundle_path: Path = DEFAULT_REVIEW_PACKETS_PATH,
) -> Path:
    """Validate and save a submitted worksheet into the ignored reviewer workspace."""
    validate_human_review_form(
        submission_path,
        packet_bundle_path=packet_bundle_path,
    )
    with submission_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if fieldnames != REVIEW_COLUMNS:
        raise ValueError("Submitted review columns do not match the expected schema")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def compare_human_review_to_catalog(
    form_path: Path,
    *,
    packet_bundle_path: Path = DEFAULT_REVIEW_PACKETS_PATH,
) -> dict[str, object]:
    """Compare a validated human review with current product-owned expectations."""
    library = load_case_library()
    records = validate_human_review_form(form_path, packet_bundle_path=packet_bundle_path)
    expected_by_id = {case.case_id: case for case in library.cases}
    disagreements: list[dict[str, str]] = []
    verdict_matches = 0
    severity_matches = 0

    for record in records:
        judgment = record.judgments[0]
        expected = expected_by_id[judgment.case_id]
        verdict_match = judgment.verdict == expected.expected_verdict
        severity_match = judgment.severity == expected.expected_severity
        verdict_matches += int(verdict_match)
        severity_matches += int(severity_match)
        if not verdict_match or not severity_match:
            disagreements.append(
                {
                    "case_id": judgment.case_id,
                    "criterion_id": judgment.criterion_id,
                    "expected_verdict": expected.expected_verdict.value,
                    "human_verdict": judgment.verdict.value,
                    "expected_severity": expected.expected_severity.value,
                    "human_severity": judgment.severity.value,
                    "human_reason": judgment.reason,
                }
            )

    total = len(records)
    return {
        "comparison_type": "human_review_vs_product_owned_expectations",
        "reviewer_attestation": records[0].reviewer_attestation if records else None,
        "case_count": total,
        "verdict_match_count": verdict_matches,
        "verdict_match_rate": verdict_matches / total if total else None,
        "severity_match_count": severity_matches,
        "severity_match_rate": severity_matches / total if total else None,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "provider_calls": 0,
    }
