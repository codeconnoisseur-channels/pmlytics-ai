"""Unit tests for Phase 10 LangSmith distributed tracing, fail-open resilience, secret redaction, and token budgeting."""

import json
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.config.settings import get_max_tokens_for_role
from app.integrations.llm.client import LLMMessage, OpenRouterClient
from app.integrations.llm.exceptions import LLMMalformedOutputError
from app.integrations.observability.tracer import InvestigationTracer, sanitize_payload


def test_explicit_role_token_ceilings() -> None:
    """Verify all 6 approved logical AI roles resolve to evidence-based token bounds."""
    assert get_max_tokens_for_role("planner") == 1024
    assert get_max_tokens_for_role("research") == 2560
    assert get_max_tokens_for_role("analytics") == 2560
    assert get_max_tokens_for_role("engineering") == 2560
    assert get_max_tokens_for_role("pm") == 5120
    assert get_max_tokens_for_role("pm_synthesis") == 5120
    assert get_max_tokens_for_role("critic") == 2048

    # Verify unapproved or obsolete roles raise ValueError
    with pytest.raises(ValueError, match="Unknown or unapproved agent role 'assessment'"):
        get_max_tokens_for_role("assessment")

    with pytest.raises(ValueError, match="Unknown or unapproved agent role 'manager'"):
        get_max_tokens_for_role("manager")


def test_tracer_secret_redaction() -> None:
    """Verify strict key-based and regex-based redaction of secrets and credentials."""
    raw_payload = {
        "user_query": "Investigate payment failure",
        "api_key": "sk-or-v1-abcdef1234567890abcdef1234567890",
        "headers": {
            "Authorization": "Bearer sk-or-v1-secretkey9999999999999999",
            "X-Custom-Token": "lsv2_pt_1234567890abcdef_secret",
        },
        "posthog_config": {
            "posthog_project_token": "phc_token_secret_value_12345",
            "posthog_api_key": "phx_key_secret_value_67890",
        },
        "nested_list": [
            {"token": "secret_token_val"},
            "Contains inline sk-or-v1-abcdef1234567890abcdef1234567890 key inside string",
        ],
    }

    sanitized = sanitize_payload(raw_payload)

    # Key denylist assertions
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["headers"]["Authorization"] == "[REDACTED]"
    assert sanitized["headers"]["X-Custom-Token"] == "[REDACTED]"
    assert sanitized["posthog_config"]["posthog_project_token"] == "[REDACTED]"
    assert sanitized["posthog_config"]["posthog_api_key"] == "[REDACTED]"
    assert sanitized["nested_list"][0]["token"] == "[REDACTED]"

    # Regex scrubbing assertion
    assert "sk-or-v1-" not in sanitized["nested_list"][1]
    assert "[REDACTED]" in sanitized["nested_list"][1]


def test_tracer_hierarchy_and_correlation() -> None:
    """Verify RunTree hierarchical span creation and investigation_id correlation."""
    tracer = InvestigationTracer(
        investigation_id="inv_test_hier_001",
        enabled=True,
        environment="test",
    )

    assert tracer.root_run is not None
    assert tracer.root_run.name == "investigation_workflow"
    assert tracer.root_run.extra["metadata"]["investigation_id"] == "inv_test_hier_001"

    # Start child specialist node span
    specialist_span = tracer.start_span(
        name="research_agent",
        run_type="chain",
        inputs={"task": "search tickets"},
    )
    assert specialist_span is not None
    assert specialist_span.parent_run_id == tracer.root_run.id
    assert specialist_span.extra["metadata"]["investigation_id"] == "inv_test_hier_001"

    # Start grandchild tool span under specialist
    tool_span = tracer.start_span(
        name="search_tickets",
        run_type="tool",
        inputs={"query": "transfer delay"},
        parent_span=specialist_span,
    )
    assert tool_span is not None
    assert tool_span.parent_run_id == specialist_span.id

    # End spans
    tracer.end_span(tool_span, outputs={"result_count": 5})
    tracer.end_span(specialist_span, outputs={"status": "completed"})
    tracer.close(final_status="completed")


