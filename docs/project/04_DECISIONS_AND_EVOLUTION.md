# Decisions and Evolution

PMLytics AI did not arrive at its current architecture in one step. This document records the decisions that materially shaped the product, the evidence that changed those decisions, and the trade-offs that remain. Pocket is the fictional fintech context used by the demo data; it is not the product name or a real customer.

## 1. Build a decision product, not another dashboard

**Initial assumption.** Product managers needed a faster way to inspect product signals spread across tools.

**Context/problem.** Zendesk explains what customers report, PostHog shows what users do, and Jira records engineering knowledge. A chart or search result from any one source leaves the PM to reconcile terminology, time periods, contradictions, and confidence manually.

**Options considered.** Add more dashboards; build federated search; provide a generic chat interface; or build a bounded investigation workflow that produces an evidence-backed decision brief.

**Evidence.** The demo scenarios repeatedly required cross-source interpretation rather than a single lookup. They also showed that an unsupported answer was worse than an explicit “investigate further” outcome.

**Decision.** PMLytics AI is a decision-support product. It gathers scoped evidence, preserves provenance, distinguishes facts from interpretations and hypotheses, and recommends a next move with confidence and follow-up needs.

**Trade-off.** A decision brief takes longer and costs more than search. It must earn that cost through better grounding and decision quality.

**What happened later.** Report projection and evidence presentation required further work because technically valid agent output was not automatically clear product output.

**Current state.** The final report is a product-facing projection of typed investigation state, backed by an auditable Evidence Ledger.

**At larger scale.** I would measure decision adoption, time to decision, follow-through, and recommendation reversals, not just investigation completion.

## 2. Use AI for synthesis under ambiguity, not for every operation

**Initial assumption.** An LLM could connect differently worded evidence across systems and draft a useful recommendation.

**Context/problem.** The work includes semantic search, conflicting signals, incomplete evidence, uncertainty, and judgement. Those are difficult to encode as a fixed dashboard query. Authentication, ownership, validation, persistence, and access control are not judgement tasks.

**Options considered.** Fully deterministic rules, one unconstrained LLM, or a hybrid system.

**Evidence.** LLMs helped with planning and synthesis but also produced unsupported causal language, schema failures, repetition, and variable latency. Deterministic checks caught failures that prose review could miss.

**Decision.** Use models for planning, evidence interpretation, synthesis, and critique. Keep schemas, role permissions, citations, authorization, lifecycle transitions, loop limits, and persistence deterministic.

**Trade-off.** The hybrid design is more complex than a chat completion, but it makes failure visible and boundaries enforceable.

**What happened later.** More validation was added around report projection, citations, and specialist outputs. This reinforced the boundary rather than replacing it with more prompting.

**Current state.** AI contributes judgement; application code owns control and safety.

**At larger scale.** I would expand deterministic pre-computation and reserve expensive models for decisions where semantic judgement changes the outcome.

## 3. Separate specialist retrieval from PM synthesis

**Initial assumption.** One general agent might be the simplest implementation.

**Context/problem.** Zendesk, PostHog, and Jira have different semantics and failure modes. Giving one agent every tool makes permission boundaries, debugging, and source-specific evaluation harder.

**Options considered.** One agent with all tools; sequential source agents; or role-bound specialists running in parallel and feeding a separate synthesizer.

**Evidence.** Source tasks were independent enough to parallelize, while synthesis required all available evidence. Role-specific contracts made it possible to identify whether a failure came from retrieval or judgement.

**Decision.** Keep six logical roles: Planner, Research, Analytics, Engineering, PM Synthesis, and Critic. Specialists receive only their domain tools. PM and Critic receive no external tools.

**Trade-off.** Multiple model calls increase token use, latency, and orchestration complexity. They do not automatically outperform a single agent.

**What happened later.** The large baseline comparison was not completed because provider-credit failures invalidated the run. The architecture therefore has a defensibility rationale and stress-test evidence, but no valid claim of universal multi-agent superiority.

**Current state.** Specialists run concurrently after planning; the PM synthesizes their ledger-backed findings.

**At larger scale.** I would route simple questions to a cheaper single-agent path and use the full workflow only when source breadth, contradiction, or decision risk warrants it.

