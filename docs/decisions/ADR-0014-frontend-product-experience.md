# ADR-0014: Frontend Product Experience Architecture & Technology Evaluation

## Status
Accepted (Formally Approved)

## Context
In Phase 11, a prototype web interface was implemented using vanilla HTML5, vanilla CSS, and vanilla JavaScript (`app/ui/index.html`, `app/ui/styles.css`, `app/ui/app.js`), served directly by FastAPI via a static files mount.

While this V0 prototype successfully proved end-to-end API integration and browser execution, Phase 13 introduces formal product requirements for:
1. **Multi-Route Information Architecture:** Distinct routes for Launchpad (`/app`), Investigation Workspace (`/app/investigations/:id`), History (`/app/history`), Saved (`/app/saved`), Settings (`/app/settings`), and Shared Briefs (`/share/:token`).
2. **Complex Interactive Evidence UX:** Deep-linking between inline recommendation citation badges and an interactive, searchable, filterable Evidence Ledger drawer.
3. **Session & State Management:** Live SSE streaming catch-up on page refresh, optimistic UI transitions, and client-side caching of past investigations.
4. **Professional Design System & Accessibility:** Strict WCAG 2.1 AA keyboard navigation, focus management, screen-reader live regions, and responsive multi-pane layout.
5. **Executive PDF Export:** Generation of multi-page, publication-grade executive decision briefs.

We evaluate whether to continue extending the vanilla JS/HTML prototype or adopt a component-based frontend framework (React / Next.js), while defining the exact architectural boundary between the frontend and the existing FastAPI backend.

---

## Architectural Boundary & Current-vs-Target Alignment

### 1. Authoritative Backend Boundary
> [!IMPORTANT]
> **Orchestration & Backend Boundary Definition**:
> **The existing FastAPI/LangGraph orchestration architecture remains authoritative and does not require redesign. However, future product capabilities including persistence, authentication, sharing, and export will require additive backend/API capabilities.**
> The frontend redesign itself should initially consume the existing verified API contracts (`/api/v1/investigations`, `/events`, `/result`, `/health`).

### 2. Current Implementation vs. Target Product State
- **Current Backend (Phases 11–12A):**
  - FastAPI + LangGraph stateful multi-agent DAG.
  - Process-local in-memory investigation runtime (`InvestigationManager`).
  - Existing Phase 11 investigation APIs (`POST /api/v1/investigations`, `GET /events` SSE, `GET /result`).
  - Existing `ProductRecommendation` and `EvidenceLedger` typed schemas.
- **Target Product Additions (Phases 13–14):**
  - Modern decoupled frontend application (Next.js / React).
  - Durable investigation history backed by persistent storage.
  - Staged user authentication (Guest demo $\rightarrow$ basic accounts $\rightarrow$ team workspaces).
  - Permanent public/token share links (`/share/:token`).
  - Server-assisted and print-CSS executive PDF export.
  - Organization workspace and account ownership.

---

## Architectural Comparison: Vanilla HTML/JS vs. React / Next.js

| Architectural Concern | Current V0 Prototype (Vanilla JS/HTML) | Modern Web Application (React / Next.js) | Evaluation & Trade-Off |
|---|---|---|---|
| **Client-Side Routing** | No client routing. Relies on URL query parameters (`?investigation_id=...`) on a single monolithic `index.html`. Deep linking to distinct screens is brittle. | Native file-based routing (`app/investigations/[id]/page.tsx`, `app/history/page.tsx`, `share/[token]/page.tsx`) with instant client transitions. | **React/Next.js strongly superior** for multi-screen architecture. |
| **Component Modularity** | Imperative DOM manipulation (`document.getElementById`, `innerHTML += ...`) in an 800-line script. Components cannot be isolated or tested independently. | Declarative, typed component tree (`EvidenceDrawer`, `CitationBadge`, `EpistemicDeck`, `RecommendationCard`, `Stepper`). | **React/Next.js strongly superior** for code maintainability and reuse. |
| **State Synchronization & SSE** | Manual event listeners and mutable global variables. Race conditions when switching between concurrent or past investigations. | Structured hooks (`useInvestigationStream`, `useEvidenceLedger`) with deterministic state reducers and automated reconnection. | **React/Next.js strongly superior** for robust async stream handling. |
| **Design System & Tokens** | Monolithic CSS file with repetitive selector overrides. High risk of CSS drift as screens multiply. | Cohesive design system using TailwindCSS or CSS Modules with structured design tokens and Radix UI primitives. | **React/Next.js strongly superior** for design system scalability. |
| **Accessibility (a11y)** | Manual focus trapping, aria attribute updates, and keyboard handlers require hundreds of lines of error-prone boilerplate. | Headless accessible primitives (Radix UI / Headless UI) provide built-in focus trapping, keyboard navigation, and ARIA out of the box. | **React/Next.js strongly superior** for accessibility compliance. |
| **Backend Coupling** | Monolithically bundled in FastAPI static files folder (`/static`). | Clean decoupling via OpenAPI/Fetch client connecting to the existing FastAPI backend (`http://localhost:8000/api/v1`). | **Identical backend contract preserved**. |

