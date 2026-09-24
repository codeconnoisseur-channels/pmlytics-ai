# Frontend API Integration Specification: Pocket AI Product Discovery System

**Document Version:** 1.0.0  
**Phase:** 14 (Next.js Frontend Foundation)  
**Status:** Draft / Needs Review  
**Date:** 2026-09-17  
**Author:** AI Product Discovery Engineering Team  

---

## 1. Executive Summary & Authoritative Contract Principles

This specification establishes the communication boundary between the Next.js production frontend and the authoritative FastAPI backend (`app/api/`).

### Integration Invariants
1. **Single Source of Truth:** The backend Pydantic models (`app/api/schemas.py`) and FastAPI route definitions (`app/api/routes.py`) are the sole authoritative contract.
2. **Automated Type Generation:** TypeScript interfaces are **never** manually hand-copied. They are generated directly from FastAPI's OpenAPI 3.1 specification (`http://127.0.0.1:8000/openapi.json`) using `openapi-typescript`.
3. **No Frontend Bypasses:** The frontend connects exclusively to the documented `/api/v1/*` endpoints. It never interacts directly with OpenRouter, LangGraph internals, PostHog, Zendesk, or Jira.
4. **Resilient Streaming with Polling Fallback:** The frontend consumes Server-Sent Events (SSE) for live execution feedback with an automated fallback to status polling if the SSE connection drops or is blocked by intermediate proxies.

---

## 2. API Contract & Endpoint Mapping

All application endpoints are versioned under `/api/v1/`.

```text
FastAPI Endpoints                  Frontend Responsibility / Consumer
─────────────────────────────────────────────────────────────────────────────
POST /api/v1/investigations        → New Inquiry Modal: Form submission & trigger
GET  /api/v1/investigations/{id}   → Fallback lifecycle polling & metadata refresh
GET  /api/v1/investigations/{id}/events → LiveProgressStream: Real-time SSE listener
GET  /api/v1/investigations/{id}/result → Investigation Workspace: Structured synthesis
GET  /api/v1/investigations        → Launchpad & Sidebar: Recent inquiries list
GET  /api/v1/health                → App Shell & System Status Badge
```

---

### 2.1 Investigation Creation (`POST /api/v1/investigations`)

Launches an asynchronous multi-agent investigation.

* **HTTP Method:** `POST`
* **Path:** `/api/v1/investigations`
* **Success Status:** `202 Accepted`
* **Request Payload (`InvestigationCreateRequest`):**
  ```typescript
  export interface InvestigationCreateRequest {
    /** Non-empty, trimmed question (max 2000 characters). */
    user_query: string;
    /** Optional context parameters (e.g. date ranges, targeted tags). */
    context?: Record<string, unknown>;
  }
  ```
* **Response Payload (`InvestigationSummaryResponse`):**
  ```typescript
  export interface InvestigationSummaryResponse {
    investigation_id: string;
    status: "pending" | "planning" | "gathering_evidence" | "synthesizing" | "reviewing" | "revising" | "completed" | "failed" | "cancelled";
    created_at: string; // ISO 8601
    status_url: string;
    events_url: string;
    result_url: string;
  }
  ```
* **Frontend Handling:**
  1. Validate `user_query.trim().length > 0 && length <= 2000` client-side before submission.
  2. On `202 Accepted`, immediately navigate to `/investigations/${response.investigation_id}`.
  3. Pre-seed local cache with the inquiry string and initial status.

---

### 2.2 Live Progress Stream (`GET /api/v1/investigations/{id}/events`)

Streams real-time execution milestones, active agent changes, and completion signals.

* **HTTP Method:** `GET`
* **Path:** `/api/v1/investigations/{id}/events`
* **Media Type:** `text/event-stream`
* **Headers:** `Cache-Control: no-cache`, `Connection: keep-alive`
* **Event Payload Structure:**
  ```typescript
  export interface InvestigationProgressEvent {
    investigation_id: string;
    stage: "planning" | "gathering_evidence" | "synthesizing" | "reviewing" | "revising" | "completed" | "failed";
    status: "in_progress" | "completed" | "failed";
    active_agent?: "planner" | "research" | "analytics" | "engineering" | "pm" | "critic";
    milestone?: string;
    elapsed_seconds: number;
    revision_count?: number;
    error?: string | null;
  }
  ```
* **SSE Event Types:**
  * `initial_state`: Emitted immediately upon connection with the current snapshot.
  * `progress`: Emitted whenever LangGraph transitions nodes or changes active agents.
  * `complete`: Emitted when the investigation finishes successfully.
  * `failed`: Emitted if the investigation raises an unhandled exception.
  * `ping`: Heartbeat sent every 15 seconds to prevent network timeouts.

---

### 2.3 Status Polling (`GET /api/v1/investigations/{id}`)

Lightweight lifecycle poll used as an SSE fallback or for stale tab revalidation.

