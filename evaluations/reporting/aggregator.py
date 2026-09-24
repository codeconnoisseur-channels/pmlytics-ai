"""Statistical aggregation, bootstrap confidence intervals, Wilcoxon signed-rank testing, and weighted kappa."""

import math
import random
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from evaluations.runner import ScenarioRunResult


class BootstrapConfidenceInterval(BaseModel):
    """95% bootstrap confidence interval."""

    model_config = ConfigDict(frozen=True)
    mean: float
    ci_lower: float
    ci_upper: float
    std_dev: float


class WilcoxonTestResult(BaseModel):
    """Result of paired two-tailed Wilcoxon signed-rank test on scenario means."""

    model_config = ConfigDict(frozen=True)
    statistic_w: float
    p_value: float
    n_pairs: int
    significant_at_05: bool


class DimensionKappaResult(BaseModel):
    """Quadratically weighted Cohen's kappa for one judge dimension with 95% bootstrap CI."""

    model_config = ConfigDict(frozen=True)
    dimension: str
    weighted_kappa: float
    ci_lower: float
    ci_upper: float
    meets_qualification_threshold: bool  # kappa >= 0.75


def compute_bootstrap_ci(
    values: Sequence[float],
    n_resamples: int = 1000,
    seed: int = 20260914,
) -> BootstrapConfidenceInterval:
    """Compute 95% bootstrap confidence interval for the mean."""
    if not values:
        return BootstrapConfidenceInterval(mean=0.0, ci_lower=0.0, ci_upper=0.0, std_dev=0.0)

    n = len(values)
    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    std_dev = math.sqrt(variance)

    if n == 1:
        return BootstrapConfidenceInterval(
            mean=round(mean_val, 4),
            ci_lower=round(mean_val, 4),
            ci_upper=round(mean_val, 4),
            std_dev=0.0,
        )

    rng = random.Random(seed)
    boot_means: list[float] = []
    for _ in range(n_resamples):
        sample = [rng.choice(values) for _ in range(n)]
        boot_means.append(sum(sample) / n)

    boot_means.sort()
    lower_idx = int(0.025 * n_resamples)
    upper_idx = int(0.975 * n_resamples)

    return BootstrapConfidenceInterval(
        mean=round(mean_val, 4),
        ci_lower=round(boot_means[lower_idx], 4),
        ci_upper=round(boot_means[upper_idx], 4),
        std_dev=round(std_dev, 4),
    )


