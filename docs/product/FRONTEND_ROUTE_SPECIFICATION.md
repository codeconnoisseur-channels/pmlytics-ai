# Frontend Route and Screen Specification: Pocket AI Product Discovery System

**Document Version:** 1.0.0  
**Phase:** 14 (Next.js Frontend Foundation)  
**Status:** Draft / Needs Review  
**Date:** 2026-09-17  
**Author:** AI Product Discovery Engineering Team  

---

## 1. Route Architecture & Navigation Model

The production Next.js frontend implements a clean, shallow route structure mapping directly to the validated Phase 13 user journeys.

```text
Route                      Type      Purpose & Experience
─────────────────────────────────────────────────────────────────────────────
/                          Public    Marketing, Value Prop, Interactive Preview, Evaluation Proof
/investigations            App       Launchpad, New Inquiry Input, Recent Investigations List
/investigations/[id]       App       Authoritative Workspace, Live Progress, Synthesis & Evidence
```

### 1.1 Scope Boundaries & Deferred Infrastructure
In accordance with project invariants, this specification deliberately excludes:
* User Authentication & Session Management (Login/Signup/SSO)
* Multi-tenant Workspace RBAC
* Supabase / External Database Persistence
* PDF Report Generation & Export
* Email Notification Infrastructure
* Public Sharing Links & Collaborative Annotations

These capabilities belong to future phases and will be integrated additively without disrupting these core routes.

---

## 2. Route Specifications

### 2.1 Public Landing Page (`/`)

* **File:** `src/app/page.tsx`
* **Rendering Mode:** Hybrid (React Server Component layout + Client Component interactive preview).
* **Target Audience:** Product managers, technical leaders, and evaluators evaluating Pocket's multi-agent product discovery paradigm.
* **SEO Metadata:**
  * Title: `Pocket AI Product Discovery Team — Multi-Agent System for Product Managers`
  * Description: `Autonomous multi-agent product investigations grounded in Zendesk customer support, PostHog product analytics, and Jira engineering systems.`

#### Screen Structure (Top-to-Bottom Flow):
1. **Public Header (`LandingHeader.tsx`):**
   * Sticky top bar (`height: 56px`, `bg: #ffffff/95%`, `border-b: #e2e8f0`).
   * Brand lockup: Pocket logo + `AI Product Discovery`.
   * Anchor navigation links: `Product`, `Problem`, `How It Works`, `Evidence`, `Evaluation`.
   * Action button: `Launch Workspace` $\rightarrow$ navigates to `/investigations`.
   * Mobile ($< 768\text{px}$): Accessible hamburger trigger opening `MobileNavModal.tsx`.
2. **Hero Section (`HeroSection.tsx`):**
   * Subtitle tag: `MULTI-AGENT PRODUCT INVESTIGATION SYSTEM`.
   * Main headline: `Rigorous product discovery without the data-silo drag.`
   * Body copy: `When conversion drops or complaints surge, product teams spend days stitching together Zendesk tickets, PostHog funnels, and Jira issues. Pocket deploys specialist agents to investigate root causes, isolate contradictions, and deliver defensible recommendations.`
   * Primary CTA: `Investigate a Question` (opens `/investigations`).
   * Secondary CTA: `View Sample Investigation` (smooth-scrolls to preview).
3. **Interactive Hero Preview (`InteractiveHeroPreview.tsx`):**
   * Pre-rendered, high-fidelity sample investigation based on Scenario 1 (Delayed Payment Status).
   * Tabbed scenario switcher (Scenario 1: Checkout Delay, Scenario 2: Onboarding Drop-off, Scenario 3: Legacy API Deprecation).
   * Interactive citation pills that open the inline evidence viewer.
4. **Problem Section (`ProblemSection.tsx`):**
   * Highlights the "Three Blind Men and the Elephant" problem in modern software:
     * Support sees customer frustration but lacks technical telemetry.
     * Analytics sees drop-offs but lacks customer voice.
     * Engineering sees code logs but lacks revenue context.
