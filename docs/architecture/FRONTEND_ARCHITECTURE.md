# Frontend Architecture Specification: Pocket AI Product Discovery System

**Document Version:** 1.0.0  
**Phase:** 14 (Next.js Frontend Foundation)  
**Status:** Draft / Needs Review  
**Date:** 2026-09-17  
**Author:** AI Product Discovery Engineering Team  

---

## 1. Executive Summary & Architectural Invariants

This specification defines the production React / Next.js frontend architecture for the **Pocket AI Product Discovery Team** as a typed and accessible web application.

### Architectural Invariants
1. **Authoritative Backend Boundary:** The backend (FastAPI + LangGraph multi-agent DAG running on port 8000) remains the single source of truth for business logic, agent orchestration, evidence synthesis, and lifecycle states.
2. **Zero Business Logic in Frontend:** The frontend is strictly a presentation, observation, and inquiry-triggering layer. It performs no agent coordination, external vendor API calls, or heuristic metric calculations.
3. **Zero Data Simulation:** The UI renders only verified API payloads and lifecycle milestones emitted by the backend. It will never fabricate progress bars, fake streaming text, or synthetic token/call counters.
4. **Epistemic & Evidentiary Rigor:** Canonical evidence IDs (`[EV-xxx]`) and the separation between **Facts**, **Inferences**, and **Hypotheses** remain strictly enforced at the component and data layer.

---

## 2. Technology Stack & Dependency Justification

Every frontend dependency is vetted against necessity, maintenance burden, bundle size, and accessibility compliance. No convenience libraries or unvetted "AI UI" wrappers are permitted.

| Concern | Approved Choice | Justification & Role |
| :--- | :--- | :--- |
| **Framework** | Next.js 16.x (App Router) | Modern React framework providing server/client component boundaries, optimized asset loading, built-in routing, and unified build tooling. |
| **UI Library** | React 19.x | Component runtime for declarative presentation. |
| **Runtime Baseline** | Node.js 24.x LTS | Active LTS baseline for development and production builds (Next.js 16 minimum framework compatibility floor is Node.js 20.9+). |
| **Language** | TypeScript strict | Enforces end-to-end type safety. `noImplicitAny: true`, `strictNullChecks: true`. All API contracts match backend schemas. |
| **Styling** | TailwindCSS 3.4+ | Utility-first CSS configured strictly with design tokens from `FRONTEND_DESIGN_SYSTEM.md`. Zero ad-hoc arbitrary styles. |
| **Accessible Primitives** | Radix UI (`@radix-ui/react-*`) | Unstyled, fully accessible (WAI-ARIA compliant) headless primitives for dialogs, sheets/drawers, accordions, dropdowns, and tooltips. |
| **Icons** | Lucide React | Lightweight, tree-shakeable icon set matching the clean, analytical line-icon aesthetic of the prototype. |
| **Server State / Caching** | TanStack React Query v5 | Manages asynchronous API queries, caching, background revalidation, and retry policies for HTTP endpoints. |
| **Contract Generation** | `openapi-typescript` | Generates committed TypeScript types directly from FastAPI's `/openapi.json`. Verified in CI without requiring live backend in production builds. |
| **Unit / Component Testing** | Vitest + React Testing Library | Fast ESM-native unit and component interaction testing with DOM emulation. |
| **End-to-End Testing** | Playwright | Multi-browser headless integration testing across desktop (1600px, 1440px, 1280px) and mobile (390px) viewports. |

### Explicitly Excluded Libraries
- **No Heavy Component Suites (MUI, AntD, Chakra):** Avoids opinionated design overrides and heavy runtime CSS-in-JS overhead.
- **No AI / Chat Wrapper Libraries (Vercel AI SDK, LangChain JS):** The backend uses custom typed SSE streams and structured REST responses; generic chat wrappers encourage chat-bubble paradigms which violate our anti-chat-bubble mandate.
- **No CSS Animation Engines (Framer Motion, GSAP):** Complex animation frameworks add bundle bloat and encourage distracting "AI pulse" gimmicks. Standard CSS transitions handle our subtle micro-interactions.

