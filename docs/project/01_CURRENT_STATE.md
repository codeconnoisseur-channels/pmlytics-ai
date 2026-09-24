# PMLytics AI: Current State

This document is the narrative source of truth for what PMLytics AI is today. It reconciles the current implementation with the repository's historical specifications and phase reports.

**Product:** PMLytics AI  
**Fictional company context:** Pocket

Pocket names the synthetic fintech environment whose customer support, product analytics, and engineering records are investigated. It is not the product name and no real Pocket customer data is used.

## Product

### Purpose

PMLytics AI helps a product manager investigate a product question that cannot be answered from one system alone. It brings together:

- customer conversations from support;
- observed behaviour from product analytics;
- known defects, incidents, and delivery context from engineering tracking.

The output is a decision brief, not a raw data dump. It leads with a recommendation and then explains the executive finding, affected users, facts, inferences, hypotheses, success measures, risks, evidence tensions, remaining validation questions, and source records.

### Intended user

The primary user is a product manager or product lead who needs to decide whether to prioritise a fix, change the experience, gather more evidence, or avoid acting on an unsupported premise. The product assumes the organisation already has operational data sources. It does not replace support operations, analytics instrumentation, or engineering issue management.

### Core use case

The user asks a bounded product question, optionally selects a date range, and starts an asynchronous investigation. The system gathers evidence, reports progress, and returns one of four honest outcomes:

- `completed`: evidence, recommendation, and final Critic review satisfy all completion invariants;
- `partial`: a useful decision is available, but material follow-up or unresolved quality issues remain;
- `failed`: the workflow could not produce a defensible brief;
- `recovery_required`: an active step was interrupted in a way that could make an automatic paid retry unsafe.

### Current user journey

1. A visitor can inspect the public landing page and four cached scenario briefs without spending model credit.
2. A user signs up or signs in with Supabase email/password authentication.
3. The user enters a question and an optional complete start/end date range.
4. FastAPI creates and persists an owner-scoped investigation before starting model work.
5. The frontend receives lifecycle progress over authenticated Server-Sent Events. It reconnects with bounded backoff and falls back to polling after repeated stream failures.
6. On completion or partial completion, the frontend retrieves the structured brief and groups supporting records by source.
7. The user's recent investigations remain available after navigation and backend restart. Terminal investigations can be renamed or deleted; failed investigations can be retried as a new run.
8. A safely checkpointed interrupted workflow can resume automatically. Ambiguous in-flight paid work requires an explicit recovery action.

## Current architecture

### Frontend

The authoritative user interface is the Next.js application in [`frontend/`](../../frontend/). It owns presentation, Supabase browser/server session handling, protected-route redirects, bearer-token attachment, progress rendering, polling fallback, and cached public sample reports. It does not own investigation logic or evidence interpretation.

An earlier static prototype remains in [`app/ui/`](../../app/ui/) and is still mounted at the FastAPI root for historical compatibility. It is not the current product frontend. A production deployment should route users to the Next.js application; removing the prototype and its compatibility tests is remaining cleanup rather than a second supported frontend architecture.

### Backend

FastAPI exposes authenticated lifecycle, result, history, rename, delete, retry, recovery, SSE, and health routes. The API verifies the Supabase access token and derives the user ID from the verified JWT. It never accepts a user ID from the request payload as an authorization decision.

The API manager owns live task coordination, lifecycle projection, event broadcasting, persistence, leases, restart handling, and customer-safe report projection. The substantive investigation remains in LangGraph.

### LangGraph workflow

The current graph is:

```text
START
  ↓
Planner
  ↓ conditional parallel fan-out
Research ─┐
Analytics ├─→ Assessment ─→ optional targeted follow-up ─→ Assessment
Engineering┘                                      │
                                                  ↓
                                            PM Synthesis
                                                  ↓
                                               Critic
                                         PASS ↙        ↘ REVISE
                                          Finalize ← Critic ← PM Revision
                                                  ↓
                                                 END
```

The Assessment and targeted-follow-up nodes are orchestration controls, not additional public-facing agent personas. The six logical roles remain Planner/Orchestrator, Research, Analytics, Engineering, PM Synthesis, and Critic.

### Agents and tools

Tool access is enforced in code:

| Role | Tool access |
| --- | --- |
| Research | Search and read Zendesk tickets and comments |
| Analytics | Query PostHog through the analytics domain tool |
| Engineering | Search and read Jira issues, comments, and links |
| PM | None |
| Critic | None |