5. **How It Works (`HowItWorksSection.tsx`):**
   * Step-by-step multi-agent architecture breakdown:
     1. Planning (Deconstruct question into domain hypotheses).
     2. Specialist Investigation (Parallel read-only queries to Zendesk, PostHog, Jira).
     3. PM Synthesis (Epistemic separation into Facts, Inferences, Hypotheses).
     4. Adversarial Critic Review (Bounded challenge loop with PASS/REVISE verdict).
6. **Evidence Proof Section (`EvidenceProofSection.tsx`):**
   * Demonstrates canonical evidence IDs (`[EV-001]`), source attribution badges, and contradiction detection.
7. **Evaluation Section (`EvaluationSection.tsx`):**
   * Displays formal benchmark results from Phase 9:
     * Grounding Accuracy: `18–20 / 20`
     * Contradiction Handling: `100% detection`
     * Multi-Agent vs. Single-Agent comparative metrics.
8. **Footer (`LandingFooter.tsx`):**
   * Architectural boundaries disclosure: Read-only external access, zero synthetic hallucinations, LangGraph orchestration.

---

### 2.2 Investigation Launchpad (`/investigations`)

* **File:** `src/app/investigations/page.tsx`
* **Rendering Mode:** Client Component.
* **Layout:** Wrapped inside `WorkspaceShell.tsx` (navigation sidebar visible).

#### Screen Structure:
1. **Header:**
   * Title: `Product Investigations`
   * Subtitle: `Ask an open product question or select a verified discovery scenario.`
2. **Inquiry Input Card (`NewInquiryInput.tsx`):**
   * Large textarea with placeholder: *"e.g., Why are enterprise checkout conversion rates dropping after the v2.4 mobile release?"*
   * Character counter (0 / 2000).
   * Launch button: `Start Investigation` (`primary-md`).
   * Subtext: *"Pocket will plan hypotheses, query support tickets, analyze product telemetry, and inspect engineering bugs."*
3. **Pre-configured Scenario Cards:**
   * Grid of 3 verified scenario templates for instant zero-friction evaluation:
     * **Scenario 1:** Checkout Settlement Status Delay (`inv_p12a_scenario_1`).
     * **Scenario 2:** Mobile Onboarding Verification Drop-off.
     * **Scenario 3:** Legacy Webhook Deprecation Impact.
   * Clicking a card automatically populates and submits the inquiry.
4. **Recent Inquiries Table (`RecentInquiriesTable.tsx`):**
   * Authoritatively hydrated from `GET /api/v1/investigations`.
   * Columns: `Investigation ID`, `Question`, `Status`, `Duration`, `Date`, `Action`.
   * Click navigates to `/investigations/[id]`.
   * **State Boundary & Known Limitation:**
     * Investigation records are process-local on the backend (`InvestigationManager`).
     * Browser refresh fetches the currently active/recent investigations from the running FastAPI instance.
     * Backend restart clears process-local investigations by design.
     * **No Pseudo-Persistence:** The frontend does not store investigation records in browser `localStorage`. Durable, cross-session persistence is deferred to a future database phase.

---

### 2.3 Investigation Workspace (`/investigations/[id]`)

* **File:** `src/app/investigations/[id]/page.tsx`
* **Rendering Mode:** Client Component.
* **URL Parameter:** `id` (e.g., `inv_p12a_scenario_1` or auto-generated UUID).
* **Backward Compatibility Query Param:** Supports `/?investigation_id=...` redirecting seamlessly to `/investigations/[id]`.

#### Screen Structure & Reading Hierarchy:
1. **Workspace Sticky Header (`WorkspaceHeader.tsx`):**
   * Top bar (56px) with breadcrumbs (`Pocket / Investigations / {id}`).
   * Status Pill (`Completed`, `Executing`, `Failed`).
   * Active Agent Badge (during execution).
   * Elapsed time indicator.
   * Evidence Drawer Toggle button with item count badge (`Evidence Ledger (18)`).
2. **Investigation Question & Cohort Metadata:**
   * `h1`: The investigated question in crisp 24px bold typography.
   * Metadata row: Investigation ID, timestamp, elapsed duration, LangSmith trace link.
