import re

from app.domain.recommendation import ProductRecommendation
from app.orchestration.state import InvestigationState
from pydantic import BaseModel, ConfigDict, Field

from evaluations.ground_truth.schema import EvaluationScenario, SourceDomain


class DeterministicMetrics(BaseModel):
    """Programmatic metrics calculated directly from state and ground truth."""

    model_config = ConfigDict(frozen=True)

    # Citation & Provenance
    structural_citation_validity: float = 1.0
    total_citations: int = 0
    valid_citations: int = 0
    hallucinated_citations: int = 0
    citation_to_evidence_consistent: bool = True
    evidence_record_existence: bool = True
    provenance_validity: float = 1.0
    unsupported_or_fabricated_ids: int = 0

    # Schema Validity
    schema_validity: bool = True

    # Evidence Coverage (Scenario-Aware)
    evidence_coverage: float = 1.0

    # Retrieval (Deduplicated by Unique Evidence Records)
    context_recall: float = 0.0
    context_precision: float = 0.0
    unique_retrieved_records_count: int = 0
    expected_records_count: int = 0
    retrieval_redundancy_rate: float = 0.0

    # Source Selection (Mapped from Specialist Tasks)
    source_selection_precision: float = 1.0
    source_selection_recall: float = 1.0
    source_selection_jaccard: float = 1.0
    selected_sources: list[SourceDomain] = Field(default_factory=list)

    # Contradiction Handling & Limits
    deterministic_contradiction_fidelity: bool = True
    tool_iteration_limits_respected: bool = True
    execution_integrity_valid: bool = True

    # Epistemic & Confidence Calibration
    epistemic_separation_valid: bool = True
    confidence_matched_expected_range: bool = True
    overconfidence_penalty: int = 0


def evaluate_structural_citations(
    state: InvestigationState,
    recommendation: ProductRecommendation | None,
) -> tuple[float, int, int, int]:
    """Verify 100% structural citation resolution against state evidence ledger.

    Returns:
        (validity_ratio, total_citations, valid_citations, hallucinated_citations)
    """
    if not recommendation:
        return 1.0, 0, 0, 0

    citations = recommendation.evidence
    total = len(citations)
    if total == 0:
        return 0.0, 0, 0, 0

    valid = 0
    hallucinated = 0

    ledger = state.evidence_ledger_entries

    for c in citations:
        entry = ledger.get(c.ledger_entry_id)
        if entry is None:
            hallucinated += 1
            continue

        # Verify source type and reference format match
        if entry.source_type != c.source_type or entry.source_reference != c.source_reference:
            hallucinated += 1
            continue

        valid += 1

    validity_ratio = valid / total if total > 0 else 1.0
    return validity_ratio, total, valid, hallucinated


def map_tasks_to_sources(state: InvestigationState) -> set[SourceDomain]:
    """Map selected specialist tasks in plan to corresponding source domains."""
    selected_domains: set[SourceDomain] = set()
    if not state.plan or not state.plan.tasks:
        return selected_domains

    role_to_domain: dict[str, SourceDomain] = {
        "research": "zendesk",
        "analytics": "posthog",
        "engineering": "jira",
    }

    for task in state.plan.tasks:
        domain = role_to_domain.get(task.specialist)
        if domain:
            selected_domains.add(domain)

    return selected_domains


def evaluate_source_selection(
    selected_sources: set[SourceDomain],
    required_sources: list[SourceDomain],
) -> tuple[float, float, float]:
    """Calculate source set precision, recall, and Jaccard similarity."""
    req_set = set(required_sources)
    if not selected_sources and not req_set:
        return 1.0, 1.0, 1.0
    if not selected_sources or not req_set:
        return 0.0, 0.0, 0.0

    intersection = selected_sources & req_set
    union = selected_sources | req_set

    precision = len(intersection) / len(selected_sources)
    recall = len(intersection) / len(req_set)
    jaccard = len(intersection) / len(union)

    return precision, recall, jaccard


def extract_unique_evidence_records(
    state: InvestigationState,
    scenario: EvaluationScenario,
) -> tuple[set[str], int]:
    """Extract unique underlying evidence records from ledger entries.

    Returns:
        (unique_record_identifiers, total_ledger_entries)
    """
    unique_ids: set[str] = set()
    total_entries = len(state.evidence_ledger_entries)

    for entry in state.evidence_ledger_entries.values():
        if entry.source_type == "zendesk":
            # Support records identify by ticket ID
            unique_ids.add(f"zendesk:{entry.source_reference}")
        elif entry.source_type == "jira":
            # Engineering records identify by issue key
            unique_ids.add(f"jira:{entry.source_reference}")
        elif entry.source_type == "posthog":
            # Map query to canonical ground truth observation ID
            matched_obs_id: str | None = None
            for obs in scenario.expected_analytics_observations:
                # Match metric or event filter keywords in data summary
                if (
                    obs.metric.lower() in entry.data_summary.lower()
                    or obs.event_filter.lower() in entry.data_summary.lower()
                ):
                    matched_obs_id = obs.obs_id
                    break

            if matched_obs_id:
                unique_ids.add(matched_obs_id)
            else:
                # Fallback to source reference if not matching specific obs_id
                unique_ids.add(f"posthog:{entry.source_reference}")

    return unique_ids, total_entries


