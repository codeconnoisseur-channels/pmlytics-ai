# Streaming & TTFT Compatibility and Architectural Design Analysis

**Document Version:** 1.0  
**Date:** 2026-09-17  
**Status:** PROPOSED (Pending Review - Phase 10 Observability Defect Resolution)  
**Author:** AI Engineering & Architecture Team  

---

## 1. Executive Summary

This document presents a comprehensive compatibility and architectural design analysis regarding whether Server-Sent Events (SSE) streaming can be safely introduced into `OpenRouterClient` to achieve genuine **Time To First Token (TTFT)** measurement without destabilizing existing agent contracts, structured JSON outputs, tool calling, retry semantics, or truncation protections.

### Key Findings:
1. **Zero Role Dependency on Non-Streamed Wire Buffering:** None of the six approved logical AI roles (Planner, Research, Analytics, Engineering, PM, Critic) consume or require raw non-streamed HTTP wire buffering. Crucially, **all roles require fully assembled, complete responses** before executing tools, validating Pydantic models, or executing state transitions.
2. **Safe Wire-Level Streaming Adapter:** Streaming can be introduced cleanly and safely **strictly within `OpenRouterClient.complete()`**. By accumulating streaming deltas (content and tool calls) into the existing, frozen `LLMResponse` dataclass, the entire downstream agent layer (`complete_structured`, `PlannerNode`, `BaseSpecialistAgent`, `PMAgent`, `CriticAgent`) remains 100% untouched.
3. **True TTFT Measurement:** By recording the exact wall-clock timestamp of the request dispatch (`t_request_start`) and the arrival timestamp of the first non-empty content or tool-call delta (`t_first_token`), true `ttft_seconds = t_first_token - t_request_start` can be measured with millisecond precision without approximation or faking.
4. **Dual Cost Accounting:** OpenRouter-reported usage/cost can be captured from the terminal stream chunk (`stream_options: {"include_usage": true}`) and stored alongside the internal pricing snapshot estimate (`2026-09-01-frozen`), clearly distinguishing `provider_reported_cost` from `internally_estimated_cost`.

---

## 2. Agent Response Architecture & Role Inspection

An exhaustive audit of the six logical AI roles in the Pocket architecture was conducted to determine how each role consumes LLM completions:

### 2.1 Planner Node (`app/orchestration/nodes/planner.py`)
- **Invocation Pattern:** Calls `self.llm.complete_structured(messages, model, response_model=InvestigationPlan, role="planner")`.
- **Consumption Requirement:** The planner validates the complete JSON text against the `InvestigationPlan` Pydantic model. It requires the complete plan (task list, required sources, diagnostic questions) before dispatching work to specialists.
- **Streaming Impact:** Because `complete_structured()` awaits the accumulated string from `complete()` before validating JSON, streaming the underlying HTTP chunks has zero impact on the planner's validation logic or repair loop.

### 2.2 Domain Specialists: Research, Analytics, Engineering (`app/agents/base.py`)
Specialists operate in two sequential phases:
1. **Bounded Tool-Selection Loop:**
   - **Invocation Pattern:** Calls `self.llm.complete(messages, model, tools=tools_def, role=self.role)`.
   - **Consumption Requirement:** The specialist inspects `response.tool_calls`. For each requested tool call, it validates the arguments against Pydantic input schemas (`SearchTicketsInput`, `QueryAnalyticsInput`, `SearchIssuesInput`, etc.) and executes the tool via `RoleBoundToolset`.
   - **Streaming Impact:** Tools cannot execute on partial arguments. Streaming tool-call deltas require accumulating argument fragments by index until the stream ends. Once accumulated into `ToolCallRequest(id, function_name, arguments)`, the specialist execution loop receives the exact same structure as a non-streamed response.
2. **Evidence-Grounded Final Structured Synthesis:**
   - **Invocation Pattern:** Calls `self.llm.complete_structured(synthesis_messages, model, response_model=self.result_model_type, role=self.role)`.
   - **Consumption Requirement:** The synthesis response is validated into `SpecialistResult[Finding]` and verified against the authoritative `EvidenceLedger`.
   - **Streaming Impact:** The ledger validator checks the finalized finding and evidence references. Accumulating streamed text before validation preserves 100% compatibility.