3. **Elevated Recommendation Panel (`RecommendationPanel.tsx`):**
   * **Visual Priority:** Appears at the very top of the reading canvas (immediately visible within first viewport at 1440×900 and 390×844).
   * Header: `PRIMARY RECOMMENDATION` badge + Action type + `HIGH CONFIDENCE`.
   * Body: Clear, actionable PM recommendation statement.
   * Success metrics & risks bullet points.
4. **Executive Problem Statement & Affected Cohort (`ExecutiveFinding.tsx`):**
   * `h2`: "Executive Finding & Problem Context".
   * Synthesizes what is happening, who is affected (e.g., *"Users transacting between 14:00–16:00 UTC with third-party banking rails"*), and why it matters to business metrics.
5. **Epistemic Findings Flow (`EpistemicFlow.tsx`):**
   * `h2`: "Evidence-Backed Findings".
   * Continuous editorial reading flow with 3px color-coded left gutter borders:
     * **Factual Observations (Emerald gutter):** Direct facts from tickets, telemetry, and Jira bugs.
     * **Inferences (Blue gutter):** Deductions synthesized across multiple sources.
     * **Hypotheses (Amber gutter):** Plausible explanations requiring further validation.
   * All findings contain interactive `CitationPill` components (`[EV-001]`).
6. **Contradictions & Tensions Banner (`TensionsBanner.tsx`):**
   * Explicit disclosure of conflicting evidence (e.g. user perceptions vs. backend truth).
7. **Limitations & Data Gaps Banner (`LimitationsBanner.tsx`):**
   * Data sources with zero records or telemetry coverage gaps.
8. **Critic Review Accordion (`CriticAccordion.tsx`):**
   * Adversarial review verdict (`PASS` / `REVISE`).
   * Number of revision cycles completed.
   * Critique summary detailing challenges raised and how the PM addressed them.
9. **Evidence Ledger Sheet / Drawer (`EvidenceLedgerSheet.tsx`):**
   * Docked on ultra-wide screens ($\ge 1600\text{px}$).
   * Slide-over modal sheet on standard screens ($< 1600\text{px}$).
   * Complete scrollable list of attributable evidence entries with source badges, quotes, and timestamps.
   * Deep-link target highlighting.

---

## 3. Responsive Screen Layout Matrix

| Viewport | Route `/` | Route `/investigations` | Route `/investigations/[id]` |
| :--- | :--- | :--- | :--- |
| **Ultra-Wide ($\ge 1600\text{px}$)** | Centered 1200px max container | Sidebar (240px) + Launchpad | Sidebar (240px) + Canvas (840px) + Docked Evidence (420px) |
| **Standard Desktop ($1280–1599\text{px}$)** | Centered 1200px container | Sidebar (240px) + Launchpad | Sidebar (240px) + Canvas (840px) + Slide-over Evidence (440px) |
| **Compact Desktop ($1024–1279\text{px}$)** | Centered 960px container | Sidebar (64px) + Launchpad | Sidebar (64px) + Canvas (840px) + Slide-over Evidence (440px) |
| **Tablet ($768–1023\text{px}$)** | Full width with 24px padding | Off-canvas Sidebar + Launchpad | Off-canvas Sidebar + Canvas + Slide-over Evidence (400px) |
| **Mobile ($< 768\text{px}$)** | Stacked, mobile nav modal | Stacked Launchpad, full-width | Full-width Canvas + Fullscreen 100vw Evidence Sheet |

---

## 4. Route Error & Loading Boundaries

* **`loading.tsx` (Investigation Workspace):**
  * Displays a light-first editorial skeleton screen matching the workspace layout (header, recommendation box outline, 3 epistemic row outlines).
* **`error.tsx` (Investigation Workspace):**
  * Catches unhandled runtime exceptions.
  * Displays clear error message, request correlation ID, and a "Retry Loading" button without reloading the whole application shell.
* **`not-found.tsx`:**
  * Clean, minimal 404 screen with link to `/investigations`.
