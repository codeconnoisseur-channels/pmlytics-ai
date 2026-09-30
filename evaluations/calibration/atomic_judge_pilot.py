"""Plan or run the explicitly approved atomic-judge pilot."""

import argparse
import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from app.config.settings import get_settings
from app.integrations.llm.client import OpenRouterClient

from evaluations.calibration.atomic_judge import (
    ATOMIC_JUDGE_PROMPT_VERSION,
    AtomicJudgeEvaluator,
    AtomicJudgeResponse,
)
from evaluations.calibration.live_gate import (
    PaidEvaluationPreflight,
    calculate_preflight,
    require_paid_evaluation_opt_in,
)
from evaluations.calibration.loader import load_case_library
from evaluations.calibration.schema import AtomicJudgment, AuditRecord
from evaluations.config import DEFAULT_PRICING_RATES, MODEL_PROVIDER_ROUTING

PILOT_PATH = Path("evaluations/cases/reference_sets/judge_pilot_v1.json")
PACKETS_PATH = Path("evaluations/reviews/human_review/review_packets.json")
CACHE_PATH = Path("evaluations/reviews/workspace/atomic_judge_cache.json")
RESULT_PATH = Path("evaluations/reviews/workspace/atomic_judge_pilot_v1.json")


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _case_mapping(case_ids: list[str]) -> dict[str, str]:
    return {f"review_case_{index:03d}": case_id for index, case_id in enumerate(case_ids, 1)}


def _cache_key(
    *,
    packet_sha256: str,
    rubric_version: str,
    criterion_id: str,
    model_name: str,
) -> str:
    content = "|".join(
        [
            packet_sha256,
            rubric_version,
            criterion_id,
            ATOMIC_JUDGE_PROMPT_VERSION,
            model_name,
        ]
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _load_inputs(
    model_name: str,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, str]]:
    library = load_case_library()
    pilot_raw = _load_json(PILOT_PATH)
    packets_raw = _load_json(PACKETS_PATH)
    if not isinstance(pilot_raw, dict) or not isinstance(packets_raw, list):
        raise ValueError("Pilot configuration or packet bundle is invalid")
    pilot = cast(dict[str, object], pilot_raw)
    packets = [
        cast(dict[str, object], packet) for packet in packets_raw if isinstance(packet, dict)
    ]
    mappings = _case_mapping(library.development.case_ids)
    if pilot.get("rubric_version") != library.rubric.rubric_version:
        raise ValueError("Pilot rubric version does not match the active case catalog")
    if model_name not in DEFAULT_PRICING_RATES:
        raise ValueError(f"No checked-in pricing snapshot exists for {model_name}")
    return pilot, packets, mappings


def build_preflight(model_name: str, approved_cost_usd: float = 0.15) -> PaidEvaluationPreflight:
    pilot, packets, _ = _load_inputs(model_name)
    selected_ids = cast(list[str], pilot["review_case_ids"])
    packet_map = {str(packet["review_case_id"]): packet for packet in packets}
    if not set(selected_ids) <= set(packet_map):
        raise ValueError("Pilot references a review packet that does not exist")
    cache_raw = _load_json(CACHE_PATH) if CACHE_PATH.exists() else {}
    cache = cast(dict[str, object], cache_raw) if isinstance(cache_raw, dict) else {}
    library = load_case_library()
    mappings = _case_mapping(library.development.case_ids)
    cache_hits = 0
    for review_case_id in selected_ids:
        case = library.get_case(mappings[review_case_id])
        packet = packet_map[review_case_id]
        key = _cache_key(
            packet_sha256=str(packet["packet_sha256"]),
            rubric_version=library.rubric.rubric_version,
            criterion_id=case.criterion_id,
            model_name=model_name,
        )
        cache_hits += int(key in cache)
    pricing = DEFAULT_PRICING_RATES[model_name]
    return calculate_preflight(
        case_count=len(selected_ids),
        cache_hits=cache_hits,
        model_name=model_name,
        estimated_input_tokens_per_case=cast(int, pilot["estimated_input_tokens_per_case"]),
        maximum_output_tokens_per_case=cast(int, pilot["maximum_output_tokens_per_case"]),
        input_cost_per_million=pricing.input_cost_per_million,
        output_cost_per_million=pricing.output_cost_per_million,
        approved_maximum_cost_usd=approved_cost_usd,
    )