* **HTTP Method:** `GET`
* **Path:** `/api/v1/investigations/{id}`
* **Success Status:** `200 OK`
* **Response Payload (`InvestigationStatusResponse`):**
  ```typescript
  export interface InvestigationStatusResponse {
    investigation_id: string;
    user_query: string;
    status: "pending" | "planning" | "gathering_evidence" | "synthesizing" | "reviewing" | "revising" | "completed" | "failed" | "cancelled";
    current_stage: string;
    active_agent: string | null;
    revision_count: number;
    elapsed_seconds: number;
    created_at: string;
    completed_at: string | null;
    error: string | null;
  }
  ```

---

### 2.4 Result Retrieval (`GET /api/v1/investigations/{id}/result`)

Retrieves the final structured synthesis, reviewed recommendation, evidence ledger, and telemetry.

* **HTTP Method:** `GET`
* **Path:** `/api/v1/investigations/{id}/result`
* **Status Codes & Semantics:**
  * `200 OK`: Investigation finished; returns complete detail payload.
  * `409 Conflict`: Investigation still executing. Response contains `active_agent` and `elapsed_seconds`.
  * `410 Gone`: Investigation was cancelled.
  * `500 Internal Server Error`: Investigation failed during execution. Detail contains `error`.
  * `404 Not Found`: Investigation ID does not exist in backend memory.
* **Response Payload (`InvestigationDetailResponse`):**
  ```typescript
  export interface InvestigationDetailResponse {
    investigation_id: string;
    user_query: string;
    status: string;
    duration_seconds: number;
    recommendation: ProductRecommendation;
    evidence_ledger: Record<string, EvidenceLedgerItem>;
    critic_review: CriticReview;
    telemetry_summary: TelemetrySummary;
  }

  export interface ProductRecommendation {
    problem_statement: string;
    why_it_matters: string;
    affected_users: string;
    factual_observations: StructuredFinding[];
    inferences: StructuredFinding[];
    hypotheses: StructuredFinding[];
    recommendation: string;
    recommendation_type: string;
    confidence: "high" | "medium" | "low";
    success_metrics: string[];
    risks: string[];
    likely_causes: string[];
    conflicting_evidence: string[];
    disclosed_limitations: string[];
    evidence_citations: StructuredEvidenceCitation[];
  }

  export interface StructuredFinding {
    statement: string;
    epistemic_type: "fact" | "inference" | "hypothesis";
    evidence_ids: string[];
  }

  export interface EvidenceLedgerItem {
    ledger_entry_id: string;
    source_type: "zendesk" | "posthog" | "jira";
    source_reference: string;
    finding: string;
    support_excerpt: string;
    confidence: "high" | "medium" | "low";
    retrieved_at: string;
  }

  export interface CriticReview {
    status: "PASS" | "REVISE";
    revisions_completed: number;
    critique_summary: string;
    issues_addressed: string[];
  }

  export interface TelemetrySummary {
    investigation_id: string;
    trace_id?: string | null;
    llm_calls: number;
    total_tokens: number;
    provider_reported_cost?: number | null;
    internally_estimated_cost?: number | null;
  }
  ```

---

### 2.5 Recent Investigations Listing (`GET /api/v1/investigations`)

Returns recent investigations held in backend process memory.

* **HTTP Method:** `GET`
* **Path:** `/api/v1/investigations`
* **Success Status:** `200 OK`
* **Response Payload:** `InvestigationStatusResponse[]`
* **Usage:** Hydrates the workspace sidebar and the recent inquiries list on `/investigations`.
* **Authoritative Boundary & Process-Local Limitation:**
  * Investigation state is process-local on the backend (`InvestigationManager`).
  * Browser refresh retrieves currently available investigations directly from this API endpoint.
  * Backend restart clears process-local investigations by design.
  * Durable cross-session history is deferred to a future persistence phase.
  * **Strict Invariant:** Client-side `localStorage` caching of investigation IDs is explicitly prohibited. No secondary client-side source of truth is permitted.

---

### 2.6 System Health Check (`GET /api/v1/health`)

Provides sanitized dependency readiness.

* **HTTP Method:** `GET`
* **Path:** `/api/v1/health`
* **Success Status:** `200 OK`
* **Response Payload (`HealthResponse`):**
  ```typescript
  export interface HealthResponse {
    status: "ok" | "degraded";
    process: string;
    investigation_service_initialized: boolean;
    active_investigations_count: int;
    dependencies: {
      openrouter: boolean;
      posthog: boolean;
      zendesk_mock: boolean;
      jira_mock: boolean;
      langsmith: boolean;
    };
  }
  ```

---

## 3. TypeScript Type Generation Workflow

To guarantee zero drift between backend and frontend contracts, type definitions are generated automatically from the authoritative FastAPI contract.