---

## 3. Directory Layout (`frontend/`)

The frontend lives in a top-level `frontend/` directory within the existing repository (monorepo structure), preserving atomic versioning with backend schemas.

```text
frontend/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── next.config.mjs
├── vitest.config.ts
├── playwright.config.ts
├── public/
│   ├── favicon.ico
│   └── fonts/                     # Inter and JetBrains Mono woff2
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx             # Root HTML layout with fonts and providers
│   │   ├── page.tsx               # Public Marketing & Demo Landing Page
│   │   ├── not-found.tsx          # 404 handler
│   │   ├── error.tsx              # Root error boundary
│   │   ├── investigations/
│   │   │   ├── page.tsx           # Launchpad & recent investigations list
│   │   │   └── [id]/
│   │   │       ├── page.tsx       # Investigation Workspace page (dynamic route)
│   │   │       ├── loading.tsx    # Investigation skeleton loading state
│   │   │       └── error.tsx      # Investigation error boundary (404/500/410)
│   │   └── api/                   # (Optional Next.js API routes if proxying is needed)
│   ├── components/
│   │   ├── common/                # Shared atomic primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── SourceBadge.tsx
│   │   │   ├── CitationPill.tsx
│   │   │   ├── ConfidenceBadge.tsx
│   │   │   └── Tooltip.tsx
│   │   ├── landing/               # Public landing page components
│   │   │   ├── LandingHeader.tsx
│   │   │   ├── MobileNavModal.tsx
│   │   │   ├── HeroSection.tsx
│   │   │   ├── InteractiveHeroPreview.tsx
│   │   │   ├── ProblemSection.tsx
│   │   │   ├── HowItWorksSection.tsx
│   │   │   ├── EvidenceProofSection.tsx
│   │   │   ├── EvaluationSection.tsx
│   │   │   └── LandingFooter.tsx
│   │   ├── workspace/             # Investigation workspace components
│   │   │   ├── WorkspaceShell.tsx # Sticky top bar, collapsible sidebar, main grid
│   │   │   ├── WorkspaceHeader.tsx# Investigation title, badges, actions, timer
│   │   │   ├── RecommendationPanel.tsx # Elevated primary recommendation banner
│   │   │   ├── ExecutiveFinding.tsx    # Problem statement & cohort context
│   │   │   ├── EpistemicFlow.tsx       # Integrated editorial Facts/Inferences/Hypotheses
│   │   │   ├── TensionsBanner.tsx      # Conflicting evidence and trade-offs
│   │   │   ├── LimitationsBanner.tsx   # Missing data and telemetry disclosures
│   │   │   ├── CriticAccordion.tsx     # Adversarial review verdict & revision audit
│   │   │   ├── EvidenceLedgerSheet.tsx # Docked / modal slide-over evidence viewer
│   │   │   └── LiveProgressStream.tsx  # Investigation live stage timeline & active agent
│   │   └── modals/
│   │       └── NewInquiryModal.tsx     # Investigation trigger dialog
│   ├── hooks/
│   │   ├── useInvestigationStream.ts   # SSE lifecycle management with auto-reconnect
│   │   ├── useInvestigationResult.ts   # TanStack Query hook for /result
│   │   ├── useActiveInvestigation.ts   # Workspace state orchestration
│   │   └── useEvidenceDrawer.ts        # Evidence drawer open/close and active citation
│   ├── lib/
│   │   ├── api-client.ts          # Typed HTTP client communicating with FastAPI
│   │   ├── formatters.ts          # Timestamps, elapsed time, duration formatting
│   │   └── utils.ts               # Tailwind class merger (clsx + twMerge)
│   └── types/
│       ├── api.generated.ts       # Auto-generated OpenAPI TypeScript schema
│       └── domain.ts              # Extended UI view models & helper unions
└── tests/
    ├── unit/                      # Component unit tests (Vitest)
    └── e2e/                       # End-to-end tests (Playwright)
```

---

## 4. Application Shell & Layout Architecture

