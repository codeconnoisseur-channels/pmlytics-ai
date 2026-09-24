# Phase 11 Implementation Plan: Product UI & API Server

**Author**: Pocket AI Engineering Team  
**Date**: 2026-09-17  
**Status**: REVISED DRAFT / PENDING REVIEW (Planning Mode Only)  
**Corpus**: `c:/Users/Progressive/Desktop/Multi-Agent Product Discovery System`  

---

## 1. Architectural Framing & Mission

> **Architectural Framing**:  
> Pocket uses a single-process asynchronous FastAPI service for portfolio/demo deployment. `InvestigationService` remains the orchestration boundary, while the frontend is a presentation layer over the existing LangGraph investigation engine. Runtime state is process-local in this phase; durable job execution and persistence are explicitly deferred.

Phase 11 delivers:
1. **Asynchronous HTTP API Server (`app/api/`)**: A single-process FastAPI application exposing structured, typed endpoints for launching investigations (`202 Accepted`), tracking real-time milestone transitions via Server-Sent Events (SSE) and polling, and retrieving structured product recommendations and evidence ledgers.
2. **Interactive Product Management Interface**: A responsive, accessible single-page web interface purpose-built for Product Managers, featuring:
   - Resilient progress tracking with live reconnection across the ~280–290s execution lifecycle.
   - **Explicit Epistemic Distinction Triad**: Visually distinguishing **Observed Facts**, **Analytical Inferences**, and **Testable Hypotheses**.
   - **Structured Evidence Transparency Drawer**: Direct inspection of underlying customer support tickets, telemetry funnels, and engineering context without exposing raw tool payloads or sensitive credentials.
   - **Adversarial Critique & Bounded Revision Card**: Transparent presentation of Critic review outcomes, addressed issues, and revision counts (bounded at 2).
3. **Strict Scope Control**: No authentication, billing, multi-tenancy, message brokers, persistent databases, or autonomous writes.

---

## 2. Background Execution Model & Persistence Limitations

### 2.1 Single-Process Asynchronous Model
- **Mechanism**: Background execution uses process-local `asyncio.create_task` managed by an in-memory `InvestigationManager`.
- **Intended Target**: Portfolio, local evaluation, and demonstration deployments.
- **Explicit Limitations**:
  - **Non-Durable Execution**: If the server process restarts or crashes while an investigation is running, the in-memory task is lost.
  - **Ephemeral History**: Investigation history exists only for the lifetime of the running application process. `GET /api/v1/investigations` lists only recent investigations known to the current process memory.
  - **Single-Worker Topology**: Multiple workers (e.g. `gunicorn -w 4`) are **not** supported by this phase, as in-memory state is not shared across processes.
- **Future Production Note**: Durable job orchestration (e.g. distributed workers, Redis/Postgres job queues, durable persistence) is explicitly recognized as a future production infrastructure concern and is out of scope for Phase 11.

---

## 3. Authoritative Lifecycle Mapping (No Duplicate State Machine)

The approved LangGraph investigation lifecycle remains the single source of truth:
$$\text{DRAFT} \longrightarrow \text{SUBMITTED} \longrightarrow \text{PLANNING} \longrightarrow \text{INVESTIGATING} \longrightarrow \text{SYNTHESISING} \longrightarrow \text{CRITIQUING} \longrightarrow \text{REVISING} \longrightarrow \text{COMPLETED}$$

The API derives its presentation-friendly statuses directly from the underlying graph state without maintaining an independent state machine:

| LangGraph Workflow State | API Presentation Status (`status`) | UI Stage Label |
|---|---|---|
| `InvestigationLifecycle.SUBMITTED` | `pending` | "Queued for investigation" |
| `InvestigationLifecycle.PLANNING` | `planning` | "Formulating investigation plan" |
| `InvestigationLifecycle.INVESTIGATING` | `gathering_evidence` | "Specialists querying Zendesk, PostHog, Jira" |
| `InvestigationLifecycle.SYNTHESISING` | `synthesizing` | "PM synthesizing multi-source evidence" |
| `InvestigationLifecycle.CRITIQUING` | `reviewing` | "Critic evaluating recommendation for causal overreach" |
| `InvestigationLifecycle.REVISING` | `revising` | "PM revising recommendation (Iteration $N$/2)" |
| `InvestigationLifecycle.COMPLETED` | `completed` | "Investigation complete" |
| Internal execution error | `failed` | "Investigation encountered an error" |
| Explicit cancellation (if invoked) | `cancelled` | "Investigation cancelled" |