def evaluate_retrieval_quality(
    unique_retrieved: set[str],
    scenario: EvaluationScenario,
    total_ledger_entries: int,
) -> tuple[float, float, float]:
    """Compute Context Recall, Context Precision on unique records, and Redundancy Rate."""
    expected_set: set[str] = set()

    for ticket in scenario.expected_support_tickets:
        expected_set.add(f"zendesk:{ticket}")
    for issue in scenario.expected_jira_issues:
        expected_set.add(f"jira:{issue}")
    for obs in scenario.expected_analytics_observations:
        expected_set.add(obs.obs_id)

    if not expected_set:
        return 1.0, 1.0, 0.0

    intersection = unique_retrieved & expected_set
    recall = len(intersection) / len(expected_set)
    precision = len(intersection) / len(unique_retrieved) if unique_retrieved else 0.0

    # Redundancy rate: duplicate retrievals beyond unique records
    redundancy = 0.0
    if total_ledger_entries > 0:
        redundancy = max(0.0, (total_ledger_entries - len(unique_retrieved)) / total_ledger_entries)

    return recall, precision, redundancy


def evaluate_confidence_calibration(
    recommendation: ProductRecommendation | None,
    scenario: EvaluationScenario,
) -> tuple[bool, int]:
    """Deterministic confidence calibration evaluation."""
    if not recommendation:
        return False, 0

    conf = recommendation.confidence
    min_conf, max_conf = scenario.expected_confidence_range

    confidence_order = {"low": 1, "medium": 2, "high": 3}
    actual_val = confidence_order.get(conf, 2)
    min_val = confidence_order.get(min_conf, 1)
    max_val = confidence_order.get(max_conf, 3)

    is_matched = min_val <= actual_val <= max_val

    # Overconfidence penalty: expected was strictly low, but recommendation claimed high
    overconfidence_penalty = 1 if max_conf == "low" and conf == "high" else 0

    return is_matched, overconfidence_penalty


def evaluate_citation_consistency_and_provenance(
    state: InvestigationState,
    recommendation: ProductRecommendation | None,
) -> tuple[bool, bool, float, int]:
    """Verify citation-to-evidence consistency, evidence record existence, and provenance validity.

    Returns:
        (consistent, all_exist, provenance_ratio, unsupported_count)
    """
    if not recommendation or not recommendation.evidence:
        return True, True, 1.0, 0

    ledger = state.evidence_ledger_entries
    all_exist = True
    consistent = True
    valid_provenance_count = 0
    unsupported_count = 0
    total = len(recommendation.evidence)

    for c in recommendation.evidence:
        entry = ledger.get(c.ledger_entry_id)
        if entry is None:
            all_exist = False
            consistent = False
            unsupported_count += 1
            continue

        if entry.source_type != c.source_type or entry.source_reference != c.source_reference:
            consistent = False

        # Provenance format verification
        is_prov_valid = False
        ref = c.source_reference
        if c.source_type == "zendesk":
            is_prov_valid = bool(ref.startswith("zen_") or ref.startswith("t_") or ref.isdigit())
        elif c.source_type == "jira":
            is_prov_valid = bool(re.match(r"^[A-Z0-9]+-\d+$", ref))
        elif c.source_type == "posthog":
            is_prov_valid = bool(len(ref) > 0)

        if is_prov_valid:
            valid_provenance_count += 1

    prov_ratio = valid_provenance_count / total if total > 0 else 1.0
    return consistent, all_exist, prov_ratio, unsupported_count


def evaluate_schema_completeness(recommendation: ProductRecommendation | None) -> bool:
    """Verify structural schema completeness of candidate product recommendation."""
    if not recommendation:
        return False

    return bool(
        recommendation.problem_statement
        and recommendation.problem_statement.strip()
        and recommendation.why_it_matters
        and recommendation.why_it_matters.strip()
        and recommendation.affected_users
        and recommendation.affected_users.strip()
        and len(recommendation.factual_observations) > 0
        and len(recommendation.inferences) > 0
        and len(recommendation.hypotheses) > 0
        and recommendation.recommendation
        and recommendation.recommendation.strip()
        and len(recommendation.success_metrics) > 0
        and len(recommendation.risks) > 0
        and recommendation.confidence in {"low", "medium", "high"}
    )