The application layout implements the approved viewport geometry established in [ADR-0015](../decisions/ADR-0015-visual-ux-implementation-strategy.md) and frozen in Phase 13.

### 4.1 Root Shell (`app/layout.tsx`)
- Provides font declarations (`Inter` for editorial UI, `JetBrains Mono` for evidence IDs and code).
- Injects global stylesheet containing verified tokens (`globals.css`).
- Wraps application with `QueryClientProvider` for server state management.
- Does **not** include heavy auth wrappers or mock session providers in MVP.

### 4.2 Workspace Layout (`components/workspace/WorkspaceShell.tsx`)
The workspace layout is a responsive 3-zone composition:
1. **Application Header (Sticky, 56px height):**
   - Brand lockup with live environment indicator.
   - Breadcrumbs (`Pocket / Investigations / inv_...`).
   - Action controls (New Investigation button, Evidence Ledger toggle button with record count badge).
2. **Left Navigation Sidebar:**
   - **Desktop ($\ge 1024\text{px}$):** Persistent collapsible navigation rail. Expanded (240px) shows recent investigations, launch trigger, and system status. Collapsed (64px) shows icons with tooltips. User toggle state is preserved in local storage.
   - **Tablet / Mobile ($< 1024\text{px}$):** Off-canvas drawer triggered by header hamburger button.
3. **Main Content Canvas:**
   - Background `#f8fafc`.
   - Constrained reading width: Maximum 840px for analytical prose (65–75 characters per line for optimal reading ergonomics).
   - Centered inside viewport with responsive padding (`px-4` on mobile, `px-8` on tablet, `px-12` on desktop).
4. **Evidence Ledger Sheet / Drawer:**
   - **Large Desktop ($\ge 1600\text{px}$):** Docked right-hand column (420px fixed width), allowing simultaneous reading of PM synthesis and evidentiary proof.
   - **Standard Desktop ($1280\text{px}–1599\text{px}$):** Slide-over overlay drawer anchored to right margin (440px width) with dimmed backdrop.
   - **Mobile / Tablet ($< 1280\text{px}$):** Full-width bottom/side sheet (100vw on mobile, 480px on tablet) with swipe/tap dismiss.
   - Each canonical evidence item is a concise source summary. An expandable second level exposes bounded supporting customer conversations, aggregated metric rows, or engineering issues without adding them to the main report.
   - Drawer search matches both summary content and supporting-record references, titles, excerpts, statuses, and display attributes.

---

## 5. Server Component vs. Client Component Boundaries

Next.js App Router enforces explicit separation between React Server Components (RSC) and Client Components (`"use client"`).

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Server Components (RSC)                                                 │
│ • Layouts (fonts, metadata, shell wrappers)                             │
│ • Landing page marketing copy (Hero, Problem, How it works, Evaluation) │
│ • Static SEO metadata & OpenGraph tags                                  │
│ • Initial SSR page hydration                                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Client Components ("use client")                                        │
│ • InteractiveHeroPreview (sample scenario switcher & live view)         │
│ • WorkspaceShell (responsive sidebar state & keyboard shortcuts)        │
│ • LiveProgressStream (Server-Sent Events event listener)                │
│ • EvidenceLedgerSheet (Radix Dialog/Sheet with active record highlight) │
│ • CitationPill (interactive deep-link trigger with focus transfer)      │
│ • CriticAccordion (Radix Accordion expand/collapse)                     │
│ • NewInquiryModal (form state, query submission, validation)            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Boundary Rules
- Keep Server Components as high as possible in the component tree to minimize client bundle size.
- Mark components `"use client"` only when they require:
  - React state (`useState`, `useReducer`).
  - React lifecycle effects (`useEffect`).
  - Browser DOM events (click handlers, keyboard listeners).
  - Web APIs (`EventSource` for SSE, `window.innerWidth`, `localStorage`).

---

## 6. State Management & Data Fetching

State management is separated strictly into **Server State**, **Stream State**, and **Local UI State**. No complex global store (e.g., Redux, Zustand) is required.

