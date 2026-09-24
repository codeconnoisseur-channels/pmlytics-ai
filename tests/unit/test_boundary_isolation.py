"""Architectural test asserting boundary isolation between runtime, seed, and evaluations."""

import ast
from pathlib import Path


def _get_imports_from_file(file_path: Path) -> list[str]:
    """Parse a python file and return all imported module root names."""
    with open(file_path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imported_roots: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.append(node.module.split(".")[0])
    return imported_roots


def test_app_runtime_does_not_import_seed_or_evaluations() -> None:
    """Verify runtime code (app/) never imports from seed or evaluations."""
    root_dir = Path(__file__).parents[2]
    app_dir = root_dir / "app"
    assert app_dir.exists()

    forbidden_targets = {"seed", "evaluations"}

    violations: list[str] = []
    for py_file in app_dir.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            if imp in forbidden_targets:
                rel_path = py_file.relative_to(root_dir)
                violations.append(f"{rel_path} imports '{imp}'")

    assert not violations, (
        "Architectural Boundary Violation: Runtime code must not import from seed or evaluations:\n"
        + "\n".join(violations)
    )


def test_seed_does_not_import_evaluations() -> None:
    """Verify seed generation code does not import from evaluations."""
    root_dir = Path(__file__).parents[2]
    seed_dir = root_dir / "seed"
    assert seed_dir.exists()

    violations: list[str] = []
    for py_file in seed_dir.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            if imp == "evaluations":
                rel_path = py_file.relative_to(root_dir)
                violations.append(f"{rel_path} imports 'evaluations'")

    assert not violations, (
        "Architectural Boundary Violation: Seed code must not import from evaluations:\n"
        + "\n".join(violations)
    )


def test_evaluations_does_not_import_seed() -> None:
    """Verify evaluation code does not import from seed."""
    root_dir = Path(__file__).parents[2]
    eval_dir = root_dir / "evaluations"
    assert eval_dir.exists()

    violations: list[str] = []
    for py_file in eval_dir.rglob("*.py"):
        imports = _get_imports_from_file(py_file)
        for imp in imports:
            if imp == "seed":
                rel_path = py_file.relative_to(root_dir)
                violations.append(f"{rel_path} imports 'seed'")

    assert not violations, (
        "Architectural Boundary Violation: Evaluations code must not import from seed:\n"
        + "\n".join(violations)
    )
