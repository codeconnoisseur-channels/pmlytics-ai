"""Deterministic task identity canonicalization and hashing."""

import hashlib


def compute_canonical_task_fingerprint(
    specialist: str,
    objective: str,
    questions: list[str],
) -> str:
    """Compute a deterministic hash for a specialist task under canonical normalization.

    Normalizes:
    - Specialist role: lowercased and stripped
    - Objective: lowercased and collapsed whitespace
    - Questions: lowercased, collapsed whitespace, sorted lexicographically
    """
    norm_specialist = specialist.strip().lower()
    norm_objective = " ".join(objective.strip().lower().split())
    norm_questions = "|".join(sorted(" ".join(q.strip().lower().split()) for q in questions))
    raw = f"{norm_specialist}::{norm_objective}::{norm_questions}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