def test_tracer_fail_open_on_endpoint_error() -> None:
    """Verify that tracing failures never raise exceptions or alter execution."""
    with patch(
        "langsmith.run_trees.RunTree.post", side_effect=ConnectionError("Endpoint unreachable")
    ):
        tracer = InvestigationTracer(
            investigation_id="inv_fail_open_test",
            enabled=True,
            environment="test",
        )
        # Root run should safely degrade to None
        assert tracer.root_run is None

        # Child spans become safe no-ops
        span = tracer.start_span("planner", run_type="chain", inputs={"q": "test"})
        assert span is None

        # Ending no-op span succeeds cleanly without error
        tracer.end_span(span, outputs={"done": True})
        tracer.close()


@pytest.mark.asyncio
async def test_openrouter_client_enforces_role_max_tokens() -> None:
    """Verify that OpenRouterClient passes explicit bounded max_tokens for each role."""
    client = OpenRouterClient(api_key="mock-key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "ok"}'
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"status": "ok"}'}, "finish_reason": "stop"}],
        "usage": {"total_tokens": 150},
        "model": "openai/gpt-5.4",
    }

    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = mock_response
    client._external_client = mock_http_client

    messages = [LLMMessage(role="user", content="Hello")]

    # Call with role="planner"
    await client.complete(messages, model="openai/gpt-5.4", role="planner")
    assert mock_http_client.post.call_count == 1
    sent_payload = mock_http_client.post.call_args[1]["json"]
    assert sent_payload["max_tokens"] == 1024

    # Call with role="pm"
    await client.complete(messages, model="openai/gpt-5.4", role="pm")
    sent_payload = mock_http_client.post.call_args[1]["json"]
    assert sent_payload["max_tokens"] == 5120

    # Call with explicit override
    await client.complete(messages, model="openai/gpt-5.4", max_tokens=500)
    sent_payload = mock_http_client.post.call_args[1]["json"]
    assert sent_payload["max_tokens"] == 500


@pytest.mark.asyncio
async def test_openrouter_client_raises_on_truncation() -> None:
    """Verify that finish_reason == 'length' raises explicit LLMMalformedOutputError (no silent truncation)."""
    client = OpenRouterClient(api_key="mock-key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"partial": "data"}'
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"partial": "data'}, "finish_reason": "length"}],
        "usage": {"total_tokens": 1024},
        "model": "openai/gpt-5.4",
    }

    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = mock_response
    client._external_client = mock_http_client

    messages = [LLMMessage(role="user", content="Hello")]

    with pytest.raises(
        LLMMalformedOutputError, match="Model response was truncated: exceeded token budget ceiling"
    ):
        await client.complete(messages, model="openai/gpt-5.4", role="planner")


@pytest.mark.asyncio
async def test_all_six_roles_use_exact_configured_token_budgets() -> None:
    """User Correction #2: Add test proving every actual role invocation uses its configured budget."""
    client = OpenRouterClient(api_key="mock-key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"status": "ok"}'
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"status": "ok"}'}, "finish_reason": "stop"}],
        "usage": {"total_tokens": 100},
        "model": "openai/gpt-5.4",
    }
    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = mock_response
    client._external_client = mock_http_client

    messages = [LLMMessage(role="user", content="Test query")]

    from app.config.settings import ROLE_MAX_TOKENS

    for role, expected_ceiling in ROLE_MAX_TOKENS.items():
        mock_http_client.post.reset_mock()
        await client.complete(messages, model="openai/gpt-5.4", role=role)
        assert mock_http_client.post.call_count == 1
        payload = mock_http_client.post.call_args[1]["json"]
        assert payload["max_tokens"] == expected_ceiling, (
            f"Role '{role}' sent max_tokens={payload['max_tokens']}, expected configured ceiling {expected_ceiling}"
        )


