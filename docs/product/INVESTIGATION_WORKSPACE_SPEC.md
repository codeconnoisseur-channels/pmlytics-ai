# Pocket AI Product Discovery Team
## Investigation Workspace Screen Specification

**Document Version:** 1.1  
**Status:** Approved Specification (Step 1 Approved)  
**Related Documents:**
- [UX Product Specification](UX_PRODUCT_SPEC.md)
- [Information Architecture](INFORMATION_ARCHITECTURE.md)
- [UX State Matrix](UX_STATE_MATRIX.md)
- [Data & API Specification](../api/DATA_API_SPECIFICATION.md)

---

# 1. Screen Philosophy & Anti-Card-Wall Principle

The **Investigation Workspace** (`/app/investigations/:id`) is an editorial analytical workspace, not an AI dashboard. 

### 1.1 Avoiding the "Card Wall" Trap
Many AI interfaces arrange every finding, metric, and paragraph into identical stacked rounded rectangles, creating visual noise, poor vertical rhythm, and reading fatigue. The Pocket workspace avoids this by distinguishing between five distinct surface types:

1. **Editorial Reading Flow:** The Executive Problem Statement and Primary Recommendation render as a continuous, document-grade reading experience with high typographic fidelity and bold lead-ins.
2. **Analytical Panels:** The Epistemic Findings Deck uses clear tabular rows with semantic left border accents (Emerald for Facts, Blue for Inferences, Amber for Hypotheses), treating findings as a structured analytical document.
3. **Alerts & Tension Banners:** Full-width callout banners with subtle warm/tinted backgrounds for Contradictions and Disclosed Limitations.
4. **Interactive Evidence Surface:** A docked or slide-out drawer housing the authoritative Evidence Ledger with independent scrolling, search, and source-filtering tabs.
5. **Bounded Cards (Strictly Controlled):** Reserved exclusively for atomic interactive elements: individual evidence items in the drawer and historical preview tiles.

---

# 2. The Formal Reading Hierarchy (Time-to-Insight)

The layout directly enforces the product's reading hierarchy:

```text
+---------------------------------------------------------------------------------------------------------+
| [15 SECONDS: AWARENESS]                                                                                 |
| Header: Query Title | Status Pill (Completed/Running) | Elapsed Timer (01:48) | Actions (Share, Export) |
+---------------------------------------------------------------------------------------------------------+
| Live Pipeline Strip: [Planning ✓] -> [Specialists ✓] -> [Synthesis ✓] -> [Critic ✓] -> [Finalized ✓]   |
+-----------------------------------------------------------------------+---------------------------------+
| [30 SECONDS: EXECUTIVE TAKEAWAY]                                      | [3 MINUTES: EVIDENCE AUDIT]     |
|                                                                       |                                 |
| 1. Executive Problem Statement & Affected Cohort (Editorial Flow)     | Evidence Ledger Drawer (420px)  |
| 2. Actionable Recommendation Banner:                                  |                                 |
|    - Action Type Badge (e.g. "INVESTIGATE FURTHER")                   | Source Filter Tabs:             |
|    - Primary Recommendation Text                                      | [All: 13] [Zendesk: 5]          |
|    - Confidence Gauge & Rationale (Low / Medium / High)               | [PostHog: 4] [Jira: 4]          |
|    - Success Metrics & Operational Risks                              |                                 |
|                                                                       | Search: [Filter evidence...   ] |
| [60 SECONDS: ANALYTICAL EVALUATION]                                   |                                 |
|                                                                       | Evidence Card [EV-003]:         |
| 3. Epistemic Findings Panel (Structured Document Rows):               | [Zendesk] TICKET-1042           |
|    - Observed Facts (100% cited [EV-001] [EV-003])                    | "Customer reports transfer      |
|    - Logical Inferences (Inductive interpretations)                   |  stuck in pending status."      |
|    - Working Hypotheses (Provisional explanations)                    | Confidence: High                |
|                                                                       |                                 |
| 4. Contradictions & Evidentiary Tensions (Callout Banner)             | Evidence Card [EV-007]:         |
|    - Discrepancies between Support, Telemetry & Engineering           | [Jira] PAY-892                  |
|                                                                       | "Timeout in callback hook"      |
| 5. Disclosed Limitations & Evidence Gaps (Warning Banner)             | Confidence: Medium              |
|    - Unmeasured variables and telemetry coverage gaps                |                                 |
|                                                                       | Evidence Card [EV-011]:         |
| 6. Adversarial Critic Review (Collapsible Audit Accordion)            | [PostHog] funnel:checkout       |
|    - Decision: PASS | Revisions: 1 | Issues Addressed: 6              | "No conversion drop in v2.4"    |
+-----------------------------------------------------------------------+---------------------------------+
```

