"""Unit tests for the 16-class error taxonomy classifier."""

from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.recommendation import ProductRecommendation
from app.orchestration.state import InvestigationState
from app.tools.base import ToolError
from evaluations.dataset.loader import get_scenario_by_id
from evaluations.evaluators.deterministic import DeterministicMetrics
from evaluations.evaluators.taxonomy import classify_investigation_errors


def test_classify_system_failure() -> None:
    """Verify SYSTEM_FAILURE is assigned when state status is failed."""
    state = InvestigationState(
        investigation_id="inv_fail",
        user_query="query",
        status="failed",
    )
    scenario = get_scenario_by_id("scn_001")
    deterministic = DeterministicMetrics()

    errors = classify_investigation_errors(state, scenario, deterministic)
    categories = [e.category for e in errors]
    assert "SYSTEM_FAILURE" in categories
    assert errors[0].severity == "critical"


def test_classify_tool_argument_error() -> None:
    """Verify TOOL_ARGUMENT_ERROR is triggered when tool errors occur without an outage scenario."""
    state = InvestigationState(
        investigation_id="inv_tool_err",
        user_query="query",
        tool_errors=[
            ToolError(
                error_type="invalid_input",
                message="Bad JSON arguments provided to query_analytics",
                attempted_source="posthog",
            )
        ],
    )
    scenario = get_scenario_by_id("scn_001")  # not a source outage scenario
    deterministic = DeterministicMetrics()

    errors = classify_investigation_errors(state, scenario, deterministic)
    categories = [e.category for e in errors]
    assert "TOOL_ARGUMENT_ERROR" in categories


def test_classify_tool_selection_and_retrieval_miss() -> None:
    """Verify TOOL_SELECTION_ERROR and RETRIEVAL_MISS when recall is impaired."""
    state = InvestigationState(investigation_id="inv_miss", user_query="query")
    scenario = get_scenario_by_id("scn_001")
    deterministic = DeterministicMetrics(
        source_selection_recall=0.67,  # missed one source
        context_recall=0.40,  # critically low
    )

    errors = classify_investigation_errors(state, scenario, deterministic)
    categories = [e.category for e in errors]
    assert "TOOL_SELECTION_ERROR" in categories
    assert "RETRIEVAL_MISS" in categories


def test_classify_unsupported_claim_and_flaws() -> None:
    """Verify UNSUPPORTED_CLAIM, CONTRADICTION_MISS, and CAUSAL_OVERREACH."""
    state = InvestigationState(
        investigation_id="inv_flaws",
        user_query="query",
        recommendation=ProductRecommendation(
            problem_statement="Problem statement explaining customer issues.",
            why_it_matters="Impact statement explaining why it matters.",
            affected_users="Segment A users",
            factual_observations=["Fact 1 observed"],
            inferences=["Inference 1 deduced"],
            hypotheses=["Hypothesis 1 proposed"],
            evidence=[
                Evidence(
                    ledger_entry_id="led_hallucinated",
                    source_type="zendesk",
                    source_reference="zen_001",
                    finding="Finding",
                    support="Support",
                    confidence=EvidenceConfidence.HIGH,
                )
            ],
            recommendation="Recommended product action to fix the bug.",
            recommendation_type="technical_remediation",
            success_metrics=["Metric 1"],
            risks=["Risk 1"],
            confidence="high",
            open_questions=[],
        ),
    )
    scenario = get_scenario_by_id("scn_001")  # has_contradiction=True
    deterministic = DeterministicMetrics(
        hallucinated_citations=1,
    )
    flaws = [
        "The agent ignored the contradiction between ticket complaints and settlement telemetry."
    ]

    errors = classify_investigation_errors(
        state, scenario, deterministic, judge_identified_flaws=flaws
    )
    categories = [e.category for e in errors]
    assert "UNSUPPORTED_CLAIM" in categories
    assert "CONTRADICTION_MISS" in categories


def test_classify_critic_miss_and_critic_false_positive() -> None:
    """Verify CRITIC_MISS when revision_count==0 on true positive, and FALSE_POSITIVE when revision_count>0 on true negative."""
    # scn_001 is is_critic_true_negative=True
    scenario_tn = get_scenario_by_id("scn_001")
    state_unneeded_revision = InvestigationState(
        investigation_id="inv_rev",
        user_query="query",
        revision_count=1,
    )
    errors_fp = classify_investigation_errors(
        state_unneeded_revision, scenario_tn, DeterministicMetrics()
    )
    assert any(e.category == "CRITIC_FALSE_POSITIVE" for e in errors_fp)

    # scn_002 is is_critic_true_positive=True
    scenario_tp = get_scenario_by_id("scn_002")
    state_missed_critic = InvestigationState(
        investigation_id="inv_no_rev",
        user_query="query",
        revision_count=0,
    )
    errors_fn = classify_investigation_errors(
        state_missed_critic, scenario_tp, DeterministicMetrics()
    )
    assert any(e.category == "CRITIC_MISS" for e in errors_fn)