async def run_pilot(*, model_name: str, approved_cost_usd: float, live: bool) -> None:
    preflight = build_preflight(model_name, approved_cost_usd)
    print(preflight.model_dump_json(indent=2))
    require_paid_evaluation_opt_in(live=live, preflight=preflight)

    pilot, packets, mappings = _load_inputs(model_name)
    library = load_case_library()
    criteria = {criterion.criterion_id: criterion for criterion in library.rubric.criteria}
    packet_map = {str(packet["review_case_id"]): packet for packet in packets}
    cache_raw = _load_json(CACHE_PATH) if CACHE_PATH.exists() else {}
    cache = cast(dict[str, object], cache_raw) if isinstance(cache_raw, dict) else {}
    settings = get_settings()
    evaluator = AtomicJudgeEvaluator(
        OpenRouterClient(
            api_key=settings.openrouter_api_key,
            provider_routing=MODEL_PROVIDER_ROUTING[model_name],
        ),
        model_name,
    )
    records: list[dict[str, object]] = []

    for review_case_id in cast(list[str], pilot["review_case_ids"]):
        case = library.get_case(mappings[review_case_id])
        criterion = criteria[case.criterion_id]
        packet = packet_map[review_case_id]
        key = _cache_key(
            packet_sha256=str(packet["packet_sha256"]),
            rubric_version=library.rubric.rubric_version,
            criterion_id=criterion.criterion_id,
            model_name=model_name,
        )
        if key in cache:
            response = AtomicJudgeResponse.model_validate(cache[key])
        else:
            response = await evaluator.evaluate(
                packet=packet,
                criterion=criterion,
                rubric=library.rubric,
            )
            cache[key] = response.model_dump(mode="json")
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CACHE_PATH.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")

        judgment = AtomicJudgment(
            case_id=case.case_id,
            criterion_id=criterion.criterion_id,
            verdict=response.verdict,
            severity=response.severity,
            reason=response.reason,
            claim_reference=response.claim_reference,
            evidence_references=response.evidence_references,
        )
        record = AuditRecord(
            audit_id=f"judge_{review_case_id}_{ATOMIC_JUDGE_PROMPT_VERSION}",
            reviewer_type="llm_judge",
            reviewer_id="atomic_judge_pilot",
            packet_sha256=str(packet["packet_sha256"]),
            rubric_version=library.rubric.rubric_version,
            created_at_utc=datetime.now(UTC),
            judge_model=model_name,
            judge_prompt_version=ATOMIC_JUDGE_PROMPT_VERSION,
            judgments=[judgment],
        )
        records.append(record.model_dump(mode="json"))

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(
        json.dumps(
            {
                "pilot_id": pilot["pilot_id"],
                "model": model_name,
                "rubric_version": library.rubric.rubric_version,
                "prompt_version": ATOMIC_JUDGE_PROMPT_VERSION,
                "records": records,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Pilot results saved to {RESULT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Atomic judge pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--model", default=os.getenv("DEFAULT_MODEL", "openai/gpt-5.4"))
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--model", default=os.getenv("DEFAULT_MODEL", "openai/gpt-5.4"))
    run_parser.add_argument("--live", action="store_true")
    run_parser.add_argument("--max-provider-cost-usd", type=float, required=True)
    args = parser.parse_args()

    if args.command == "plan":
        print(build_preflight(args.model).model_dump_json(indent=2))
        return
    asyncio.run(
        run_pilot(
            model_name=args.model,
            approved_cost_usd=args.max_provider_cost_usd,
            live=args.live,
        )
    )


if __name__ == "__main__":
    main()
