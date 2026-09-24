"""Run empirical validation of the three Phase 12 scenarios in Standard profile.

Captures all performance, cost, telemetry, quality, and epistemic metrics.
"""

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

# Force standard profile
os.environ["INVESTIGATION_PROFILE"] = "standard"

from app.config.settings import get_model_for_role, get_settings
from app.orchestration.service import InvestigationService
from evaluations.evaluators.deterministic import evaluate_structural_citations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phase12_validation")

SCENARIOS = [
    {
        "id": "scenario_1",
        "name": "Surge in Failed Transfers",
        "query": "Why are customers reporting a surge in failed transfers this week?",
        "baseline": {
            "investigation_id": "inv_20260917_075720_cb2741",
            "runtime_s": 558.08,
            "llm_calls": 21,
            "tool_calls": 26,
            "provider_cost": 0.788899,
            "status": "historical_verified",
        },
    },
    {
        "id": "scenario_2",
        "name": "Checkout Conversion Drop",
        "query": "Why did checkout conversion drop in release 2.4?",
        "baseline": None,  # Noted per spec: obtain matched baseline only when budget allows
    },
    {
        "id": "scenario_3",
        "name": "Mobile EUR Transfer Delays",
        "query": "Why are mobile EUR transfers experiencing extended delays?",
        "baseline": None,  # Noted per spec: obtain matched baseline only when budget allows
    },
]


async def get_key_usage(api_key: str) -> float:
    """Fetch total usage from OpenRouter key endpoint."""
    url = "https://openrouter.ai/api/v1/auth/key"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        if res.status_code == 200:
            return float(res.json().get("data", {}).get("usage", 0.0))
    return 0.0