The Planner, Assessment, PM, and Critic reason over typed state rather than making arbitrary HTTP requests. All runtime tools are read-only.

### Evidence model

Every successful tool result becomes an immutable Evidence Ledger entry with an invocation-level ID, source type, source reference, retrieval time, compact factual summary, and typed payload. Failed tool attempts are recorded separately as errors and limitations, never as evidence.

Specialist findings must cite existing ledger IDs with matching source type and reference. Finalization validates provenance again. The API then creates a customer-safe report projection while retaining a deeper evidence drawer for individual tickets, issues, comments, and aggregated analytics rows.

### Model and provider layer

All inference goes through OpenRouter. Role model names and token ceilings are centrally configured rather than embedded in agents.

The Standard profile routes planning, assessment, and specialists to GPT-4.1 mini; PM synthesis to GPT-5.4; and PM revision and Critic to GPT-5.4 mini. The Deep profile falls back to the configured default model, currently GPT-5.4, unless a role override is provided. The checked-in configuration currently defaults to the Deep profile, so deployment configuration matters when interpreting cost and latency.

### Observability

LangSmith captures investigation, node, tool, and direct model spans when enabled. OpenRouter streaming is used internally to measure actual time to first token, token counts, finish reason, total latency, and provider-reported cost. Downstream agents receive a complete typed response, not partial chunks.

Observability is fail-open: a LangSmith outage must not change evidence, retry a model call, or fail an otherwise valid investigation.

### Supabase, authentication, and ownership

Supabase now owns two distinct concerns:

1. **Identity:** Supabase Auth provides email/password accounts, email confirmation links, password reset, cookie-backed sessions, and access tokens.
2. **Durable storage:** Supabase PostgreSQL stores application investigation records, lifecycle events, final typed workflow state, lease/recovery metadata, and LangGraph checkpoint tables.

The frontend uses `@supabase/ssr` to create browser and server clients. Next.js middleware refreshes sessions, protects `/investigations`, preserves the intended return path, and leaves cached sample scenario routes public.

FastAPI validates JWT signature, issuer, audience, expiry, and subject against Supabase's public JWKS. The token subject becomes the trusted `owner_id`. Every protected route uses that owner ID in repository lookups. Unknown and other-user investigation IDs both return `404`, reducing resource-enumeration risk.

### Persistence and recovery

The `investigations` table persists:

- investigation ID, owner ID, question, optional display name, and requested scope;
- lifecycle status, current stage, active role, revision count, timestamps, and safe error text;
- the final typed investigation state, including recommendation and evidence state;
- run attempt, heartbeat, lease owner/expiry, and current/last-completed graph node.

The `investigation_events` table stores ordered lifecycle events. LangGraph's `AsyncPostgresSaver` owns its checkpoint tables and uses the investigation ID as the thread ID.

The application still keeps an in-process cache of loaded records, live `asyncio` tasks, active subscriber queues, and tracer objects. Those improve live coordination but are not the durable source of truth. Active execution also occurs in the API process; checkpoints make node-boundary recovery possible without turning the system into a distributed job platform.

### Access-control model

Authorization is enforced primarily in FastAPI and the storage adapter:

- trusted owner identity comes from the verified token;
- reads, writes, renames, deletes, retries, streams, and recovery are owner-scoped;
- active investigations cannot be deleted until stopped;
- agents have no database tool and cannot use another investigation as model memory.

Row Level Security is enabled on the application tables as defense in depth for Supabase Data API access. The initial migration defines authenticated owner policies for investigation select/insert/update and event select. The backend still performs mandatory owner checks because its direct pooled database connection may not execute as the browser's authenticated Postgres role. No service-role secret is required in the browser.

## Current capabilities

The implementation currently supports:

- authenticated account creation, sign-in, sign-out, confirmation links, password reset, and session refresh;
- owner-scoped investigation creation and history;
- complete date-range scoping in UTC;
- asynchronous progress with server-authoritative stages;
- authenticated SSE with reconnect and polling fallback;
- parallel specialist evidence gathering;
- one optional targeted follow-up round;
- bounded PM/Critic revision;
- explicit completed, partial, failed, cancelled, and recovery-required states;
- durable completed reports and lifecycle history;
- checkpointed restart recovery;
- rename, delete, cancel, retry, and explicit recover operations;
- traceable citations and nested source records;
- customer-safe report wording separated from deeper audit evidence;
- four no-credit reference briefs for the canonical synthetic scenarios.

## Current data environment

