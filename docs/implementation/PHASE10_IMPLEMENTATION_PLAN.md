# Phase 10 Implementation Plan: Application Observability, Token Budgeting & Pipeline Optimisation

## 1. Goal & Objectives
Transform the Pocket AI Product Discovery investigation engine into an observable, resilient, production-grade application service in preparation for the Phase 11 Product Interface.

Following the formal closure of Phase 9 (`EVALUATION_FRAMEWORK_COMPLETE`, `LARGE_BENCHMARK_DEFERRED`), Phase 10 delivers:
1. **Direct-HTTP LangSmith Distributed Tracing**: Explicit custom instrumentation of the direct OpenRouter HTTP execution path and LangGraph workflow using `langsmith.run_trees.RunTree`, establishing hierarchical parent/child spans correlated by `investigation_id`.
2. **Evidence-Based Token Ceilings with No Silent Truncation**: Replace unconstrained 65,536-token model defaults with empirical, role-specific `max_tokens` bounds across the six approved AI roles. Token ceilings are selected from observed structured-output sizes with safety margins, and any `finish_reason == "length"` is treated as an explicit execution failure rather than silently accepting truncation.
3. **Fail-Open Observability Architecture**: Ensure LangSmith network blips, timeouts, or service outages never cause investigation failures, evidence mutations, agent terminations, extra retries, or altered product outputs.
4. **Data Minimization & Redaction**: Enforce strict sanitization of authorization headers, API keys, and customer PII before telemetry dispatch, avoiding raw query dumping in metadata.
5. **Production Application Service & Smoke Test**: Create the authoritative `InvestigationService` application entrypoint and execute **one end-to-end investigation that exercises the approved multi-source workflow across Zendesk, PostHog, and Jira, producing a valid ProductRecommendation**, visible in LangSmith without running large benchmarks.

---

## 2. Locked Architecture & Topology Preservation

Phase 10 strictly preserves the approved technical baseline.

### A. Locked 6-Role Topology
The system contains exactly six logical AI roles:
```text
1. Planner / Orchestrator
2. Research Agent (Customer Support / Zendesk)
3. Analytics Agent (Product Analytics / PostHog)
4. Engineering Agent (Engineering Issues / Jira)
5. PM Synthesis Agent (Evidence Synthesis & Decision Support)
6. Critic Agent (Adversarial Quality Review & Bounded Revision)
```
> [!IMPORTANT]
> **No Assessment Node / Role**:
> All references to an "Assessment" agent, node, budget ceiling, or trace span are completely removed. The pipeline flows directly from parallel specialists into PM Synthesis (or bounded targeted research within specialist boundaries).

### B. Prohibited Architectural Additions
In accordance with `AGENTS.md`:
- **NO** new agents, manager agents, or summarizer agents.
- **NO** RAG, embeddings, or vector databases.
- **NO** long-term agent memory across investigations.
- **NO** Model Context Protocol (MCP).
- **NO** autonomous write capabilities (agents remain 100% read-only).
- **NO** modification to Phase 9 frozen judge prompt (`v3.0-frozen-calibrated`, SHA256: `8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`).

---

## 3. Scope & Non-Goals

### In Scope
* **Direct-HTTP LangSmith Tracing via `RunTree`**:
  - Top-level investigation run (`run_type="chain"`, tagged with `investigation_id`, `environment`, sanitized query).
  - Node spans for Planner, Research, Analytics, Engineering, PM Synthesis, Critic, and PM Revision.
  - Tool spans (`run_type="tool"`) as child runs of the calling specialist.
  - LLM spans (`run_type="llm"`) as child runs of the calling node/agent, capturing model name, latency, token usage, and sanitized payloads.
* **Evidence-Based Token Ceilings**:
  - Explicit configuration of `max_tokens` across all six roles with required role resolution at call sites (no unsafe generic 65,536 fallback).
  - Test verification that every actual role invocation uses its configured budget.
* **Fail-Open Resilience**:
  - Non-blocking asynchronous ingestion; tracing errors caught and logged without raising exceptions.
  - Partial source failure handling: when Zendesk, Jira, or PostHog returns 503 or empty data, the outage is disclosed in `state.limitations` and investigation completes.
* **Observability Data Minimization**:
  - Key-based and regex-based redaction of secrets (`OPENROUTER_API_KEY`, `LANGSMITH_API_KEY`, `POSTHOG_API_KEY`, `JIRA_API_TOKEN`, `ZENDESK_API_KEY`).
  - Metadata limited to operational fields (`investigation_id`, environment, architecture, model).
  - Truncation of large data tables in trace inputs/outputs, retaining evidence identifiers (`zen_*`, `PAY-*`, `analytics:obs_*`).
