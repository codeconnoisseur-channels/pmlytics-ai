# PMLytics AI: Product and Architecture

This document explains what was built, why AI is appropriate, and how the current architecture supports evidence-grounded product decisions. Detailed schemas and implementation contracts remain in the existing specifications and ADRs.

## Product problem

### The user

PMLytics AI is designed for product managers and product leads investigating ambiguous product problems: failed payments, onboarding abandonment, delayed transfers, support spikes, or contradictory customer and behavioural signals.

### The fragmented-evidence problem

A PM rarely gets the answer from one source:

- support tickets are rich in customer language but biased toward people who contact support;
- analytics can quantify behaviour but cannot explain sentiment or intent by itself;
- Jira can reveal known defects and remediation status but does not establish customer impact or causal magnitude.

The manual alternative is to search each system, align time periods and terminology, reconcile contradictions, decide which evidence is trustworthy, and write a recommendation. That work is slow and often non-reproducible. It also creates predictable judgement errors: treating ticket volume as prevalence, treating issue priority as impact, or treating temporal correlation as causation.

## Why AI

### Why a dashboard is insufficient

A dashboard is strong when the metrics and questions are known in advance. The questions PMLytics AI handles are open-ended and cross-source. “Why are customers abandoning identity upload?” may require ticket themes, a step funnel, cohort segmentation, issue history, and uncertainty about what is not instrumented. A fixed dashboard can expose the numbers, but it does not plan that investigation or reconcile narrative and operational evidence.

### Why search is insufficient

Search retrieves matching records. It does not decide which sources are needed, distinguish a broad keyword match from a journey-specific match, compare normal and affected periods, or turn conflicting evidence into a bounded recommendation.

### Why a generic chatbot is insufficient

A generic chatbot tends to collapse retrieval, interpretation, and recommendation into one conversational turn. That makes tool permissions, provenance, failures, and causal overreach difficult to audit. It can also treat plausible domain knowledge as if it came from the organisation's data.

### What AI contributes

PMLytics AI uses models for tasks that benefit from language and judgement:

- converting a product question into source-specific investigation tasks;
- selecting focused tool calls within hard permissions;
- extracting patterns from tickets and issues;
- selecting useful analytics queries;
- synthesising incomplete and contradictory evidence;
- calibrating confidence and follow-up questions;
- challenging the recommendation for unsupported claims.

Deterministic code still owns permissions, schemas, budgets, citation identity, routing bounds, terminal status, authentication, and ownership.

## Product job

The product is not trying to produce a perfect root-cause statement on demand. It helps a PM decide:

- whether the premise is supported;
- which customer or product problem is most material;
- what is known, inferred, and still hypothetical;
- whether to act, contain, instrument, test, or investigate further;
- what success would look like;
- what evidence could invalidate the decision.

“Investigate further” is a legitimate outcome when the available evidence cannot support a stronger commitment. It should still be specific about the next evidence needed and the decision that evidence will unlock.

## Why multi-agent

The design uses separate roles because each evidence source has a different epistemic risk and tool boundary. The separation is not a claim that more agents are automatically better. It is a control mechanism whose value must justify added latency and cost.

### Planner / Orchestrator

| Question | Answer |
| --- | --- |
| Purpose | Turn the user's question and time scope into an investigation plan. |
| Responsibility | Select required sources and define source-specific objectives and diagnostic questions. |
| Inputs | User question, investigation scope, configured workflow contract. |
| Outputs | Typed `InvestigationPlan` and specialist tasks. |
| Tool access | No evidence-source tools. |
| Why the boundary exists | Planning should decide what evidence is needed without silently becoming a retriever or answerer. |
| Main failure risk | Over-broad tasks that waste tool calls or encode the user's premise as a conclusion. |

### Research Agent

| Question | Answer |
| --- | --- |
| Purpose | Explain what customers are saying and experiencing. |
| Responsibility | Search relevant support conversations, inspect representative records, preserve customer language, and identify recurring themes and limitations. |
| Inputs | Research task, date scope, Zendesk tool contracts. |
| Outputs | Typed customer findings with evidence references. |
| Tool access | `search_tickets`, `get_ticket`, `get_ticket_comments`. |
| Why the boundary exists | Customer statements must not be blended with analytics or engineering assumptions before provenance is preserved. |
| Main failure risk | Treating complaint volume as population prevalence, or summarising ticket IDs without reading available content. |