| Concern | Real, mocked, or synthetic | Current behaviour |
| --- | --- | --- |
| Supabase Auth | Real managed service | Creates and validates application user identities |
| Supabase PostgreSQL | Real managed database | Persists user-owned investigations, events, final state, and checkpoints |
| OpenRouter | Real provider gateway | Executes configured model calls for live investigations |
| LangSmith | Real optional observability service | Receives traces when enabled; failure is non-blocking |
| PostHog | Real hosted integration | Stores and serves deterministic synthetic Pocket events, filtered to dataset version `2.0` |
| Zendesk | Local API-compatible mock | Serves deterministic synthetic Pocket support tickets and comments |
| Jira | MockServer `7.6.0` | Serves deterministic Jira-compatible Pocket issues and comments |
| Cached samples | Frontend repository data | Provides illustrative decision briefs without a live model call |

The latest dataset report records 51 support tickets and 15,223 PostHog events. Current Jira expectations are generated from code and include targeted scenario and API responses; the older dataset report's expectation count predates later scoping corrections.

## Current evaluation and performance state

### What is current

- The deterministic evaluator, frozen semantic judge, baseline implementations, stress fixtures, and preserved run artifacts exist in the repository.
- The evaluator's final behavioural stress gate is 15/15.
- The semantic judge is not human-qualified ground truth. A provenance audit invalidated the attempted clean human re-rating because the submitted ratings were generated in the agent environment rather than supplied independently by human raters.
- Citation identity and provenance are also enforced at runtime, not only during offline evaluation.
- The current graph restores a Critic review after PM revision and permits one specialist repair call only when a structured specialist synthesis is invalid.

### What is historical

The best controlled performance set is the Phase 12A Standard-profile, three-scenario validation:

| Context | Historical result |
| --- | --- |
| Wall-clock latency | 98.46s, 121.41s, 107.43s; average 109.10s |
| Provider cost | $0.0559, $0.0807, $0.0601; average $0.0656 |
| Quality | 20/20, 18/20, 20/20 on the frozen five-dimension judge |
| Citation validity | 8/8, 8/8, 9/9; zero hallucinated citations |
| Truncation | Zero in that validation set |

These results predate ADR-0025's restored post-revision Critic and ADR-0026's conditional repair allowance. They demonstrate the effect of the Phase 12A optimisation, not the current system's guaranteed latency, cost, or exact call count. No new controlled benchmark has reconciled those later safety changes.

The original full-model profiling run remains useful as a diagnosis, not as a current baseline: 558.08 seconds, 21 model calls, 26 tool calls, 164,734 tokens, and $0.788899 provider-reported cost for one investigation.

## Current limitations

1. **Synthetic evidence:** the application has not been validated on real customer support, production Jira, or real customer-event data.
2. **No current post-hardening benchmark:** later reliability changes make the historical Phase 12A exact call-count and latency claims stale.
3. **Provider variability:** a prior run showed a 170.62-second PM generation despite 2.82-second TTFT, demonstrating that good connection latency does not guarantee stable generation latency.
4. **Node-boundary recovery:** a completed node is durable, but an unresolved paid request is intentionally not retried automatically because billing state is ambiguous.
5. **Single-user ownership, not enterprise tenancy:** users own investigations directly. Organisations, workspaces, tenant roles, delegated administration, SSO, and audit administration are not implemented.
6. **RLS is defense in depth:** backend authorization remains essential; the product has not undergone an independent production security assessment.
7. **No autonomous writes:** the system recommends actions but cannot execute them in Jira, Zendesk, PostHog, or production systems.
8. **No RAG or long-term agent memory:** each investigation uses explicit current state and retrieved source evidence. Historical reports are not automatically added to a new model context.
9. **No public sharing model:** cached samples are public, but live user investigations are private and owner-scoped.
10. **Limited scale evidence:** there is no production load test for many concurrent tenants or 1,000 investigations per day.

## Historical and superseded documentation

The files below are retained because they show how the system evolved. They should not be read as a current-state contract without the listed superseding source.