@pytest.mark.asyncio
async def test_investigation_service_fail_open_when_langsmith_disabled_or_failing() -> None:
    """User Correction #5 & #9: Tracing failures or disabled state must never fail the investigation."""
    from app.domain.recommendation import ProductRecommendation
    from app.orchestration.service import InvestigationService
    from app.orchestration.state import InvestigationState

    mock_llm = AsyncMock()
    mock_research = AsyncMock()
    mock_analytics = AsyncMock()
    mock_engineering = AsyncMock()

    service = InvestigationService(
        llm_client=mock_llm,
        research_agent=mock_research,
        analytics_agent=mock_analytics,
        engineering_agent=mock_engineering,
    )

    from app.domain.evidence import Evidence, EvidenceConfidence

    mock_final_state = InvestigationState(
        investigation_id="inv_test_fail_open",
        user_query="Why are transactions failing?",
        recommendation=ProductRecommendation(
            problem_statement="Transfers failing due to webhook timeout.",
            why_it_matters="High user friction and transaction abandonment.",
            affected_users="Instant deposit users on mobile.",
            factual_observations=["Observed 50 support tickets regarding pending deposits."],
            inferences=["Core banking webhook is timing out."],
            evidence=[
                Evidence(
                    ledger_entry_id="entry_001",
                    source_type="zendesk",
                    source_reference="ticket:101",
                    finding="Customer report",
                    support="Ticket 101 body",
                    confidence=EvidenceConfidence.HIGH,
                )
            ],
            recommendation="Remediate webhook timeout in banking gateway.",
            recommendation_type="technical_remediation",
            success_metrics=["Instant deposit success rate > 95%"],
            risks=["Temporary gateway downtime during deployment"],
            confidence="high",
        ),
    )
    service.graph.ainvoke = AsyncMock(return_value=mock_final_state.model_dump())

    # Case A: Tracing disabled
    service.settings.langsmith_tracing = False
    result_a = await service.investigate(
        user_query="Test question", investigation_id="inv_test_fail_open_a"
    )
    assert result_a.recommendation is not None
    assert result_a.recommendation.recommendation == "Remediate webhook timeout in banking gateway."

    # Case B: Tracing enabled but RunTree throws
    service.settings.langsmith_tracing = True
    service.settings.langsmith_api_key = "fake_key"
    with patch(
        "langsmith.run_trees.RunTree.post", side_effect=RuntimeError("LangSmith API Outage 503")
    ):
        result_b = await service.investigate(
            user_query="Test question", investigation_id="inv_test_fail_open_b"
        )
        assert result_b.recommendation is not None
        assert (
            result_b.recommendation.recommendation
            == "Remediate webhook timeout in banking gateway."
        )


class MockStreamResponse:
    """Mock asynchronous SSE stream response."""

    def __init__(self, lines: list[str], status_code: int = 200) -> None:
        self.lines = lines
        self.status_code = status_code

    async def aiter_lines(self):
        for line in self.lines:
            yield line

    async def aread(self) -> bytes:
        return b""


class MockStreamClient:
    """Mock client supporting async with client.stream(...)."""

    def __init__(self, lines: list[str], status_code: int = 200) -> None:
        self.lines = lines
        self.status_code = status_code
        self._supports_stream = True
        self.calls: list[dict[str, Any]] = []

    @asynccontextmanager
    async def stream(
        self, method: str, url: str, headers: dict | None = None, json: dict | None = None
    ):
        self.calls.append({"method": method, "url": url, "headers": headers, "json": json})
        yield MockStreamResponse(self.lines, self.status_code)


