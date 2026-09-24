"""Integration tests for LangGraph multi-agent orchestration workflow."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.agents.ledger import EvidenceLedgerEntry
from app.agents.research import ResearchTask
from app.domain.analytics import AnalyticsQueryResult
from app.domain.critic import CriticReview
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.jira import JiraIssue
from app.domain.plan import InvestigationPlan, InvestigationTask
from app.domain.recommendation import ProductRecommendation
from app.domain.specialists import (
    AnalyticsFinding,
    CustomerFinding,
    EngineeringFinding,
    SpecialistResult,
)
from app.domain.zendesk import ZendeskTicket
from app.integrations.llm.client import LLMClient
from app.orchestration.graph import create_investigation_graph
from app.orchestration.state import (
    EvidenceAssessment,
    InvestigationState,
)


def _make_sample_ticket() -> ZendeskTicket:
    return ZendeskTicket(
        id=101,
        subject="Transfer delayed",
        description="Desc 101",
        status="open",
        priority="normal",
        channel="web",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester_id="usr_000001",
        tags=[],
    )


def _make_sample_jira() -> JiraIssue:
    return JiraIssue(
        id=10001,
        key="PAY-117",
        summary="Webhook timeout issue",
        description="Desc",
        issue_type="Bug",
        status="In Progress",
        priority="High",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        components=[],
    )


def _make_sample_analytics() -> AnalyticsQueryResult:
    return AnalyticsQueryResult(
        query_description="Transfer funnel",
        metric="conversion_rate",
        value=0.25,
        rows=[],
    )


@pytest.mark.asyncio
async def test_parallel_fan_out_and_reducer_aggregation() -> None:
    """Verify that concurrent specialist nodes aggregate into InvestigationState without clobbering."""
    mock_llm = MagicMock(spec=LLMClient)

    # 1. Mock Planner output
    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Understand why transfers fail"],
        tasks=[
            InvestigationTask(
                specialist="research", objective="Search customer tickets", priority="required"
            ),
            InvestigationTask(
                specialist="analytics", objective="Analyze failure funnels", priority="required"
            ),
            InvestigationTask(
                specialist="engineering", objective="Inspect timeout issues", priority="required"
            ),
        ],
        required_sources=["zendesk", "posthog", "jira"],
        success_condition="Evidence gathered from all three domains",
    )

    # 2. Mock Assessment output (sufficient, no follow-up)
    assessment = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
        identified_gaps=[],
    )

    # Configure mock LLM structured returns (plan, assessment, pm_recommendation, critic_review)
    rec_evidence = Evidence(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer complains of transfer delay",
        support="Ticket 101",
        confidence=EvidenceConfidence.HIGH,
    )
    pm_rec = ProductRecommendation(
        problem_statement="Customers experience transaction delays during peak hours.",
        why_it_matters="Degrades user trust and increases support ticket burden.",
        affected_users="Mobile wallet transfer users",
        factual_observations=["Customer complains of transfer delay in Ticket 101"],
        inferences=["Users experience transaction latency spikes"],
        hypotheses=["Client-side polling fallback would alleviate confusion"],
        evidence=[rec_evidence],
        recommendation="Implement client-side polling fallback.",
        recommendation_type="prioritise",
        risks=["Increased server polling traffic"],
        success_metrics=["Transfer tickets drop by 50%"],
        confidence="high",
    )
    critic_pass = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="All claims are verified and grounded in authoritative ledger evidence.",
        required_changes=[],
    )
    mock_llm.complete_structured = AsyncMock(side_effect=[plan, assessment, pm_rec, critic_pass])

    # 3. Setup Mock Specialists returning grounded evidence
    now = datetime.now(UTC)

    # Research
    research_agent = MagicMock()
    research_agent.tool_call_count = 3
    research_agent.llm_call_count = 4
    research_entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Customer ticket",
        typed_payload=_make_sample_ticket(),
    )
    research_agent.ledger.entries = [research_entry]
    research_finding = CustomerFinding(
        finding="Customer complains of transfer delay",
        facts=["Ticket 101 filed"],
        interpretations=["Customers experience delays"],
        evidence=[
            Evidence(
                ledger_entry_id="research:r0:led_001",
                source_type="zendesk",
                source_reference="ticket_id:101",
                finding="Customer complains",
                support="Ticket 101",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay",
    )
    research_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="research",
            findings=[research_finding],
            overall_facts=["Fact 1"],
            overall_interpretations=["Interp 1"],
            tool_call_count=3,
            llm_call_count=4,
            investigation_complete=True,
        )
    )

    # Analytics
    analytics_agent = MagicMock()
    analytics_agent.tool_call_count = 2
    analytics_agent.llm_call_count = 3
    analytics_entry = EvidenceLedgerEntry(
        ledger_entry_id="analytics:r0:led_001",
        source_type="posthog",
        source_reference="query:funnel",
        retrieved_at=now,
        data_summary="Funnel metrics",
        typed_payload=_make_sample_analytics(),
    )
    analytics_agent.ledger.entries = [analytics_entry]
    analytics_finding = AnalyticsFinding(
        finding="Funnel drop-off 75%",
        facts=["25% conversion observed"],
        interpretations=["High drop-off"],
        evidence=[
            Evidence(
                ledger_entry_id="analytics:r0:led_001",
                source_type="posthog",
                source_reference="query:funnel",
                finding="Funnel drop-off",
                support="25% conversion",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
        metric="funnel_conversion",
        value="25%",
    )
    analytics_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="analytics",
            findings=[analytics_finding],
            overall_facts=["Fact 2"],
            overall_interpretations=["Interp 2"],
            tool_call_count=2,
            llm_call_count=3,
            investigation_complete=True,
        )
    )

    # Engineering
    engineering_agent = MagicMock()
    engineering_agent.tool_call_count = 3
    engineering_agent.llm_call_count = 4
    engineering_entry = EvidenceLedgerEntry(
        ledger_entry_id="engineering:r0:led_001",
        source_type="jira",
        source_reference="issue_key:PAY-117",
        retrieved_at=now,
        data_summary="Bug report",
        typed_payload=_make_sample_jira(),
    )
    engineering_agent.ledger.entries = [engineering_entry]
    engineering_finding = EngineeringFinding(
        finding="Active bug PAY-117 in progress",
        facts=["PAY-117 active"],
        interpretations=["Technical timeout root cause"],
        evidence=[
            Evidence(
                ledger_entry_id="engineering:r0:led_001",
                source_type="jira",
                source_reference="issue_key:PAY-117",
                finding="Active bug",
                support="PAY-117 in progress",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
        issue_status="In Progress",
        technical_context="Webhook timeout in core banking gateway",
        relationship_to_problem="Directly causes transactions to remain in pending state",
    )
    engineering_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="engineering",
            findings=[engineering_finding],
            overall_facts=["Fact 3"],
            overall_interpretations=["Interp 3"],
            tool_call_count=3,
            llm_call_count=4,
            investigation_complete=True,
        )
    )

    # Assemble graph
    graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )

    initial_state = InvestigationState(
        investigation_id="inv_test_e2e",
        user_query="Why are transfers failing?",
    )

    final_dict = await graph.ainvoke(initial_state)
    final_state = InvestigationState.model_validate(final_dict)

    # 4. Assertions: all three branches merged without clobbering
    assert len(final_state.customer_findings) == 1
    assert len(final_state.analytics_findings) == 1
    assert len(final_state.engineering_findings) == 1

    assert len(final_state.evidence_ledger_entries) == 3
    assert "research:r0:led_001" in final_state.evidence_ledger_entries
    assert "analytics:r0:led_001" in final_state.evidence_ledger_entries
    assert "engineering:r0:led_001" in final_state.evidence_ledger_entries

    assert final_state.status == "completed"
    assert final_state.sufficient_for_synthesis is True

    # Budget ceiling checks
    assert final_state.budget_usage.total_tool_calls <= 26
    assert final_state.budget_usage.total_llm_calls <= 45


@pytest.mark.asyncio
async def test_parallel_failure_isolation_engineering_crash() -> None:
    """Verify that if Engineering crashes, Research and Analytics evidence survives and status is 'partial'."""
    mock_llm = MagicMock(spec=LLMClient)

    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Investigate transfer delay"],
        tasks=[
            InvestigationTask(
                specialist="research", objective="Search customer tickets", priority="required"
            ),
            InvestigationTask(
                specialist="analytics", objective="Analyze metrics", priority="required"
            ),
            InvestigationTask(
                specialist="engineering", objective="Inspect bugs", priority="required"
            ),
        ],
        required_sources=["zendesk", "posthog", "jira"],
        success_condition="Evidence from all sources",
    )

    assessment = EvidenceAssessment(
        sufficient_for_synthesis=False,
        has_blocking_gaps=True,
        identified_gaps=["Engineering technical context is missing due to system failure"],
    )

    mock_llm.complete_structured = AsyncMock(side_effect=[plan, assessment])

    now = datetime.now(UTC)

    # Research succeeds
    research_agent = MagicMock()
    research_agent.tool_call_count = 2
    research_agent.llm_call_count = 3
    research_entry = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Customer ticket",
        typed_payload=_make_sample_ticket(),
    )
    research_agent.ledger.entries = [research_entry]
    research_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="research",
            findings=[
                CustomerFinding(
                    finding="Customer complains",
                    facts=["Fact 1"],
                    interpretations=["Interp 1"],
                    evidence=[
                        Evidence(
                            ledger_entry_id="research:r0:led_001",
                            source_type="zendesk",
                            source_reference="ticket_id:101",
                            finding="Customer complains",
                            support="Ticket 101",
                            confidence=EvidenceConfidence.HIGH,
                        )
                    ],
                    confidence=EvidenceConfidence.HIGH,
                    observed_pattern="transfer_delay",
                )
            ],
            overall_facts=["Fact 1"],
            overall_interpretations=["Interp 1"],
            tool_call_count=2,
            llm_call_count=3,
            investigation_complete=True,
        )
    )

    # Analytics succeeds
    analytics_agent = MagicMock()
    analytics_agent.tool_call_count = 2
    analytics_agent.llm_call_count = 3
    analytics_entry = EvidenceLedgerEntry(
        ledger_entry_id="analytics:r0:led_001",
        source_type="posthog",
        source_reference="query:funnel",
        retrieved_at=now,
        data_summary="Funnel metrics",
        typed_payload=_make_sample_analytics(),
    )
    analytics_agent.ledger.entries = [analytics_entry]
    analytics_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="analytics",
            findings=[
                AnalyticsFinding(
                    finding="Funnel drop-off",
                    facts=["Fact 2"],
                    interpretations=["Interp 2"],
                    evidence=[
                        Evidence(
                            ledger_entry_id="analytics:r0:led_001",
                            source_type="posthog",
                            source_reference="query:funnel",
                            finding="Funnel drop-off",
                            support="25% conversion",
                            confidence=EvidenceConfidence.HIGH,
                        )
                    ],
                    confidence=EvidenceConfidence.HIGH,
                    metric="funnel_conversion",
                    value="25%",
                )
            ],
            overall_facts=["Fact 2"],
            overall_interpretations=["Interp 2"],
            tool_call_count=2,
            llm_call_count=3,
            investigation_complete=True,
        )
    )

    # Engineering FAILS / CRASHES
    engineering_agent = MagicMock()
    engineering_agent.tool_call_count = 1
    engineering_agent.llm_call_count = 1
    engineering_agent.ledger.entries = []
    engineering_agent.execute = AsyncMock(
        side_effect=RuntimeError("Jira MockServer connection timed out")
    )

    graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )

    initial_state = InvestigationState(
        investigation_id="inv_test_failure_isolation",
        user_query="Why are transfers failing?",
    )

    final_dict = await graph.ainvoke(initial_state)
    final_state = InvestigationState.model_validate(final_dict)

    # Provenance and evidence assertions:
    # 1. Research and Analytics findings survived intact
    assert len(final_state.customer_findings) == 1
    assert len(final_state.analytics_findings) == 1
    # 2. Zero fabricated Engineering evidence appears
    assert len(final_state.engineering_findings) == 0
    # 3. Engineering failure became structured state error & limitation
    assert len(final_state.tool_errors) == 1
    assert final_state.tool_errors[0].error_type == "upstream_error"
    assert "Jira MockServer connection timed out" in final_state.tool_errors[0].message
    assert any("Engineering specialist crashed" in lim for lim in final_state.limitations)
    # 4. Graph terminates as partial with sufficient_for_synthesis=False
    assert final_state.status == "partial"
    assert final_state.sufficient_for_synthesis is False


@pytest.mark.asyncio
async def test_targeted_follow_up_round_and_cumulative_budget_enforcement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that a single targeted follow-up round executes with remaining budget and terminates."""
    monkeypatch.setattr(
        "app.orchestration.nodes.assessment.get_settings",
        lambda: MagicMock(investigation_profile="deep"),
    )
    mock_llm = MagicMock(spec=LLMClient)

    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Investigate why transfers fail"],
        tasks=[
            InvestigationTask(
                specialist="research", objective="Search customer tickets", priority="required"
            ),
            InvestigationTask(
                specialist="analytics", objective="Analyze failure funnels", priority="required"
            ),
            InvestigationTask(
                specialist="engineering", objective="Inspect timeout issues", priority="required"
            ),
        ],
        required_sources=["zendesk", "posthog", "jira"],
        success_condition="Evidence gathered from all three domains",
    )

    # First assessment identifies a gap in research and recommends follow-up
    assessment_round_0 = EvidenceAssessment(
        sufficient_for_synthesis=False,
        has_blocking_gaps=True,
        identified_gaps=["Customer switch timeout details missing from ticket samples"],
        recommended_specialist="research",
        recommended_gap="Customer switch timeout details missing from ticket samples",
        recommended_objective="Search for tickets mentioning core banking switch timeouts",
        recommended_questions=["Are there comments mentioning switch timeouts?"],
    )

    # Second assessment after follow-up concludes investigation is complete
    assessment_round_1 = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
        identified_gaps=[],
    )

    rec_evidence_3 = Evidence(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer complains of transfer delay",
        support="Ticket 101",
        confidence=EvidenceConfidence.HIGH,
    )
    pm_rec_3 = ProductRecommendation(
        problem_statement="Customers experience transaction delays during peak hours.",
        why_it_matters="Degrades user trust and increases support ticket burden.",
        affected_users="Mobile wallet transfer users",
        factual_observations=["Customer complains of transfer delay in Ticket 101"],
        inferences=["Users experience transaction latency spikes"],
        hypotheses=["Client-side polling fallback would alleviate confusion"],
        evidence=[rec_evidence_3],
        recommendation="Implement client-side polling fallback.",
        recommendation_type="prioritise",
        risks=["Increased server polling traffic"],
        success_metrics=["Transfer tickets drop by 50%"],
        confidence="high",
    )
    critic_pass_3 = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="All claims are verified and grounded in authoritative ledger evidence.",
        required_changes=[],
    )

    mock_llm.complete_structured = AsyncMock(
        side_effect=[plan, assessment_round_0, assessment_round_1, pm_rec_3, critic_pass_3]
    )

    now = datetime.now(UTC)

    # Setup Research agent with initial result and follow-up result
    research_agent = MagicMock()
    research_agent.tool_call_count = 3
    research_agent.llm_call_count = 4

    entry_initial = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Customer ticket",
        typed_payload=_make_sample_ticket(),
    )
    entry_followup = EvidenceLedgerEntry(
        ledger_entry_id="research:r1:led_001",
        source_type="zendesk",
        source_reference="ticket_id:102",
        retrieved_at=now,
        data_summary="Follow-up ticket",
        typed_payload=_make_sample_ticket(),
    )
    research_agent.ledger.entries = [entry_initial]

    finding_initial = CustomerFinding(
        finding="Customer complains of transfer delay",
        facts=["Ticket 101 filed"],
        interpretations=["Customers experience delays"],
        evidence=[
            Evidence(
                ledger_entry_id="research:r0:led_001",
                source_type="zendesk",
                source_reference="ticket_id:101",
                finding="Customer complains",
                support="Ticket 101",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="transfer_delay",
    )
    finding_followup = CustomerFinding(
        finding="Switch timeouts confirmed in customer support comments",
        facts=["Ticket 102 confirms switch timeout"],
        interpretations=["Switch timeouts confirmed"],
        evidence=[
            Evidence(
                ledger_entry_id="research:r1:led_001",
                source_type="zendesk",
                source_reference="ticket_id:102",
                finding="Switch timeout confirmed",
                support="Ticket 102",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="switch_timeout",
    )

    # First execute call (round 0), second execute call (follow-up round 1)
    res_initial = SpecialistResult(
        agent_role="research",
        findings=[finding_initial],
        overall_facts=["Fact 1"],
        overall_interpretations=["Interp 1"],
        tool_call_count=3,
        llm_call_count=4,
        investigation_complete=True,
    )
    res_followup = SpecialistResult(
        agent_role="research",
        findings=[finding_followup],
        overall_facts=["Fact 2"],
        overall_interpretations=["Interp 2"],
        tool_call_count=2,
        llm_call_count=2,
        investigation_complete=True,
    )

    async def _mock_research_execute(
        task: ResearchTask,
        *,
        round_index: int | None = None,
        tool_budget_override: int | None = None,
        llm_budget_override: int | None = None,
    ) -> SpecialistResult[CustomerFinding]:
        if research_agent.execute.call_count == 1:
            research_agent.ledger.entries = [entry_initial]
            return res_initial
        else:
            research_agent.ledger.entries = [entry_followup]
            return res_followup

    research_agent.execute = AsyncMock(side_effect=_mock_research_execute)

    # Analytics agent
    analytics_agent = MagicMock()
    analytics_agent.tool_call_count = 2
    analytics_agent.llm_call_count = 3
    analytics_entry = EvidenceLedgerEntry(
        ledger_entry_id="analytics:r0:led_001",
        source_type="posthog",
        source_reference="query:funnel",
        retrieved_at=now,
        data_summary="Funnel metrics",
        typed_payload=_make_sample_analytics(),
    )
    analytics_agent.ledger.entries = [analytics_entry]
    analytics_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="analytics",
            findings=[
                AnalyticsFinding(
                    finding="Funnel drop-off",
                    facts=["Fact 2"],
                    interpretations=["Interp 2"],
                    evidence=[
                        Evidence(
                            ledger_entry_id="analytics:r0:led_001",
                            source_type="posthog",
                            source_reference="query:funnel",
                            finding="Funnel drop-off",
                            support="25% conversion",
                            confidence=EvidenceConfidence.HIGH,
                        )
                    ],
                    confidence=EvidenceConfidence.HIGH,
                    metric="funnel_conversion",
                    value="25%",
                )
            ],
            overall_facts=["Fact 2"],
            overall_interpretations=["Interp 2"],
            tool_call_count=2,
            llm_call_count=3,
            investigation_complete=True,
        )
    )

    # Engineering agent
    engineering_agent = MagicMock()
    engineering_agent.tool_call_count = 3
    engineering_agent.llm_call_count = 4
    engineering_entry = EvidenceLedgerEntry(
        ledger_entry_id="engineering:r0:led_001",
        source_type="jira",
        source_reference="issue_key:PAY-117",
        retrieved_at=now,
        data_summary="Bug report",
        typed_payload=_make_sample_jira(),
    )
    engineering_agent.ledger.entries = [engineering_entry]
    engineering_agent.execute = AsyncMock(
        return_value=SpecialistResult(
            agent_role="engineering",
            findings=[
                EngineeringFinding(
                    finding="Active bug PAY-117 in progress",
                    facts=["PAY-117 active"],
                    interpretations=["Technical timeout root cause"],
                    evidence=[
                        Evidence(
                            ledger_entry_id="engineering:r0:led_001",
                            source_type="jira",
                            source_reference="issue_key:PAY-117",
                            finding="Active bug",
                            support="PAY-117 in progress",
                            confidence=EvidenceConfidence.HIGH,
                        )
                    ],
                    confidence=EvidenceConfidence.HIGH,
                    issue_status="In Progress",
                    technical_context="Webhook timeout mechanism",
                    relationship_to_problem="Directly causes delay",
                )
            ],
            overall_facts=["Fact 3"],
            overall_interpretations=["Interp 3"],
            tool_call_count=3,
            llm_call_count=4,
            investigation_complete=True,
        )
    )

    graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )

    initial_state = InvestigationState(
        investigation_id="inv_test_follow_up",
        user_query="Why are transfers failing?",
    )

    final_dict = await graph.ainvoke(initial_state)
    final_state = InvestigationState.model_validate(final_dict)

    # Assertions on follow-up execution:
    # 1. Research execute called twice (initial + follow-up)
    assert research_agent.execute.call_count == 2
    # Verify remaining budget was injected into follow-up:
    # Initial research used 3 tools and 4 LLM calls -> remaining = 10 - 3 = 7 tools, 15 - 4 = 11 LLM
    second_call_kwargs = research_agent.execute.call_args_list[1].kwargs
    assert second_call_kwargs["tool_budget_override"] == 7
    assert second_call_kwargs["llm_budget_override"] == 11

    # 2. Evidence accumulated from both initial and follow-up
    assert len(final_state.customer_findings) == 2
    assert "research:r0:led_001" in final_state.evidence_ledger_entries
    assert "research:r1:led_001" in final_state.evidence_ledger_entries

    # 3. Round index advanced to 1 and graph terminated as completed
    assert final_state.round_index == 1
    assert final_state.status == "completed"
    assert final_state.sufficient_for_synthesis is True

    # 4. Total graph ceilings respected
    assert final_state.budget_usage.total_tool_calls <= 26
    assert final_state.budget_usage.total_llm_calls <= 45


@pytest.mark.asyncio
async def test_same_specialist_follow_up_round_preserves_both_evidence_sets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that same specialist executing in Round 0 and Round 1:

    1. Research runs in Round 0 and produces at least one evidence entry (research:r0:led_001).
    2. Assessment requests a valid Research follow-up.
    3. Research runs again in Round 1 and produces another evidence entry (research:r1:led_001).
    4. Both Round 0 and Round 1 evidence remain present in the final state.
    5. Every ledger ID is unique across rounds.
    6. No Round 0 evidence is overwritten.
    7. Evidence references still resolve to exactly one ledger entry.
    8. validate_investigation_evidence succeeds without provenance violation.
    """
    from app.orchestration.validation import validate_investigation_evidence

    monkeypatch.setattr(
        "app.orchestration.nodes.assessment.get_settings",
        lambda: MagicMock(investigation_profile="deep"),
    )
    mock_llm = MagicMock(spec=LLMClient)

    plan = InvestigationPlan(
        question_type="diagnostic",
        objectives=["Investigate transaction status uncertainty"],
        tasks=[
            InvestigationTask(
                specialist="research",
                objective="Search customer tickets on pending transfers",
                priority="required",
            ),
        ],
        required_sources=["zendesk"],
        success_condition="Evidence gathered from Zendesk",
    )

    assessment_round_0 = EvidenceAssessment(
        sufficient_for_synthesis=False,
        has_blocking_gaps=True,
        identified_gaps=["Need clarification on whether users receive timeout error banner"],
        recommended_specialist="research",
        recommended_gap="Need clarification on whether users receive timeout error banner",
        recommended_objective="Search for tickets mentioning timeout error banners",
        recommended_questions=["Do customers see error banner or spinner?"],
    )

    assessment_round_1 = EvidenceAssessment(
        sufficient_for_synthesis=True,
        has_blocking_gaps=False,
        identified_gaps=[],
    )

    rec_evidence_4 = Evidence(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer complains of transfer delay",
        support="Ticket 101",
        confidence=EvidenceConfidence.HIGH,
    )
    pm_rec_4 = ProductRecommendation(
        problem_statement="Customers experience transaction delays during peak hours.",
        why_it_matters="Degrades user trust and increases support ticket burden.",
        affected_users="Mobile wallet transfer users",
        factual_observations=["Customer complains of transfer delay in Ticket 101"],
        inferences=["Users experience transaction latency spikes"],
        hypotheses=["Client-side polling fallback would alleviate confusion"],
        evidence=[rec_evidence_4],
        recommendation="Implement client-side polling fallback.",
        recommendation_type="prioritise",
        risks=["Increased server polling traffic"],
        success_metrics=["Transfer tickets drop by 50%"],
        confidence="high",
    )
    critic_pass_4 = CriticReview(
        decision="PASS",
        issues=[],
        overall_assessment="All claims are verified and grounded in authoritative ledger evidence.",
        required_changes=[],
    )

    mock_llm.complete_structured = AsyncMock(
        side_effect=[plan, assessment_round_0, assessment_round_1, pm_rec_4, critic_pass_4]
    )

    now = datetime.now(UTC)

    # Setup Research agent simulating round-scoped execution
    research_agent = MagicMock()
    research_agent.tool_call_count = 2
    research_agent.llm_call_count = 2

    entry_r0 = EvidenceLedgerEntry(
        ledger_entry_id="research:r0:led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        retrieved_at=now,
        data_summary="Customer ticket 101: transfer pending spinner",
        typed_payload=_make_sample_ticket(),
    )
    entry_r1 = EvidenceLedgerEntry(
        ledger_entry_id="research:r1:led_001",
        source_type="zendesk",
        source_reference="ticket_id:102",
        retrieved_at=now,
        data_summary="Customer ticket 102: timeout banner confirmed",
        typed_payload=_make_sample_ticket(),
    )

    finding_r0 = CustomerFinding(
        finding="Customers observe infinite spinner on pending transfer",
        facts=["Ticket 101 mentions indefinite loading spinner"],
        interpretations=["Customers experience uncertainty"],
        evidence=[
            Evidence(
                ledger_entry_id="research:r0:led_001",
                source_type="zendesk",
                source_reference="ticket_id:101",
                finding="Indefinite loading spinner observed",
                support="Ticket 101 description",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="pending_spinner",
    )

    finding_r1 = CustomerFinding(
        finding="Customers see gateway timeout banner after 60s",
        facts=["Ticket 102 confirms timeout error banner after 60 seconds"],
        interpretations=["Timeout notification delayed"],
        evidence=[
            Evidence(
                ledger_entry_id="research:r1:led_001",
                source_type="zendesk",
                source_reference="ticket_id:102",
                finding="Gateway timeout banner appears after 60s",
                support="Ticket 102 customer note",
                confidence=EvidenceConfidence.HIGH,
            )
        ],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delayed_banner",
    )

    res_r0 = SpecialistResult(
        agent_role="research",
        findings=[finding_r0],
        overall_facts=["Fact R0"],
        overall_interpretations=["Interp R0"],
        tool_call_count=2,
        llm_call_count=2,
        investigation_complete=True,
    )
    res_r1 = SpecialistResult(
        agent_role="research",
        findings=[finding_r1],
        overall_facts=["Fact R1"],
        overall_interpretations=["Interp R1"],
        tool_call_count=2,
        llm_call_count=2,
        investigation_complete=True,
    )

    async def _mock_research_execute_lifecycle(
        task: ResearchTask,
        *,
        round_index: int | None = None,
        tool_budget_override: int | None = None,
        llm_budget_override: int | None = None,
    ) -> SpecialistResult[CustomerFinding]:
        # Round 0 execute
        if research_agent.execute.call_count == 1:
            research_agent.ledger.entries = [entry_r0]
            return res_r0
        # Round 1 follow-up execute
        else:
            research_agent.ledger.entries = [entry_r1]
            return res_r1

    research_agent.execute = AsyncMock(side_effect=_mock_research_execute_lifecycle)

    analytics_agent = MagicMock()
    analytics_agent.tool_call_count = 0
    analytics_agent.llm_call_count = 0
    analytics_agent.ledger.entries = []

    engineering_agent = MagicMock()
    engineering_agent.tool_call_count = 0
    engineering_agent.llm_call_count = 0
    engineering_agent.ledger.entries = []

    graph = create_investigation_graph(
        llm_client=mock_llm,
        research_agent=research_agent,
        analytics_agent=analytics_agent,
        engineering_agent=engineering_agent,
    )

    initial_state = InvestigationState(
        investigation_id="inv_test_same_specialist_rounds",
        user_query="Why are customers reporting pending transfer issues?",
    )

    final_dict = await graph.ainvoke(initial_state)
    final_state = InvestigationState.model_validate(final_dict)

    # 1. Research ran twice (Round 0 + Round 1)
    assert research_agent.execute.call_count == 2

    # 2. Both Round 0 and Round 1 evidence remain present in the final state
    assert "research:r0:led_001" in final_state.evidence_ledger_entries
    assert "research:r1:led_001" in final_state.evidence_ledger_entries
    assert len(final_state.evidence_ledger_entries) == 2

    # 3. No Round 0 evidence was overwritten
    assert (
        final_state.evidence_ledger_entries["research:r0:led_001"].data_summary
        == "Customer ticket 101: transfer pending spinner"
    )
    assert (
        final_state.evidence_ledger_entries["research:r1:led_001"].data_summary
        == "Customer ticket 102: timeout banner confirmed"
    )

    # 4. Both findings are preserved in state
    assert len(final_state.customer_findings) == 2
    assert final_state.customer_findings[0].observed_pattern == "pending_spinner"
    assert final_state.customer_findings[1].observed_pattern == "delayed_banner"

    # 5. Every ledger entry ID is unique
    ledger_ids = list(final_state.evidence_ledger_entries.keys())
    assert len(ledger_ids) == len(set(ledger_ids))

    # 6. Evidence references resolve to exactly one ledger entry and pass provenance validation
    validate_investigation_evidence(final_state)

    # 7. Final status is completed
    assert final_state.round_index == 1
    assert final_state.status == "completed"
    assert final_state.sufficient_for_synthesis is True