## 4. Add a separate Critic and bound revision

**Initial assumption.** Structured PM output and prompt instructions would be enough to control quality.

**Context/problem.** A fluent recommendation can overstate causality, ignore contradictory evidence, or express confidence that its citations do not support.

**Options considered.** Rely on the PM; use only deterministic validators; add an independent critic; or allow an open-ended debate loop.

**Evidence.** Evaluation exposed unsupported claims and missed contradictions that schema validity alone could not catch. Profiling also showed that revisions were the most expensive part of the workflow.

**Decision.** The Critic returns `PASS` or `REVISE`. Revision is bounded, and the revised recommendation must pass through the Critic again.

**Trade-off.** The quality gate adds latency and cost. A critic is also an LLM and can be wrong.

**What happened later.** One optimization accidentally allowed revised output to bypass the final critic. ADR-0025 restored the post-revision quality gate, accepting a longer worst-case call path for correctness.

**Current state.** Revision is finite and every final recommendation follows the required quality gate.

**At larger scale.** I would use risk-based critique: deterministic-only checks for low-risk summaries and model critique for consequential or low-confidence decisions.

## 5. Make the Evidence Ledger the grounding boundary

**Initial assumption.** Passing specialist prose into the PM would preserve enough context.

**Context/problem.** Free-form handoffs blur source records, interpretation, and provenance. Repeating full evidence in multiple prompts also drove context growth.

**Options considered.** Raw tool output, narrative summaries, retrieval at synthesis time, or a typed, append-only ledger.

**Evidence.** Citation and context failures showed that the PM needed stable evidence identifiers and structured support fields. The stress evaluator initially missed support because the evaluator context itself omitted that field.

**Decision.** Normalize meaningful evidence into ledger entries with source type, reference, finding, support, interpretation, confidence, and limitations. Keep source failures separate. Final citations resolve back to these entries and their underlying records.

**Trade-off.** Normalization can discard nuance if schemas or projections are too narrow, and a ledger can become large.

**What happened later.** Evidence handoff and projection were strengthened after generic report text and missing record detail appeared. Nested audit records now support a clean brief plus deeper inspection.

**Current state.** The ledger is the provenance boundary, not a vector store or long-term memory.

**At larger scale.** I would add evidence deduplication, retention rules, and source snapshots while preserving immutable references used by issued reports.

## 6. Enforce domain tools and remain read-only

**Initial assumption.** Models should have access only to the information required by their role.

**Context/problem.** Raw HTTP or shared credentials would let models cross source boundaries or construct arbitrary requests. Automatic writes would turn an uncertain recommendation into an operational risk.

**Options considered.** General-purpose HTTP, MCP, broad shared tools, or application-owned domain tools and adapters.

**Evidence.** Source-specific failures were easier to contain and diagnose when each specialist used a narrow interface. Nothing in the MVP required autonomous mutation.

**Decision.** Agents call typed domain tools through adapters. Research can read Zendesk, Analytics can query PostHog, Engineering can read Jira, and PM/Critic have no external tools. Runtime agents do not write to source systems. MCP was not introduced.

**Trade-off.** Every new capability needs an explicit application interface. The system is less flexible than an unconstrained agent by design.

**What happened later.** The desire for an “agentic” action layer was discussed, but it was deliberately kept out of this release.

**Current state.** Recommendations remain human-controlled; data access is read-only and role-bound.

**At larger scale.** I would add proposed actions first, then approval-gated execution with separate credentials, policy checks, idempotency, and audit logs.

## 7. Choose a mixed real, mocked, and synthetic data environment

**Initial assumption.** A realistic demo needed all three evidence classes without using real customer data.

**Context/problem.** Production Zendesk and Jira accounts were not available, but analytical behaviour and cross-source relationships still needed to be testable and repeatable.

**Options considered.** Static fixtures only; mock every service; connect every live service; or use API-compatible mocks for operational systems and a real PostHog project seeded with deterministic synthetic events.

**Evidence.** Independent seeds produced weak cross-source stories, so scenario definitions became the source for related tickets, events, issues, noise, and contradictions.

**Decision.** Use mock Zendesk, MockServer-backed Jira, and real hosted PostHog with synthetic events. Keep dataset generation deterministic and disclose that none of it is real Pocket customer data.