### Analytics Agent

| Question | Answer |
| --- | --- |
| Purpose | Explain what users actually did. |
| Responsibility | Define metrics, inspect funnels and segments, establish relevant baselines, and distinguish observed association from causation. |
| Inputs | Analytics task, date scope, PostHog analytics tool. |
| Outputs | Typed analytics findings with query context and evidence references. |
| Tool access | `query_analytics`. |
| Why the boundary exists | Measurement requires a different discipline from interpreting complaints or issue status. |
| Main failure risk | Asking an invalid funnel question, hiding useful tabular results when a scalar is absent, or claiming causality from correlation. |

### Engineering Agent

| Question | Answer |
| --- | --- |
| Purpose | Identify technical and delivery context that may explain the product problem. |
| Responsibility | Search focused issues, inspect status, descriptions, comments, and links, and distinguish active from historical work. |
| Inputs | Engineering task, date scope, Jira tool contracts. |
| Outputs | Typed engineering findings with issue provenance. |
| Tool access | `search_issues`, `get_issue`, `get_issue_comments`, `get_linked_issues`. |
| Why the boundary exists | Jira priority or a keyword match must not automatically become evidence of customer impact or root cause. |
| Main failure risk | Anchoring on a broad, irrelevant issue or overstating engineering context as causal proof. |

### PM Synthesis Agent

| Question | Answer |
| --- | --- |
| Purpose | Turn the evidence into product judgement. |
| Responsibility | Reconcile sources, separate facts/inferences/hypotheses, identify affected users and tensions, recommend an action, calibrate confidence, and define measures and open questions. |
| Inputs | Typed specialist findings, Evidence Ledger summaries, assessment gaps, tool errors, and prior Critic feedback during revision. |
| Outputs | Typed `ProductRecommendation`. |
| Tool access | None. |
| Why the boundary exists | The recommendation should be based on the recorded evidence set, not on new untracked retrieval during synthesis. |
| Main failure risk | Narrative overreach, repeated content, invented targets, or a recommendation stronger than the evidence. |

### Critic Agent

| Question | Answer |
| --- | --- |
| Purpose | Act as a bounded quality gate on the PM candidate. |
| Responsibility | Check grounding, causal discipline, contradictions, magnitude, segmentation, confidence, and recommendation defensibility. |
| Inputs | Candidate recommendation and the same verified evidence context. |
| Outputs | Typed `PASS` or `REVISE` review with evidence-linked issues. |
| Tool access | None. |
| Why the boundary exists | Generation and review have different incentives. A separate review pass can challenge a coherent but unsupported narrative. |
| Main failure risk | Becoming an unbounded perfection loop, penalising reasonable uncertainty, or requesting stylistic rather than material revisions. |

### Why specialists run in parallel

Customer, analytics, and engineering retrieval are independent after planning. LangGraph fans them out concurrently and waits at an assessment barrier. In the ideal case, elapsed specialist time is determined by the slowest branch rather than the sum of all three.

Parallelism does not make model calls free. It can increase provider concurrency and budget reservation pressure. The implementation therefore keeps per-role budgets and central model configuration, while the historical performance work evaluated the critical path rather than simply counting calls.

## Architecture walkthrough

### 1. Authentication

Next.js obtains and refreshes a Supabase session using cookie-backed SSR helpers. Protected routes require a session. API calls attach the Supabase access token as a bearer token.

FastAPI verifies the token against Supabase's JWKS and validates issuer, audience, expiry, signature, and subject. The verified subject is the only trusted user identifier.

### 2. Investigation creation

The user submits a question plus an optional complete date range. The frontend normalises the selected dates to UTC boundaries. FastAPI creates an investigation row owned by the verified user before any model work begins, then launches the workflow as an in-process asynchronous task.

### 3. Planning

The Planner produces typed specialist tasks and required sources. LangGraph conditionally fans out only to the relevant specialist nodes; if planning does not identify sources, all three are used as a safe default.

### 4. Specialist evidence gathering

Each specialist receives only its role-bound tools. A normal Standard specialist path uses one model turn to request a batch of tools and one structured synthesis turn. If structured synthesis is invalid, one additional repair turn is permitted. Date scope is injected deterministically into support and analytics tools so a model-supplied relative range cannot override the PM's explicit period.

