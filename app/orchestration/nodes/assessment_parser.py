"""Safe parser and normalizer for EvidenceAssessment outputs.

Enforces strict safety invariants:
1. Valid direct Assessment instances are parsed and validated via Pydantic.
2. Only explicitly recognized wrappers ('assessment', 'result', 'data') containing plausible Assessment instances are unwrapped.
3. JSON Schema objects (with 'properties', 'type', '$schema', etc.) masquerading as output are strictly rejected.
4. Malformed wrappers, missing required fields, or incorrect field types fail closed with explicit validation errors.
"""

import json
import logging
from typing import Any

from app.orchestration.state import EvidenceAssessment

logger = logging.getLogger(__name__)

RECOGNIZED_WRAPPERS = ("assessment", "result", "data")
SCHEMA_INDICATORS = ("$schema", "definitions", "$defs")


def safe_parse_assessment_payload(raw_input: str | dict[str, Any]) -> EvidenceAssessment:
    """Parse and safely normalize an EvidenceAssessment payload.

    Raises:
        ValueError: If JSON is invalid, wrapper is unrecognized, or payload is a schema definition.
        ValidationError: If fields are missing or have incorrect types.
    """
    if isinstance(raw_input, str):
        cleaned = raw_input.strip()
        # Strip markdown fences if present
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Assessment payload is not valid JSON: {exc}") from exc
    elif isinstance(raw_input, dict):
        data = raw_input
    else:
        raise ValueError(
            f"Assessment payload must be a JSON string or dict, got {type(raw_input).__name__}"
        )

    if not isinstance(data, dict):
        raise ValueError(
            f"Assessment payload must be a JSON object (dict), got {type(data).__name__}"
        )

    # Invariant 3: Reject JSON Schema definitions masquerading as output
    if data.get("type") == "object":
        raise ValueError(
            "Payload is a JSON Schema definition ('type': 'object') masquerading as output"
        )
    if any(k in data for k in SCHEMA_INDICATORS):
        raise ValueError("Payload contains JSON Schema metadata keys ($schema/definitions/$defs)")
    if (
        "properties" in data
        and ("description" in data or "title" in data)
        and "sufficient_for_synthesis" not in data
    ):
        raise ValueError(
            "Payload is a JSON Schema definition with 'properties' and 'description'/'title' masquerading as output"
        )

    # Invariant 1: Direct instance with expected top-level field
    if "sufficient_for_synthesis" in data:
        return EvidenceAssessment.model_validate(data)

    # Invariant 2: Explicit recognized single-key wrapper
    if len(data) == 1:
        wrapper_key = next(iter(data.keys()))
        if wrapper_key in RECOGNIZED_WRAPPERS:
            inner = data[wrapper_key]
            if not isinstance(inner, dict):
                raise ValueError(f"Recognized wrapper '{wrapper_key}' does not contain an object")
            if inner.get("type") == "object":
                raise ValueError(
                    f"Recognized wrapper '{wrapper_key}' contains a JSON Schema definition"
                )
            if (
                "properties" in inner
                and ("description" in inner or "title" in inner)
                and "sufficient_for_synthesis" not in inner
            ):
                raise ValueError(
                    f"Recognized wrapper '{wrapper_key}' contains a JSON Schema definition"
                )
            if "sufficient_for_synthesis" in inner or "has_blocking_gaps" in inner:
                return EvidenceAssessment.model_validate(inner)
            raise ValueError(
                f"Recognized wrapper '{wrapper_key}' does not contain a plausible EvidenceAssessment"
            )
        raise ValueError(
            f"Unrecognized wrapper key '{wrapper_key}'; recognized wrappers are: {RECOGNIZED_WRAPPERS}"
        )

    # Fallback to standard validation to produce comprehensive ValidationError
    return EvidenceAssessment.model_validate(data)