```text
                  ┌────────────────────────────────────────┐
                  │          FastAPI Backend (8000)        │
                  └───────┬────────────────────────┬───────┘
                          │                        │
       POST /investigations (202)                  │ GET /events (SSE stream)
       GET /result (200)                           │
                          │                        │
                          ▼                        ▼
       ┌───────────────────────────────┐ ┌─────────────────────────────────┐
       │   TanStack Query (Server)     │ │  useInvestigationStream (Stream)│
       │ • Investigation Result Cache  │ │ • Live active_agent             │
       │ • Recent Investigations List  │ │ • Lifecycle stage milestones    │
       │ • System Health               │ │ • Reconnect backoff & fallback  │
       └──────────────┬────────────────┘ └────────────────┬────────────────┘
                      │                                   │
                      └─────────────────┬─────────────────┘
                                        ▼
                       ┌─────────────────────────────────┐
                       │   Local React State (UI/DOM)    │
                       │ • Sidebar collapsed (boolean)   │
                       │ • Evidence drawer open (boolean)│
                       │ • Active evidence ID highlight  │
                       │ • Active scenario tab (preview) │
                       └─────────────────────────────────┘
```

### 6.1 Server State (TanStack Query) & Persistence Boundary
- **Investigation Detail:** Keyed by `["investigation", id, "result"]`. Cached indefinitely once `status === "completed"` (immutable).
- **Recent Inquiries (Authoritative Backend State):** Keyed by `["investigations", "recent"]`. Hydrated strictly from the FastAPI `GET /api/v1/investigations` endpoint. Stale time 15 seconds.
- **System Health:** Keyed by `["system", "health"]`. Stale time 60 seconds.
- **Strict Prohibition of Client-Side Pseudo-Persistence:**
  - Browser `localStorage` must **never** be used to store or cache investigation IDs, queries, or results.
  - Investigation state is process-local on the backend (`InvestigationManager`).
  - Browser refresh retrieves currently available investigations directly from the API.
  - Backend restart clears process-local investigations by design.
  - Durable cross-session history is deferred to the future persistence phase. No secondary client-side source of truth is permitted.

### 6.2 Stream State (`useInvestigationStream`)
- Connects to `/api/v1/investigations/{id}/events`.
- Maintains live execution state: `stage`, `status`, `active_agent`, `elapsed_seconds`, `revision_count`, `error`.
- When terminal status (`completed`) is received via SSE, it invalidates the TanStack Query cache for `["investigation", id, "result"]`, triggering immediate retrieval of the final synthesized recommendation.
- **Resilience:** Implements exponential backoff on disconnect. If SSE fails 3 times, gracefully falls back to polling `GET /api/v1/investigations/{id}` every 3 seconds.

### 6.3 Local UI State
- Managed with standard React hooks (`useState`, `useContext`) localized to the Workspace or Sheet components.
- Client-side `localStorage` is restricted strictly to non-domain UI preferences: the sidebar collapsed preference (`pocket_sidebar_collapsed`).

### 6.4 Development Proxy Architecture
- Local development leverages Next.js rewrites in `next.config.mjs` to proxy `/api/v1/:path*` to `http://127.0.0.1:8000/api/v1/:path*`.
- **Architectural Boundary:** This proxy is strictly a local development and staging convenience to avoid CORS configuration overhead. It is not an application-layer BFF (Backend-For-Frontend) or architectural facade. FastAPI remains the sole authoritative API boundary.

---

## 7. Deep-Linking & Evidence Citation Interaction Model

The interaction model validated in Phase 13 must be preserved with pixel and focus fidelity:

1. **Citation Pill Click:**
   - When a user clicks a citation pill (e.g., `[EV-001]`), the `useEvidenceDrawer` hook sets `selectedEvidenceId = "EV-001"` and `isOpen = true`.
2. **Drawer Open & Scroll Transfer:**
   - If the drawer is docked ($\ge 1600\text{px}$), it smoothly scrolls the target evidence row into view.
   - If the drawer is overlay or sheet ($< 1600\text{px}$), it animates open and scrolls the target record to the top of the drawer container.