* **Verification**:
  - Automated test suite for tracing, token bounds, fail-open behavior, and secret redaction.
  - Exactly one multi-source smoke investigation query through the real application entrypoint verified in LangSmith.

### Non-Goals (Explicitly Out of Scope)
* Running large-scale comparative benchmarks or multi-repetition model sweeps.
* Building the web UI frontend (reserved for Phase 11).
* Modifying agent role prompts, rubrics, or deterministic evaluators from Phase 9.
* Conflating runtime application telemetry with Phase 9 evaluation artifacts (LangSmith is runtime observability, not an evaluation prerequisite).

---

## 4. Evidence-Based Token Budgets Across the 6 Roles

### Empirical Baseline Analysis & Truncation Invariants
Measurements of candidate outputs from Phase 9 stress fixtures and valid checkpoint runs reveal the following empirical distributions:

| Role | Output Schema | Min Chars | Mean Chars | Max Chars | Max Observed Tokens | Approved Ceiling (`max_tokens`) | Safety Margin |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Planner** | `InvestigationPlan` | 620 | 880 | 1,150 | ~320 tokens | **1,024** | **3.2x** |
| **2. Research Agent** | Tool Calls & Findings | 450 | 820 | 1,200 | ~340 tokens | **1,536** | **4.5x** |
| **3. Analytics Agent** | Tool Calls & Findings | 480 | 850 | 1,250 | ~360 tokens | **1,536** | **4.3x** |
| **4. Engineering Agent** | Tool Calls & Findings | 510 | 890 | 1,300 | ~370 tokens | **1,536** | **4.1x** |
| **5. PM Synthesis Agent** | `ProductRecommendation` | 806 | 1,262 | 1,935 | ~552 tokens | **2,560** | **4.6x** |
| **6. Critic Agent** | `CriticReview` | 750 | 1,100 | 1,450 | ~415 tokens | **1,536** | **3.7x** |

### Rationale & Guarantees
1. **Reservation Cost Elimination**: The maximum reservation on ANY request is 2,560 tokens (costing $0.0384 at $15/1M tokens). This permanently prevents OpenRouter HTTP 402 ("Payment Required") errors.
2. **No Silent Truncation**: Token ceilings are selected from observed structured-output sizes with safety margins, and any `finish_reason == "length"` is treated as an explicit execution failure (`LLMMalformedOutputError`) rather than silently accepting truncation.
3. **No Unsafe Generic Default**: Every agent and node invocation explicitly passes its configured role budget (`role="planner"`, `role="pm"`, etc.) resolved through `get_max_tokens_for_role(role)`. No request can fall back to 65,536 tokens.

---

## 5. Direct-HTTP LangSmith Tracing Architecture

Because `OpenRouterClient` communicates directly via HTTP (`httpx.AsyncClient`), it does not automatically inherit LangChain callback hooks. We implement an explicit, lightweight tracing module using `langsmith.run_trees.RunTree` (verified API in installed `langsmith 0.12.5`).

### Hierarchy & Span Model
```text
Root RunTree: investigation_workflow [chain]
  ├── Metadata: investigation_id, environment, model
  │
  ├── Span: planner [chain]
  │     └── Span: openrouter_completion [llm] (model, tokens, latency)
  │
  ├── Parallel Specialist Spans:
  │     ├── Span: research_agent [chain]
  │     │     ├── Span: search_tickets [tool] (sanitized params, ticket count)
  │     │     └── Span: openrouter_completion [llm]
  │     ├── Span: analytics_agent [chain]
  │     │     ├── Span: query_analytics [tool] (query, series count)
  │     │     └── Span: openrouter_completion [llm]
  │     └── Span: engineering_agent [chain]
  │           ├── Span: search_issues [tool] (jql, issue keys)
  │           └── Span: openrouter_completion [llm]
  │
  ├── Span: pm_synthesis [chain]
  │     └── Span: openrouter_completion [llm] (model, tokens, latency)
  │
  └── Span: critic [chain]
        └── Span: openrouter_completion [llm] (verdict, points, latency)
```

### Fail-Open Implementation Pattern
Every tracing operation is encapsulated within a fail-open execution wrapper:
```python
class InvestigationTracer:
    """Manages hierarchical RunTree spans with strict fail-open guarantees."""

    def __init__(self, investigation_id: str, query: str, enabled: bool = True):
        self.investigation_id = investigation_id
        self.enabled = enabled
        self.root_run: RunTree | None = None
        if self.enabled:
            try:
                self.root_run = RunTree(
                    name="investigation_workflow",
                    run_type="chain",
                    inputs={"investigation_id": investigation_id},
                    extra={"metadata": {"investigation_id": investigation_id, "environment": "production"}},
                    tags=["pocket_investigation", "production"],
                )
                self.root_run.post()
            except Exception as exc:
                logger.warning("LangSmith root trace initiation failed (fail-open): %s", exc)
                self.root_run = None
```
If LangSmith is unreachable, `self.root_run` safely degrades to `None` and all child span operations are no-ops. Tracing errors never mutate state, fail investigations, or cause extra retries.