### 3.1 Policy & Workflow Rules
1. **Authoritative Contract:** FastAPI `/openapi.json` is the sole authoritative API specification.
2. **Local Generation:** In local development, developers run `npm run generate:api` against the active local backend (`http://127.0.0.1:8000/openapi.json`).
3. **Committed Types:** The generated output (`src/types/api.generated.ts`) is committed directly to the git repository.
4. **CI Verification Gate:** Continuous Integration spins up the backend container, runs type generation, and executes `git diff --exit-code src/types/api.generated.ts`. The pipeline fails if committed types diverge from the active backend schema.
5. **Decoupled Production Build:** The production frontend build (`npm run build`) uses the committed TypeScript types and does **not** require a live running backend container.
6. **No Duplicate OpenAPI Snapshots:** We do not maintain a separate, manually edited OpenAPI static file in the repository unless an isolated deployment constraint strictly demands it in a future phase.

### 3.2 Tooling & Script Configuration
The `frontend/package.json` includes:
```json
{
  "scripts": {
    "generate:api": "openapi-typescript http://127.0.0.1:8000/openapi.json -o src/types/api.generated.ts"
  },
  "devDependencies": {
    "openapi-typescript": "^7.4.0"
  }
}
```

---

## 4. Connection Resilience, Streaming & Error Handling

```text
┌────────────────────────────────────────────────────────┐
│               useInvestigationStream Hook              │
└───────────────────────────┬────────────────────────────┘
                            │
            Open EventSource(/events)
                            │
               ┌────────────┴────────────┐
               │                         │
         Connection OK             Connection Error
               │                         │
      Receive SSE Events         Retry with Backoff (1s, 2s, 4s)
               │                         │
        Stage Updates            If 3 consecutive errors:
               │                         │
       Status === "completed"            ▼
               │                Fallback to Polling
               │             GET /investigations/{id}
               │                (Interval: 3000ms)
               ▼                         │
    Trigger Query Invalidation           │
    GET /result ─────────────────────────┘
```

### 4.1 SSE Connection Lifecycle
1. **Initiation:** When the workspace loads an in-progress investigation, `useInvestigationStream` mounts an `EventSource`.
2. **Auto-Reconnect with Backoff:** If the SSE socket disconnects unexpectedly, the hook attempts reconnection with exponential backoff: 1000ms, 2000ms, 4000ms.
3. **Graceful Degradation:** If 3 consecutive connection attempts fail (e.g. strict corporate proxy terminating long-lived HTTP streams), the hook switches seamlessly to polling `GET /api/v1/investigations/{id}` every 3000ms.
4. **Completion Handoff:** As soon as either the SSE stream or a polling response emits `status === "completed"`, the stream listener disconnects and TanStack Query immediately fetches `/api/v1/investigations/{id}/result`.

### 4.2 HTTP Status Code Matrix & Frontend Behavior

| Status Code | Endpoint | Meaning | UI Presentation / Action |
| :--- | :--- | :--- | :--- |
| `202 Accepted` | `POST /investigations` | Pipeline successfully queued | Navigate to workspace; begin streaming. |
| `200 OK` | `GET /result` | Final synthesis complete | Render elevated recommendation and findings. |
| `400 Bad Request` | `POST /investigations` | Blank or overly long query | Display inline validation error under input. |
| `404 Not Found` | Any | Investigation ID missing | Display 404 screen with "Return to Launchpad" CTA. |
| `409 Conflict` | `GET /result` | Still actively executing | Expected behavior; maintain live progress stream. |
| `410 Gone` | `GET /result` | Investigation was cancelled | Display cancellation notice and restart option. |
| `500 Server Error`| `GET /result` | Pipeline raised an error | Display sanitized failure card with retry action. |
| `503 Unavailable` | `POST /investigations` | Backend unavailable | Toast: *"Discovery engine offline. Please retry shortly."* |

### 4.3 Development Proxy Architecture
* **Local Rewrites:** In local development, `next.config.mjs` configures rewrites:
  ```javascript
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*',
      },
    ];
  }
  ```
* **Integration Boundary:** This proxy is strictly a development and staging integration mechanism to eliminate local browser CORS overhead.
* **Invariant:** It is not an application-level BFF or architectural mediator. FastAPI remains the sole authoritative API boundary.

---

## 5. Summary of Frontend API Client Interface

The frontend encapsulates all network operations in `src/lib/api-client.ts`:

```typescript
export const apiClient = {
  // Investigations
  createInvestigation: (req: InvestigationCreateRequest) => Promise<InvestigationSummaryResponse>,
  getInvestigationStatus: (id: string) => Promise<InvestigationStatusResponse>,
  getInvestigationResult: (id: string) => Promise<InvestigationDetailResponse>,
  listRecentInvestigations: () => Promise<InvestigationStatusResponse[]>,
  
  // Health
  getHealth: () => Promise<HealthResponse>,
};
```

All methods wrap native `fetch`, inject standard JSON headers, set a 15-second network timeout, and format errors into typed exceptions.