**Trade-off.** The integration path is realistic, but the dataset does not prove performance or retrieval quality on messy production schemas.

**What happened later.** Scenario data was expanded and validated as report weaknesses exposed missing or poorly linked evidence.

**Current state.** The environment supports repeatable demos and evaluation, not production-data claims.

**At larger scale.** I would add tenant-specific schema mapping, redaction, data-quality diagnostics, and shadow evaluation against authorized production snapshots.

## 8. Centralize model routing instead of using one model everywhere

**Initial assumption.** A strong default model across all roles would simplify quality control.

**Context/problem.** Profiling showed that expensive synthesis and revision calls dominated cost, while planning and retrieval-oriented tasks did not always need the same model capacity.

**Options considered.** One model for every node; provider-specific code in each agent; or centralized role-based routing through OpenRouter.

**Evidence.** The historical baseline used 164,734 tokens and cost $0.788899 in one run. PM and Critic work represented 73.2% of cost, and revisions represented 55.8%. Routing PM revision to a smaller model cut that historical stage to 15.55 seconds, saving roughly 20 to 32 seconds in the measured cases.

**Decision.** Keep OpenRouter as the gateway and centralize role allocation. The standard path uses smaller models for planning, assessment, specialists, revision, and critique, with the stronger model for PM synthesis; configuration can override roles.

**Trade-off.** Smaller models reduce cost and latency but can increase invalid structured output or weaker reasoning.

**What happened later.** ADR-0026 added bounded specialist repair for invalid synthesis rather than silently accepting malformed output.

**Current state.** Routing is configurable and role-aware; historical improvements are not represented as a current SLA.

**At larger scale.** I would add evaluation-gated routing by query difficulty, source coverage, and business risk.

## 9. Parallelize independent specialists, then optimize the critical path

**Initial assumption.** Parallel source work would be the main latency win.

**Context/problem.** Sequential specialist execution unnecessarily adds independent retrieval times, but total latency also includes provider queueing, generation, retries, PM synthesis, and critique.

**Options considered.** Sequential execution; unrestricted concurrency; or bounded parallel specialists followed by ordered synthesis and review.

**Evidence.** Profiling showed that parallelism helped, but long PM generations, repeated context, retries, and tail latency still dominated some runs. A later outlier reached 310.35 seconds even after median behaviour improved.

**Decision.** Run specialists in parallel, deduplicate context, constrain outputs, and keep downstream quality gates sequential where dependency requires it.

**Trade-off.** Concurrency can create provider bursts and makes lifecycle reporting more complex.

**What happened later.** The frontend added durable events, SSE reconnection, and polling fallback so a dropped stream did not imply a lost investigation.

**Current state.** Parallelism reduces avoidable waiting but does not eliminate provider variability.

**At larger scale.** I would add queueing, per-tenant limits, concurrency shaping, cancellation, cached deterministic queries, and explicit latency SLOs.

## 10. Treat evaluation as layered evidence, not one score

**Initial assumption.** A combined automated score plus human ratings could provide a clean quality benchmark.

**Context/problem.** Agent output must be structurally valid, grounded, cautious, cross-source, and useful. Any single evaluator can miss a different failure.

**Options considered.** Manual review only; LLM judge only; deterministic tests only; or a layered approach.

**Evidence.** Deterministic validators caught citation and contract failures. The frozen judge captured semantic quality but initially lacked a support field. Initial human comparison was informationally asymmetric and sometimes lenient. A later supposedly clean human re-rating was invalidated when a provenance audit showed that it had been generated in the agent environment rather than by independent human raters. A large architecture benchmark then failed operationally because of HTTP 402 provider-credit errors.

**Decision.** Use deterministic checks, a frozen LLM judge, stress scenarios, and qualitative human review. Treat deterministic checks as hard gates, do not describe the judge as human-qualified ground truth, and do not publish invalid human-calibration or benchmark aggregates.

**Trade-off.** The result is more honest but less convenient than a single headline score.

**What happened later.** Stress performance reached 15/15 after evaluator-context repair, while the incomplete large benchmark remained documented as a limitation.

