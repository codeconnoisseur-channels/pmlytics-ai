# Pocket AI Product Discovery Team
## UX & Product Experience Specification

**Document Version:** 1.1  
**Status:** Approved Specification (Step 1 Approved)  
**Related Documents:**
- [PRD](PRD.md)
- [Product Specification](PRODUCT_SPECIFICATION.md)
- [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)
- [Agent Specification](../architecture/AGENT_SPECIFICATION.md)
- [ADR-0014: Frontend Product Experience Architecture](../decisions/ADR-0014-frontend-product-experience.md)

---

# 1. Product Definition & Context

### 1.1 What is Pocket?
**Pocket is an AI product investigation workspace that helps product teams turn fragmented customer, behavioral, and engineering evidence into a structured, evidence-backed product assessment.**

It is designed to support, rather than replace, product manager judgment. Pocket coordinates specialist AI agents that collect evidence across customer support, product telemetry, and engineering issue trackers, synthesizes findings under strict epistemic discipline, subjects the result to an adversarial critique, and presents a defensible product recommendation.

### 1.2 Current Implementation vs. Target Product

To maintain architectural integrity, this specification strictly distinguishes what is implemented today from what is planned for future product phases:

| Dimension | Current Implementation (Phases 11–12A) | Target Product (Phase 13+ Roadmap) |
|---|---|---|
| **Backend & Orchestration** | **Authoritative:** FastAPI + LangGraph stateful multi-agent DAG. | **Preserved:** FastAPI + LangGraph orchestration remains authoritative; future additive endpoints support persistence, sharing, and auth. |
| **Runtime Persistence** | **Process-Local:** Investigations and evidence ledgers reside in volatile server memory (`InvestigationManager`). In-memory history is lost upon server restart. | **Durable Persistence Layer:** Investigations, evidence ledgers, and critique records persisted to durable database storage across sessions. |
| **Identity & Access** | **Unauthenticated Local Service:** Open local/internal API without accounts, logins, or user ownership. | **Staged Identity Model:** Initial guest demo session + basic authenticated user accounts; later workspace membership and team roles. |
| **Artifact Durability & Sharing** | **Ephemeral Local View:** Single-page prototype with local URL parameter (`?investigation_id=...`). | **Durable Artifacts & Permalinks:** Shareable read-only links (`/share/:token`), executive PDF export, and team bookmarks. |
| **Frontend Architecture** | **V0 Prototype:** Vanilla HTML/CSS/JS served directly from FastAPI static files mount. | **Modern Frontend Workspace:** Decoupled Next.js / React application consuming FastAPI backend APIs. |

### 1.3 The Primary User
- **Role:** Product Managers (PMs), Technical Product Managers (TPMs), and Product Operations Leads.
- **Context:** Managing digital products (modeled on a consumer fintech domain with payments, cross-border transfers, and onboarding).
- **Core Frustration:** When a metric drops or user complaints spike, evidence is fragmented across Zendesk, PostHog, and Jira. Gathering data, reconciling vocabulary, distinguishing correlation from causation, and synthesizing findings takes hours of manual, ad-hoc investigation.

### 1.4 The Primary User Job
> *"When an unexpected symptom or product question arises, help me rapidly understand what customers are reporting, what telemetry actually shows, and what engineering knows—highlighting where they contradict and identifying what is unverified—so I can make an evidence-backed, defensible prioritization decision."*

### 1.5 Core User Journey (Target State)
```text
1. First Visit / Demo Entry → 2. Query Submission → 3. Multi-Source Evidence Gathering
         ↓
6. Save / Export / Revisit ← 5. Finalized Decision ← 4. Synthesis & Adversarial Review
```

---

# 2. What Makes Pocket Feel Like Real Product Software (Not an AI Demo)

General AI chat interfaces fail product teams because they present unverified assertions in unstructured prose, suffer from conversational drift, and lack institutional accountability. Pocket establishes credibility through deliberate product design:

| AI Demo Anti-Pattern | Pocket Product Experience |
|---|---|
| **Chat bubble conversational stream** | **Structured Analytical Workspace** with clear editorial hierarchy (Executive Problem Statement, Epistemic Findings, Actionable Recommendation). |
| **Unsubstantiated factual claims** | **100% Attributable Evidence Ledger** with clickable citations mapping directly to authentic underlying records (tickets, funnels, issues). |
| **Collapsed certainty & causal overreach** | **Strict Epistemic Separation** distinguishing observed **Facts**, inductive **Inferences**, and provisional **Hypotheses**. |
| **Sycophantic agreement** | **Embedded Adversarial Critic** that actively challenges unsupported leaps, missing evidence, and unearned confidence before publication. |
| **Ephemeral chat history** | **Durable Investigation Artifacts** (target state) that can be revisited, shared via link, audited, and exported as professional PDF briefs. |
| **Flashing neon futuristic styling** | **Calm, Dense, Typography-First Analytical Tool** designed for high reading comprehension and executive review. |

---

# 3. Formal Reading Hierarchy: Time-to-Insight UX Principle

The completed investigation workspace is structured around four distinct reading timeframes to accommodate executive triage, deep analytical work, and evidentiary audits without requiring separate screens:

- **15 seconds (Immediate Awareness):**
  - The user grasps *what is happening*: the investigation query, current execution status (`completed`, `revising`, `failed`), and elapsed duration.
- **30 seconds (Executive Takeaway):**
  - The user grasps Pocket's *main conclusion and recommendation*: the synthesized Problem Statement, the Action Type badge (e.g. `INVESTIGATE FURTHER`, `REMEDIATE`), the Primary Recommendation text, and the Confidence rating (`High`, `Medium`, `Low`).