---

## 4. Product Workflow & Long-Running UX Design

### 4.1 Submission & Validation (No Arbitrary Minimum Length)
- **Input Validation**:
  - `user_query` is required.
  - Must be non-empty after trimming: `len(user_query.strip()) > 0`.
  - Maximum length: 2,000 characters.
  - Concise questions (e.g., *"Churn?"*, *"Why are transfers failing?"*) are fully valid and accepted.
- **Duplicate Prevention**:
  - UI disables the submit button immediately upon form submission and generates or receives a unique `investigation_id`.
  - The browser updates its URL to `/?investigation_id=inv_...` using `history.pushState()`.
  - Reloading or refreshing the browser retains the existing `investigation_id` and reconnects rather than launching a duplicate run.

### 4.2 SSE Reconnection & State Recovery
Given the ~280–290s baseline duration, client connections may drop or users may refresh their browser.
- **Server-Side State Reconstruction**:
  - The `InvestigationManager` tracks the current state, active role, elapsed time, and event history for each active `investigation_id`.
  - When an SSE client connects or reconnects to `/api/v1/investigations/{id}/events`:
    1. The endpoint checks `manager.get(id)`. If not found, returns `404 Not Found`.
    2. Immediately emits an initial `snapshot` event with current status, active role, elapsed duration, and completed stages.
    3. If the investigation is already `completed` or `failed`, emits the final event (`complete` or `failed`) and closes the stream cleanly.
    4. If still running, subscribes the client to live progress queue events until completion.
  - Reconnection is completely idempotent and **never** creates or triggers duplicate execution.

### 4.3 Client-Side Authoritative Pattern
- UI never executes orchestration logic or polling-only state mutations.
- The UI workflow:
  1. Submits question once via `POST /api/v1/investigations`.
  2. Receives `202 Accepted` with `investigation_id`.
  3. Connects to `/api/v1/investigations/{id}/events`.
  4. If SSE fails or disconnects, falls back to polling `GET /api/v1/investigations/{id}` every 3 seconds.
  5. When status is `completed`, fetches full typed payload from `GET /api/v1/investigations/{id}/result` once.

---

## 5. API Design & Error Semantics (`app/api/`)

### 5.1 Technology Stack & Directory Structure
- **Framework**: `FastAPI` ($\ge 0.111.0$) with `uvicorn` ASGI server.
- **Package Layout**:
```text
app/api/
├── __init__.py
├── main.py              # FastAPI app factory, CORS, static mounts, error handlers, lifespan
├── routes.py            # Route handlers for /investigations and /health
├── schemas.py           # Pydantic v2 typed request/response models
├── manager.py           # Single-process in-memory InvestigationManager & task tracker
└── dependencies.py      # Dependency injection for InvestigationService and settings
```

### 5.2 Explicit HTTP Status Codes & Error Semantics

| Scenario | HTTP Status | Response Body / Behavior |
|---|---|---|
| Investigation Accepted | `202 Accepted` | Returns `investigation_id`, `status: "pending"`, status & events URLs. |
| Status Poll (In Progress) | `200 OK` | Returns current presentation status, active agent, elapsed timer. |
| Status Poll (Completed) | `200 OK` | Returns `status: "completed"`, `duration_seconds`. |
| Result Retrieval (Completed) | `200 OK` | Returns full typed `InvestigationDetailResponse`. |
| Result Retrieval (Still Running) | `409 Conflict` | Error: `{"detail": "Investigation is still running. Poll status endpoint instead."}` |
| Result Retrieval (Failed) | `502 Bad Gateway` / `500` | Error: `{"detail": "Investigation failed during execution: <reason>"}`. Never returns 200 for execution failures. |
| Invalid / Unknown ID | `404 Not Found` | Error: `{"detail": "Investigation '{investigation_id}' not found."}` |
| Malformed / Empty Query | `422 Unprocessable Entity` | Pydantic validation error: empty string after trim or exceeds 2000 chars. |
| Unexpected Internal Error | `500 Internal Server Error` | Generic sanitized error body with correlation ID. |

