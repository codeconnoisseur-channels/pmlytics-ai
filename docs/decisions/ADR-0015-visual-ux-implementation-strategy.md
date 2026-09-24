# ADR-0015: Visual UX Implementation Strategy & Component Architecture

## Status
Accepted (Step 2 Approved)

## Context
Step 1 defined the authoritative Product UX Specification, Information Architecture, Investigation Workspace Specification, State Matrix, and Frontend Architecture evaluation ([ADR-0014](ADR-0014-frontend-product-experience.md)).

Step 2 translates these specifications into a concrete visual design system, screen compositions, component inventory, responsive breakpoint models, and an anti-AI-slop quality checklist:
- [`VISUAL_UX_SPEC.md`](../product/VISUAL_UX_SPEC.md)
- [`SCREEN_COMPOSITION_SPEC.md`](../product/SCREEN_COMPOSITION_SPEC.md)
- [`COMPONENT_DESIGN_SPEC.md`](../product/COMPONENT_DESIGN_SPEC.md)
- [`RESPONSIVE_DESIGN_SPEC.md`](../product/RESPONSIVE_DESIGN_SPEC.md)
- [`UX_REVIEW_CHECKLIST.md`](../product/UX_REVIEW_CHECKLIST.md)

Before beginning any frontend code implementation, we formally record the visual implementation strategy, component technology stack, and API boundary invariants.

---

## Decisions

### 1. Visual Design & Reading Philosophy
- **Light-First / Neutral-First Foundation:** Optimized for reading comprehension, analytical credibility, and daylight office review. Canvas: `#f8fafc`; Surface: `#ffffff`; Borders: `#e2e8f0`; Text: `#0f172a`.
- **Anti-"Card-Wall" Discipline:** The workspace rejects generic dashboard stacks of rounded rectangles. It uses continuous editorial typography for problem statements and recommendations, structured analytical rows for epistemic findings, full-width alert banners for tensions, and reserves cards strictly for atomic items (evidence drawer records, history preview tiles).
- **Desktop Geometry Standards:**
  - $\ge 1600\text{px}$: Full three-column analytical workspace (sidebar 240px or 64px, flexible main region with maximum reading width of 840px, evidence drawer ~420px).
  - $1280–1599\text{px}$: Sidebar + flexible main region + compact evidence panel where space permits.
  - $< 1280\text{px}$: Evidence Drawer becomes overlay/slide-over.
  - $< 1024\text{px}$: Sidebar becomes off-canvas.
  - $< 768\text{px}$: Mobile investigation layout.
  - *Reading Width Rule:* 840px is a maximum reading line-length constraint (65–75 characters), not a fixed-width column.
- **Canonical Evidence IDs:** All citations strictly preserve `[EV-001]`, `[EV-002]`, etc. Source identity is communicated via adjacent `SourceBadge` metadata (`[EV-003] · Zendesk · TICKET-1042`).
- **Epistemic vs. Source Separation:** Color is never the sole differentiator for epistemic types. Source identities have dedicated badge tints (Zendesk Emerald, PostHog Violet, Jira Sky Blue). Facts, Inferences, and Hypotheses are differentiated primarily by section headings, typography, and structural placement.
- **User-Controlled Sidebar:** Sidebar defaults to Expanded (240px); user controls collapse/expand; investigation state changes never alter application chrome.
- **Formal Reading Hierarchy (Time-to-Insight):**
  - **15 seconds:** Immediate awareness of inquiry, status, and duration.
  - **30 seconds:** Executive understanding of core problem, action type, recommendation, and confidence.
  - **60 seconds:** Analytical evaluation of verified facts, contradictions, and limitations.
  - **3 minutes:** Evidentiary audit via deep-linked citations in the docked Evidence Drawer.

### 2. Frontend Component Stack & Repository Structure
- **Placement:** The frontend application will reside in a dedicated `frontend/` directory within this repository (monorepo layout), preserving atomic versioning with FastAPI backend schemas.
- **Framework:** Next.js (App Router) + TypeScript + React.
- **Styling & Design Tokens:** TailwindCSS configured strictly with the design tokens specified in `VISUAL_UX_SPEC.md`.
- **Accessible Primitives:** Headless accessible primitives (Radix UI) for drawers, dialogs, accordions, and tooltips, ensuring native WCAG 2.1 AA keyboard operability and focus management.

### 3. API Boundary & Zero-Data-Simulation Invariant
- **Authoritative Backend Engine:** The existing FastAPI/LangGraph backend on port 8000 remains authoritative and unchanged.
- **Initial Contract Consumption:** The frontend initially consumes existing verified Phase 11 API endpoints (`POST /api/v1/investigations`, `GET /events` SSE, `GET /result`, `GET /health`).
- **Zero Data Simulation:** The UI must strictly render supported API payloads. During the ~100–120s investigation execution, the interface displays verified lifecycle stages (`planning`, `specialists`, `pm`, `critic`). It will **never** fabricate progress percentages, synthetic tool call counters, or fake streaming text.
- **Additive Evolution:** Future capabilities requiring persistence (database storage), user authentication, permanent share tokens, and PDF rendering will be introduced via clean additive backend endpoints in later phases without altering the LangGraph multi-agent DAG.

---

## Invariants Preserved
1. Bit-for-bit preservation of the authoritative Evidence Ledger and epistemic separation contracts.
2. Read-only boundary: Agents and frontend have zero autonomous write permissions to external systems.
3. Clean-context invariant: No hidden cross-investigation agent memory.
4. Step 2 remains strictly specification and design; zero implementation code written in this step.

---

## Consequences & Next Steps
- **Immediate:** Complete Step 2 review gate and await user authorization.
- **Subsequent (Step 3+):** Initialize the Next.js workspace in `frontend/`, configure TailwindCSS design tokens, build the accessible component library, and wire to the FastAPI server.