### 2.3 PM Synthesis & Revision Agent (`app/agents/pm.py`)
- **Invocation Pattern:**
  - Initial Synthesis: `self.llm.complete_structured(messages, model, response_model=ProductRecommendation, role="pm")`.
  - Revision: `self.llm.complete_structured(messages, model, response_model=ProductRecommendation, role="pm")`.
- **Consumption Requirement:** The PM agent validates the synthesized or revised `ProductRecommendation` schema (problem statement, factual observations, inferences, evidence citations, confidence, success metrics, risks).
- **Streaming Impact:** Both synthesis and revision operate on the complete recommendation model. Underlying streaming deltas are assembled before Pydantic parsing, causing no deviation in PM behavior.

### 2.4 Critic Agent (`app/agents/critic.py`)
- **Invocation Pattern:** Calls `self.llm.complete_structured(messages, model, response_model=CriticReview, role="critic")`.
- **Consumption Requirement:** Validates `CriticReview` structure and executes `_validate_critic_review()` to ensure ledger ID consistency and enforce decision invariants (`PASS` requires zero issues; `REVISE` requires >= 1 issue).
- **Streaming Impact:** The adversarial validation runs exclusively on the completed `CriticReview` object. Streaming deltas accumulated into JSON do not alter the validation rules.

---

## 3. Detailed Compatibility Analysis

| Capability / Concern | Current Non-Streaming Implementation | Streaming (SSE) Implementation | Compatibility Assessment |
|---|---|---|---|
| **Structured Outputs (`complete_structured`)** | Strips markdown fences from `response.content`, runs `model_validate_json`, falls back to `raw_decode`. | Aggregates all streamed `content` deltas into a single string, then executes the exact same fence-stripping and `model_validate_json`. | **100% Compatible.** Downstream code sees identical string input. |
| **Tool Calling & Arguments** | `choice["message"]["tool_calls"]` parsed from single JSON response. | Streamed deltas aggregated across chunks by `index`. Argument fragments concatenated and parsed with `json.loads` upon stream completion. | **100% Compatible.** Standard OpenAI SSE tool accumulation pattern. |
| **Finish Reason Handling** | Inspects `choice["finish_reason"]`. If `"length"`, raises `LLMMalformedOutputError`. | Captures `finish_reason` from the terminal chunk. If `"length"`, raises identical `LLMMalformedOutputError`. | **100% Compatible.** Preserves strict guarantee against silent truncation. |
| **Token Budget Ceilings (`max_tokens`)** | Sent in HTTP JSON payload (`payload["max_tokens"] = resolved_max_tokens`). | Sent in identical HTTP JSON payload (`payload["max_tokens"] = resolved_max_tokens`). Provider enforces ceiling mid-stream. | **100% Compatible.** Role-based bounds remain strictly enforced. |
| **Retry & Error Semantics** | Retries on `httpx.TimeoutException`, `httpx.RequestError`, 429, and 402 backoff. | Retries on connection errors, timeout, mid-stream disconnects (`httpx.RemoteProtocolError`), 429, and 402 backoff. | **100% Compatible.** If a stream drops mid-flight, the attempt is discarded and retried up to `max_retries`. |
| **Concurrency & Credit Protection** | Controlled via `asyncio.Semaphore(1)` per client instance. | Same `asyncio.Semaphore(1)` wraps the streaming session, ensuring serial execution and zero credit race conditions. | **100% Compatible.** |
| **PM / Critic Bounded Loops** | Bounded repair loops (max 3 calls) handle schema errors or validation failures. | Schema errors continue to trigger the same bounded repair loops because exceptions are raised after full JSON assembly. | **100% Compatible.** |
| **Fail-Open Tracing** | Tracing errors caught in try/except without failing the client. | Stream timing and span management wrapped in fail-open try/except. Tracing failures never abort the stream. | **100% Compatible.** |

---

## 4. Proposed Streaming & Telemetry Architecture