| Document | Original purpose | What is now different | What supersedes it |
| --- | --- | --- | --- |
| [`docs/product/PRD.md`](../product/PRD.md) and [`PRODUCT_SPECIFICATION.md`](../product/PRODUCT_SPECIFICATION.md) | Original product definition under the former project name | Product identity is PMLytics AI; authentication, persistence, recovery, and the final product experience were added later | Current implementation, this document, ADR-0018 onward |
| [`docs/architecture/SYSTEM_ARCHITECTURE.md`](../architecture/SYSTEM_ARCHITECTURE.md) | Original multi-agent and integration architecture | It predates Supabase ownership, PostgreSQL records, checkpoint recovery, and current report projection | Current code, ADR-0018, ADR-0019, ADR-0025, ADR-0026 |
| [`docs/architecture/AGENT_SPECIFICATION.md`](../architecture/AGENT_SPECIFICATION.md) | Original agent contracts and boundaries | Core role boundaries remain, but call budgets, model routing, prompt behaviour, follow-up, and repair rules evolved | Current agents/graph, ADR-0012, ADR-0013, ADR-0025, ADR-0026 |
| [`docs/architecture/TECHNICAL_STACK.md`](../architecture/TECHNICAL_STACK.md) | Locked initial technology choices | Supabase Auth/PostgreSQL and checkpoint persistence are now implemented additions | Current dependencies, ADR-0018 and ADR-0019 |
| [`docs/api/FRONTEND_API_INTEGRATION.md`](../api/FRONTEND_API_INTEGRATION.md) | Initial frontend/API lifecycle contract | Its process-local state and restart-loss sections are obsolete | Current API routes/storage, ADR-0018 and ADR-0019 |
| [`docs/architecture/FRONTEND_ARCHITECTURE.md`](../architecture/FRONTEND_ARCHITECTURE.md) | Next.js frontend plan | Its persistence deferral is obsolete; authenticated SSE uses fetch with bearer tokens | Current frontend, ADR-0018 |
| [`docs/product/INFORMATION_ARCHITECTURE.md`](../product/INFORMATION_ARCHITECTURE.md), [`FRONTEND_ROUTE_SPECIFICATION.md`](../product/FRONTEND_ROUTE_SPECIFICATION.md), and [`INVESTIGATION_WORKSPACE_SPEC.md`](../product/INVESTIGATION_WORKSPACE_SPEC.md) | Planned routes and states | Statements that history is process-local or durable revisit is future work are obsolete | Current routes, migrations, ADR-0018, ADR-0019, ADR-0024 |
| [`docs/evaluation/EVALUATION_STRATEGY.md`](../evaluation/EVALUATION_STRATEGY.md) | Intended evaluation methodology | The large benchmark was deferred; the attempted clean human re-rating failed provenance review and no human-qualified judge claim is retained | [`phase9_human_rating_provenance_audit.md`](../../evaluations/runs/phase9_human_rating_provenance_audit.md), [`phase9_final_report.md`](../../evaluations/runs/phase9_final_report.md), and Phase 12A results |
| [`phase9_validation_integrity_amendment.md`](../../evaluations/runs/phase9_validation_integrity_amendment.md) | Recorded a provisional clean human requalification | Its claim that two fresh independent human ratings were obtained was invalidated by the later provenance audit; the ratings were generated in the agent environment | [`phase9_human_rating_provenance_audit.md`](../../evaluations/runs/phase9_human_rating_provenance_audit.md) |
| [`docs/implementation/IMPLEMENTATION_PLAN.md`](../implementation/IMPLEMENTATION_PLAN.md) | Original phase sequence | Later correction and hardening work extended the phase story and changed several gates | Phase completion reports and accepted ADRs |
| [`docs/implementation/PHASE12A_COMPLETION_REPORT.md`](../implementation/PHASE12A_COMPLETION_REPORT.md) | Historical optimisation baseline | Its 11-call revision path bypassed a final Critic and is no longer current | ADR-0025; ADR-0026 for conditional specialist repair |
| [`docs/implementation/DEMO_DATASET_V2_REPORT.md`](../implementation/DEMO_DATASET_V2_REPORT.md) | Dataset v2 validation snapshot | Jira expectation count and later source-scoping corrections changed after the report | Current seed and mock code; ADR-0026 and later correction work |
| [`docs/decisions/ADR-0018-supabase-auth-and-investigation-persistence.md`](../decisions/ADR-0018-supabase-auth-and-investigation-persistence.md) | Introduced auth and durable records | Its original “interrupted after restart” limitation was subsequently narrowed by checkpoints | ADR-0019 |
| [`docs/decisions/ADR-0023-email-otp-account-verification.md`](../decisions/ADR-0023-email-otp-account-verification.md) | Proposed an email OTP verification experience | The implemented flow currently uses Supabase email confirmation links and password reset links; OTP is not the current contract | Current authentication code and this document |

Historical visual specifications are also preserved, but they are not authoritative for system behaviour and are intentionally outside this knowledge base's scope.
