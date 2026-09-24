# ADR-0016: Next.js Production Frontend Foundation & Prototype Freeze

## Status
Accepted (Phase 14 Step 1 Approved)

## Context
In Phase 13, the web experience was refined, audited across multiple viewports (1440×900, 1280×800, and 390×844), and formally validated using a vanilla HTML/CSS/JavaScript prototype (`app/ui/index.html`, `app/ui/styles.css`, `app/ui/app.js`). The visual gate for Phase 13 closed with unanimous approval:
* Landing page visual direction: **APPROVED & FROZEN**
* Investigation workspace hierarchy and editorial layout: **APPROVED & FROZEN**
* Multi-viewport adversarial QA: **PASS**

With the UX hierarchy, visual language, and interaction models established, we must formalize the production frontend technology stack for Phase 14. We evaluate the transition from the vanilla prototype to a production React / Next.js implementation and record the explicit operational boundaries.

---

## Decisions

### 1. Freeze the Vanilla Prototype as the Authoritative Visual Reference
The existing vanilla implementation in `app/ui/` is immediately **FROZEN**.
* **Role:** It serves as the immutable, executable reference implementation and visual benchmark.
* **Inviolability:** No further code edits, design alterations, or layout restructurings are permitted in `app/ui/` unless an explicit regression is identified.
* **Fidelity Requirement:** The production Next.js implementation must reproduce the validated UX, typography, responsive behavior, epistemic color language, and citation deep-linking bit-for-bit against this reference.

### 2. Adopt Next.js 16.x + React 19.x + TypeScript Strict as Production Frontend
The production frontend will be implemented in a dedicated `frontend/` directory within this repository (monorepo layout), utilizing:
* **Next.js 16.x (App Router):** Provides server/client component boundaries, optimized code splitting, built-in routing, and unified build tooling.
* **React 19.x:** Modern component runtime for declarative presentation.
* **Node.js 24.x LTS:** Production runtime and development baseline (Next.js 16 requires Node.js 20.9+ as its minimum compatibility floor; Node.js 20 reached end-of-life on March 24, 2026).
* **TypeScript Strict Mode:** Eliminates type ambiguity across complex investigation payloads, ensuring end-to-end type safety with backend Pydantic models.
* **TailwindCSS:** Configured strictly to mirror the design tokens extracted from the frozen `styles.css`.
* **Radix UI Primitives:** Provides headless, unstyled, WAI-ARIA compliant primitives for drawers, dialogs, accordions, and tooltips, ensuring native accessibility without opinionated CSS conflicts.

### 3. Rejection of Alternative Frontend Stacks
* **Rejection of Streamlit / Gradio:**
  * Streamlit was evaluated and rejected because its opinionated layout engine cannot accommodate the approved three-column geometry (sidebar, 840px constrained reading canvas, 420px docked evidence ledger).
  * Streamlit inherently nudges applications toward generic "chat-bubble" threads and widget stacks, directly violating our anti-chat-bubble and anti-card-wall design mandates.
  * Streamlit lacks granular DOM focus control necessary for citation pill deep-linking and keyboard-accessible slide-over drawers.
* **Rejection of Continuing Vanilla JS/CSS in Production:**
  * Managing multi-page routing, complex asynchronous SSE reconnections, modal focus traps, and deeply nested DOM mutations in imperative vanilla JavaScript introduces extreme brittleness and maintenance overhead as the feature surface expands.

### 4. Preservation of Authoritative FastAPI / LangGraph Backend & OpenAPI Contract
* **Authoritative Engine:** FastAPI and the LangGraph multi-agent orchestration engine remain the authoritative core of the system.
* **No Frontend Business Logic:** The frontend is strictly a presentation and interaction layer. It will never perform agent orchestration, synthesize evidence, calculate metrics, or query external systems directly.
* **Contract Generation Workflow:**
  * FastAPI `/openapi.json` is the sole authoritative API contract.
  * Local development runs `npm run generate:api` against the running backend to generate `src/types/api.generated.ts`.
  * Generated TypeScript types are committed to git.
  * CI starts the backend, regenerates types, and asserts `git diff --exit-code`, failing on contract drift.
  * The frontend production build operates decoupled and does not require a live backend during compilation.
  * No duplicate static OpenAPI snapshot is maintained unless required by a future deployment constraint.

### 5. Intentional Deferral of Persistence & Rejection of Pseudo-Persistence
* **No Client-Side Pseudo-Persistence:** We explicitly reject storing investigation history in browser `localStorage`.
* **Process-Local Reality:** Investigation state is process-local on the backend (`InvestigationManager`). The launchpad queries `GET /api/v1/investigations`. Browser refresh queries the API. Backend restart clears active records by design.
* **Deferred Capabilities:** The following enterprise capabilities are deliberately deferred from Phase 14 foundation work:
  * User authentication (SSO, OAuth, session management)
  * Multi-tenant workspace RBAC
  * Supabase or external database persistence
  * Server-side PDF export generation
  * Email alerting and notification infrastructure
  * Public share links and collaborative annotations

### 6. Development Proxy Architecture
* For local development, Next.js rewrites in `next.config.mjs` proxy `/api/v1/:path*` from `http://localhost:3000` to `http://127.0.0.1:8000`.
* This is documented explicitly as a development/staging integration convenience to prevent CORS friction. It is not an architectural BFF layer. FastAPI remains the direct, authoritative API boundary.

---

## Invariants Preserved
1. **Zero Data Simulation:** The UI will never fabricate streaming text, synthetic progress percentages, or fake tool-call counters.
2. **Epistemic Integrity:** Facts, Inferences, and Hypotheses remain distinct at both the schema and presentation layers.
3. **Canonical Evidence Citations:** Canonical evidence IDs (`[EV-xxx]`) remain immutable and deep-link directly to supporting records.
4. **Read-Only Agent Access:** Neither agents nor the frontend possess autonomous write capabilities to external production tools.
5. **No Cross-Investigation Memory Leaks:** Investigations remain self-contained, stateless, and fully reproducible.

---

## Consequences & Next Steps
* **Positive:**
  * Delivers a maintainable, type-safe, accessible production frontend.
  * Eliminates CSS drift and imperative DOM bugs through modular React components and Tailwind design tokens.
  * Preserves single-source-of-truth contract between FastAPI schemas and TypeScript interfaces.
* **Operational:**
  * Complete Phase 14 Step 1 review gate.
  * Upon approval, proceed to Step 2 (Initializing `frontend/` Next.js workspace, Tailwind configuration, component scaffold, and API client).