---

## 6. Observability Data Minimization & Secret Redaction

### Redaction Rules
1. **Strict Key Denylist**: Any key matching `api_key`, `token`, `authorization`, `secret`, `password`, `bearer` is completely replaced with `[REDACTED]`.
2. **Regex Secret Scrubbing**: All input/output strings are scanned for patterns matching known API key prefixes (`sk-or-v1-*`, `lsv2_pt_*`, `phc_*`, `phx_*`) and redacted.
3. **Metadata Sanitization**: Full raw queries are excluded from high-level metadata; metadata is restricted to `investigation_id`, environment, architecture, and model.
4. **Payload Compaction**: Large tool responses are summarized into record counts and primary identifiers (`zen_*`, `PAY-*`, `analytics:obs_*`).

---

## 7. Proposed Code Changes

### A. Configuration & Token Bounding
#### [MODIFY] [settings.py](../../app/config/settings.py)
* Add explicit role-specific token ceilings:
  * `planner_max_tokens: int = 1024`
  * `research_max_tokens: int = 1536`
  * `analytics_max_tokens: int = 1536`
  * `engineering_max_tokens: int = 1536`
  * `pm_max_tokens: int = 2560`
  * `critic_max_tokens: int = 1536`
* Expose helper `get_max_tokens_for_role(role: str) -> int`.
* Ensure LangSmith environment variables (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT`) are automatically populated.

#### [MODIFY] [client.py](../../app/integrations/llm/client.py)
* Require `role: str` or explicit `max_tokens: int` on `complete()` and `complete_structured()`.
* Include `max_tokens` in the OpenRouter HTTP payload.
* If `finish_reason == "length"`, raise explicit `LLMMalformedOutputError("Response truncated: model exceeded max_tokens budget")`.

---

### B. Direct-HTTP LangSmith Tracing Module
#### [NEW] [tracer.py](../../app/integrations/observability/tracer.py)
* Implement `InvestigationTracer` and `SpanContext` using verified `langsmith.run_trees.RunTree` APIs (`create_child()`, `post()`, `patch()`).
* Implement `sanitize_payload(data: Any) -> Any` with recursive secret redaction and payload compaction.
* Enforce strict fail-open wrappers around all tracing calls.

---

### C. Node & Graph Instrumentation
#### [MODIFY] [graph.py](../../app/orchestration/graph.py)
* Cleanly remove all obsolete `assessment` node terminology and references.
* Connect parallel specialist outputs directly to PM synthesis via join barrier.
* Attach `InvestigationTracer` to execution context and pass span handles to nodes.

#### [MODIFY] [specialists.py](../../app/orchestration/nodes/specialists.py)
* Instrument `ResearchNode`, `AnalyticsNode`, and `EngineeringNode` with child spans under the root trace.
* Pass configured role `max_tokens` to specialist agent completion calls.

#### [MODIFY] [pm_synthesis.py](../../app/orchestration/nodes/pm_synthesis.py) & [critic_node.py](../../app/orchestration/nodes/critic_node.py)
* Instrument PM Synthesis and Critic review execution with child spans.
* Use `pm_max_tokens` (2,560) and `critic_max_tokens` (1,536).

#### [MODIFY] [base.py (tools)](../../app/tools/base.py)
* Create `tool` run spans under the calling specialist span with sanitized parameters and execution latency.

---

### D. Production Service Entrypoint
#### [NEW] [service.py](../../app/orchestration/service.py)
* Production application service: `InvestigationService` and `run_investigation(query: str, investigation_id: str | None = None) -> InvestigationState`.
* Initializes clients, adapters, registry, agents, and graph.
* Coordinates `InvestigationTracer` lifecycle and produces final validated `ProductRecommendation`.

---

### E. Automated Test Suite
#### [NEW] [test_observability_tracing.py](../../tests/observability/test_observability_tracing.py)
* Test 1: Verify `RunTree` span hierarchy and parent-child linkage in isolated test.
* Test 2: Verify `investigation_id` correlation across all spans.
* Test 3: Verify secret redaction (API keys and auth headers replaced with `[REDACTED]`).
* Test 4: Verify fail-open resilience when LangSmith endpoint is invalid (`https://127.0.0.1:9999`) — investigation completes with 100% success.
* Test 5: Verify explicit role-specific `max_tokens` is sent in OpenRouter payloads and no call sends unconstrained 65,536 tokens.
* Test 6: Verify `finish_reason == "length"` raises explicit `LLMMalformedOutputError`.

#### [NEW] [test_smoke_investigation_trace.py](../../tests/observability/test_smoke_investigation_trace.py)
* Executes **one end-to-end investigation through `InvestigationService` that exercises the approved multi-source workflow across Zendesk, PostHog, and Jira, producing a valid ProductRecommendation**.
* Verifies all 13 smoke checklist items.

---

## 8. Verification Plan & Test Commands

### 1. Automated Unit & Integration Tests
```powershell
# Run existing evaluation unit tests (regression check: must remain 42 passed)
.\.venv\Scripts\pytest tests/evaluations/ -q

# Run new observability, token bounding, and fail-open tests
.\.venv\Scripts\pytest tests/observability/test_observability_tracing.py -v
```

### 2. Live Smoke Investigation Query via Production Service
```powershell
# Run the single multi-source smoke investigation query
.\.venv\Scripts\pytest tests/observability/test_smoke_investigation_trace.py -v -s
```

### 3. Smoke Investigation Verification Checklist
- [ ] Invokes `InvestigationService` application entrypoint.
- [ ] Planner node executes and forms multi-source plan.
- [ ] Research Agent executes and queries Zendesk mock.
- [ ] Analytics Agent executes and queries PostHog project.
- [ ] Engineering Agent executes and queries Jira MockServer.
- [ ] PM Synthesis executes and produces a valid `ProductRecommendation`.
- [ ] Critic Agent executes review and issues verdict.
- [ ] Evidence provenance is preserved across all 3 source systems.
- [ ] LangSmith trace exists in project `Multi-Agent-Product-Discovery-Team`.
- [ ] Trace hierarchy is valid (`investigation_workflow` -> `planner`, `research`, `analytics`, `engineering`, `pm_synthesis`, `critic`).
- [ ] Every span contains matching `investigation_id` metadata.
- [ ] Exactly 0 HTTP 402 errors occur during execution.
- [ ] 0 API keys, bearer tokens, or sensitive credentials appear in trace inputs/outputs.

---

## 9. Acceptance Criteria & Phase 10 Completion Gate

Phase 10 is complete ONLY when all 10 criteria are satisfied:
1. **All existing tests pass**: 42/42 evaluation tests in `tests/evaluations/` continue to pass.
2. **New observability tests pass**: All tests in `tests/observability/test_observability_tracing.py` pass.
3. **Frozen prompt SHA invariant**: `JUDGE_SYSTEM_PROMPT` SHA256 remains `8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`.
4. **Smoke investigation success**: Exactly one genuine multi-source end-to-end investigation succeeds across Zendesk, PostHog, and Jira via `InvestigationService`.
5. **LangSmith visibility**: The smoke investigation is confirmed visible in LangSmith with the approved root-to-leaf span hierarchy.
6. **Direct-HTTP LLM traceability**: Direct HTTP LLM calls are traced with model name, latency, and token counters.
7. **Fail-open verified**: Investigation executes successfully even when LangSmith network connection is blocked.
8. **Token bounds enforced**: No HTTP 402 errors occur; every call sends bounded `max_tokens` (1,024 to 2,560).
9. **Zero secrets exposed**: Automated redaction tests verify no API keys or credentials leak into telemetry.
10. **Phase 10 Completion Report**: `docs/implementation/PHASE10_COMPLETION_REPORT.md` is created and documents the implementation, token bounds, and smoke trace URL.

---

## 10. Execution Plan Steps

1. Update `app/config/settings.py` with role-specific token ceilings and LangSmith configuration.
2. Update `app/integrations/llm/client.py` with required role budget resolution and `finish_reason == "length"` exception handling.
3. Implement `app/integrations/observability/tracer.py` using verified `langsmith.run_trees.RunTree` APIs with fail-open wrappers and secret redaction.
4. Implement unit tests in `tests/observability/test_observability_tracing.py` and verify isolated tracer behavior.
5. Create `app/orchestration/service.py` (`InvestigationService`) as the production application entrypoint.
6. Instrument `app/orchestration/graph.py`, nodes, agents, and tools with tracer spans.
7. Run all evaluation unit tests (ensure 42/42 PASS).
8. Run the single multi-source application smoke investigation (`test_smoke_investigation_trace.py`).
9. Verify LangSmith trace and create `docs/implementation/PHASE10_COMPLETION_REPORT.md`.