---

# 3. Live UI Elements: Current vs. Target API Capability Matrix

To ensure the UI never presents simulated or fabricated data, every live element is classified against the current backend API:

| Workspace UI Feature | Proposed Interaction | Implementation Status | Current API Endpoint / Source | Target / Future Work Required |
|---|---|---|---|---|
| **Investigation Status Transitions** | Stepper updates dynamically (`planning`, `gathering_evidence`, `synthesizing`, `reviewing`, `revising`, `completed`). | **SUPPORTED NOW** | SSE `/api/v1/investigations/:id/events` and `GET /api/v1/investigations/:id`. | None. Fully supported by LangGraph lifecycle. |
| **Elapsed Execution Timer** | Real-time ticking MM:SS timer during execution. | **SUPPORTED NOW** | Client-side timer initialized from `created_at` or updated via `elapsed_seconds`. | None. |
| **Active Agent Moniker** | Displays currently executing agent (e.g. `planner`, `research_agent`, `pm`). | **SUPPORTED NOW** | `InvestigationStatusResponse.active_agent`. | None. |
| **Completed Recommendation Payload** | Problem statement, recommendation, confidence, success metrics, risks. | **SUPPORTED NOW** | `GET /api/v1/investigations/:id/result` returning `ProductRecommendationSchema`. | None. |
| **Epistemic Findings Deck** | Facts, Inferences, Hypotheses with citations. | **SUPPORTED NOW** | `ProductRecommendationSchema.factual_observations`, `.inferences`, `.hypotheses`. | None. |
| **Authoritative Evidence Ledger** | Complete dictionary of attributable evidence items with excerpts. | **SUPPORTED NOW** | `InvestigationDetailResponse.evidence_ledger` (populated on completion). | None. |
| **Inline Citation Deep Linking** | Clicking `[EV-001]` scrolls to and highlights evidence item. | **SUPPORTED NOW** | Client-side DOM navigation mapping citation ID to ledger dictionary key. | None. Pure frontend capability. |
| **Critic Review Outcome** | Decision (`PASS`/`REVISE`), revisions completed, and addressed issues log. | **SUPPORTED NOW** | `InvestigationDetailResponse.critic_review`. | None. |
| **Execution Telemetry Summary** | Total LLM calls, total tokens, provider cost. | **SUPPORTED NOW** | `InvestigationDetailResponse.telemetry_summary`. | None. |
| **Live Incremental Evidence Counts** | Live count of evidence items ticking up *during* gathering stage. | **REQUIRES FUTURE API SUPPORT** | Current SSE emits macro stage events; does not emit item-by-item evidence events. | Add incremental `evidence_added` SSE event to backend streaming generator. |
| **Source-Specific Parallel Progress** | Independent progress bars for Zendesk vs. PostHog vs. Jira. | **REQUIRES FUTURE API SUPPORT** | Backend executes specialists concurrently inside a single graph node `specialists`. | Add per-specialist sub-task progress events to SSE stream. |
| **Live Revision Issue Counts** | Real-time counter of Critic issues *while* revising is in progress. | **REQUIRES FUTURE API SUPPORT** | Current SSE notifies `revising` stage, but issue list is only in finalized payload. | Add `critic_critique` event with issue count to SSE stream. |
| **In-Flight Cancellation** | "Cancel" button to abort an active LangGraph execution. | **REQUIRES FUTURE API SUPPORT** | Schema defines `status="cancelled"` and HTTP 410, but `/cancel` route is not yet wired. | Implement `POST /api/v1/investigations/:id/cancel` endpoint and task cancellation. |
| **Durable Revisit Across Restarts** | Opening an investigation after server restart. | **REQUIRES FUTURE API SUPPORT** | Current backend uses in-memory dictionary; server restart clears history. | Implement persistent database storage layer for completed records. |
| **Share Link Token Generation** | Creating public read-only link `/share/:token`. | **REQUIRES FUTURE API SUPPORT** | No token generation or public snapshot endpoint exists. | Implement `POST /share` and `GET /api/v1/share/:token` endpoints. |