### 4.1 Wire-Level Streaming Mechanics (`OpenRouterClient.complete`)
```python
# 1. Request Configuration
payload["stream"] = True
payload["stream_options"] = {"include_usage": True}

# 2. Timing Variables
t_start = time.perf_counter()
t_first_token: float | None = None

# 3. Accumulation Buffers
content_fragments: list[str] = []
tool_calls_accumulator: dict[int, dict[str, Any]] = {}
finish_reason: str = "stop"
usage_dict: dict[str, Any] | None = None
model_used: str = model

# 4. SSE Stream Processing
async with client.stream("POST", url, headers=headers, json=payload) as res:
    # Check status codes (401, 403, 429, 402, 500)
    ...
    async for line in res.aiter_lines():
        if not line.startswith("data: "):
            continue
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            break
        
        chunk = json.loads(data_str)
        # Capture model if reported
        if "model" in chunk:
            model_used = chunk["model"]
            
        # Capture usage if included in chunk
        if "usage" in chunk and chunk["usage"]:
            usage_dict = chunk["usage"]
            
        choices = chunk.get("choices", [])
        if not choices:
            continue
            
        choice = choices[0]
        if choice.get("finish_reason"):
            finish_reason = choice["finish_reason"]
            
        delta = choice.get("delta", {})
        
        # Check for first token (content or tool call)
        if t_first_token is None:
            if delta.get("content") or delta.get("tool_calls"):
                t_first_token = time.perf_counter()
                
        # Accumulate text content
        if delta.get("content"):
            content_fragments.append(delta["content"])
            
        # Accumulate tool calls by index
        if delta.get("tool_calls"):
            for tc_delta in delta["tool_calls"]:
                idx = tc_delta.get("index", 0)
                if idx not in tool_calls_accumulator:
                    tool_calls_accumulator[idx] = {
                        "id": tc_delta.get("id", ""),
                        "name": tc_delta.get("function", {}).get("name", ""),
                        "arguments": tc_delta.get("function", {}).get("arguments", ""),
                    }
                else:
                    if tc_delta.get("id"):
                        tool_calls_accumulator[idx]["id"] = tc_delta["id"]
                    if tc_delta.get("function", {}).get("name"):
                        tool_calls_accumulator[idx]["name"] += tc_delta["function"]["name"]
                    if tc_delta.get("function", {}).get("arguments"):
                        tool_calls_accumulator[idx]["arguments"] += tc_delta["function"]["arguments"]

t_end = time.perf_counter()
total_latency = t_end - t_start
ttft = (t_first_token - t_start) if t_first_token is not None else None
```

### 4.2 Handling Truncation
```python
if finish_reason == "length":
    logger.error(
        "Model completion truncated due to token budget ceiling: model=%s, max_tokens=%d",
        model,
        resolved_max_tokens,
    )
    raise LLMMalformedOutputError(
        f"Model response was truncated: exceeded token budget ceiling of {resolved_max_tokens} tokens. "
        f"Silent truncation is prohibited."
    )
```

### 4.3 Tool Call Finalization
```python
parsed_tcs: list[ToolCallRequest] = []
for idx in sorted(tool_calls_accumulator.keys()):
    tc_info = tool_calls_accumulator[idx]
    raw_args = tc_info["arguments"]
    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    except Exception:
        args = {}
    parsed_tcs.append(
        ToolCallRequest(
            id=tc_info["id"] or f"call_{idx}",
            function_name=tc_info["name"],
            arguments=args,
        )
    )
```

### 4.4 Dual Usage and Cost Telemetry
OpenRouter responses may report provider usage and cost, or omit cost. We capture both explicitly without conflation:
1. **Provider Usage:** Extracted directly from `usage_dict`:
   - `prompt_tokens`: `usage_dict.get("prompt_tokens")`
   - `completion_tokens`: `usage_dict.get("completion_tokens")`
   - `total_tokens`: `usage_dict.get("total_tokens")`
   - `provider_reported_cost`: `usage_dict.get("cost")` (if reported by OpenRouter, otherwise `None`)
2. **Internal Estimated Cost:** Calculated against the frozen snapshot (`PRICING_SNAPSHOT_2026_09_01`):
   - `input_cost = (prompt_tokens / 1_000_000.0) * rate.input_cost_per_million`
   - `output_cost = (completion_tokens / 1_000_000.0) * rate.output_cost_per_million`
   - `total_estimated_cost = input_cost + output_cost`
   - `pricing_snapshot_version = "2026-09-01-frozen"`