### 5. Evidence Ledger

Successful tool results are recorded before specialist synthesis. Ledger IDs are namespaced by role and investigation round. Specialists can cite only those entries, and validation requires the ID, source type, and source reference to agree.

Compact prompt summaries reduce token volume, while typed payloads preserve the richer record for audit and frontend drill-down. This separates prompt efficiency from evidence retention.

### 6. Assessment and optional follow-up

The Assessment node asks whether a material, answerable evidence gap remains. Deterministic routing permits at most one targeted follow-up round, only for an authorised specialist, an identified gap, a new canonical task, and remaining tool/model budget. If useful evidence exists but the gap cannot be closed, the workflow proceeds to synthesis with the limitation. If no usable evidence exists, it finalises without fabricating a report.

### 7. PM synthesis and Critic

The PM creates the candidate recommendation. Deterministic validation checks its evidence references and epistemic structure. The Critic then returns `PASS` or `REVISE`.

Standard mode permits one PM revision; Deep mode permits two. Every revised candidate returns to the Critic. This is important: an earlier optimisation bypassed the final Critic after revision, but that allowed finalisation against a review of a different candidate. ADR-0025 restored the quality gate.

### 8. Finalisation

Final status is deterministic. `completed` requires usable evidence, completed assigned specialists, no tool errors, a valid recommendation, sufficient evidence, a final Critic `PASS`, and no unresolved Critic issues. Otherwise, a useful recommendation becomes `partial`; no usable evidence becomes `failed`.

### 9. Persistence and progress

Lifecycle events are broadcast to authenticated SSE subscribers and persisted. The frontend uses a fetch-based SSE reader because native `EventSource` cannot attach the bearer token. It reconnects with exponential backoff and falls back to status polling after repeated errors. Progress never moves backward when a stale snapshot arrives.

The final state is persisted before a completion event is announced. This ordering prevents the interface from reporting completion before the report is durable.

### 10. Restart recovery

LangGraph checkpoints state synchronously at node boundaries. A database lease and 30-second heartbeat identify the process that owns active execution. On startup, stale records are claimed atomically:

- if the next node is safe and the prior node is durable, execution resumes from the checkpoint;
- if the process may have died during an unresolved paid model step, the record becomes `recovery_required`;
- the user may explicitly retry only that checkpointed step.

This avoids both pretending a dead task is still running and silently spending twice on an ambiguous call.

## Important architecture concepts

### Typed state

**Why it exists:** Agents and graph nodes need a shared contract for plans, evidence, findings, recommendations, errors, budgets, and reviews.  
**Owns:** State shape, validation, reducer behaviour across parallel branches.  
**Does not own:** Product judgement or external access.  
**Trade-off:** More schema work and occasional repair calls, in exchange for inspectable failures and safer orchestration.

### Domain tools and role-bound permissions

**Why they exist:** Models should request business operations, not construct arbitrary HTTP.  
**Own:** Input validation, adapter calls, provenance, normalised errors, and permission checks.  
**Do not own:** Cross-source synthesis.  
**Trade-off:** Less flexibility than open-ended browsing, but a much smaller security and hallucination surface.

### Provenance and Evidence Ledger

**Why they exist:** A recommendation is only useful if claims can be traced to retrieved records.  
**Own:** Immutable evidence identity, source attribution, typed payload retention, and failed-attempt separation.  
**Do not own:** Whether the evidence is sufficient for a product decision.  
**Trade-off:** More state and prompt-management complexity, but defensible citations and auditable synthesis.

### Facts, inferences, and hypotheses

**Why they exist:** Product investigation necessarily includes interpretation, but interpretation must not masquerade as observation.  
**Own:** Epistemic labelling in specialist and PM contracts.  
**Do not own:** Causal proof.  
**Trade-off:** Reports can feel more qualified, but they are less likely to convert correlation into a false root cause.

### Bounded loops

**Why they exist:** Follow-up and critique can improve quality but can also create runaway cost.  
**Own:** Maximum research round, revision count, tool calls, model calls, and conditional repair.  
**Do not own:** Provider latency.  
**Trade-off:** The system may return `partial` instead of chasing certainty indefinitely.

### Error handling