### 5.3 Typed Response Schemas & Structured Evidence

The API preserves the typed domain models from `app/domain/` rather than flattening outputs:

```python
class EvidenceLedgerItemSchema(BaseModel):
    ledger_entry_id: str
    source_type: Literal["zendesk", "posthog", "jira"]
    source_reference: str
    finding: str
    support_excerpt: str
    confidence: Literal["high", "medium", "low"]
    retrieved_at: datetime
    # Raw tool payloads, customer PII, and internal secrets are strictly excluded

class StructuredFindingSchema(BaseModel):
    statement: str
    epistemic_type: Literal["fact", "inference", "hypothesis"]
    evidence_ids: list[str] = Field(default_factory=list)

class ProductRecommendationSchema(BaseModel):
    problem_statement: str
    why_it_matters: str
    affected_users: str
    factual_observations: list[StructuredFindingSchema]
    inferences: list[StructuredFindingSchema]
    hypotheses: list[StructuredFindingSchema]
    recommendation: str
    recommendation_type: str
    confidence: Literal["high", "medium", "low"]
    success_metrics: list[str]
    risks: list[str]
    disclosed_limitations: list[str]

class CriticReviewSchema(BaseModel):
    status: Literal["PASS", "REVISE"]
    revisions_completed: int
    critique_summary: str
    issues_addressed: list[str]

class TelemetrySummarySchema(BaseModel):
    investigation_id: str
    trace_id: str | None = None
    llm_calls: int
    total_tokens: int
    provider_reported_cost: float | None = None
    internally_estimated_cost: float | None = None

class InvestigationDetailResponse(BaseModel):
    investigation_id: str
    user_query: str
    status: str
    duration_seconds: float
    recommendation: ProductRecommendationSchema
    evidence_ledger: dict[str, EvidenceLedgerItemSchema]  # keyed by ledger_entry_id
    critic_review: CriticReviewSchema
    telemetry_summary: TelemetrySummarySchema
```

### 5.4 Sanitized Health Endpoint (`GET /api/v1/health`)
- **Safety**: Does **not** expose API keys, provider credentials, project IDs, or environment variable values.
- **Scope**:
  - `status`: `"ok"` / `"degraded"`
  - `process`: `"healthy"`
  - `investigation_service`: `true` / `false`
  - `active_investigations_count`: integer
  - `dependencies`:
    - `openrouter_configured`: boolean (`bool(settings.openrouter_api_key)`)
    - `posthog_configured`: boolean (`bool(settings.posthog_api_key)`)
    - `mock_zendesk_reachable`: boolean
    - `mock_jira_reachable`: boolean
- **Fail-Open Observability**: LangSmith reachability is **not** a requirement for healthy status, as tracing is fail-open.

### 5.5 Configurable CORS
- Does **not** default to permissive `*`.
- Default configuration:
  ```python
  cors_origins: list[str] = [
      "http://localhost:8000",
      "http://127.0.0.1:8000",
      "http://localhost:3000",
  ]
  ```
- Reject requests with unexpected `Origin` headers.

---

## 6. UI Design, Accessibility & Evidence Transparency

### 6.1 Design Tokens & Responsive Layout
- **Palette**:
  - Base Obsidian: `#0a0e17`
  - Card Surfaces: `#111827` (elevated `#161f33`)
  - Border Accents: `#243048` (active `#3b82f6`)
  - Epistemic Green (Facts): `#10b981` (bg `#064e3b33`)
  - Epistemic Amber (Inferences): `#f59e0b` (bg `#78350f33`)
  - Epistemic Cyan (Hypotheses): `#06b6d4` (bg `#164e6333`)
  - Critic Rose (Revision/Alert): `#f43f5e` (bg `#88133733`)
  - Primary Indigo CTA: `#6366f1`
- **Typography**: Inter / Outfit sans-serif hierarchy with high WCAG AA contrast (ratio $> 4.5:1$).

### 6.2 Accessibility & Resilience Standards (WCAG AA)
- **Keyboard Navigation**:
  - Full tab-index flow: Input area $\to$ Submit $\to$ Sample query chips $\to$ Epistemic cards $\to$ Evidence drawer.
  - Escape key closes the evidence drawer modal.
  - Enter / Space activates interactive citation chips.
