"""Build reviewer-identical packets without exposing expected behavior."""

import hashlib
import json

from evaluations.calibration.loader import CaseLibrary
from evaluations.calibration.schema import EvaluationPacket
from evaluations.dataset.evaluator_stress_suite import STRESS_CASES


def _stable_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_evaluation_packet(library: CaseLibrary, case_id: str) -> EvaluationPacket:
    """Resolve a case packet while excluding expected verdicts and rationales."""
    definition = library.get_case(case_id)
    prefix = "legacy_stress_fixture:"
    if not definition.packet_source.startswith(prefix):
        raise ValueError(f"Unsupported packet source: {definition.packet_source}")

    fixture_id = definition.packet_source.removeprefix(prefix)
    fixture = next((case for case in STRESS_CASES if case.case_id == fixture_id), None)
    if fixture is None:
        raise ValueError(f"Missing preserved stress fixture: {fixture_id}")

    content: dict[str, object] = {
        "packet_version": "1",
        "case_id": definition.case_id,
        "user_query": fixture.user_query,
        "evidence": [entry.model_dump(mode="json") for entry in fixture.evidence_ledger_entries],
        "candidate_recommendation": fixture.candidate_recommendation.model_dump(mode="json"),
        "source_failures": fixture.source_failures,
    }
    return EvaluationPacket(
        packet_version="1",
        case_id=definition.case_id,
        user_query=fixture.user_query,
        evidence=[entry.model_dump(mode="json") for entry in fixture.evidence_ledger_entries],
        candidate_recommendation=fixture.candidate_recommendation.model_dump(mode="json"),
        source_failures=fixture.source_failures,
        content_sha256=_stable_hash(content),
    )