async def run_scenario(
    scenario_def: dict[str, Any], service: InvestigationService
) -> dict[str, Any]:
    query = scenario_def["query"]
    scenario_id = scenario_def["id"]
    api_key = get_settings().openrouter_api_key

    timestamp_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    inv_id = f"inv_p12_{scenario_id}_{timestamp_str}"

    logger.info("==================================================================")
    logger.info("STARTING SCENARIO %s: '%s'", scenario_id, query)
    logger.info("Investigation ID: %s", inv_id)
    logger.info("==================================================================")

    usage_before = await get_key_usage(api_key)
    t0 = time.perf_counter()

    try:
        final_state = await service.investigate(
            user_query=query,
            investigation_id=inv_id,
        )
        duration_s = time.perf_counter() - t0
        status = "completed" if final_state.recommendation else "incomplete"
    except Exception as exc:
        duration_s = time.perf_counter() - t0
        logger.exception("Investigation failed with exception: %s", exc)
        return {
            "scenario_id": scenario_id,
            "name": scenario_def["name"],
            "query": query,
            "investigation_id": inv_id,
            "status": "error",
            "error": str(exc),
            "duration_s": round(duration_s, 2),
        }

    # Short wait for OpenRouter usage accounting
    await asyncio.sleep(2.0)
    usage_after = await get_key_usage(api_key)
    provider_cost = max(0.0, usage_after - usage_before)

    # 1. Inspect State Counters
    budget = final_state.budget_usage
    total_tool_calls = (
        budget.research_tool_calls + budget.analytics_tool_calls + budget.engineering_tool_calls
    )
    specialist_llm_calls = (
        budget.research_llm_calls + budget.analytics_llm_calls + budget.engineering_llm_calls
    )
    pm_synthesis_calls = 1 if final_state.recommendation else 0
    pm_revision_calls = final_state.revision_count
    critic_calls = len(final_state.critic_reviews)
    planner_calls = 1 if final_state.plan else 0
    assessment_calls = 1 if final_state.assessment else 0
    total_llm_calls = (
        specialist_llm_calls
        + pm_synthesis_calls
        + pm_revision_calls
        + critic_calls
        + planner_calls
        + assessment_calls
    )

    # 2. Inspect Critic & Revision
    critic_model = get_model_for_role("critic")
    critic_outcome = "NO_REVIEW"
    critic_issue_count = 0
    critic_issue_categories: list[str] = []
    if final_state.critic_reviews:
        first_review = final_state.critic_reviews[0]
        critic_outcome = first_review.decision
        critic_issue_count = len(first_review.issues)
        critic_issue_categories = [i.category for i in first_review.issues]

    revision_triggered = bool(final_state.revision_count > 0 or critic_outcome == "REVISE")
    final_revision_count = final_state.revision_count

    # 3. Deterministic Evidence Citation Validity
    rec = final_state.recommendation
    validity_ratio, total_citations, valid_citations, hallucinated = evaluate_structural_citations(
        final_state, rec
    )

    # 4. Epistemic Separation
    has_facts = bool(rec and len(rec.factual_observations) > 0)
    has_inferences = bool(rec and len(rec.inferences) > 0)
    epistemic_separation_valid = has_facts and has_inferences

    # 5. Ledger stats
    total_ledger_entries = len(final_state.evidence_ledger_entries)

    result_data = {
        "scenario_id": scenario_id,
        "name": scenario_def["name"],
        "query": query,
        "investigation_id": inv_id,
        "status": status,
        "runtime_s": round(duration_s, 2),
        "total_llm_calls": total_llm_calls,
        "total_tool_calls": total_tool_calls,
        "llm_calls_breakdown": {
            "planner": planner_calls,
            "research": budget.research_llm_calls,
            "analytics": budget.analytics_llm_calls,
            "engineering": budget.engineering_llm_calls,
            "assessment": assessment_calls,
            "pm_synthesis": pm_synthesis_calls,
            "critic": critic_calls,
            "pm_revision": pm_revision_calls,
        },
        "tool_calls_breakdown": {
            "research": budget.research_tool_calls,
            "analytics": budget.analytics_tool_calls,
            "engineering": budget.engineering_tool_calls,
        },
        "provider_cost": round(provider_cost, 6),
        "critic_validation": {
            "critic_model": critic_model,
            "critic_outcome": critic_outcome,
            "critic_issue_count": critic_issue_count,
            "issue_categories": critic_issue_categories,
            "revision_triggered": revision_triggered,
            "final_revision_count": final_revision_count,
        },
        "evidence_metrics": {
            "total_ledger_entries": total_ledger_entries,
            "total_citations": total_citations,
            "valid_citations": valid_citations,
            "hallucinated_citations": hallucinated,
            "citation_validity_ratio": validity_ratio,
            "epistemic_separation_valid": epistemic_separation_valid,
        },
        "recommendation_summary": {
            "recommendation_type": rec.recommendation_type if rec else None,
            "confidence": rec.confidence if rec else None,
            "problem_statement": rec.problem_statement[:150] + "..." if rec else None,
            "recommendation": rec.recommendation[:150] + "..." if rec else None,
            "facts_count": len(rec.factual_observations) if rec else 0,
            "inferences_count": len(rec.inferences) if rec else 0,
            "hypotheses_count": len(rec.hypotheses) if rec else 0,
            "likely_causes_count": len(rec.likely_causes) if rec else 0,
            "conflicting_evidence_count": len(rec.conflicting_evidence) if rec else 0,
        },
        "historical_baseline": scenario_def.get("baseline"),
    }

    logger.info("COMPLETED SCENARIO %s in %.2fs!", scenario_id, duration_s)
    logger.info(
        "LLM Calls: %d | Tool Calls: %d | Cost: $%.4f | Critic: %s | Revisions: %d",
        total_llm_calls,
        total_tool_calls,
        provider_cost,
        critic_outcome,
        final_revision_count,
    )
    logger.info(
        "Citations: %d/%d valid (ratio=%.2f) | Epistemic Separation: %s",
        valid_citations,
        total_citations,
        validity_ratio,
        epistemic_separation_valid,
    )

    return result_data


async def main() -> None:
    service = InvestigationService.create_default()
    all_results: list[dict[str, Any]] = []

    for scen in SCENARIOS:
        res = await run_scenario(scen, service)
        all_results.append(res)
        # Brief pause between scenarios
        await asyncio.sleep(3.0)

    out_path = "evaluations/phase12_validation_results.json"
    os.makedirs("evaluations", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    logger.info("Saved all scenario results to %s", out_path)


if __name__ == "__main__":
    asyncio.run(main())
