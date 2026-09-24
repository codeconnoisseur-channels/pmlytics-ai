"""Tests for UI static assets and client-side secret non-leakage."""

import re
from pathlib import Path

import pytest
from app.api.main import create_app
from httpx import ASGITransport, AsyncClient

UI_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "ui"

SECRET_PATTERNS = [
    re.compile(r"sk-or-v1-[a-f0-9]{32,}", re.IGNORECASE),
    re.compile(r"lsv2_pt_[a-zA-Z0-9_]{16,}", re.IGNORECASE),
    re.compile(r"phc_[a-zA-Z0-9_]{16,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{16,}", re.IGNORECASE),
]


@pytest.mark.asyncio
async def test_ui_root_serves_index_html() -> None:
    """GET / serves the single-page application index.html."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        text = resp.text
        assert "<title>Pocket AI Product Discovery Team</title>" in text
        assert "Observed Facts" in text
        assert "Analytical Inferences" in text
        assert "Testable Hypotheses" in text


@pytest.mark.asyncio
async def test_static_assets_are_accessible() -> None:
    """Static assets styles.css and app.js are served correctly."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        css_resp = await client.get("/static/styles.css")
        assert css_resp.status_code == 200
        assert "--bg-base" in css_resp.text

        js_resp = await client.get("/static/app.js")
        assert js_resp.status_code == 200
        assert "Pocket AI Product Discovery Team" in js_resp.text


def test_ui_files_contain_zero_secrets() -> None:
    """Verify that none of the client-delivered UI files contain hardcoded API keys or secrets."""
    assert UI_DIR.exists(), f"UI directory '{UI_DIR}' must exist."

    for file_path in UI_DIR.glob("*"):
        if file_path.is_file() and file_path.suffix in (".html", ".css", ".js"):
            content = file_path.read_text(encoding="utf-8")
            for pattern in SECRET_PATTERNS:
                matches = pattern.findall(content)
                assert not matches, f"Secret pattern matched in {file_path.name}: {matches}"

            assert "OPENROUTER_API_KEY" not in content
            assert "LANGSMITH_API_KEY" not in content
            assert "POSTHOG_API_KEY" not in content