> [!IMPORTANT]
> **Strict Rendering Rule**: In Step 2 frontend development, any feature classified as `REQUIRES FUTURE API SUPPORT` must display a clean, honest fallback (e.g. showing "Gathering evidence from support, analytics, and engineering..." rather than a fabricated progress bar or synthetic item counter).

---

# 4. Section-by-Section Screen Specification

## 4.1 Header & Status Area
- **Purpose:** Identifies the active inquiry and reports execution status.
- **Priority:** High (Sticky at top).
- **Structure:**
  - Query Title: Rendered in clear `h1` typography (20px, bold).
  - Status Pill: Real-time badge (`Planning`, `Gathering Evidence`, `Synthesizing`, `Reviewing`, `Revising`, `Completed`, `Failed`).
  - Timer: Ticking duration counter.
  - Action Toolbar: `Share` (Target), `Export PDF` (Target), `Bookmark` (Target).

## 4.2 Executive Diagnosis (Editorial Flow)
- **Purpose:** Immediate executive comprehension.
- **Structure:**
  - **Problem Statement:** 2–3 sentence synthesized summary.
  - **Why It Matters:** Business/product impact.
  - **Affected Users:** Defined user cohort or segment.
- **Styling:** Cohesive editorial reading layout; no unnecessary card borders.

## 4.3 Actionable Recommendation
- **Purpose:** Clear decision guidance.
- **Structure:**
  - **Action Type Badge:** Styled by category (`INVESTIGATE FURTHER`, `REMEDIATE`, `MONITOR`, `NO ACTION`).
  - **Recommendation Text:** Concrete immediate next steps.
  - **Confidence Gauge & Rationale:** Explicit rating (`High`, `Medium`, `Low`) with transparent explanation of evidentiary limitations.
  - **Success Metrics & Risks:** Bulleted criteria and operational risks.

## 4.4 Epistemic Findings Panel (Structured Analytical Rows)
- **Purpose:** Critical thinking through epistemic separation.
- **Structure:**
  - **Observed Facts:** Verified data points with interactive citations (e.g. `[EV-001]`). Semantic Emerald left accent.
  - **Logical Inferences:** Inductive interpretations derived from facts. Semantic Sapphire left accent.
  - **Working Hypotheses:** Provisional causal explanations requiring technical validation. Semantic Amber left accent.

## 4.5 Contradictions & Evidentiary Tensions
- **Purpose:** Surfaces cross-system conflicts.
- **Structure:**
  - Callout alert banner highlighting tensions between customer complaints, telemetry, and engineering status.

## 4.6 Disclosed Limitations & Evidence Gaps
- **Purpose:** Explicit accounting of what is unmeasured or unproven.
- **Structure:**
  - Callout alert banner detailing telemetry blind spots, small sample sizes, or missing segmentations.

## 4.7 Adversarial Critic Review (Audit Trail)
- **Purpose:** Transparent accountability of adversarial vetting.
- **Structure:**
  - Collapsible accordion displaying Critic decision (`PASS`/`REVISE`), revision count, critique summary, and addressed challenges.

## 4.8 Evidence Ledger Drawer (Interactive Surface)
- **Purpose:** Authoritative audit trail for all claims.
- **Structure:**
  - Right-docked or slide-out drawer (420px width).
  - Source filter tabs (`All`, `Zendesk`, `PostHog`, `Jira`).
  - Search filter input.
  - Individual evidence cards containing Ledger ID (`EV-001`), Source Reference (`TICKET-1042`), Finding summary, verbatim Support excerpt, and confidence.
  - Deep-linking: Clicking any inline citation in the main canvas opens the drawer, scrolls to the card, and highlights it with an attention glow.