- **Visible States (No Animation-Only Cues)**:
  - Loading / Running state conveys status with explicit text (*"Active Agent: Engineering Agent querying Jira"*), an elapsed timer (*"02:14"*), and an accessible ARIA live region (`aria-live="polite"`).
  - Screen readers are notified on stage transitions.
  - Error states feature high-contrast warning icons with explicit explanation text and a retry button.
  - Empty states guide the user on first load with 3 pre-crafted realistic product discovery queries.

### 6.3 Epistemic Distinction Triad & Structured Evidence Transparency
1. **Facts Column (Observed Reality)**:
   - Statements grounded in verified ledger entries.
   - Each fact renders structured inline badges for linked evidence IDs (e.g. `[ZD#1042]`, `[PH#transfer_failed]`).
2. **Inferences Column (Cross-Source Synthesis)**:
   - Analytical deductions bridging customer symptoms and technical mechanisms.
   - Shows which factual observations support the inference.
3. **Hypotheses Column (Testable Forward Actions)**:
   - Explicitly framed as testable theories, separating what has been observed from what is proposed.
4. **Interactive Evidence Drawer**:
   - Clicking any evidence badge opens the slide-out drawer on the right.
   - Pulls data directly from `evidence_ledger[evidence_id]`:
     - **Source**: `Zendesk Support Ticket`, `PostHog Funnel Telemetry`, or `Jira Issue`
     - **Reference**: Clean ID (e.g. `Ticket #1042`, `Event: transfer_failed`, `Issue: PROD-8821`)
     - **Excerpt**: Verbatim verified excerpt
     - **Confidence & Timestamp**: Explicit confidence badge and ISO timestamp
   - Zero raw HTTP payload dumps or database credentials.

---

## 7. LangSmith Correlation & Data Minimization

- **Trace Correlation**:
  - The API extracts or generates `investigation_id`.
  - Injects `investigation_id` into `InvestigationService.investigate(investigation_id=...)`.
  - `InvestigationTracer` establishes the root `RunTree` tagged with `investigation_id` and metadata `{"source": "fastapi", "runtime": "python"}`.
- **Client Non-Exposure**:
  - `LANGSMITH_API_KEY` is strictly managed server-side.
  - The API response optionally includes a sanitized `trace_id` in `telemetry_summary`.
  - The frontend never depends on LangSmith credentials or private endpoints to render the investigation.

---

## 8. Implementation Steps & File Modifications

### Component 1: Dependencies & Configuration
- **[MODIFY] [`pyproject.toml`](../../pyproject.toml)**: Add `fastapi>=0.111.0` and `uvicorn>=0.30.0`.
- **[MODIFY] [`app/config/settings.py`](../../app/config/settings.py)**: Add `api_host: str = "127.0.0.1"`, `api_port: int = 8000`, and `cors_origins: list[str]`.

### Component 2: API Server Implementation (`app/api/`)
- **[NEW] [`app/api/__init__.py`](../../app/api/__init__.py)**: Package initialization.
- **[NEW] [`app/api/schemas.py`](../../app/api/schemas.py)**: Typed Pydantic v2 schemas:
  - `InvestigationCreateRequest` (validates trimmed non-empty query $\le 2000$ chars)
  - `InvestigationStatusResponse` (derived from LangGraph lifecycle)
  - `InvestigationDetailResponse` (structured recommendation, epistemic triad, evidence ledger, critic review, telemetry)
  - `HealthResponse` (sanitized status, zero credential leakage)
  - `ErrorResponse` (sanitized standard error contract)
- **[NEW] [`app/api/manager.py`](../../app/api/manager.py)**:
  - In-memory `InvestigationManager` wrapping single-process `asyncio.create_task`.
  - Lifecycle derivation mapping LangGraph states to presentation statuses.
  - Reconnection-aware event queues for SSE streaming with initial state snapshot.
  - Safe exception trapping ensuring background failures transition state to `failed` and record error details.
- **[NEW] [`app/api/routes.py`](../../app/api/routes.py)**:
  - `POST /api/v1/investigations` $\to$ `202 Accepted`
  - `GET /api/v1/investigations/{id}` $\to$ `200 OK` (status)
  - `GET /api/v1/investigations/{id}/events` $\to$ `text/event-stream` (SSE)
  - `GET /api/v1/investigations/{id}/result` $\to$ `200 OK` (or `409 Conflict` if still running)
  - `GET /api/v1/investigations` $\to$ `200 OK` (process-local recent investigations)
  - `GET /api/v1/health` $\to$ `200 OK`
