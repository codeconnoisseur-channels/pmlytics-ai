"""Unit tests verifying Assessment output unwrapping safety invariants.

Tests cover:
1. Valid direct Assessment
2. Valid recognized wrapper containing an actual Assessment object
3. JSON Schema masquerading as output (must reject)
4. Malformed/unrecognized wrapper (must reject)
5. Missing required fields (must reject)
6. Incorrect field types (must reject)
"""

import pytest
from app.orchestration.nodes.assessment_parser import safe_parse_assessment_payload
from app.orchestration.state import EvidenceAssessment
from pydantic import ValidationError


def test_valid_direct_assessment() -> None:
    """Case 1: Direct JSON dictionary conforming to EvidenceAssessment schema."""
    raw = {
        "sufficient_for_synthesis": True,
        "has_blocking_gaps": False,
        "identified_gaps": [],
        "unanswered_questions": [],
        "recommended_specialist": None,
        "recommended_gap": None,
    }
    result = safe_parse_assessment_payload(raw)
    assert isinstance(result, EvidenceAssessment)
    assert result.sufficient_for_synthesis is True
    assert result.has_blocking_gaps is False


def test_valid_recognized_wrapper() -> None:
    """Case 2: Recognized single-key wrapper envelopes ('assessment', 'result', 'data')."""
    for wrapper in ["assessment", "result", "data"]:
        raw = {
            wrapper: {
                "sufficient_for_synthesis": False,
                "has_blocking_gaps": True,
                "identified_gaps": ["Missing breakdown of transfers by payment method"],
                "unanswered_questions": ["Which payment method had the highest failure rate?"],
                "recommended_specialist": "analytics",
                "recommended_gap": "Missing breakdown of transfers by payment method",
            }
        }
        result = safe_parse_assessment_payload(raw)
        assert isinstance(result, EvidenceAssessment)
        assert result.sufficient_for_synthesis is False
        assert result.has_blocking_gaps is True
        assert len(result.identified_gaps) == 1
        assert result.recommended_specialist == "analytics"


def test_json_schema_masquerading_as_output_is_rejected() -> None:
    """Case 3: JSON Schema definition containing 'properties', 'description', and 'type' must be rejected."""
    # Pattern A: Standard JSON schema output produced by confused models
    raw_schema_a = {
        "description": "Structured assessment produced by assessment_node.",
        "type": "object",
        "properties": {
            "sufficient_for_synthesis": False,
            "has_blocking_gaps": True,
            "identified_gaps": ["Some gap"],
        },
    }
    with pytest.raises(ValueError, match="JSON Schema definition"):
        safe_parse_assessment_payload(raw_schema_a)

    # Pattern B: Schema description with properties without sufficient_for_synthesis at root
    raw_schema_b = {
        "description": "EvidenceAssessment schema definition",
        "properties": {
            "sufficient_for_synthesis": {"type": "boolean"},
            "has_blocking_gaps": {"type": "boolean"},
        },
    }
    with pytest.raises(ValueError, match="JSON Schema definition"):
        safe_parse_assessment_payload(raw_schema_b)


def test_malformed_unrecognized_wrapper_is_rejected() -> None:
    """Case 4: Unrecognized wrapper key or malformed envelope structure fails closed."""
    raw_unrecognized = {
        "output_payload": {
            "sufficient_for_synthesis": True,
            "has_blocking_gaps": False,
        }
    }
    with pytest.raises(ValueError, match="Unrecognized wrapper key 'output_payload'"):
        safe_parse_assessment_payload(raw_unrecognized)

    raw_non_dict_wrapper = {"assessment": "not a dictionary object"}
    with pytest.raises(ValueError, match="does not contain an object"):
        safe_parse_assessment_payload(raw_non_dict_wrapper)


def test_missing_required_fields_fails_validation() -> None:
    """Case 5: Payload missing required fields fails validation rather than fabricating defaults."""
    # Missing has_blocking_gaps
    raw = {
        "sufficient_for_synthesis": True,
    }
    with pytest.raises(ValidationError) as exc_info:
        safe_parse_assessment_payload(raw)
    assert "has_blocking_gaps" in str(exc_info.value)


def test_incorrect_field_types_fails_validation() -> None:
    """Case 6: Payload with incorrect field types fails validation."""
    raw = {
        "sufficient_for_synthesis": "not_a_boolean_value_definitely",
        "has_blocking_gaps": False,
    }
    with pytest.raises(ValidationError):
        safe_parse_assessment_payload(raw)

    raw_bad_list = {
        "sufficient_for_synthesis": True,
        "has_blocking_gaps": False,
        "identified_gaps": 12345,  # Must be list of strings
    }
    with pytest.raises(ValidationError):
        safe_parse_assessment_payload(raw_bad_list)
