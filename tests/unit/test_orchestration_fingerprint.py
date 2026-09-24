"""Unit tests for deterministic task canonicalization and hashing."""

from app.orchestration.fingerprint import compute_canonical_task_fingerprint


def test_canonical_fingerprint_invariance() -> None:
    """Verify that canonical normalization produces identical hashes for equivalent tasks."""
    fp1 = compute_canonical_task_fingerprint(
        specialist="Research",
        objective="Investigate why users report delayed transfers",
        questions=["Why are transfers delayed?", "Are there timeout tickets?"],
    )

    fp2 = compute_canonical_task_fingerprint(
        specialist="  research  ",
        objective="Investigate   why   users report delayed  transfers",
        questions=["Are there timeout tickets?", "Why are transfers delayed?"],  # Reversed order
    )

    assert fp1 == fp2


def test_canonical_fingerprint_distinctness() -> None:
    """Verify that differing objectives or specialists yield distinct hashes."""
    fp_research = compute_canonical_task_fingerprint(
        specialist="research",
        objective="Investigate why users report delayed transfers",
        questions=["Question 1"],
    )

    fp_engineering = compute_canonical_task_fingerprint(
        specialist="engineering",
        objective="Investigate why users report delayed transfers",
        questions=["Question 1"],
    )

    fp_diff_obj = compute_canonical_task_fingerprint(
        specialist="research",
        objective="Analyze KYC onboarding drop-off",
        questions=["Question 1"],
    )

    assert fp_research != fp_engineering
    assert fp_research != fp_diff_obj
