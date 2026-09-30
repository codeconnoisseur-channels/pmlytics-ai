"""Load and validate product-owned cases independently of evaluation runners."""

import csv
import json
from pathlib import Path
from typing import cast

from pydantic import BaseModel, ConfigDict

from evaluations.calibration.schema import CaseDefinition, ReferenceSet, RubricDefinition

DEFAULT_CASES_ROOT = Path(__file__).resolve().parents[1] / "cases"


class CaseLibrary(BaseModel):
    model_config = ConfigDict(frozen=True)

    cases: list[CaseDefinition]
    rubric: RubricDefinition
    development: ReferenceSet
    held_out: ReferenceSet

    def get_case(self, case_id: str) -> CaseDefinition:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise KeyError(f"Unknown evaluation case: {case_id}")


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return cast(dict[str, object], data)


def _load_catalog(path: Path) -> list[CaseDefinition]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        if row.get("last_reviewed_utc") == "":
            row["last_reviewed_utc"] = None
    return [CaseDefinition.model_validate(row) for row in rows]


def load_case_library(root: Path | None = None) -> CaseLibrary:
    cases_root = root or DEFAULT_CASES_ROOT
    cases = _load_catalog(cases_root / "catalog.csv")
    rubric_versions = {case.rubric_version for case in cases}
    if len(rubric_versions) != 1:
        raise ValueError("The active case catalog must reference exactly one rubric version")
    rubric_version = next(iter(rubric_versions))
    rubric = RubricDefinition.model_validate(
        _load_json(cases_root / "rubrics" / f"{rubric_version}.json")
    )
    if rubric.status != "active":
        raise ValueError(f"Catalog rubric {rubric_version} is not active")
    development = ReferenceSet.model_validate(
        _load_json(cases_root / "reference_sets" / "development.json")
    )
    held_out = ReferenceSet.model_validate(
        _load_json(cases_root / "reference_sets" / "held_out.json")
    )

    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Case catalog contains duplicate case IDs")

    criteria = {criterion.criterion_id: criterion for criterion in rubric.criteria}
    for case in cases:
        if case.rubric_version != rubric.rubric_version:
            raise ValueError(
                f"Case {case.case_id} references {case.rubric_version}, expected {rubric.rubric_version}"
            )
        criterion = criteria.get(case.criterion_id)
        if criterion is None:
            raise ValueError(
                f"Case {case.case_id} references unknown criterion {case.criterion_id}"
            )
        if criterion.dimension != case.dimension:
            raise ValueError(
                f"Case {case.case_id} dimension does not match criterion {case.criterion_id}"
            )

    catalog_ids = set(case_ids)
    development_ids = set(development.case_ids)
    held_out_ids = set(held_out.case_ids)
    unknown_reference_ids = (development_ids | held_out_ids) - catalog_ids
    if unknown_reference_ids:
        raise ValueError(f"Reference sets contain unknown cases: {sorted(unknown_reference_ids)}")
    if development_ids & held_out_ids:
        raise ValueError("Development and held-out reference sets must be disjoint")

    for case_id in development_ids:
        if next(case for case in cases if case.case_id == case_id).split != "development":
            raise ValueError(f"Development set contains non-development case {case_id}")
    for case_id in held_out_ids:
        if next(case for case in cases if case.case_id == case_id).split != "held_out":
            raise ValueError(f"Held-out set contains non-held-out case {case_id}")

    return CaseLibrary(
        cases=cases,
        rubric=rubric,
        development=development,
        held_out=held_out,
    )
