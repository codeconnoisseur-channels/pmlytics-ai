"""Reporting and statistical aggregation package."""

from evaluations.reporting.aggregator import (
    BootstrapConfidenceInterval,
    DimensionKappaResult,
    WilcoxonTestResult,
    aggregate_scenario_level_metrics,
    compute_bootstrap_ci,
    compute_dimension_kappa_with_bootstrap,
    compute_paired_wilcoxon,
    compute_quadratically_weighted_kappa,
)
from evaluations.reporting.markdown_report import (
    generate_ablation_comparison_report,
    generate_summary_report,
)
from evaluations.reporting.regression import (
    RegressionGateReport,
    evaluate_regression_gates,
)

__all__ = [
    "BootstrapConfidenceInterval",
    "WilcoxonTestResult",
    "DimensionKappaResult",
    "compute_bootstrap_ci",
    "compute_paired_wilcoxon",
    "compute_quadratically_weighted_kappa",
    "compute_dimension_kappa_with_bootstrap",
    "aggregate_scenario_level_metrics",
    "generate_summary_report",
    "generate_ablation_comparison_report",
    "RegressionGateReport",
    "evaluate_regression_gates",
]