### 4.5 LangSmith LLM Span Telemetry Schema
Every LLM call generates a dedicated child span under the active agent node with `run_type="llm"`:
- **Span Name:** `f"llm:{model}"`
- **Inputs:** `{"messages": sanitized_messages, "model": model, "role": role, "max_tokens": resolved_max_tokens, "temperature": temperature}`
- **Outputs:** `{"content": assembled_content, "tool_calls": [...], "finish_reason": finish_reason}`
- **Usage Metadata (LangSmith Canonical):**
  ```python
  usage_metadata = {
      "input_tokens": prompt_tokens,
      "output_tokens": completion_tokens,
      "total_tokens": total_tokens,
      "input_cost": internal_cost["input_cost"],
      "output_cost": internal_cost["output_cost"],
      "total_cost": (
          provider_reported_cost
          if provider_reported_cost is not None
          else internal_cost["total_estimated_cost"]
      ),
  }
  ```
- **Run Metadata:**
  ```python
  metadata = {
      "model": model,
      "model_used": model_used,
      "provider": "openai" if "openai" in model else "anthropic",
      "role": role,
      "total_latency_seconds": round(total_latency, 4),
      "ttft_seconds": round(ttft, 4) if ttft is not None else None,
      "provider_reported_cost": provider_reported_cost,
      "internally_estimated_cost": internal_cost["total_estimated_cost"],
      "pricing_snapshot_version": "2026-09-01-frozen",
      "investigation_id": tracer.investigation_id,
  }
  ```

---

## 5. Risk Assessment & Defensive Safeguards

1. **Risk: Stream Drops or Incomplete SSE Payloads**
   - *Safeguard:* If a network drop occurs before `[DONE]` or before terminal chunks, `httpx` will raise a connection/protocol error. The existing retry loop catches this, waits with exponential backoff (2s, 4s), and retries the entire request.
2. **Risk: Provider Omits Usage in Stream**
   - *Safeguard:* `"stream_options": {"include_usage": True}` is passed in the request body. If `usage_dict` is still missing from the stream, token counts are not fabricated (`usage_metadata = None`), and `internally_estimated_cost` is marked as unavailable.
3. **Risk: OpenRouter Rate Limits (429) or In-Flight Budget (402)**
   - *Safeguard:* The single-request semaphore (`asyncio.Semaphore(1)`) remains active, preventing concurrent in-flight credit exhaustion. Transient 429/402 responses are handled before stream reading begins.
4. **Risk: Truncation Masked as Stop**
   - *Safeguard:* `finish_reason` is tracked and checked explicitly against `"length"`. If truncated, `LLMMalformedOutputError` is raised immediately.

---

## 6. Implementation Plan & STOP Gate

### Summary of Changes Required Upon Approval:
1. **`app/integrations/llm/pricing.py` [NEW]:** Frozen pricing rates (`openai/gpt-5.4`, `anthropic/claude-sonnet-4.6`, version `2026-09-01-frozen`), cost calculation function.
2. **`app/integrations/llm/client.py` [MODIFY]:** Implement streaming SSE accumulator in `complete()`, calculate true `ttft_seconds`, parse usage/cost, spawn LLM `RunTree` child spans, and attach canonical `UsageMetadata`.
3. **`app/integrations/observability/tracer.py` [MODIFY]:** Support `usage_metadata` and extended metadata on `InvestigationTracer.end_span()`.
4. **`tests/observability/test_observability_tracing.py` [MODIFY]:** Add unit tests for streaming chunk assembly, TTFT calculation, tool call accumulation, token parsing, cost calculation, and fail-open tracing.
5. **`tests/observability/test_smoke_investigation_trace.py` [MODIFY]:** Execute exactly one end-to-end smoke investigation and verify in LangSmith that LLM spans display `input_tokens`, `output_tokens`, `total_tokens`, `ttft_seconds`, `total_latency_seconds`, and cost.

### STOP Gate Notice
In accordance with User Instruction #10:
> **1. complete the streaming compatibility analysis;**  
> **2. persist the analysis;**  
> **3. STOP.**  
> **Do not implement streaming until the compatibility analysis is reviewed.**

Execution is stopped at this gate pending user review and approval of this architectural analysis.