def evaluate_scenario_aware_evidence_coverage(
    state: InvestigationState,
    scenario: EvaluationScenario,
) -> float:
    """Calculate evidence coverage strictly against source domains required by the scenario."""
    req_sources = set(scenario.required_sources)
    if not req_sources:
        return 1.0

    retrieved_sources = {entry.source_type for entry in state.evidence_ledger_entries.values()}
    covered = req_sources & retrieved_sources
    return len(covered) / len(req_sources)


def evaluate_deterministic_contradictions(
    recommendation: ProductRecommendation | None,
    scenario: EvaluationScenario,
) -> bool:
    """Verify that scenarios with explicit expected contradictions acknowledge them."""
    if not scenario.expected_contradictions:
        return True  # Scenarios without contradictions are never penalized

    if not recommendation:
        return False

    # Check explicit conflicting_evidence field or textual tension reconciliation
    if len(recommendation.conflicting_evidence) > 0:
        return True

    text_corpus = (
        recommendation.problem_statement
        + " "
        + " ".join(recommendation.inferences)
        + " "
        + " ".join(recommendation.factual_observations)
    ).lower()

    keywords = ["contradict", "conflict", "tension", "discrepan", "however", "despite", "divergen"]
    return any(kw in text_corpus for kw in keywords)


def evaluate_execution_integrity_and_limits(state: InvestigationState) -> tuple[bool, bool]:
    """Verify tool iteration limits and execution integrity."""
    limits_respected = True
    rev_count = getattr(state, "revision_count", getattr(state, "pm_revision_count", 0))
    if rev_count > 2:
        limits_respected = False

    errors_list = getattr(state, "tool_errors", getattr(state, "errors", []))
    integrity_valid = state.recommendation is not None and not any(
        "fatal" in str(err).lower() for err in errors_list
    )
    return limits_respected, integrity_valid


def evaluate_deterministic_metrics(
    state: InvestigationState,
    scenario: EvaluationScenario,
) -> DeterministicMetrics:
    """Run all deterministic structural and deduplicated evaluations on an investigation state."""
    rec = state.recommendation

    # 1. Structural Citations & Provenance
    validity, total_cites, valid_cites, hallucinated = evaluate_structural_citations(state, rec)
    consistent, all_exist, prov_validity, unsupp_ids = evaluate_citation_consistency_and_provenance(
        state, rec
    )

    # 2. Schema Completeness
    schema_valid = evaluate_schema_completeness(rec)

    # 3. Source Selection & Scenario-Aware Evidence Coverage
    selected_sources = map_tasks_to_sources(state)
    src_prec, src_rec, src_jaccard = evaluate_source_selection(
        selected_sources, scenario.required_sources
    )
    evidence_coverage = evaluate_scenario_aware_evidence_coverage(state, scenario)

    # 4. Retrieval Quality on Unique Records
    unique_retrieved, total_entries = extract_unique_evidence_records(state, scenario)
    ctx_recall, ctx_prec, redundancy = evaluate_retrieval_quality(
        unique_retrieved, scenario, total_entries
    )

    # 5. Contradiction & Execution Bounds
    contra_valid = evaluate_deterministic_contradictions(rec, scenario)
    limits_ok, integrity_ok = evaluate_execution_integrity_and_limits(state)

    # 6. Confidence Calibration
    conf_matched, overconf_pen = evaluate_confidence_calibration(rec, scenario)

    # 7. Epistemic Separation
    epistemic_valid = False
    if rec:
        epistemic_valid = bool(rec.factual_observations and rec.inferences and rec.recommendation)

    expected_count = (
        len(scenario.expected_support_tickets)
        + len(scenario.expected_jira_issues)
        + len(scenario.expected_analytics_observations)
    )

    return DeterministicMetrics(
        structural_citation_validity=validity,
        total_citations=total_cites,
        valid_citations=valid_cites,
        hallucinated_citations=hallucinated,
        citation_to_evidence_consistent=consistent,
        evidence_record_existence=all_exist,
        provenance_validity=prov_validity,
        unsupported_or_fabricated_ids=unsupp_ids,
        schema_validity=schema_valid,
        evidence_coverage=evidence_coverage,
        context_recall=ctx_recall,
        context_precision=ctx_prec,
        unique_retrieved_records_count=len(unique_retrieved),
        expected_records_count=expected_count,
        retrieval_redundancy_rate=redundancy,
        source_selection_precision=src_prec,
        source_selection_recall=src_rec,
        source_selection_jaccard=src_jaccard,
        selected_sources=sorted(list(selected_sources)),
        deterministic_contradiction_fidelity=contra_valid,
        tool_iteration_limits_respected=limits_ok,
        execution_integrity_valid=integrity_ok,
        epistemic_separation_valid=epistemic_valid,
        confidence_matched_expected_range=conf_matched,
        overconfidence_penalty=overconf_pen,
    )