def test_internal_pricing_calculation() -> None:
    """Verify snapshot-based cost calculation for audit cross-checks."""
    from app.integrations.llm.pricing import PRICING_SNAPSHOT_VERSION, calculate_internal_cost

    assert PRICING_SNAPSHOT_VERSION == "2026-09-01-frozen"

    # gpt-5.4: $2.50 input / 1M, $15.00 output / 1M
    # 10,000 prompt tokens = $0.025, 2,000 output tokens = $0.030 -> total = $0.055
    cost_gpt = calculate_internal_cost(
        "openai/gpt-5.4", prompt_tokens=10_000, completion_tokens=2_000
    )
    assert cost_gpt == 0.055

    # claude-sonnet-4.6: $3.00 input / 1M, $15.00 output / 1M
    # 10,000 prompt tokens = $0.030, 2,000 output tokens = $0.030 -> total = $0.060
    cost_claude = calculate_internal_cost(
        "anthropic/claude-sonnet-4.6", prompt_tokens=10_000, completion_tokens=2_000
    )
    assert cost_claude == 0.060

    # Unknown model returns None
    assert calculate_internal_cost("unknown-model", 100, 100) is None


@pytest.mark.asyncio
async def test_streaming_text_accumulation_and_ttft() -> None:
    """Verify streaming chunks assemble correctly and true TTFT is captured."""
    from app.integrations.observability.tracer import trace_investigation

    lines = [
        "data: " + json.dumps({"choices": [{"delta": {"role": "assistant"}}]}),
        "data: " + json.dumps({"choices": [{"delta": {"content": "First chunk. "}}]}),
        "data: " + json.dumps({"choices": [{"delta": {"content": "Second chunk."}}]}),
        "data: "
        + json.dumps(
            {
                "choices": [{"delta": {}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 6,
                    "total_tokens": 21,
                    "cost": 0.00012,
                },
            }
        ),
        "data: [DONE]",
    ]

    mock_client = MockStreamClient(lines)
    client = OpenRouterClient(api_key="mock-key", http_client=mock_client)

    tracer = InvestigationTracer(
        investigation_id="inv_test_stream_001", enabled=True, environment="test"
    )
    with trace_investigation(tracer):
        resp = await client.complete(
            [LLMMessage(role="user", content="Hello")],
            model="openai/gpt-5.4",
            role="pm",
        )

    # 1. Verification of assembled text and stop condition
    assert resp.content == "First chunk. Second chunk."
    assert resp.finish_reason == "stop"

    # 2. Verification of token usage from terminal chunk
    assert resp.token_usage is not None
    assert resp.token_usage["prompt_tokens"] == 15
    assert resp.token_usage["completion_tokens"] == 6
    assert resp.token_usage["total_tokens"] == 21
    assert resp.token_usage["cost"] == 0.00012

    # 3. Verification of LLM child span in LangSmith RunTree
    assert tracer.root_run is not None
    assert len(tracer.root_run.child_runs) == 1
    llm_span = tracer.root_run.child_runs[0]
    assert llm_span.name == "llm:openai/gpt-5.4"
    assert llm_span.run_type == "llm"

    # 4. Verification of TTFT and latency metadata
    meta = llm_span.metadata
    assert meta["model"] == "openai/gpt-5.4"
    assert meta["role"] == "pm"
    assert meta["input_tokens"] == 15
    assert meta["output_tokens"] == 6
    assert meta["total_tokens"] == 21
    assert meta["provider_reported_cost"] == 0.00012
    assert meta["internally_estimated_cost"] is not None
    assert meta["ttft_seconds"] is not None
    assert meta["ttft_seconds"] >= 0.0
    assert meta["total_latency_seconds"] >= meta["ttft_seconds"]
    assert meta["finish_reason"] == "stop"

    # 5. Verification of canonical usage_metadata for LangSmith UI
    usage_meta = meta["usage_metadata"]
    assert usage_meta["input_tokens"] == 15
    assert usage_meta["output_tokens"] == 6
    assert usage_meta["total_tokens"] == 21
    assert usage_meta["total_cost"] == 0.00012


@pytest.mark.asyncio
async def test_streaming_tool_call_argument_fragment_accumulation() -> None:
    """Verify tool call deltas across multiple streaming chunks assemble correctly into ToolCallRequest."""
    lines = [
        "data: "
        + json.dumps(
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "call_abc123",
                                    "type": "function",
                                    "function": {"name": "search_tickets", "arguments": ""},
                                }
                            ]
                        }
                    }
                ]
            }
        ),
        "data: "
        + json.dumps(
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [{"index": 0, "function": {"arguments": '{"query":'}}]
                        }
                    }
                ]
            }
        ),
        "data: "
        + json.dumps(
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {"index": 0, "function": {"arguments": ' "transfer delay"}'}}
                            ]
                        }
                    }
                ]
            }
        ),
        "data: "
        + json.dumps(
            {
                "choices": [{"delta": {}, "finish_reason": "tool_calls"}],
                "usage": {
                    "prompt_tokens": 40,
                    "completion_tokens": 15,
                    "total_tokens": 55,
                    "cost": 0.0003,
                },
            }
        ),
        "data: [DONE]",
    ]

    mock_client = MockStreamClient(lines)
    client = OpenRouterClient(api_key="mock-key", http_client=mock_client)

    resp = await client.complete(
        [LLMMessage(role="user", content="Find tickets")],
        model="openai/gpt-5.4",
        role="research",
    )

    assert resp.finish_reason == "tool_calls"
    assert len(resp.tool_calls) == 1
    tc = resp.tool_calls[0]
    assert tc.id == "call_abc123"
    assert tc.function_name == "search_tickets"
    assert tc.arguments == {"query": "transfer delay"}