3. **Visual Confirmation:**
   - The selected evidence record receives a temporary visual highlight (emerald border flash and subtle background tint) for 1200ms.
4. **Keyboard Accessibility:**
   - Focus shifts inside the drawer to the selected record header, allowing keyboard users to immediately read the supporting excerpt or press `Escape` to return focus to the originating citation pill.

---

## 8. Loading, Empty, and Error States

### 8.1 Loading States
- **Initial Page Load:** CSS skeleton pulse reflecting the editorial hierarchy (recommendation box skeleton, 3 epistemic row skeletons).
- **Active Execution (~100s duration):** Renders the `LiveProgressStream` milestone stepper.
  - Shows verified stages: `Planning` $\rightarrow$ `Specialist Evidence Gathering` $\rightarrow$ `PM Synthesis` $\rightarrow$ `Critic Review`.
  - Shows current active agent badge: `Planner`, `Research Agent`, `Analytics Agent`, `Engineering Agent`, `PM Agent`, `Critic Agent`.
  - Displays real elapsed seconds counter.
  - **Forbidden:** No spinning spinners without context, no synthetic percentage bars (e.g., "64% done"), no simulated LLM token streams.

### 8.2 Empty States
- Clean, calm editorial layout with an instructional prompt.
- Suggests 3 verified inquiry templates (Scenario 1 checkout delay, Scenario 2 onboarding drop-off, Scenario 3 API migration).

### 8.3 Error States
- **HTTP 404 (Not Found):** "Investigation not found. The investigation may have expired from in-process memory or was never created." Offers return to launchpad.
- **HTTP 409 (Conflict):** Triggered if `/result` is called while execution is active. Frontend displays live execution stepper rather than an error toast.
- **HTTP 410 (Gone):** "This investigation was cancelled before completion."
- **HTTP 500 (Execution Failure):** Displays sanitized failure details from the backend (`error` payload), affected stage, and elapsed duration. Includes a "Retry Investigation" button.

---

## 9. Accessibility & Keyboard Navigation (WCAG 2.1 AA)

- **Semantic HTML:** Strict heading hierarchy (`h1` for investigation question, `h2` for primary recommendation, executive finding, epistemic findings, tensions, limitations, critic review; `h3` for subsection headings).
- **Focus Management:**
  - Opening the Evidence Drawer traps focus inside the drawer (on modal/mobile viewports).
  - Pressing `Escape` closes the drawer and restores focus to the triggering citation pill.
  - Mobile hamburger menu traps focus and restores focus upon close.
- **Color Contrast:** All text meets or exceeds 4.5:1 contrast against `#f8fafc` and `#ffffff` surfaces.
- **Screen Reader Support:** SSE lifecycle transitions are announced via an `aria-live="polite"` region.

---

## 10. Testing Strategy

| Level | Tool | Scope | Coverage Target |
| :--- | :--- | :--- | :--- |
| **Unit** | Vitest | Formatters, citation parsers, status badge mapping, API client response handlers. | > 90% logic coverage |
| **Component** | Vitest + React Testing Library | Citation pill click dispatch, evidence drawer scroll-into-view, collapsible sidebar toggle, mobile menu toggle, critic review accordion expand/collapse. | Core interactive primitives |
| **Integration** | Playwright | Full browser investigation walkthrough: Landing page $\rightarrow$ Scenario selection $\rightarrow$ Workspace render $\rightarrow$ Citation deep-link $\rightarrow$ Evidence drawer verification at 1440px, 1280px, and 390px. | All 3 responsive viewports |

---

## 11. Architectural Verification & Phase Gate Criteria

Phase 14 Step 1 defines this specification. Implementation in Step 2 may proceed only when:
- [x] Next.js version and App Router architecture documented.
- [x] Server vs Client component boundaries defined.
- [x] State management, SSE integration, and TanStack Query caching specified.
- [x] Directory layout under `frontend/` structured.
- [x] Dependencies justified and unnecessary packages excluded.
- [x] Accessibility and responsive invariants preserved.
