"""Offline agreement and critical false-pass reporting."""

from collections import defaultdict

from evaluations.calibration.loader import CaseLibrary
from evaluations.calibration.schema import (
    AgreementReport,
    AtomicVerdict,
    AuditRecord,
    DimensionAgreement,
    Disagreement,
    FindingSeverity,
)


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def compare_audits(
    *,
    reference: AuditRecord,
    judge: AuditRecord,
    library: CaseLibrary,
) -> AgreementReport:
    """Compare an independently reviewed reference audit with an LLM judge audit."""
    return compare_audit_sets(
        references=[reference],
        judges=[judge],
        library=library,
    )


def compare_audit_sets(
    *,
    references: list[AuditRecord],
    judges: list[AuditRecord],
    library: CaseLibrary,
) -> AgreementReport:
    """Compare matching collections of human and LLM judgments offline."""
    if not references or not judges:
        raise ValueError("Reference and judge audit collections cannot be empty")
    if any(record.reviewer_type != "human" for record in references):
        raise ValueError("Reference audits must be independently attested human reviews")
    if any(record.reviewer_attestation != "independent_human_review" for record in references):
        raise ValueError("Reference audits require independent human attestation")
    if any(record.reviewer_type != "llm_judge" for record in judges):
        raise ValueError("Judge audits must be LLM judge records")

    reference_records = {
        (judgment.case_id, judgment.criterion_id): (record, judgment)
        for record in references
        for judgment in record.judgments
    }
    judge_records = {
        (judgment.case_id, judgment.criterion_id): (record, judgment)
        for record in judges
        for judgment in record.judgments
    }
    if set(reference_records) != set(judge_records):
        raise ValueError("Reference and judge audits must cover the same cases and criteria")
    for key in reference_records:
        reference_record = reference_records[key][0]
        judge_record = judge_records[key][0]
        if reference_record.rubric_version != judge_record.rubric_version:
            raise ValueError("Reference and judge audits must use the same rubric version")
        if reference_record.packet_sha256 != judge_record.packet_sha256:
            raise ValueError("Reference and judge audits must use the same evaluation packet")

    reference_map = {key: value[1] for key, value in reference_records.items()}
    judge_map = {key: value[1] for key, value in judge_records.items()}
    shared_keys = sorted(reference_map)
    case_dimensions = {case.case_id: case.dimension for case in library.cases}

    exact = 0
    critical_total = 0
    critical_exact = 0
    false_passes = 0
    critical_false_passes = 0
    false_fails = 0
    disagreements: list[Disagreement] = []
    dimension_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "exact": 0, "false_pass": 0, "false_fail": 0}
    )

    for key in shared_keys:
        reference_item = reference_map[key]
        judge_item = judge_map[key]
        dimension = case_dimensions.get(key[0], "unknown")
        is_exact = reference_item.verdict == judge_item.verdict
        is_critical = reference_item.severity == FindingSeverity.CRITICAL
        false_pass = (
            reference_item.verdict == AtomicVerdict.FAIL
            and judge_item.verdict == AtomicVerdict.PASS
        )
        false_fail = (
            reference_item.verdict == AtomicVerdict.PASS
            and judge_item.verdict == AtomicVerdict.FAIL
        )

        exact += int(is_exact)
        critical_total += int(is_critical)
        critical_exact += int(is_critical and is_exact)
        false_passes += int(false_pass)
        critical_false_passes += int(false_pass and is_critical)
        false_fails += int(false_fail)

        counts = dimension_counts[dimension]
        counts["total"] += 1
        counts["exact"] += int(is_exact)
        counts["false_pass"] += int(false_pass)
        counts["false_fail"] += int(false_fail)

        if not is_exact:
            disagreements.append(
                Disagreement(
                    case_id=key[0],
                    criterion_id=key[1],
                    dimension=dimension,
                    reference_verdict=reference_item.verdict,
                    judge_verdict=judge_item.verdict,
                    reference_severity=reference_item.severity,
                    judge_severity=judge_item.severity,
                    critical_false_pass=false_pass and is_critical,
                )
            )

    by_dimension = [
        DimensionAgreement(
            dimension=dimension,
            comparable_count=counts["total"],
            exact_agreement_count=counts["exact"],
            exact_agreement_rate=_rate(counts["exact"], counts["total"]),
            false_pass_count=counts["false_pass"],
            false_fail_count=counts["false_fail"],
        )
        for dimension, counts in sorted(dimension_counts.items())
    ]

    return AgreementReport(
        comparable_count=len(shared_keys),
        exact_agreement_count=exact,
        exact_agreement_rate=_rate(exact, len(shared_keys)),
        critical_reference_count=critical_total,
        critical_agreement_count=critical_exact,
        critical_agreement_rate=_rate(critical_exact, critical_total),
        false_pass_count=false_passes,
        critical_false_pass_count=critical_false_passes,
        false_fail_count=false_fails,
        unresolved_disagreements=disagreements,
        by_dimension=by_dimension,
    )
