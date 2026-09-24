"""Unit tests verifying OpenRouterClient request formatting, parsing, and error mapping."""

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from app.domain.evidence import Evidence, EvidenceConfidence
from app.domain.specialists import CustomerFinding, SpecialistResult
from app.integrations.llm.client import (
    LLMMessage,
    OpenRouterClient,
)
from app.integrations.llm.exceptions import (
    LLMAuthError,
    LLMError,
    LLMMalformedOutputError,
    LLMRateLimitError,
    LLMTimeoutError,
)


@pytest.mark.asyncio
async def test_complete_formats_payload_and_parses_tool_calls() -> None:
    """Verify complete() constructs correct payload with tools and parses tool calls."""
    mock_http = MagicMock(spec=httpx.AsyncClient)

    api_response = {
        "id": "gen-123",
        "model": "openai/gpt-5.4",
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "type": "function",
                            "function": {
                                "name": "get_ticket",
                                "arguments": json.dumps({"ticket_id": 101}),
                            },
                        }
                    ],
                },
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
    }

    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps(api_response).encode("utf-8"),
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    mock_http.post = AsyncMock(return_value=mock_resp)

    client = OpenRouterClient(api_key="sk-or-test-key", http_client=mock_http)
    messages = [
        LLMMessage(role="system", content="System instruction"),
        LLMMessage(role="user", content="User prompt"),
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_ticket",
                "description": "Fetch ticket",
                "parameters": {"type": "object"},
            },
        }
    ]

    res = await client.complete(messages=messages, model="openai/gpt-5.4", tools=tools)

    assert res.finish_reason == "tool_calls"
    assert res.model_used == "openai/gpt-5.4"
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].id == "call_abc"
    assert res.tool_calls[0].function_name == "get_ticket"
    assert res.tool_calls[0].arguments == {"ticket_id": 101}
    assert res.token_usage == {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70}

    # Verify HTTP request was sent with auth header
    mock_http.post.assert_awaited_once()
    call_kwargs = mock_http.post.call_args[1]
    headers = call_kwargs["headers"]
    assert headers["Authorization"] == "Bearer sk-or-test-key"
    assert headers["HTTP-Referer"] == "https://pocket.app/discovery"
    payload = call_kwargs["json"]
    assert payload["model"] == "openai/gpt-5.4"
    assert len(payload["messages"]) == 2
    assert payload["tools"] == tools


@pytest.mark.asyncio
async def test_complete_structured_parses_model_output() -> None:
    """Verify complete_structured() strips code fences and parses into validated Pydantic model."""
    mock_http = MagicMock(spec=httpx.AsyncClient)

    ev = Evidence(
        ledger_entry_id="led_001",
        source_type="zendesk",
        source_reference="ticket_id:101",
        finding="Customer reported transfer pending",
        support="ticket.description: 'pending'",
        confidence=EvidenceConfidence.HIGH,
    )
    finding = CustomerFinding(
        finding="Transfer pending observed",
        facts=["Ticket 101 description notes pending"],
        interpretations=["Transfer was delayed"],
        evidence=[ev],
        confidence=EvidenceConfidence.HIGH,
        observed_pattern="delay",
    )
    result_obj = SpecialistResult[CustomerFinding](
        agent_role="research",
        findings=[finding],
        overall_facts=["Fact"],
        overall_interpretations=["Interp"],
        tool_call_count=1,
        llm_call_count=1,
        investigation_complete=True,
    )

    # Wrap in markdown code fence as LLMs sometimes do
    fenced_content = f"```json\n{result_obj.model_dump_json()}\n```"

    api_response = {
        "id": "gen-structured",
        "model": "openai/gpt-5.4",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": fenced_content,
                },
            }
        ],
    }

    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps(api_response).encode("utf-8"),
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    mock_http.post = AsyncMock(return_value=mock_resp)

    client = OpenRouterClient(api_key="sk-or-test-key", http_client=mock_http)
    messages = [LLMMessage(role="user", content="Synthesize findings")]

    parsed = await client.complete_structured(
        messages=messages,
        model="openai/gpt-5.4",
        response_model=SpecialistResult[CustomerFinding],
    )

    assert isinstance(parsed, SpecialistResult)
    assert parsed.agent_role == "research"
    assert len(parsed.findings) == 1
    assert parsed.findings[0].finding == "Transfer pending observed"


@pytest.mark.asyncio
async def test_complete_structured_raises_malformed_error_on_invalid_json() -> None:
    """Verify complete_structured() raises LLMMalformedOutputError on malformed response."""
    mock_http = MagicMock(spec=httpx.AsyncClient)

    api_response = {
        "id": "gen-bad",
        "model": "openai/gpt-5.4",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "This is plain text, not JSON at all.",
                },
            }
        ],
    }

    mock_resp = httpx.Response(
        status_code=200,
        content=json.dumps(api_response).encode("utf-8"),
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    mock_http.post = AsyncMock(return_value=mock_resp)

    client = OpenRouterClient(api_key="sk-or-test-key", http_client=mock_http)
    messages = [LLMMessage(role="user", content="Synthesize findings")]

    with pytest.raises(LLMMalformedOutputError) as exc:
        await client.complete_structured(
            messages=messages,
            model="openai/gpt-5.4",
            response_model=SpecialistResult[CustomerFinding],
        )
    assert "does not conform to schema" in str(exc.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "expected_exception"),
    [
        (401, LLMAuthError),
        (403, LLMAuthError),
        (429, LLMRateLimitError),
        (500, LLMError),
    ],
)
async def test_error_mapping_on_http_statuses(
    status_code: int, expected_exception: type[Exception]
) -> None:
    """Verify HTTP error status codes map to specific LLM exception types."""
    mock_http = MagicMock(spec=httpx.AsyncClient)
    mock_resp = httpx.Response(
        status_code=status_code,
        content=b"Error payload",
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    mock_http.post = AsyncMock(return_value=mock_resp)

    client = OpenRouterClient(api_key="sk-or-test-key", http_client=mock_http)
    messages = [LLMMessage(role="user", content="Hello")]

    with pytest.raises(expected_exception):
        await client.complete(messages=messages, model="openai/gpt-5.4")


@pytest.mark.asyncio
async def test_timeout_maps_to_llm_timeout_error() -> None:
    """Verify httpx.TimeoutException maps to LLMTimeoutError."""
    mock_http = MagicMock(spec=httpx.AsyncClient)
    mock_http.post = AsyncMock(side_effect=httpx.ReadTimeout("Read timed out", request=MagicMock()))

    client = OpenRouterClient(api_key="sk-or-test-key", http_client=mock_http)
    messages = [LLMMessage(role="user", content="Hello")]

    with pytest.raises(LLMTimeoutError) as exc:
        await client.complete(messages=messages, model="openai/gpt-5.4")
    assert "timed out" in str(exc.value)
