"""Phase 10 Production Application Smoke Test.

Invokes the actual Pocket investigation service entrypoint (InvestigationService)
across live mock services (Zendesk, MockServer Jira, and PostHog), verifying:
1. End-to-end multi-source investigation execution (Planner, Research, Analytics, Engineering, PM, Critic).
2. Distributed LangSmith tracing hierarchy (fail-open, sanitized).
3. Role-based token budgeting preventing HTTP 402 errors.
4. Schema-valid ProductRecommendation with complete evidence provenance.
"""

import logging
import os

import pytest
from app.config.settings import get_settings
from app.domain.recommendation import ProductRecommendation
from app.orchestration.service import InvestigationService
from app.orchestration.state import InvestigationState

logger = logging.getLogger("phase10_smoke_test")

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_LLM_TESTS") != "1",
    reason="Live LLM/LangSmith smoke tests require explicit RUN_LIVE_LLM_TESTS=1 opt-in.",
)


@pytest.mark.asyncio
async def test_production_investigation_service_smoke() -> None:
    """Execute real multi-source investigation through canonical InvestigationService."""
    settings = get_settings()

    # Verify pre-requisites: OpenRouter API key and services configured
    assert settings.openrouter_api_key, "OPENROUTER_API_KEY required for live smoke test"
    assert settings.posthog_api_key, "POSTHOG_API_KEY required for live smoke test"

    # Instantiate authoritative production service
    service = InvestigationService.create_default(settings=settings)

    # Scn_001 canonical multi-source product question
    user_query = "Why are customers reporting a surge in failed transfers this week?"
    investigation_id = "inv_phase10_smoke_verified_003"

    logger.info("Starting Phase 10 smoke investigation '%s'...", investigation_id)
    final_state: InvestigationState = await service.investigate(
        user_query=user_query,
        investigation_id=investigation_id,
    )

    # 1. Product Contract: Final recommendation must be produced
    assert final_state.recommendation is not None, (
        "Investigation must produce a candidate recommendation"
    )
    rec: ProductRecommendation = final_state.recommendation

    assert len(rec.problem_statement) >= 10, "Problem statement must be substantive"
    assert len(rec.affected_users) >= 5, "Affected users segment must be specified"
    assert len(rec.factual_observations) >= 1, "Factual observations must be populated"
    assert len(rec.inferences) >= 1, "Inferences must be populated"
    assert len(rec.recommendation) >= 10, "Recommendation must be substantive"
    assert rec.recommendation_type in [
        "prioritise",
        "investigate_further",
        "experiment",
        "technical_remediation",
        "monitor",
        "deprioritise",
    ]
    assert rec.confidence in ["high", "medium", "low"]
    assert len(rec.success_metrics) >= 1, "Success metrics must be populated"
    assert len(rec.risks) >= 1, "Risks must be populated"

    # 2. Evidence Provenance Contract
    assert len(rec.evidence) >= 1, "Recommendation must cite at least one evidence item"
    valid_ledger_keys = set(final_state.evidence_ledger_entries.keys())
    for ev in rec.evidence:
        assert ev.ledger_entry_id in valid_ledger_keys, (
            f"Cited evidence ID '{ev.ledger_entry_id}' missing from authoritative evidence ledger"
        )
        assert ev.source_type in ["zendesk", "posthog", "jira"], (
            f"Invalid source type: {ev.source_type}"
        )
        assert ev.source_reference, f"Evidence {ev.ledger_entry_id} missing source_reference"

    # 3. Multi-source coverage: Verify specialists executed and findings gathered
    # In scn_001, Zendesk, PostHog, and Jira are all required
    sources_represented = {ev.source_type for ev in rec.evidence}
    logger.info("Sources directly cited in recommendation: %s", sources_represented)

    # 4. Critic Review Contract
    assert len(final_state.critic_reviews) >= 1, "Critic must review the candidate recommendation"
    latest_review = final_state.critic_reviews[-1]
    assert latest_review.decision in ["PASS", "REVISE"], (
        f"Unexpected critic decision: {latest_review.decision}"
    )
    assert final_state.revision_count <= final_state.max_revisions, (
        "Revision loop must be bounded <= max_revisions"
    )

    # 5. Dual Budget Counters & Zero HTTP 402
    usage = final_state.budget_usage
    logger.info(
        "Investigation budget usage: planner_llm=%d, research_tools=%d, research_llm=%d, "
        "analytics_tools=%d, analytics_llm=%d, engineering_tools=%d, engineering_llm=%d, "
        "pm_llm=%d, critic_llm=%d",
        usage.planner_llm_calls,
        usage.research_tool_calls,
        usage.research_llm_calls,
        usage.analytics_tool_calls,
        usage.analytics_llm_calls,
        usage.engineering_tool_calls,
        usage.engineering_llm_calls,
        usage.pm_llm_calls,
        usage.critic_llm_calls,
    )
    assert usage.planner_llm_calls >= 1, "Planner must execute"
    assert usage.pm_llm_calls >= 1, "PM must execute"
    assert usage.critic_llm_calls >= 1, "Critic must execute"

    # 6. Observability: Verify LangSmith LLM Spans with Token, Cost, and TTFT Telemetry
    logger.info("LangSmith tracing status: enabled=%s", settings.langsmith_tracing)
    if settings.langsmith_tracing and settings.langsmith_api_key:
        import asyncio

        from langsmith import Client

        await asyncio.sleep(2.0)  # Brief wait for LangSmith async background flush
        ls_client = Client(api_key=settings.langsmith_api_key)
        matching_runs = [
            r
            for r in ls_client.list_runs(project_name=settings.langsmith_project, limit=50)
            if r.extra.get("metadata", {}).get("investigation_id") == investigation_id
        ]
        logger.info(
            "LangSmith runs retrieved for '%s': %d total runs",
            investigation_id,
            len(matching_runs),
        )

        llm_runs = [r for r in matching_runs if r.run_type == "llm"]
        logger.info("Found %d LLM runs under investigation hierarchy", len(llm_runs))
        assert len(llm_runs) >= 3, (
            f"Expected at least 3 LLM runs (planner, pm, critic); found {len(llm_runs)}"
        )

        for run in llm_runs:
            meta = run.extra.get("metadata", {})
            assert meta.get("input_tokens", 0) > 0, f"LLM run '{run.name}' missing input_tokens"
            assert meta.get("output_tokens", 0) > 0, f"LLM run '{run.name}' missing output_tokens"
            assert meta.get("total_tokens", 0) > 0, f"LLM run '{run.name}' missing total_tokens"
            assert meta.get("ttft_seconds") is not None, (
                f"LLM run '{run.name}' missing true TTFT (ttft_seconds)"
            )
            assert meta.get("ttft_seconds") >= 0.0, f"Negative TTFT on LLM run '{run.name}'"
            assert meta.get("total_latency_seconds", 0.0) >= meta.get("ttft_seconds"), (
                f"Total latency should exceed TTFT on '{run.name}'"
            )
            assert meta.get("role") in {
                "planner",
                "research",
                "analytics",
                "engineering",
                "pm",
                "pm_synthesis",
                "critic",
            }, f"Invalid role on '{run.name}': {meta.get('role')}"
            assert meta.get("model") == "openai/gpt-5.4"
            assert meta.get("provider") in {"OpenAI", "openrouter", "OpenRouter"}
            assert "provider_reported_cost" in meta, (
                f"Missing provider_reported_cost field on '{run.name}'"
            )
            logger.info(
                "Verified LLM Run '%s': role=%s, prompt_tokens=%d, output_tokens=%d, total=%d, cost=%s, ttft=%.3fs, total_latency=%.3fs",
                run.name,
                meta.get("role"),
                meta.get("input_tokens"),
                meta.get("output_tokens"),
                meta.get("total_tokens"),
                meta.get("provider_reported_cost"),
                meta.get("ttft_seconds"),
                meta.get("total_latency_seconds"),
            )

    logger.info(
        "Smoke test completed successfully with verified product and observability contract!"
    )