@pytest.mark.asyncio
async def test_streaming_missing_provider_cost_handling() -> None:
    """Verify that when OpenRouter does not return cost, provider_reported_cost is None and internal estimate is used."""
    from app.integrations.observability.tracer import trace_investigation

    lines = [
        "data: " + json.dumps({"choices": [{"delta": {"content": "Response without cost."}}]}),
        "data: "
        + json.dumps(
            {
                "choices": [{"delta": {}, "finish_reason": "stop"}],
                "usage": {
                    "prompt_tokens": 20,
                    "completion_tokens": 5,
                    "total_tokens": 25,
                },  # No 'cost' key
            }
        ),
        "data: [DONE]",
    ]

    mock_client = MockStreamClient(lines)
    client = OpenRouterClient(api_key="mock-key", http_client=mock_client)

    tracer = InvestigationTracer(
        investigation_id="inv_test_stream_002", enabled=True, environment="test"
    )
    with trace_investigation(tracer):
        resp = await client.complete(
            [LLMMessage(role="user", content="Hello")],
            model="openai/gpt-5.4",
            role="planner",
        )

    assert resp.content == "Response without cost."
    llm_span = tracer.root_run.child_runs[0]
    meta = llm_span.metadata
    assert meta["provider_reported_cost"] is None
    assert meta["internally_estimated_cost"] is not None
    assert meta["internally_estimated_cost"] > 0.0
    # Canonical usage_metadata falls back to internally_estimated_cost
    assert meta["usage_metadata"]["total_cost"] == meta["internally_estimated_cost"]


@pytest.mark.asyncio
async def test_streaming_finish_reason_length_raises_malformed_output() -> None:
    """Verify that terminal finish_reason == 'length' raises LLMMalformedOutputError (no silent truncation)."""
    lines = [
        "data: " + json.dumps({"choices": [{"delta": {"content": "Incomplete payload"}}]}),
        "data: "
        + json.dumps(
            {
                "choices": [{"delta": {}, "finish_reason": "length"}],
                "usage": {"prompt_tokens": 1024, "completion_tokens": 1024, "total_tokens": 2048},
            }
        ),
        "data: [DONE]",
    ]

    mock_client = MockStreamClient(lines)
    client = OpenRouterClient(api_key="mock-key", http_client=mock_client)

    with pytest.raises(
        LLMMalformedOutputError, match="Model response was truncated: exceeded token budget ceiling"
    ):
        await client.complete(
            [LLMMessage(role="user", content="Hello")],
            model="openai/gpt-5.4",
            role="planner",
        )