def compute_paired_wilcoxon(
    group_a: Sequence[float],
    group_b: Sequence[float],
) -> WilcoxonTestResult:
    """Paired two-tailed Wilcoxon signed-rank test on paired scenario-level outcomes."""
    if len(group_a) != len(group_b) or len(group_a) == 0:
        raise ValueError("Groups must be non-empty and of identical length.")

    diffs: list[float] = [a - b for a, b in zip(group_a, group_b, strict=True)]
    non_zero = [(abs(d), 1 if d > 0 else -1) for d in diffs if d != 0.0]

    n_r = len(non_zero)
    if n_r == 0:
        return WilcoxonTestResult(
            statistic_w=0.0,
            p_value=1.0,
            n_pairs=len(diffs),
            significant_at_05=False,
        )

    # Rank absolute differences
    non_zero.sort(key=lambda x: x[0])
    ranks: list[float] = [0.0] * n_r

    i = 0
    while i < n_r:
        j = i
        while j < n_r and non_zero[j][0] == non_zero[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    w_plus = sum(r for r, (_, sgn) in zip(ranks, non_zero, strict=True) if sgn > 0)
    w_minus = sum(r for r, (_, sgn) in zip(ranks, non_zero, strict=True) if sgn < 0)
    w_stat = min(w_plus, w_minus)

    # Normal approximation for p-value (standard for n_r >= 10, robust baseline)
    mu = (n_r * (n_r + 1)) / 4.0
    sigma = math.sqrt((n_r * (n_r + 1) * (2 * n_r + 1)) / 24.0)

    if sigma == 0.0:
        p_val = 1.0
    else:
        # Continuity-corrected z
        z = (abs(w_plus - mu) - 0.5) / sigma
        # Two-tailed normal CDF approximation via math.erf
        cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
        p_val = max(0.0, min(1.0, 2.0 * (1.0 - cdf)))

    return WilcoxonTestResult(
        statistic_w=round(w_stat, 2),
        p_value=round(p_val, 4),
        n_pairs=len(diffs),
        significant_at_05=bool(p_val < 0.05),
    )


def compute_quadratically_weighted_kappa(
    rater1_scores: Sequence[int],
    rater2_scores: Sequence[int],
    num_categories: int = 5,  # 0 to 4
) -> float:
    """Compute Quadratically Weighted Cohen's Kappa for ordinal ratings."""
    if len(rater1_scores) != len(rater2_scores) or len(rater1_scores) == 0:
        return 0.0

    n = len(rater1_scores)
    k = num_categories

    # Observed matrix O and marginals
    observed: list[list[float]] = [[0.0] * k for _ in range(k)]
    m1 = [0.0] * k
    m2 = [0.0] * k

    for s1, s2 in zip(rater1_scores, rater2_scores, strict=True):
        c1 = max(0, min(k - 1, s1))
        c2 = max(0, min(k - 1, s2))
        observed[c1][c2] += 1.0
        m1[c1] += 1.0
        m2[c2] += 1.0

    # Expected matrix E
    expected: list[list[float]] = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            expected[i][j] = (m1[i] * m2[j]) / n

    # Weights w_ij = (i - j)^2 / (k - 1)^2
    max_sq_diff = (k - 1) ** 2
    sum_weighted_observed = 0.0
    sum_weighted_expected = 0.0

    for i in range(k):
        for j in range(k):
            w = ((i - j) ** 2) / float(max_sq_diff)
            sum_weighted_observed += w * observed[i][j]
            sum_weighted_expected += w * expected[i][j]

    if sum_weighted_expected == 0.0:
        return 1.0

    kappa = 1.0 - (sum_weighted_observed / sum_weighted_expected)
    return round(kappa, 4)


def compute_dimension_kappa_with_bootstrap(
    dimension: str,
    rater1_scores: Sequence[int],
    rater2_scores: Sequence[int],
    n_resamples: int = 1000,
    seed: int = 20260914,
) -> DimensionKappaResult:
    """Compute quadratically weighted kappa and 95% bootstrap CI for one judge dimension."""
    base_kappa = compute_quadratically_weighted_kappa(rater1_scores, rater2_scores)

    n = len(rater1_scores)
    rng = random.Random(seed)
    boot_kappas: list[float] = []

    pairs = list(zip(rater1_scores, rater2_scores, strict=True))
    for _ in range(n_resamples):
        sample = [rng.choice(pairs) for _ in range(n)]
        s1 = [p[0] for p in sample]
        s2 = [p[1] for p in sample]
        boot_kappas.append(compute_quadratically_weighted_kappa(s1, s2))

    boot_kappas.sort()
    lower_idx = int(0.025 * n_resamples)
    upper_idx = int(0.975 * n_resamples)

    return DimensionKappaResult(
        dimension=dimension,
        weighted_kappa=base_kappa,
        ci_lower=round(boot_kappas[lower_idx], 4),
        ci_upper=round(boot_kappas[upper_idx], 4),
        meets_qualification_threshold=bool(base_kappa >= 0.75),
    )


def aggregate_scenario_level_metrics(
    results: Sequence[ScenarioRunResult],
) -> dict[str, float]:
    """Aggregate repeated trial runs (e.g. 3 trials) to scenario-level means without pseudo-replication."""
    by_scenario: dict[str, list[ScenarioRunResult]] = {}
    for r in results:
        by_scenario.setdefault(r.scenario_id, []).append(r)

    scenario_means: dict[str, float] = {}
    for scn_id, runs in by_scenario.items():
        # Average groundedness across trials for this scenario
        groundedness_scores = [run.judge.groundedness.score for run in runs]
        scenario_means[scn_id] = sum(groundedness_scores) / len(groundedness_scores)

    return scenario_means
