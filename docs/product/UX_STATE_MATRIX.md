# Pocket AI Product Discovery Team
## Product UX State Matrix

**Document Version:** 1.1  
**Status:** Approved Specification (Step 1 Approved)  
**Related Documents:**
- [UX Product Specification](UX_PRODUCT_SPEC.md)
- [Investigation Workspace Specification](INVESTIGATION_WORKSPACE_SPEC.md)
- [Data & API Specification](../api/DATA_API_SPECIFICATION.md)

---

# 1. Overview & Verification Policy

The Pocket application manages asynchronous multi-agent lifecycles, network streaming, partial source outages, and user collaboration. 

To maintain technical honesty:
- Every state below is explicitly tagged as **[SUPPORTED NOW]** or **[REQUIRES FUTURE API SUPPORT]**.
- In the initial frontend implementation, the UI must strictly render supported API payloads without fabricating synthetic progress bars, simulated item counters, or fake agent activity.

---

# 2. Comprehensive UX State Matrix

| State Identifier | Implementation Status | Trigger Condition | Visual Presentation | User Actions Available | Underlying API State |
|---|---|---|---|---|---|
| **ST-01: First Visit / Landing** | **[SUPPORTED NOW]** | User navigates to root domain `/` without active session. | Clean landing interface with value statement, interactive sample brief teaser, and action button. | Click "Start Investigation", Explore sample brief. | Static/client-side route. |
| **ST-02: Launchpad (Empty)** | **[SUPPORTED NOW]** | User navigates to `/app` or clicks "+ New Investigation". | Minimalist, focused query composer centered on page. Prompt suggestions by domain. Integration status strip in footer. | Type query in textarea, Click sample prompt chip. | `GET /api/v1/health` verifies backend dependencies. |
| **ST-03: Query Composition** | **[SUPPORTED NOW]** | User types in query textarea. | Character counter displayed (max 2,000 chars). "Investigate" button activates. Prompt suggestions collapse. | Submit query (`Enter` or button), Clear text. | Client-side validation: trimmed length $\in [1, 2000]$. |
| **ST-04: Submission & Init** | **[SUPPORTED NOW]** | User clicks "Investigate". | Button shows inline spinner. URL updates to `/app/investigations/:new_id`. Stepper renders with Stage 1 active. | View initialization state. | HTTP 202 `POST /api/v1/investigations` returning `InvestigationSummaryResponse`. |
| **ST-05: Planning Stage** | **[SUPPORTED NOW]** | Backend begins graph execution. | Header displays query and elapsed timer. Stepper shows `1. Planning` active with pulsating badge. Subtext: *"Formulating investigation objectives..."* | View progress. | `status="planning"`, `active_agent="planner"`, SSE milestone received. |
| **ST-06: Gathering Evidence** | **[SUPPORTED NOW]** | Specialists query mocks/PostHog in parallel. | Stepper shows `2. Specialists` active. Progress subtext: *"Specialists retrieving customer support, analytics, and engineering context..."* | View progress. *(Note: Live item-by-item counter requires future SSE event).* | `status="gathering_evidence"`, `active_agent="specialists"` (or specific specialist). |
| **ST-07: Synthesizing** | **[SUPPORTED NOW]** | PM Agent synthesizes evidence. | Stepper shows `3. PM Synthesis` active. Subtext: *"Synthesizing multi-source findings and establishing epistemic separation on frontier model..."* | View progress. | `status="synthesizing"`, `active_agent="pm"`. |
| **ST-08: Reviewing (Critic)** | **[SUPPORTED NOW]** | Adversarial Critic evaluates candidate. | Stepper shows `4. Critic Review` active. Subtext: *"Adversarial critic challenging ungrounded claims and causal leaps..."* | View progress. | `status="reviewing"`, `active_agent="critic"`. |
| **ST-09: Revising** | **[SUPPORTED NOW]** | Critic returned REVISE; PM revising. | Stepper shows `4. Critic Review` with revision indicator `(Revision 1 of 1)`. Subtext: *"Addressing critique issues on high-throughput model..."* | View progress. | `status="revising"`, `active_agent="pm_revision"`. |
| **ST-10: Completed (Normal)** | **[SUPPORTED NOW]** | Investigation completes & validates. | Full Investigation Workspace rendered: Editorial Problem Statement, Recommendation, Epistemic Findings Panel, Contradictions, Limitations, Critic Accordion, and Evidence Ledger drawer. | Click citations, Filter evidence drawer, Search evidence. *(Share/PDF export require future API wiring).* | `status="completed"`, HTTP 200 `GET /api/v1/investigations/:id/result`. |
| **ST-11: Insufficient Evidence** | **[SUPPORTED NOW]** | Data sources lack metrics/tickets for query. | Completed workspace renders with prominent amber `LOW CONFIDENCE` badge. Recommendation explicitly states `INVESTIGATE FURTHER` with telemetry advice. | Review unpopulated/zero-count evidence cards, Inspect limitations. | `status="completed"`, `confidence="low"`, `recommendation_type="investigate_further"`. |
| **ST-12: Partial Source Failure** | **[SUPPORTED NOW]** | One external source (e.g. Jira) times out/fails. | Completed workspace renders normally but includes a prominent **Degraded Source Warning**: *"Jira was unreachable during this investigation. Findings are derived exclusively from Zendesk and PostHog."* | View available evidence, Review limitations section highlighting missing engineering context. | `status="completed"`, evidence ledger contains explicit source outage limitations. |
| **ST-13: Execution Failed** | **[SUPPORTED NOW]** | Unrecoverable infrastructure or LLM error. | Friendly error banner: *"Investigation could not be completed."* Explanatory card stating failure category (e.g., *Model provider timeout*). "Retry Investigation" button. | Click "Retry Investigation", Return to launchpad. | `status="failed"`, HTTP 500 on result endpoint with sanitized error message. |
| **ST-14: In-Flight Cancellation** | **[REQUIRES FUTURE API SUPPORT]** | User clicks "Cancel" to abort running run. | Status pill displays `Cancelled`. Elapsed timer freezes. Partial evidence collected before cancellation remains browsable in drawer. | Re-run investigation, Return to Launchpad. | Schema defines `status="cancelled"` and HTTP 410, but `POST /cancel` endpoint is not yet wired. |
| **ST-15: Reconnecting Stream** | **[SUPPORTED NOW]** | User refreshes page or network drops during run. | Small non-blocking top banner: *"Reconnecting to live stream..."* Client fetches latest snapshot via GET and resumes SSE stream. | Wait for reconnect, View cached state. | SSE reconnection with `last-event-id` header; fallback to polling `GET /api/v1/investigations/:id`. |
| **ST-16: API Unavailable** | **[SUPPORTED NOW]** | Backend server is unreachable (HTTP 502/503/Offline). | Persistent full-width banner: *"Unable to connect to Pocket API server. Retrying in 5s..."* Input form disabled. | Retry Now button, Check status link. | Network fetch error or HTTP 5xx. |
| **ST-17: Empty History** | **[SUPPORTED NOW]** | User opens `/app/history` with 0 runs in memory. | Clean empty-state graphic. Subtext: *"No investigations recorded in the current session. Submit a new question to start."* | Click "+ New Investigation" CTA. | `GET /api/v1/investigations` returns `[]`. |
| **ST-18: Read-Only Shared View** | **[REQUIRES FUTURE API SUPPORT]** | External stakeholder visits `/share/:token`. | Streamlined, pristine reading layout. Displays Executive Brief, Epistemic Findings, and Evidence Drawer. Edit buttons, internal token stats, and admin actions hidden. | Read brief, Click citations, Export PDF. | Requires public token generation and snapshot endpoints. |
| **ST-19: Durable Revisit (Restart)**| **[REQUIRES FUTURE API SUPPORT]** | User attempts to reopen an investigation after server restart. | In current runtime, returns 404. In target state, loads permanently persisted record from database storage. | Browse past records. | Requires database persistence layer. |
