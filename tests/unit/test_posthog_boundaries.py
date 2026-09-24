"""Tests enforcing runtime read-only boundaries and module isolation."""

import ast
from pathlib import Path

import pytest
from app.config.settings import Settings
from app.integrations.posthog.adapter import PostHogAdapter
from app.integrations.posthog.client import PostHogClient
from seed.posthog.uploader import PostHogUploader


def test_app_does_not_import_seed_or_evaluations() -> None:
    """Enforces strict boundary: app/ must never import seed/ or evaluations/."""
    app_dir = Path(__file__).resolve().parent.parent.parent / "app"
    violations: list[str] = []

    for py_file in app_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(("seed", "evaluations")):
                        violations.append(f"{py_file.name}: import {alias.name}")
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(("seed", "evaluations"))
            ):
                violations.append(f"{py_file.name}: from {node.module} import ...")

    assert not violations, f"Boundary violations detected in app/: {violations}"


def test_runtime_adapter_and_client_are_strictly_read_only() -> None:
    """Verifies that PostHogClient and PostHogAdapter do not define write methods."""
    disallowed_method_names = {
        "post_event",
        "capture",
        "batch",
        "write",
        "create_event",
        "insert",
        "upload",
        "send_event",
    }

    client_methods = {m for m in dir(PostHogClient) if not m.startswith("_")}
    adapter_methods = {m for m in dir(PostHogAdapter) if not m.startswith("_")}

    client_violations = client_methods & disallowed_method_names
    adapter_violations = adapter_methods & disallowed_method_names

    assert not client_violations, f"PostHogClient has write methods: {client_violations}"
    assert not adapter_violations, f"PostHogAdapter has write methods: {adapter_violations}"


def test_uploader_production_safety_guard() -> None:
    """Asserts that PostHogUploader raises RuntimeError if environment is 'production'."""
    prod_settings = Settings(
        environment="production",
        posthog_host="https://app.posthog.com",
        posthog_api_key="prod_token",
    )
    with pytest.raises(RuntimeError) as exc_info:
        PostHogUploader(settings=prod_settings)
    assert "strictly forbidden when environment is 'production'" in str(exc_info.value)
