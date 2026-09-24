"""Automated regression testing and release gate verification."""

from pydantic import BaseModel, ConfigDict, Field

from evaluations.config import EVALUATION_THRESHOLDS, EvaluationThresholds
from evaluations.runner import ScenarioRunResult


class RegressionGateReport(BaseModel):
    """Structured report determining whether candidate release satisfies all regression gates."""

    model_config = ConfigDict(frozen=True)

    passed: bool
    structural_validity_pass: bool
    groundedness_pass: bool
    cross_source_pass: bool
    context_recall_pass: bool
    confidence_calibration_pass: bool
    zero_critical_safety_errors: bool

    failed_reasons: list[str] = Field(default_factory=list)
    measured_values: dict[str, float] = Field(default_factory=dict)


def evaluate_regression_gates(
    results: list[ScenarioRunResult],
    thresholds: EvaluationThresholds = EVALUATION_THRESHOLDS,
) -> RegressionGateReport:
    """Evaluate candidate benchmark results against release criteria."""
    if not results:
        return RegressionGateReport(
            passed=False,
            structural_validity_pass=False,
            groundedness_pass=False,
            cross_source_pass=False,
            context_recall_pass=False,
            confidence_calibration_pass=False,
            zero_critical_safety_errors=False,
            failed_reasons=["No evaluation results provided."],
        )

    n = len(results)

    # 1. Structural Citation Validity (Must be 100%)
    validities = [r.deterministic.structural_citation_validity for r in results]
    mean_val = sum(validities) / n
    valid_pass = bool(mean_val >= thresholds.min_structural_citation_validity)

    # 2. Groundedness (Native 0-4 scale >= 3.20)
    ground_scores = [r.judge.groundedness.score for r in results]
    mean_ground = sum(ground_scores) / n
    ground_pass = bool(mean_ground >= thresholds.min_groundedness_score)

    # 3. Cross-Source Reasoning (Native 0-4 scale >= 3.00)
    cross_scores = [r.judge.cross_source_reasoning.score for r in results]
    mean_cross = sum(cross_scores) / n
    cross_pass = bool(mean_cross >= thresholds.min_cross_source_score)

    # 4. Context Recall (>= 85%)
    recalls = [r.deterministic.context_recall for r in results]
    mean_recall = sum(recalls) / n
    recall_pass = bool(mean_recall >= thresholds.min_context_recall)

    # 5. Confidence Calibration (Overconfidence penalty == 0)
    overconf_total = sum(r.deterministic.overconfidence_penalty for r in results)
    conf_pass = bool(overconf_total <= thresholds.max_overconfidence_penalty_count)

    # 6. Critical Safety Errors
    crit_errors = sum(1 for r in results for e in r.classified_errors if e.severity == "critical")
    safety_pass = bool(crit_errors == 0)

    failed_reasons: list[str] = []
    if not valid_pass:
        failed_reasons.append(
            f"Structural validity {mean_val:.2%} < {thresholds.min_structural_citation_validity:.0%}"
        )
    if not ground_pass:
        failed_reasons.append(
            f"Mean groundedness {mean_ground:.2f} < {thresholds.min_groundedness_score:.2f}"
        )
    if not cross_pass:
        failed_reasons.append(
            f"Mean cross-source score {mean_cross:.2f} < {thresholds.min_cross_source_score:.2f}"
        )
    if not recall_pass:
        failed_reasons.append(
            f"Mean context recall {mean_recall:.2%} < {thresholds.min_context_recall:.0%}"
        )
    if not conf_pass:
        failed_reasons.append(
            f"Found {overconf_total} overconfidence penalty instances (allowed: {thresholds.max_overconfidence_penalty_count})"
        )
    if not safety_pass:
        failed_reasons.append(f"Detected {crit_errors} critical error taxonomy failures")

    all_passed = (
        valid_pass and ground_pass and cross_pass and recall_pass and conf_pass and safety_pass
    )

    measured = {
        "structural_validity": round(mean_val, 4),
        "groundedness": round(mean_ground, 4),
        "cross_source": round(mean_cross, 4),
        "context_recall": round(mean_recall, 4),
        "overconfidence_penalties": float(overconf_total),
        "critical_errors": float(crit_errors),
    }

    return RegressionGateReport(
        passed=all_passed,
        structural_validity_pass=valid_pass,
        groundedness_pass=ground_pass,
        cross_source_pass=cross_pass,
        context_recall_pass=recall_pass,
        confidence_calibration_pass=conf_pass,
        zero_critical_safety_errors=safety_pass,
        failed_reasons=failed_reasons,
        measured_values=measured,
    )
