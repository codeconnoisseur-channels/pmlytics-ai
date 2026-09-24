"""Verification of frozen judge prompt SHA256 immutability.

Enforces that JUDGE_SYSTEM_PROMPT remains bit-for-bit unchanged from the approved
Phase 9 frozen calibration baseline:
8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63
"""

import hashlib

from evaluations.evaluators.prompts.judge_prompt import JUDGE_SYSTEM_PROMPT

FROZEN_PROMPT_SHA256 = "8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63"


def test_frozen_judge_prompt_sha256() -> None:
    """Fail the test gate if JUDGE_SYSTEM_PROMPT differs from the frozen SHA256."""
    prompt_bytes = JUDGE_SYSTEM_PROMPT.strip().encode("utf-8")
    actual_sha = hashlib.sha256(prompt_bytes).hexdigest()
    assert actual_sha == FROZEN_PROMPT_SHA256, (
        f"Frozen judge prompt SHA256 mismatch! Expected: {FROZEN_PROMPT_SHA256}, got: {actual_sha}."
    )