- **60 seconds (Analytical Evaluation):**
  - The user grasps the *principal evidence and uncertainty*: key verified Facts, the Contradictions & Tensions banner, and Disclosed Limitations (what telemetry or tickets failed to show).
- **3 minutes (Evidentiary Audit):**
  - The user can *audit the underlying reasoning in detail*: clicking inline citation badges (`[EV-001]`), inspecting the concise source summary, expanding bounded underlying customer conversations, aggregate metric details, or engineering issues, and searching their customer-safe source references. Raw user-level analytics events and internal implementation detail are not exposed.

---

# 4. Avoiding the "Card Wall" Dashboard Trap

To prevent the workspace from deteriorating into a noisy, disconnected dashboard of stacked rounded rectangles, the interface enforces strict distinctions between UI surface types:

1. **Editorial Reading Flow (Document Typography):**
   - The Executive Problem Statement and Primary Recommendation render as cohesive, clean typography with disciplined line heights and bold lead-ins. They are framed with subtle structural borders rather than floating inside heavy card containers.
2. **Analytical Panels (Structured Data):**
   - The Epistemic Findings Deck uses clear tabular or bordered panel layouts with semantic left accent bars (Emerald for Facts, Blue for Inferences, Amber for Hypotheses), treating findings as a structured analytical document.
3. **Alerts & Tension Banners:**
   - Contradictions and Disclosed Limitations render as full-width callout banners with warm, low-saturation backgrounds (amber/rose tints) to signal evidentiary caution without breaking document flow.
4. **Interactive Evidence Surfaces (Docked/Slide-Out Drawer):**
   - The Evidence Ledger is housed in a dedicated side-panel surface with independent scrolling, search, and source-filtering tabs, keeping the primary reading canvas focused.
5. **Bounded Cards (Strictly Controlled):**
   - Card styling is reserved exclusively for atomic, self-contained interactive items: individual evidence items within the ledger drawer, investigation preview tiles in the history archive, and connection status cards in settings.

---

# 5. Staged Authentication & Identity Model

To avoid burdening early product implementation with unnecessary enterprise infrastructure, identity is staged pragmatically:

### 5.1 Initial Implementation (Phase 13 Target)
- **Guest Demo Session:** Allows immediate exploration of pre-computed canonical scenario investigations or execution of an ephemeral investigation without sign-up.
- **Basic Authenticated User Accounts:** Simple email/password sign-up and sign-in with secure HTTP-only session cookies.
- **Investigation Ownership:** Investigations created by an authenticated user are associated with their account ID in application storage.
- **Session Claiming:** Unauthenticated demo investigations can be claimed into an authenticated account upon sign-up.

### 5.2 Later Horizons (Post-MVP Roadmap)
- **Team Workspaces & Organization Membership:** Multiple PMs sharing an organizational workspace.
- **Role-Based Access Control (RBAC):** Admin (manages API keys and model routing), Investigator (creates/edits investigations), Viewer (read-only access).
- **OAuth Providers:** Google Workspace / GitHub OAuth for corporate logins.
- **Enterprise SAML / SSO:** Added only when required by enterprise governance and justified by product scale.

---

# 6. Persistence Semantics & Invariants

### 6.1 Target State Semantics
- In the target product, completed investigations are durable, permanent records.
- Persisted records include: the user query, timestamp, duration, full `ProductRecommendation` payload, authoritative Evidence Ledger dictionary, Critic review log, and execution telemetry summary.

### 6.2 Strict Invariant: Persistent History $\neq$ Cross-Investigation Agent Memory
A foundational architectural invariant established in the [PRD](PRD.md), the original local agent operating contract, and the [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md) is strictly preserved:

> [!IMPORTANT]
> **No Hidden Cross-Investigation Agent Memory**:
> - **Persistent History (Target Feature):** Allows users to search, browse, reopen, and export past investigations.
> - **Clean Agent Context (Strict Rule):** When an agent begins a *new* investigation, it executes with a completely clean context window. It must **never** silently inherit assumptions, past findings, or biases from prior investigations. Every new inquiry must be grounded exclusively in freshly retrieved evidence.

---

# 7. Responsive & Accessibility Requirements

### 7.1 Viewport Adaptations
- **Desktop ($\ge 1200\text{px}$):** Primary analytical workspace. Left collapsible navigation rail (64px / 240px), center reading canvas (840px max width), right docked/collapsible Evidence Ledger (420px).
- **Tablet ($768\text{px} - 1199\text{px}$):** Single reading canvas with floating toggle for Evidence Drawer. Sidebar collapses to icon drawer.
- **Mobile ($< 768\text{px}$):** Dedicated executive triage view. Stacked query header, executive recommendation, tabbed findings view, and full-screen modal for evidence inspection.

### 7.2 Accessibility & Usability Standards (Targeted for Validation)
- **Semantic HTML:** Native `<main>`, `<nav>`, `<header>`, `<section>`, `<article>`, and heading hierarchy (`h1`-`h3`).
- **Color Contrast:** Target WCAG 2.1 AA compliance ($\ge 4.5:1$ for body text, $\ge 3:1$ for large headings and badges).
- **Keyboard Operability:** Full tab navigation; citation pills (`[EV-001]`) operable via `Enter`/`Space` to focus drawer; `Escape` closes drawers.
- **Screen Reader Support:** `aria-live="polite"` regions for live status updates and citation focus shifts.
- **Reduced Motion:** Respects `prefers-reduced-motion: reduce`, disabling stepper pulses and sliding drawer transitions in favor of instant opacity toggles.