**Current state.** Evaluation supports specific quality claims, not universal superiority or production readiness.

**At larger scale.** I would establish blind expert rubrics, inter-rater agreement, production outcome measures, regression gates, and cost/latency budgets by query class.

## 11. Evolve from process-local history to Supabase ownership and checkpoint recovery

**Initial assumption.** Process-local state was acceptable while validating the workflow and avoiding premature infrastructure.

**Context/problem.** Once investigations became a user-facing product, navigation, restarts, and multiple users exposed the limits of in-memory history. A stream disconnect could look like lost work, and process death could interrupt a paid investigation.

**Options considered.** Keep memory-only state; store final reports only; add a custom database and identity service; or use Supabase for identity and Postgres persistence, plus LangGraph checkpoints.

**Evidence.** Repeated lifecycle failures showed that UI state could not be the source of truth. Users needed durable ownership, history, events, and explicit recovery semantics.

**Decision.** Add Supabase email/password authentication, owner-scoped investigation and event records, RLS as defense in depth, and Postgres-backed LangGraph checkpoints. The backend validates Supabase JWTs and treats the verified subject as the owner ID.

**Trade-off.** Identity, authorization, migrations, token handling, recovery, and deletion semantics add security and operational complexity.

**What happened later.** The original ADR-0018 limitation said active work was marked interrupted after restart. ADR-0019 added node-boundary recovery. Ambiguous in-flight paid calls require explicit user resume to prevent duplicate spend.

**Current state.** Completed reports and workflow checkpoints are durable. Live tasks, subscriber queues, and some caches remain process-local. Ownership is enforced in API queries and backed by RLS policies.

**At larger scale.** I would move execution to workers with durable queues, use organization/tenant identities, add enterprise retention and audit controls, and validate authorization with a least-privilege database role.

## 12. Use SSE with polling fallback

**Initial assumption.** A live stream would be enough to communicate investigation progress.

**Context/problem.** Browser navigation, network interruption, token-bearing requests, and backend restarts can disconnect a stream without ending the underlying workflow.

**Options considered.** Polling only; unauthenticated `EventSource`; authenticated fetch-based SSE; or WebSockets.

**Evidence.** The product experienced reconnect and stale-state problems. Durable investigation state already made recovery by polling possible.

**Decision.** Use authenticated fetch-based SSE for timely events, reconnect with backoff, and fall back to owner-scoped status polling. The persisted backend state remains authoritative.

**Trade-off.** Two delivery paths require careful event ordering and idempotent UI updates.

**What happened later.** Lifecycle state and elapsed time were moved away from page-local assumptions so navigation no longer restarted an investigation.

**Current state.** A broken stream degrades freshness, not ownership or final-result durability.

**At larger scale.** I would use a shared event broker and resumable event offsets across API replicas.

## 13. Deliberate scope boundaries

PMLytics AI deliberately does **not** include autonomous writes, RAG, a vector database, long-term agent memory, MCP, public report sharing, enterprise organizations/SSO/RBAC, or a production action layer. These are not omissions hidden behind roadmap language. Each would add a new safety, privacy, authorization, or evaluation boundary.

The next expansion should be justified by a measured user need. If action execution becomes valuable, the safest progression is recommendation, proposed action, human approval, then narrowly scoped execution. If production data replaces synthetic data, data governance and tenant isolation become release gates, not follow-up polish.

## Source documents

- [Current state](01_CURRENT_STATE.md)
- [Product and architecture](02_PRODUCT_AND_ARCHITECTURE.md)
- [Evaluation, performance, and failures](03_EVALUATION_PERFORMANCE_AND_FAILURES.md)
- [ADR-0012: performance optimization](../decisions/ADR-0012-phase12-performance-optimization.md)
- [ADR-0018: Supabase auth and persistence](../decisions/ADR-0018-supabase-auth-and-investigation-persistence.md)
- [ADR-0019: checkpoint recovery](../decisions/ADR-0019-postgres-checkpointed-investigation-recovery.md)
- [ADR-0025: post-revision quality gate](../decisions/ADR-0025-post-revision-quality-gate.md)
- [ADR-0026: report projection and bounded repair](../decisions/ADR-0026-report-projection-and-bounded-specialist-repair.md)