---

## Decision
We propose building the target frontend as a modern **React / Next.js** application located in a dedicated `frontend/` directory within this repository, consuming the existing **FastAPI / LangGraph backend** as the authoritative orchestration engine.

### Key Architectural Guidelines:
1. **Initial Consumption of Existing Contracts:** The frontend redesign will initially connect directly to the existing, verified FastAPI endpoints (`/api/v1/investigations`, `/events`, `/result`, `/health`) without requiring backend modifications for the initial workspace view.
2. **Additive Backend Evolution for Target Capabilities:** As product features like persistent storage, user accounts, and public share links are introduced, additive backend endpoints and database schemas will be developed cleanly without altering the core LangGraph multi-agent DAG.
3. **Repository Placement:** The Next.js application will reside in `frontend/` within the current repository (monorepo layout), allowing TypeScript client types to be synchronized directly with FastAPI Pydantic models.
4. **Clean Separation of Concerns:**
   - Backend (`app/`): Agent orchestration, LangGraph DAG execution, LLM client gateway, mock integrations, authoritative evidence ledger generation.
   - Frontend (`frontend/`): Information architecture, routing, design system components, evidence drawer deep-linking, client-side caching, and PDF brief rendering.
5. **No Streamlit:** Streamlit was evaluated and rejected; it cannot provide the necessary multi-pane layout, deep citation linking, or editorial typography required by the UX specification.

---

## Invariants Preserved
1. The FastAPI/LangGraph backend remains the single source of truth for all investigation execution, agent logic, and data schemas.
2. Read-only external boundary maintained: Frontend cannot trigger arbitrary direct external API requests to Zendesk, Jira, or PostHog.
3. Attributable Evidence Ledger contract strictly preserved.
4. Epistemic separation of Facts, Inferences, and Hypotheses strictly rendered.
5. Zero implementation code in Step 1 (specification and planning only).

---

## Consequences & Next Steps
- **Phase 14, Steps 1–4:** Next.js frontend scaffolded in `frontend/`; design system tokens implemented; agent workspace assembled; live SSE streaming connected.
- **Phase 14, Step 5 (Core Experience Stabilisation — completed 2026-09-18):** UI copy, branding, and PM-facing information architecture stabilised. See decisions below.

---

## Phase 14 Step 5 — Product Experience Decisions

### Branding Invariant
**"PMLytics AI"** is the name of the AI tool. **"Pocket"** is the name of the fictional fintech company being investigated. These must never be confused in copy:
- ✅ "PMLytics AI investigates across Pocket customer support (Zendesk)…"
- ❌ "Pocket formulates hypotheses…" (implies the tool is named Pocket)

The landing page (`/`) intentionally uses "Pocket" extensively because it describes the investigation subject. That page is frozen and must not be changed.

### PM-Facing Telemetry Removed
The following implementation-internal metrics were removed from the workspace header (`WorkspaceHeader.tsx`). They are observability concerns, not PM decision-making signals:
- `llmCalls` count
- `revisionCount`
- `costUsd` (provider cost)
- "PDF Brief" export button (deferred, not yet functional)

Retained in the workspace header strip: status pill, duration (plain mono `Xs`), investigation ID, "Evidence [N]" button.

### Workspace Navigation Labels
- Back link: `← Back to investigations` (was: "Overview")
- Evidence button: `Evidence [count]` (was: "Evidence Ledger")

### Recommendation Type Labels
Backend produces snake_case `rec_type` values (e.g. `technical_remediation`, `product_backlog`, `monitor_and_revisit`). The `RecommendationPanel` component maps these to PM-friendly badge labels via `recTypeLabelMap` without touching the backend contract.

### Sidebar Cleanup
Removed the "Core Engine OK" health indicator from the sidebar footer — it is a backend infrastructure status signal irrelevant to a PM using the tool.

### Component Copy Standardisation
| Component | Before | After |
|---|---|---|
| `Header.tsx` | "Pocket Product Discovery" / "Workspace" CTA | "PMLytics AI" / "New investigation" CTA |
| `InvestigationComposer.tsx` | "Launch Investigation" heading | "New investigation" heading |
| `InvestigationList.tsx` | "this Pocket session" | "this session" |
| `WorkspaceHeader.tsx` | Telemetry strip with LLM calls, cost, PDF button | Clean strip: status · duration · ID · Evidence count |
| `EpistemicDeck.tsx` | "Facts — Empirical Ground Truth" subtitle | "Facts" only |
| `app/investigations/page.tsx` | `headerTitle="Launchpad"` | `headerTitle="Investigations"` |
| `app/layout.tsx` | Title: "Pocket AI Product Discovery Team" | Title: "PMLytics AI" |

### `CriticReviewSection.tsx` — Deferred
The label "Adversarial Critic Review" in the collapsed accordion trigger was reviewed. It is acceptable at the current stage; it is collapsed by default and is accurate to the backend agent's role. Simplification to "Quality review" is deferred unless flagged by PM testing.