- **[NEW] [`app/api/main.py`](../../app/api/main.py)**:
  - FastAPI application factory.
  - CORS middleware with strict configured origins.
  - Static file mounting for the temporary prototype.
  - Standardized JSON exception handlers.

### Component 3: Product Web Interface prototype
- **Semantic HTML5**: ARIA live regions, keyboard accessibility, hero query bar, progress pipeline, epistemic triad cards, and slide-out evidence drawer.
- **Vanilla CSS design system**: Dark slate palette, typography tokens, responsive grid, high-contrast badges, and micro-animations.
- **Vanilla JavaScript client logic**:
  - Single-submission handling and duplicate prevention.
  - URL synchronization (`?investigation_id=...`) and reconnect on page reload.
  - SSE connection handling with polling fallback.
  - Epistemic triad rendering with clickable evidence chips.
  - Evidence drawer modal with escape key navigation.

### Component 4: Test Suite (`tests/api/` & `tests/ui/`)
- **[NEW] `tests/api/test_api_schemas.py`**:
  - Short valid queries (e.g. 5 chars) accepted.
  - Empty or whitespace-only queries rejected (`422`).
  - Overlong queries (>2000 chars) rejected (`422`).
  - Structured evidence mapping validation.
- **[NEW] `tests/api/test_api_routes.py`**:
  - Async HTTP tests via `httpx.AsyncClient`.
  - `POST` returns `202 Accepted` with correct headers.
  - `GET /result` returns `409 Conflict` while running.
  - `GET /result` returns `200 OK` after completion.
  - `GET /result` on failed run returns non-200.
  - Invalid ID returns `404 Not Found`.
  - CORS rejection test for unexpected origins.
- **[NEW] `tests/api/test_investigation_manager.py`**:
  - LangGraph lifecycle mapping verification.
  - Background task exception handling (transitions cleanly to `failed`).
  - Reconnect snapshot event emission.
- **[NEW] `tests/api/test_e2e_api_mock.py`**:
  - Fast end-to-end integration test with mocked `InvestigationService` validating launch $\to$ SSE stream $\to$ result retrieval in $<3$s.
- **Static prototype tests**:
  - Static asset delivery test.
  - Scans client-delivered HTML/CSS/JS ensuring zero API keys or secrets are embedded.

---

## 9. Explicit Completion Gates

| Gate | Acceptance Criteria |
|---|---|
| **Gate 1: API Endpoint Contracts** | `POST` returns `202 Accepted`; short valid queries accepted; whitespace/overlong rejected (`422`); `409 Conflict` on incomplete result query; `404` on unknown ID; zero 200 responses for execution failures. |
| **Gate 2: Lifecycle Mapping** | LangGraph states (`SUBMITTED` $\to$ `PLANNING` $\to$ `INVESTIGATING` $\to$ `SYNTHESISING` $\to$ `CRITIQUING` $\to$ `REVISING` $\to$ `COMPLETED`) cleanly mapped without independent divergent state machine. |
| **Gate 3: SSE Reconnection** | Browser refresh or reconnection receives initial snapshot event without re-triggering execution. |
| **Gate 4: UI Epistemic Distinction** | UI displays **Observed Facts**, **Analytical Inferences**, and **Testable Hypotheses** in three distinct visual sections. |
| **Gate 5: Evidence Transparency** | Clicking cited badges displays sanitized ledger excerpts in slide-out drawer with zero raw tool dumps or credential leaks. |
| **Gate 6: Health & CORS Security** | `GET /health` reports service readiness without exposing keys/tokens; CORS rejects unexpected origins. |
| **Gate 7: Accessibility & UX** | Keyboard navigable, ARIA live progress updates, visible non-animation state cues, responsive dark theme. |
| **Gate 8: Regression Immutability** | All 55 Phase 9 and 10 tests continue to pass; frozen judge prompt SHA (`8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`) remains bit-for-bit unchanged. |

---

## 10. Planning Gate: STOP

**Execution is halted.**  
No source code, dependencies, or UI files have been modified.  
This revised implementation plan is submitted for your final review and approval before implementation begins.