**Why it exists:** A missing source, invalid output, timeout, authentication failure, or interrupted process has different product meaning.  
**Own:** Typed tool errors, explicit terminal states, safe partial completion, and customer-safe projection.  
**Does not own:** Making failed evidence look complete.  
**Trade-off:** More visible uncertainty, but no silent success based on guessed data.

### Model boundary

**Why it exists:** Models should be replaceable and evaluated by role without rewriting orchestration.  
**Own:** Central model resolution, token ceilings, OpenRouter transport, typed completion parsing, and telemetry.  
**Does not own:** Role permissions or terminal status.  
**Trade-off:** Gateway dependence and model-specific performance variability remain operational risks.

### Authentication, persistence, and ownership

**Why they exist:** Investigation history is customer data. It must survive navigation and restarts without becoming globally readable.  
**Own:** Identity, owner-scoped records, lifecycle history, checkpoints, and API authorization.  
**Do not own:** Agent memory. Persisted reports are not injected into new investigations.  
**Trade-off:** More security, migration, recovery, and operational complexity than process-local state.

## Important architecture choices

### Multi-agent rather than one general agent

The choice improves source isolation, tool control, and evidence accountability. It also adds coordination, latency, and cost. The repository retains single-agent and specialist-without-Critic baselines because the architecture should remain falsifiable.

### LangGraph

LangGraph fits the need for typed state, parallel fan-out/fan-in, conditional routing, bounded revision, and checkpointed resume. The trade-off is framework complexity compared with a simple sequential service function.

### FastAPI

FastAPI is the authoritative application boundary for authentication, lifecycle, streaming, ownership, and typed result APIs. It keeps orchestration out of the frontend and exposes explicit failure semantics.

### Evidence Ledger rather than free-form context

The Ledger preserves evidence identity across specialists, PM synthesis, Critic review, evaluation, persistence, and UI citations. Compact summaries can change for efficiency without deleting the typed record.

### Critic with bounded revision

The Critic exists because a fluent recommendation can still be unsupported. It is intentionally bounded because repeated self-critique can become expensive perfectionism. The latest design requires the revised candidate to be checked, even though that adds one call.

### Read-only agents

PMLytics AI recommends actions but does not create Jira issues, change support tickets, alter analytics configuration, or execute production remediations. This keeps consequential actions human-controlled and avoids pretending the current product has a fully governed action layer.

### No MCP, RAG, or long-term agent memory

The current sources are structured systems accessed through domain adapters. MCP would add another protocol without solving a current boundary problem; RAG would duplicate structured API retrieval; long-term memory could contaminate a new investigation with old conclusions. These could be revisited only for a clear product requirement.

### Synthetic, mock, and live source mix

Real PostHog exercises an external analytics integration. Mock Zendesk and Jira make the demo reproducible and safe. Supabase and model providers are real services. The trade-off is realism without proof that production schemas, permissions, data quality, or traffic behave the same way.

### Supabase

Supabase combines managed identity and PostgreSQL, reducing the number of services needed for a portfolio-scale product. FastAPI remains the authorization and application boundary. At enterprise scale, tenant modelling, operational isolation, audit administration, and possibly a dedicated identity strategy would need separate evaluation.

### SSE with polling fallback

SSE gives immediate server-authoritative lifecycle updates without a bidirectional protocol. Fetch-based streaming supports bearer authentication. Polling provides resilience when a proxy or browser breaks the stream. The trade-off is duplicate reconciliation logic and a need to keep progress monotonic.

## Detailed sources

- [System Architecture, historical baseline](../architecture/SYSTEM_ARCHITECTURE.md)
- [Agent Specification, historical baseline](../architecture/AGENT_SPECIFICATION.md)
- [ADR-0012: performance optimisation](../decisions/ADR-0012-phase12-performance-optimization.md)
- [ADR-0013: PM revision model routing](../decisions/ADR-0013-phase12a-pm-revision-model-routing.md)
- [ADR-0018: Supabase auth and persistence](../decisions/ADR-0018-supabase-auth-and-investigation-persistence.md)
- [ADR-0019: checkpoint recovery](../decisions/ADR-0019-postgres-checkpointed-investigation-recovery.md)
- [ADR-0025: restored post-revision Critic](../decisions/ADR-0025-post-revision-quality-gate.md)
- [ADR-0026: report projection and specialist repair](../decisions/ADR-0026-report-projection-and-bounded-specialist-repair.md)
