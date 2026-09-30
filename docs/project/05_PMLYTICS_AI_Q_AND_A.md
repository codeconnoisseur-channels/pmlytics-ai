# PMLytics AI Q&A

This Q&A helps explain PMLytics AI in interviews, portfolio reviews, founder conversations, and technical discussions. It is not a script to memorise. Start with the 30-second answer, expand when the conversation calls for it, and anchor claims in the repository evidence listed under each question.

PMLytics AI is the product. Pocket is the fictional fintech company represented by synthetic demo data.

## A. Product

### 1. What problem does PMLytics AI solve, and for whom?

**30-second answer.** PMLytics AI helps product managers investigate a product question across customer support, product analytics, and engineering tracking. Those systems each show a different part of reality. The product turns their evidence into a recommendation, confidence level, success measures, and citations, while making uncertainty explicit.

**2-minute answer.** A PM investigating a payments problem might find complaints in Zendesk, a conversion change in PostHog, and a related Jira issue. The difficult work is not opening three tabs. It is aligning scope and time, deciding whether the records describe the same problem, distinguishing correlation from cause, and deciding what to do. PMLytics AI creates a bounded investigation: a planner scopes the question; source specialists gather evidence; an Evidence Ledger preserves provenance; a PM agent synthesizes a decision; and a Critic challenges unsupported claims. The output is a decision brief rather than a chat transcript or raw technical dump.

**Deep-dive points.** The intended user is a PM or product lead. The primary job is decision support, not business intelligence replacement. The system can recommend action, recommend validation first, or say that available evidence is insufficient.

**Repository evidence/source.** [Current state](01_CURRENT_STATE.md), [product and architecture](02_PRODUCT_AND_ARCHITECTURE.md), and the current [`README`](../../README.md).

**Likely follow-ups.** How would you measure product value? What decisions are in scope? When should a PM ignore the recommendation?

### 2. Why is a dashboard or generic chatbot not enough?

**30-second answer.** A dashboard visualizes predefined metrics, while this job requires cross-source investigation and judgement under incomplete evidence. A generic chatbot can sound convincing but has weak tool boundaries and provenance. PMLytics AI combines LLM judgement with typed evidence, restricted tools, citations, and bounded review.

**2-minute answer.** Dashboards are excellent when the team already knows the metric, segment, and time window. They do not naturally reconcile a customer symptom with a behavioural pattern and an engineering issue. Search retrieves records but does not decide whether they support the same explanation. A generic chatbot has the opposite problem: it is flexible, but without an evidence boundary it can blend facts and inference. I therefore kept deterministic systems responsible for identity, authorization, state, citations, and loop limits, while using models for semantic planning, interpretation, synthesis, and critique.

**Deep-dive points.** AI earns its place through ambiguity handling, not through basic retrieval. The comparison is not “AI versus dashboards”; PMLytics AI consumes analytics evidence and adds an investigation layer above it.

**Repository evidence/source.** [Why AI and product job](02_PRODUCT_AND_ARCHITECTURE.md#why-ai), [decision history](04_DECISIONS_AND_EVOLUTION.md#2-use-ai-for-synthesis-under-ambiguity-not-for-every-operation).

**Likely follow-ups.** What remains deterministic? When would you route a question to a dashboard instead? How do you stop hallucinations?

### 3. What would you measure after launch, and what could make you simplify or kill it?

**30-second answer.** I would measure time to a defensible decision, recommendation adoption, evidence inspection, follow-through, reversals, and user trust, alongside latency and cost. I would simplify or stop the product if PMs consistently use only the evidence search, if recommendations do not change decisions, or if quality gains do not justify the latency and cost.

**2-minute answer.** Completion rate is not enough because a completed brief can still be useless. I would instrument the funnel from question to completed brief, evidence inspection, copied or accepted recommendation, follow-up action, and later outcome review. I would pair behaviour with qualitative audits: did the PM understand the confidence and limitations, and did the evidence materially change the decision? Guardrails would include unsupported-claim rate, citation validity, source failure, p95 latency, abandonment, cost per useful brief, and cross-tenant security incidents. If a simpler search-plus-summary flow produced equivalent decisions, I would remove agents rather than defend complexity.

**Deep-dive points.** Separate product usefulness from model quality. Measure by question class and decision risk. Avoid treating clicks on citations as a success by themselves.

**Repository evidence/source.** [Evaluation dimensions](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#part-i-evaluation), [current limitations](01_CURRENT_STATE.md#current-limitations).

**Likely follow-ups.** What is the north-star metric? How would you establish causal product impact? What is an acceptable latency?

## B. AI product design

### 4. Why multi-agent, and why these six roles?

**30-second answer.** The six roles reflect separable responsibilities: planning, three source-specific evidence tasks, product synthesis, and independent critique. The boundary improves permissions, provenance, parallelism, and diagnosis. I do not claim that multi-agent is universally superior; the large comparative benchmark was incomplete.

**2-minute answer.** Research, analytics, and engineering systems have different query models and failure modes, so each specialist has only its domain tools. The Planner scopes work without becoming a source expert. The PM receives structured evidence rather than broad tool access, which prevents it from searching until it finds a convenient answer. The Critic is independent because a synthesizer is not the best judge of its own causal overreach. Specialists can run concurrently. The trade-off is more calls and orchestration. A planned single-agent versus multi-agent benchmark produced only 13 legitimate exploratory runs before 57 HTTP 402 failures and 134 unattempted cells, so I explicitly avoid claiming architectural superiority from that experiment.

**Deep-dive points.** Planner, Research, Analytics, Engineering, PM, and Critic are logical AI roles. Evidence assessment and targeted follow-up are orchestration controls, not extra agents. A future router could use a simpler path for low-risk questions.

**Repository evidence/source.** [Role boundaries](02_PRODUCT_AND_ARCHITECTURE.md#why-multi-agent), [evaluation limits](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#what-evaluation-has-not-established).

**Likely follow-ups.** Why not four agents? How do agents communicate? What would convince you to collapse the design?

### 5. Why separate retrieval from synthesis and add a Critic?

**30-second answer.** Retrieval should report what each system contains; synthesis should decide what it means for the product. Separating them preserves source boundaries. The Critic then challenges unsupported causality, contradictions, and confidence mismatch before a recommendation becomes final.

**2-minute answer.** If the same agent can retrieve from every system and make the decision, it can blur missing evidence into a plausible narrative. Specialists instead create typed findings and ledger entries. The PM sees the combined evidence and has no external tools. The Critic returns `PASS` or `REVISE`, and revision is bounded. A real lesson was that an optimization once let revised output skip the final Critic. That reduced calls but weakened the quality contract, so ADR-0025 restored post-revision review even though it increased the worst-case path.

**Deep-dive points.** The Critic complements deterministic validation; it does not replace it. Revision is finite to control cost and prevent agent debate loops. A critic failure must not silently certify an answer.

**Repository evidence/source.** [ADR-0025](../decisions/ADR-0025-post-revision-quality-gate.md), [Critic decision](04_DECISIONS_AND_EVOLUTION.md#4-add-a-separate-critic-and-bound-revision).

**Likely follow-ups.** Can the Critic hallucinate? Why not ask the PM to self-reflect? How many revisions are allowed?

### 6. What should be deterministic, what should be LLM-driven, and what should never be automated?

**30-second answer.** Models handle semantic planning, interpretation, synthesis, and critique. Code handles authentication, authorization, state transitions, tool permissions, schemas, citation resolution, persistence, retries, and loop limits. The current product never autonomously changes Zendesk, Jira, PostHog, or production systems.

**2-minute answer.** My rule is that model judgement is appropriate when multiple defensible interpretations exist; deterministic control is appropriate when a condition must always hold. For example, a model can judge whether evidence suggests a contributor, but it cannot decide that one user may read another user's report. It can recommend a Jira action, but the MVP cannot execute it. That read-only boundary was intentional. If I added an action layer, I would start with proposed actions and explicit human approval, then add separate write credentials, policy enforcement, idempotency, and an audit trail.

**Deep-dive points.** No MCP, RAG, long-term agent memory, or autonomous writes in the current scope. These are safety and evaluation boundaries, not missing buzzwords.

**Repository evidence/source.** [Architecture choices](02_PRODUCT_AND_ARCHITECTURE.md#important-architecture-choices), [scope boundaries](04_DECISIONS_AND_EVOLUTION.md#13-deliberate-scope-boundaries).

**Likely follow-ups.** What action would you automate first? Where should approval live? How would you evaluate an action agent?

## C. Architecture and technical depth

### 7. Walk me through the architecture end to end.

**30-second answer.** A user authenticates through Supabase in the Next.js app. The frontend sends a bearer token to FastAPI, which verifies identity and creates an owner-scoped investigation. LangGraph runs planning, parallel specialists, evidence assessment, PM synthesis, Critic review, bounded revision, and finalization. Records, events, final typed state, and checkpoints persist in Postgres; SSE streams progress with polling fallback.

**2-minute answer.** The browser session is managed by Supabase SSR. FastAPI validates the JWT's signature, issuer, audience, expiry, and subject, and uses that subject as the owner ID. The Planner produces typed tasks. Research uses only Zendesk tools, Analytics only PostHog, and Engineering only Jira. Their evidence is normalized into an append-only ledger. An assessment step can authorize one bounded follow-up when a specific gap is repairable. The PM produces a structured recommendation, the Critic reviews it, and a bounded revision may occur. The API persists lifecycle data and emits durable events. The UI reads the authoritative persisted state, not page-local assumptions. LangGraph checkpoints support node-boundary recovery.

**Deep-dive points.** Live asyncio tasks and subscriber queues remain process-local. If a paid provider request was in flight when the process died, the system requires explicit resume to avoid duplicate spend.

**Repository evidence/source.** [Current architecture](01_CURRENT_STATE.md#current-architecture), [request lifecycle](02_PRODUCT_AND_ARCHITECTURE.md#architecture-walkthrough).

**Likely follow-ups.** Where is authorization enforced? What happens on restart? Why use both events and checkpoints?

### 8. Why LangGraph and FastAPI?

**30-second answer.** LangGraph fits a stateful workflow with parallel branches, conditional follow-up, bounded revision, and checkpoints. FastAPI provides a typed Python boundary around that workflow and its source adapters. Neither is the product value by itself; each makes the control flow explicit and testable.

**2-minute answer.** The investigation is not a linear prompt chain. It branches into three specialists, joins into evidence assessment, may take one targeted follow-up path, and can enter a bounded PM/Critic revision loop. LangGraph represents those transitions explicitly and now persists checkpoints in Postgres. FastAPI exposes authentication-aware lifecycle, evidence, events, retry, rename, and delete operations while keeping orchestration out of the frontend. The trade-off is framework complexity. If the workflow collapsed into one or two calls, I would reconsider LangGraph.

**Deep-dive points.** Typed state provides the contract between nodes. The API owns user-visible lifecycle; the graph owns investigation progression. Next.js is a presentation and session layer, not the orchestration engine.

**Repository evidence/source.** [Architecture concepts](02_PRODUCT_AND_ARCHITECTURE.md#important-architecture-concepts), [current state](01_CURRENT_STATE.md).

**Likely follow-ups.** Could a queue replace LangGraph? How do checkpoints work? Why not implement everything in Next.js?

### 9. How do tool permissions, provenance, the Evidence Ledger, and citations work together?

**30-second answer.** Tool permissions limit what each specialist can retrieve. Retrieved findings become typed ledger entries with source references and support. The PM cites ledger IDs, and the product resolves those IDs to summary evidence and underlying records. That creates a trace from recommendation back to source.

**2-minute answer.** Prompt instructions alone are not a security or grounding boundary. The application exposes only Zendesk methods to Research, only the analytics query to Analytics, and only Jira methods to Engineering. PM and Critic have no external tools. Each meaningful finding retains source type, source reference, support, interpretation, confidence, and limitations. Source failures are separate from evidence. Citations are validated against the ledger before presentation. The evidence drawer can expose nested source records without flooding the main brief. One failure taught us that preserving an identifier is not sufficient if the handoff omits the substantive support text, so both evaluator context and report projection were strengthened.

**Deep-dive points.** Provenance does not prove causality; it proves where a claim came from. The ledger is not RAG or long-term memory. It is investigation-scoped state.

**Repository evidence/source.** [Evidence model](02_PRODUCT_AND_ARCHITECTURE.md#important-architecture-concepts), [failure analysis](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#part-iii-failures-that-changed-the-system), [ADR-0020](../decisions/ADR-0020-nested-evidence-audit-records.md).

**Likely follow-ups.** How do you deduplicate evidence? What if a cited record changes? Can an LLM invent an evidence ID?

### 10. How do you stop loops and recover from failures?

**30-second answer.** Every iterative path has a fixed budget: tool calls, targeted follow-up, and PM revision are bounded. Failures are typed rather than converted into guessed evidence. Durable records and LangGraph checkpoints allow node-boundary recovery; ambiguous paid calls require explicit user resume.

**2-minute answer.** The workflow can continue with a partial source failure only when the remaining evidence supports a useful answer, and confidence must reflect the gap. Schema-invalid specialist synthesis gets a bounded repair attempt under ADR-0026. The PM/Critic loop cannot run indefinitely. Lifecycle events and state are persisted, so SSE disconnection does not restart work. On backend restart, the system can recover from a checkpoint, but it avoids automatically replaying an uncertain in-flight provider call because that could double spend.

**Deep-dive points.** Distinguish transport failure, source failure, invalid output, insufficient evidence, and provider failure. “Completed” must mean a valid final state, not merely that a task stopped.

**Repository evidence/source.** [Failure handling](02_PRODUCT_AND_ARCHITECTURE.md#important-architecture-concepts), [ADR-0019](../decisions/ADR-0019-postgres-checkpointed-investigation-recovery.md), [ADR-0026](../decisions/ADR-0026-report-projection-and-bounded-specialist-repair.md).

**Likely follow-ups.** What is safe to retry? How do you make retries idempotent? What happens when only Jira fails?

## D. Data and evidence

### 11. Which data sources are real, mocked, or synthetic, and why?

**30-second answer.** Supabase, OpenRouter, and the hosted PostHog integration are real services. PostHog contains deterministic synthetic Pocket events. Zendesk is an API-compatible mock with synthetic tickets, and Jira is represented through MockServer with synthetic issues. No real Pocket customer data is used.

**2-minute answer.** The goal was to exercise real integration boundaries without requiring production customer access. Zendesk and Jira mocks let the project control scenarios, noise, and contradictions. Using a real PostHog project tests the analytics adapter against an actual service while keeping events fictional. Scenario definitions generate related evidence across sources so the demo is coherent rather than three independent fixture sets. The limitation is important: this validates product and integration behaviour in a controlled environment, not production schema diversity, data quality, volume, privacy, or tenant isolation.

**Deep-dive points.** Dataset version and seed support reproducibility. MockServer is a mocking engine, not a full Jira implementation. The current code, not an old dataset count report, is authoritative.

**Repository evidence/source.** [Current data environment](01_CURRENT_STATE.md#current-data-environment), [data decision](04_DECISIONS_AND_EVOLUTION.md#7-choose-a-mixed-real-mocked-and-synthetic-data-environment).

**Likely follow-ups.** Why not mock PostHog too? How would onboarding a real company work? How do you avoid demo overfitting?

### 12. How do you handle incomplete, absent, or contradictory evidence?

**30-second answer.** The system preserves missing-source failures and contradictions instead of smoothing them into a confident answer. It distinguishes absence of evidence from evidence of absence, lowers confidence, and can recommend targeted validation rather than a product fix.

**2-minute answer.** A zero-result search may mean there were no matching records, the vocabulary was wrong, tagging was incomplete, or retrieval failed. Those cases should not become “customers are unaffected.” Similarly, a Jira issue can be plausible context without proving user impact or causality. Specialists record limitations; evidence assessment determines whether one bounded follow-up could resolve a specific gap; the PM labels facts, interpretations, and hypotheses; and the Critic checks overreach. The resulting decision can be “investigate further,” but it must still say what to validate, why, and what outcome would change the decision.

**Deep-dive points.** Contradiction is useful evidence. Partial-source completion is acceptable only when the decision remains defensible. Confidence concerns evidence strength, not writing certainty.

**Repository evidence/source.** [Evidence concepts](02_PRODUCT_AND_ARCHITECTURE.md#important-architecture-concepts), [incomplete evidence failures](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#part-iii-failures-that-changed-the-system).

**Likely follow-ups.** How do you communicate low confidence without overwhelming users? When should the workflow fail entirely? How is targeted follow-up selected?

## E. Evaluation

### 13. How did you evaluate the system?

**30-second answer.** I evaluate retrieval and reasoning separately. Deterministic checks cover citations, permissions, schemas, budgets, and workflow state. Scenario tests ask whether agents retrieved the expected source evidence. A version-controlled LLM judge reviews semantic questions such as causal discipline and recommendation proportionality, while humans independently audit samples and adjudicate disagreements.

**2-minute answer.** I originally focused more heavily on whether the final recommendation was grounded in its supplied evidence. The evaluation now has five layers: retrieval quality, deterministic correctness, semantic review, human audit, and operational performance. Product-owned cases and rubrics are separate from runner infrastructure. The semantic judge answers one explicit pass-or-fail question at a time rather than compressing the whole report into one score. Fifteen development stress cases cover fabricated metrics, contradictions, causal overreach, missing sources, irrelevant citations, and instructions embedded in evidence. The suite moved from 14/15 to 15/15 after the evaluator's packet builder was found to be omitting evidence support. A later live wallet-funding investigation showed the next gap: the answer was cautious relative to its packet, but the agents had failed to retrieve PostHog and Zendesk evidence that existed. That is why retrieval correctness is now a distinct evaluation target.

**Deep-dive points.** A valid citation proves that a claim points to a retrieved record. It does not prove that the investigation retrieved the records it should have found. Do not collapse retrieval, reasoning, evaluator calibration, latency, and cost into one score.

**Repository evidence/source.** [Evaluation](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#part-i-evaluation), [evaluation strategy](../evaluation/EVALUATION_STRATEGY.md).

**Likely follow-ups.** What did the deterministic layer catch? How do you test retrieval recall? What would you add before production?

### 14. What were the evaluator weaknesses, and how did you rebuild human calibration?

**30-second answer.** The judge initially missed support because the evaluator payload omitted the ledger's support field. The first human comparisons were also invalid because reviewers did not receive identical information and one later artifact was not independently human-authored. I withdrew those results and rebuilt the process around identical content-hashed packets, atomic pass/fail criteria, reviewer attestation, and explicit false-pass reporting. A later blind five-case pilot achieved 5/5 verdict and severity agreement with no false passes, while remaining too small and too development-oriented to count as a held-out benchmark.

**2-minute answer.** This was a useful reminder that an evaluator is another product surface. The system had valid support, yet the judge could not see it, causing a 14/15 stress result. After serializing the missing field and refining the fixture, the suite reached 15/15. Separately, the original human process was informationally asymmetric, and a later rating artifact failed provenance review. I invalidated those comparisons rather than report a convenient score. The replacement design gives humans and the automated judge the same content-hashed packet, records atomic verdicts and severity, requires independent-human attestation, and reports dangerous false passes separately. The first paid pilot also exposed a defective missing-source packet. After correcting it, the cache prevented four unchanged cases from being purchased again. A blind independent product manager then matched the final judge on all five cases. I still kept the held-out set empty because those cases had already been used during development.

**Deep-dive points.** Human review is not automatically ground truth. Blindness, rubric clarity, reviewer provenance, evidence parity, critical false-pass rate, and held-out isolation matter. Paid judge execution is opt-in and budget-gated.

**Repository evidence/source.** [Evaluator and calibration failures](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#part-iii-failures-that-changed-the-system), historical evaluation reports referenced there.

**Likely follow-ups.** How would you redesign human evaluation? Can an LLM judge grade its own model family? What is evaluator leakage?

### 15. What did evaluation prove, and what did it not prove?

**30-second answer.** It showed that objective workflow safeguards can be tested, known semantic failures can become regression cases, and the current judge protocol worked on a five-case independently reviewed development sample. It did not prove reliable live retrieval across every scenario, production readiness, universal judge accuracy, or multi-agent superiority.

**2-minute answer.** The valid evidence is specific. Deterministic and stress suites exercised contracts, citations, contradictions, causal discipline, missing-source handling, and security boundaries. GPT-5.4 and an independent product manager agreed on all verdicts and severities across five blind development packets, including two critical failures. Those cases were not held out, so the result validates the protocol only on that sample. The broader architecture benchmark also did not complete: 13 executions were legitimate, 57 failed with HTTP 402, and 134 were unattempted. The live wallet-funding failure further showed that correct reasoning over a defective retrieval set remains possible. Real customer data, production traffic, enterprise tenancy, end-to-end retrieval reliability, and outcome impact remain unvalidated.

**Deep-dive points.** Separate “workflow completed” from “the investigation found the right evidence,” and separate both from “the product created user value.” Treat incomplete experiments as findings about the test environment, not model quality.

**Repository evidence/source.** [What evaluation established](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#what-evaluation-has-established) and [has not established](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#what-evaluation-has-not-established).

**Likely follow-ups.** What is the next most important evaluation? How would you compare single and multi-agent fairly? What production metric matters most?

## F. Performance and economics

### 16. Why were investigations slow and expensive, and what did profiling reveal?

**30-second answer.** The first profiled run took 558.08 seconds, used 164,734 tokens, and cost $0.788899. The main problem was not just specialist retrieval: PM and Critic work represented 73.2% of cost, revisions 55.8%, duplicate context exceeded 75,000 input tokens, and five outputs truncated.

**2-minute answer.** I initially expected multiple specialists to dominate latency. Profiling showed a different story. Large repeated ledger context, long PM generation, revision, retries, and provider tail latency dominated the critical path. I reduced redundant context, constrained outputs, kept specialists parallel, and routed some roles to smaller models. In a historical three-scenario controlled run, average latency was 109.10 seconds and average cost $0.0656, with scenario-level results reported separately. That is a phase-specific improvement, not a current SLA. A later tail outlier still reached 310.35 seconds, showing that provider variability remained material.

**Deep-dive points.** TTFT and generation time are different. One outlier PM call took 170.62 seconds with 2.82-second TTFT, implicating output generation rather than queue wait. Optimization must preserve the quality gate.

**Repository evidence/source.** [Performance and cost](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#part-ii-performance-and-cost), [Phase 12 profiling](../implementation/PHASE12_PROFILING_REPORT.md).

**Likely follow-ups.** Which optimization had the highest leverage? Why not shorten every prompt? What is the current p95?

### 17. How would you reduce cost and latency at 10x or 100x usage?

**30-second answer.** I would first route by question complexity, pre-compute deterministic source metrics, cache safe source queries, cap context by evidence relevance, and reserve the strongest model for consequential synthesis. Operationally I would add queues, tenant limits, cancellation, and cost budgets.

**2-minute answer.** At scale I would not run the six-role path for every question. A classifier could distinguish a direct metric lookup, a single-source investigation, and a high-risk cross-source decision. Deterministic query planning and compact evidence representations reduce tokens before model selection does. I would batch or cache immutable source reads, use smaller models for planning and critique when evaluation supports them, and trigger revision only on concrete issues. I would track cost per useful completed brief, not just per call. On the platform side, durable workers, backpressure, provider failover policies, and per-tenant concurrency protect reliability.

**Deep-dive points.** Cost controls must not silently reduce source coverage or skip critique. Any new route needs its own evaluation slice. Provider pricing and latency are external dependencies.

**Repository evidence/source.** [Model routing and scaling decisions](04_DECISIONS_AND_EVOLUTION.md#8-centralize-model-routing-instead-of-using-one-model-everywhere), [current limitations](01_CURRENT_STATE.md#current-limitations).

**Likely follow-ups.** Would you cache LLM output? How would you set budgets? What happens when provider prices rise?

### 18. What would 1,000 investigations per day imply?

**30-second answer.** It would turn provider variability, queueing, tenant isolation, observability, and unit economics into product requirements. I would need workload classes, durable workers, per-tenant quotas, SLOs, failure budgets, and explicit data-retention controls before treating that volume as routine.

**2-minute answer.** The historical average cannot simply be multiplied into a forecast because query complexity, revisions, and provider tails vary. I would model arrival rate, peak concurrency, model-call distribution, token percentiles, source quotas, retries, and abandonment. The current API-process execution model would move to a durable job system. SSE would consume events from a shared broker rather than local subscriber queues. I would define p50/p95 completion targets, maximum cost by investigation class, and graceful degradation rules. I would also evaluate whether most traffic really requires a full investigation.

**Deep-dive points.** Capacity planning needs percentile distributions, not averages. Replay safety matters because provider calls can be paid and non-idempotent. Multi-tenant privacy becomes a hard release gate.

**Repository evidence/source.** [Process-local limitations](01_CURRENT_STATE.md#current-limitations), [scaling evolution](04_DECISIONS_AND_EVOLUTION.md#11-evolve-from-process-local-history-to-supabase-ownership-and-checkpoint-recovery).

**Likely follow-ups.** How would you estimate concurrency? What is your retry strategy? Where would you introduce a queue?

## G. Persistence and authentication

### 19. Why was persistence initially deferred, and why introduce Supabase later?

**30-second answer.** Early on, process-local state kept attention on validating the investigation workflow. Once users needed durable history, ownership, navigation without restarts, and recovery after process failure, memory-only state became a product defect. Supabase provided identity and Postgres persistence without building both from scratch.

**2-minute answer.** Deferring persistence was reasonable while the core risk was whether the multi-agent investigation could produce a grounded recommendation. The assumption stopped being reasonable when the app became an authenticated user product. Repeated lifecycle problems showed that page state and API memory could not be authoritative. Supabase now handles email/password identity and sessions; Postgres stores owner-scoped investigations, durable events, final typed state, and LangGraph checkpoints. This improved trust but introduced migrations, token validation, authorization, recovery, deletion, and operational responsibilities.

**Deep-dive points.** Earlier documents that say auth and persistence are deferred are historical. Supabase is not agent memory. The backend still owns workflow semantics.

**Repository evidence/source.** [Authentication and ownership](01_CURRENT_STATE.md#supabase-authentication-and-ownership), [persistence and recovery](01_CURRENT_STATE.md#persistence-and-recovery), [ADR-0018](../decisions/ADR-0018-supabase-auth-and-investigation-persistence.md), [ADR-0019](../decisions/ADR-0019-postgres-checkpointed-investigation-recovery.md).

**Likely follow-ups.** Why Supabase instead of a custom auth service? What remains in memory? What new risks did auth create?

### 20. How are investigations associated with users, and where is authorization enforced?

**30-second answer.** The frontend sends the Supabase access token. FastAPI verifies its cryptographic and semantic claims and uses the verified `sub` as the owner ID. Every investigation query is owner-scoped and returns not found for cross-user access. Database RLS provides defense in depth.

**2-minute answer.** Next.js protects private routes and manages the cookie-backed session, but UI routing is not the security boundary. The API validates signature through Supabase JWKS, issuer, audience `authenticated`, expiry, and subject. Creation writes the subject as `owner_id`; list, get, stream, evidence, resume, rename, and delete all constrain by that owner. Returning 404 for an inaccessible ID avoids confirming that another user's investigation exists. RLS policies protect direct user-context access, while backend owner checks remain mandatory because a backend database connection may hold broader privileges.

**Deep-dive points.** Authentication answers who the caller is; authorization answers which investigation they may access. Public cached sample routes are an explicit exception, not accidental leakage.

**Repository evidence/source.** [Access-control model](01_CURRENT_STATE.md#access-control-model), [architecture ownership](02_PRODUCT_AND_ARCHITECTURE.md#important-architecture-concepts).

**Likely follow-ups.** How do deletes work? What if the JWT is expired? How would organization sharing change the model?

### 21. What changes for enterprise multi-tenancy?

**30-second answer.** Owner IDs are sufficient for individual accounts, not enterprise tenancy. I would introduce organizations, memberships, roles, organization-scoped investigations, explicit sharing rules, tenant-aware source credentials, audit logs, retention policy, and authorization tests at every boundary.

**2-minute answer.** The current model binds an investigation to one authenticated subject. Enterprise use adds a separate tenant identity and multiple principals: creator, viewer, admin, service account, and possibly guest. Source credentials must be isolated per organization, and evidence must never cross tenant boundaries. RLS would become organization-aware; the API would check membership and entitlement; background jobs and logs would carry tenant context; exports and deletion would follow retention policy. I would validate this with adversarial authorization tests before connecting real customer data.

**Deep-dive points.** Enterprise auth also implies SSO, provisioning, auditability, regional data controls, and incident response. It is not a UI switch.

**Repository evidence/source.** [Current auth limitations](01_CURRENT_STATE.md#current-limitations), [larger-scale persistence trade-off](04_DECISIONS_AND_EVOLUTION.md#11-evolve-from-process-local-history-to-supabase-ownership-and-checkpoint-recovery).

**Likely follow-ups.** Would you use tenant-per-database? How would service accounts work? How would you test RLS?

## H. Failure and learning

### 22. What was the biggest technical/product failure?

**30-second answer.** The most important product failure was a paid wallet-funding investigation that produced a cautious, cited answer from an incorrectly empty evidence packet. PostHog and Zendesk contained relevant evidence, but the agents used a semantically invalid analytics filter and overly narrow support searches. The system reasoned responsibly over the wrong evidence set.

**2-minute answer.** **Situation:** the question claimed that debit-card wallet funding failures were elevated. **Initial belief:** typed tool schemas, specialist prompts, provenance, and Critic review were enough to make the investigation safe. **What happened:** the Analytics Agent used `user_type = debit_card`, even though `debit_card` was a payment method, so valid wallet-funding events disappeared. The Research Agent repeated searches containing “failure” and never ran the broad journey search that returned 12 relevant tickets. Jira correctly returned no incident. **Evidence:** a direct read-only check found 483 starts, 283 submissions, 283 completions, zero recorded failure events, and 12 support tickets about unexpected cost. **Decision:** separate retrieval evaluation from final-answer evaluation and make this an end-to-end regression case before another paid demo run. **Outcome:** the failure is documented, but I do not claim it is fixed yet. **Lesson:** provenance proves where retrieved evidence came from; it does not prove that the system retrieved what it should have found.

**Deep-dive points.** Distinguish schema-valid from semantically valid tool calls. Test the user's premise before searching only for confirming language. A Critic without source tools cannot recover omitted evidence.

**Repository evidence/source.** [Correct reasoning over incorrect retrieval](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#10-correct-reasoning-over-incorrect-retrieval), [current evaluation strategy](../evaluation/EVALUATION_STRATEGY.md#1-retrieval-quality).

**Likely follow-ups.** Why did the Critic not catch it? How would you test retrieval recall? Why not hardcode the four demo answers?

### 23. Tell me about a design assumption evaluation disproved.

**30-second answer.** I assumed a valid schema and a review step meant every final recommendation had passed the Critic. Later inspection showed the revised branch could bypass post-revision critique. I restored the quality gate and accepted the added call cost.

**2-minute answer.** **Situation:** the workflow already had PM and Critic roles. **Initial belief:** the bounded revision path preserved the same standard as the initial path. **What happened:** an optimization finalized revised PM output without another Critic pass. **Evidence:** graph-path review and tests exposed that the contract differed by branch. **Decision:** ADR-0025 routed revised output back through Critic and kept termination bounded. **Outcome:** worst-case latency increased, but the architecture again matched the product claim that final recommendations are independently reviewed. **Lesson:** optimize a workflow only after naming the invariant that cannot be traded away.

**Deep-dive points.** Graph topology is product policy. A “successful” endpoint is not enough if different paths have different assurance.

**Repository evidence/source.** [ADR-0025](../decisions/ADR-0025-post-revision-quality-gate.md), [failure story](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#8-post-revision-quality-gate-bypass).

**Likely follow-ups.** How was the regression tested? Could another branch bypass validation? Why not allow more revisions?

### 24. What did tool and incomplete-evidence failures teach you?

**30-second answer.** They taught me that transport success, retrieval correctness, evidence sufficiency, and decision quality are separate states. A tool can return HTTP 200 and still answer the wrong analytical question. Zero rows may mean no evidence, or they may mean the query removed evidence that was actually present.

**2-minute answer.** The project exposed several distinct failures. PostHog can return useful table rows while a scalar `value` is empty. Jira can return broad keyword matches whose content does not support the question. A source can fail entirely. The wallet investigation added another case: a successful query can return zero because the model selected an invalid domain value. These states need different responses. Transport failure should be disclosed. Empty but valid evidence may lower confidence. A suspiciously empty baseline should trigger retrieval validation. Missing evidence cannot be repaired by rewriting the recommendation. Where no defensible decision exists, the system should return a specific validation plan rather than fill the gap with plausible prose.

**Deep-dive points.** Validate property-value combinations, not only JSON shape. Inspect record content, not issue keys alone. Treat repeated equivalent zero-result searches as one source outcome. Partial completion needs a policy, not improvisation.

**Repository evidence/source.** [Analytics result-shape failure](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#9-analytics-rows-hidden-by-an-empty-scalar-value), [retrieval failure](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md#10-correct-reasoning-over-incorrect-retrieval), and [ADR-0026](../decisions/ADR-0026-report-projection-and-bounded-specialist-repair.md).

**Likely follow-ups.** When is partial evidence enough? How do you set confidence? What should the UI disclose?

## I. Product judgment

### 25. Why allow “investigate further” instead of forcing an answer?

**30-second answer.** A forced answer creates false confidence. “Investigate further” is valuable when it identifies the missing evidence, proposes the smallest validation step, defines a target and review window, and explains what result would change the decision.

**2-minute answer.** The product operates in environments where tags are incomplete, events may be missing, and Jira context may be suggestive rather than causal. Pretending every question has a root cause would make the product dangerous. The key is to avoid a vague refusal. A strong follow-up recommendation says, for example, establish a baseline for a named event and segment before committing engineering work. It preserves decision momentum while being honest about evidence quality.

**Deep-dive points.** Confidence is not binary. “Investigate further” should not expose internal model failures or raw system jargon. It is a product decision state, not an error state.

**Repository evidence/source.** [Product job](02_PRODUCT_AND_ARCHITECTURE.md#product-job), [limitations and evidence handling](01_CURRENT_STATE.md#current-capabilities).

**Likely follow-ups.** How often is this outcome acceptable? How do you keep it from becoming a default? What makes a validation plan actionable?

### 26. Why expose citations and separate facts, interpretations, and hypotheses?

**30-second answer.** The recommendation is more useful when a PM can verify its basis. Facts describe retrieved evidence, interpretations connect patterns, and hypotheses identify explanations that still need testing. Citations let the user inspect that distinction rather than trust fluent prose.

**2-minute answer.** Product questions invite causal shortcuts. Seventeen tickets mentioning pending transfers is a fact. Saying customers are uncertain is an interpretation. Saying delayed callbacks cause the uncertainty is a hypothesis unless stronger evidence exists. The ledger preserves those layers and source references, while the evidence drawer provides deeper records without cluttering the decision brief. This design supports trust and review, but it does not mean every user should read every record before acting.

**Deep-dive points.** Citation validity is a necessary but insufficient quality measure. A valid citation can still be weak support for the sentence attached to it.

**Repository evidence/source.** [Evidence Ledger and citations](02_PRODUCT_AND_ARCHITECTURE.md#important-architecture-concepts), [ADR-0020](../decisions/ADR-0020-nested-evidence-audit-records.md).

**Likely follow-ups.** How do you test citation entailment? Can too much evidence reduce usability? Should citations be public?

### 27. What did you deliberately not build, and what would you cut first?

**30-second answer.** I did not add autonomous writes, RAG, a vector database, long-term agent memory, MCP, public report sharing, or enterprise tenancy. If I had to simplify, I would route simple questions away from the full agent graph before removing provenance, authorization, or the final quality gate.

**2-minute answer.** Each excluded capability creates a new risk boundary. Autonomous writes require approvals and auditability. RAG is not needed for the current structured API sources. Long-term memory could leak context between investigations or tenants. Public sharing changes authorization. Enterprise tenancy requires a different ownership model. The system already has enough complexity in evidence quality and orchestration. I would cut complexity that is not tied to measured user value, but preserve the controls that make recommendations defensible.

**Deep-dive points.** “Agentic” should mean purposeful controlled action, not maximum autonomy. A future action layer should begin with draft actions and human approval.

**Repository evidence/source.** [Deliberate scope](04_DECISIONS_AND_EVOLUTION.md#13-deliberate-scope-boundaries), [current limitations](01_CURRENT_STATE.md#current-limitations).

**Likely follow-ups.** When would RAG become appropriate? What is the first proposed action? Why no public links?

## J. Scaling

### 28. What changes if the dataset becomes real production data?

**30-second answer.** Data governance becomes a release gate. I would need tenant-specific connectors, least-privilege credentials, schema mapping, PII minimization, retention and deletion rules, audit logs, source snapshots, and evaluation on representative but authorized production cases.

**2-minute answer.** Synthetic data is coherent and known; production data is inconsistent, delayed, duplicated, and sensitive. The product would need an onboarding diagnostic that measures event coverage, ticket taxonomy, Jira hygiene, and time-zone alignment before promising a recommendation. Evidence access would be scoped by tenant and user entitlement. Prompts and traces would minimize sensitive payloads. I would run in shadow mode, compare outputs with PM decisions, and audit false confidence before enabling broad use.

**Deep-dive points.** Source data quality should be surfaced as a product signal. LangSmith and application logs need privacy review. Deletion must cover records, evidence snapshots, events, and checkpoints.

**Repository evidence/source.** [Data limitations](01_CURRENT_STATE.md#current-limitations), [data environment decision](04_DECISIONS_AND_EVOLUTION.md#7-choose-a-mixed-real-mocked-and-synthetic-data-environment).

**Likely follow-ups.** How would you handle PII? What data would you persist? How would you validate connector quality?

### 29. How would model routing evolve if costs rise or latency requirements tighten?

**30-second answer.** I would route by complexity and risk, not switch the whole system to a cheaper model. Deterministic lookups and low-risk summaries could use smaller models or no model; high-impact synthesis would retain stronger reasoning. Every routing change would have an evaluation gate.

**2-minute answer.** The current role-based gateway already separates model choice from agent code. The next step is evidence-based dynamic routing using factors such as number of sources, contradiction, confidence, requested depth, and decision risk. I would set latency and cost budgets per class, support provider fallbacks only after compatibility testing, and compare quality regressions by dimension. If a smaller model creates more schema repairs or revisions, its nominal call price may be a false economy.

**Deep-dive points.** Include retries and output length in total economics. Preserve model and prompt metadata for observability. Avoid provider-specific logic inside agents.

**Repository evidence/source.** [Model/provider layer](01_CURRENT_STATE.md#current-architecture), [model allocation decision](04_DECISIONS_AND_EVOLUTION.md#8-centralize-model-routing-instead-of-using-one-model-everywhere).

**Likely follow-ups.** What features would drive the router? Would you use a model to choose a model? How would failover affect reproducibility?

### 30. What would you rebuild differently?

**30-second answer.** I would define the durable investigation lifecycle, evidence projection, and evaluation harness earlier. I would still start with synthetic scenarios, but I would establish compact evidence contracts and a valid human-review protocol before optimizing prompts or adding UI depth.

**2-minute answer.** The project correctly validated the investigation concept before adding production infrastructure, but the process-local lifecycle survived too long and caused repeated trust problems. I also treated rich context as automatically beneficial until profiling showed the opposite. Finally, human calibration and the large benchmark were designed before provider budgets and evaluator parity were fully controlled. If rebuilding, I would make ownership and state transitions explicit from the first user-facing version, design one canonical evidence representation for agents, evaluation, and UI, and require budget-aware experiment preflight. I would still preserve the read-only boundary and the separation between retrieval, synthesis, and critique.

**Deep-dive points.** This is not an argument for building every production feature on day one. It is an argument for identifying which product invariants become expensive to retrofit: ownership, provenance, lifecycle semantics, and evaluation comparability.

**Repository evidence/source.** [Decision evolution](04_DECISIONS_AND_EVOLUTION.md), [failure history](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md).

**Likely follow-ups.** What would remain the same? What was the highest-value decision? What would you do in the first four weeks?

## K. Product strategy

### 31. What is the product strategy, and where would you start?

**30-second answer.** I would start with evidence-heavy product investigations where support, analytics, and engineering each contain part of the answer. The product sits between retrieval and decision-making: it does not replace source systems or PM judgement, but creates an auditable first-pass investigation that helps a PM decide whether to act, validate, instrument, or investigate further.

**2-minute answer.** The broad problem is fragmented evidence, but that is too wide for an initial market. The focused wedge is a recurring, material question such as a funnel decline, complaint surge, apparent transaction failure, low feature adoption, or disagreement between customer and behavioural signals. These questions justify a structured investigation because the cost of a plausible but wrong conclusion is meaningful. The initial user is a PM or product lead. The economic buyer is still a hypothesis and could be a Head of Product, Product Operations leader, business-unit leader, or founder. I would begin with read-only source access, compare the brief with the team's normal process, and expand only after proving retrieval reliability, decision usefulness, and repeated usage.

**Deep-dive points.** The product is not a replacement for BI, analytics, or enterprise search. It should route simple questions to cheaper paths rather than use the full graph every time. Market demand, buyer ownership, and willingness to pay remain unvalidated.

**Repository evidence/source.** [AI Product Strategy](06_AI_PRODUCT_STRATEGY.md), [product problem](02_PRODUCT_AND_ARCHITECTURE.md#product-problem).

**Likely follow-ups.** Why this wedge? Which vertical would you choose first? What user research would you run? What would you exclude from the first commercial version?

### 32. How would you measure product value and drive adoption?

**30-second answer.** The product succeeds when it helps a team reach a defensible decision faster, not when it merely generates a report. I would measure time to decision, whether the brief changed or clarified action, recommendation adoption, evidence inspection, later reversals, user trust, repeat use, and cost per useful investigation.

**2-minute answer.** The candidate north-star measure is the percentage of investigations that help a team reach a defensible decision faster than its existing process. I would establish a baseline using recent investigations, then compare the normal workflow with PMLytics AI. A user is meaningfully activated when they complete an investigation, inspect the evidence, and say that it accelerated a decision, changed the decision, or identified a validation gap that prevented premature action. Adoption should begin with a recurring high-friction investigation class, read-only access, transparent evidence, and guided comparison with the existing process. Retention should come from repeated trust and time saved, not from the novelty of an AI-generated brief.

**Deep-dive points.** Separate product-value measures from model-quality and operational measures. Citation clicks do not prove a useful decision. Recommendation adoption is not always success because a responsible investigate-further result may prevent a bad action.

**Repository evidence/source.** [Business outcome validation](06_AI_PRODUCT_STRATEGY.md#business-outcome-validation), [adoption strategy](06_AI_PRODUCT_STRATEGY.md#adoption-strategy).

**Likely follow-ups.** How would you measure a better decision? What is the activation event? How would you avoid confirmation bias in a pilot? What would make teams return?

### 33. What makes PMLytics AI defensible?

**30-second answer.** The current implementation does not yet have a proven moat. Agents, prompts, models, and standard SaaS integrations are reproducible. Defensibility could develop through organisation-specific source mappings, a trusted evaluation library built from real failures, decision-to-outcome feedback, workflow embedding, and demonstrated governance.

**2-minute answer.** I would not present LangGraph or six agents as a moat. The harder assets would emerge only through use. First, reliable mappings between each organisation's events, properties, ticket language, Jira taxonomy, and metric definitions. Second, independently reviewed evaluation cases created from real retrieval and reasoning failures. Third, feedback connecting recommendations with later decisions and outcomes. Fourth, integration into recurring product-review and prioritisation processes. Finally, a trust layer built through provenance, privacy, ownership, and disciplined uncertainty. These are a defensibility thesis, not achievements I can claim from synthetic data.

**Deep-dive points.** Distinguish feature advantage from durable defensibility. Customer data alone is not a moat if it is poorly governed or cannot improve the product safely. Workflow switching costs should reflect real value rather than lock-in.

**Repository evidence/source.** [Defensibility thesis](06_AI_PRODUCT_STRATEGY.md#defensibility-thesis), [strategic risks](06_AI_PRODUCT_STRATEGY.md#strategic-risks-and-responses).

**Likely follow-ups.** What could an incumbent copy? How would outcome feedback improve the product? Does customer-specific configuration create a services business? What is the risk of vendor bundling?

## L. Operating model and safe release

### 34. How would you decide whether PMLytics AI is safe to release?

**30-second answer.** I would name the maturity stage first, then require evidence across identity, retrieval, provenance, recommendation quality, workflow recovery, evaluation, performance, user trust, and data governance. A portfolio demo and a production customer release should not share the same gate.

**2-minute answer.** The operating plan defines three decisions: approved, approved with documented limitations, or blocked. The current controlled portfolio demo is approved with limitations because the reference reports, authentication, ownership, provenance, and development evaluation can be demonstrated honestly with synthetic data. Private pilot or production use is blocked because end-to-end retrieval is incomplete, production-shaped source data has not been validated, the held-out set is empty, enterprise governance is absent, sustained concurrency is untested, and business outcomes are unproven. Each material release should have a compact evidence package with the changed components, relevant tests, evaluation, cost and latency impact, known limitations, and rollback path.

**Deep-dive points.** Release gates should be proportional to the claim. Objective conditions remain deterministic. A polished result cannot override a failed retrieval or ownership gate. Accepted limitations require a named owner and must be appropriate for the declared stage.

**Repository evidence/source.** [Release gates](07_AI_OPERATING_AND_SAFE_RELEASE_PLAN.md#release-gates), [current readiness decision](07_AI_OPERATING_AND_SAFE_RELEASE_PLAN.md#current-readiness-decision).

**Likely follow-ups.** Which gate is currently blocked? Who approves an exception? What would you require for a design-partner pilot? How do you roll back a model change?

### 35. How would you operate failures and prevent expensive repetition?

**30-second answer.** I classify the failure before deciding whether to retry. A transient provider error, semantically wrong query, missing source, oversized context, credit failure, and ambiguous paid call need different responses. Material failures are preserved, diagnosed at the boundary that owns them, and converted into regression cases.

**2-minute answer.** The response sequence is contain, classify, assess impact, correct the smallest responsible boundary, verify, and learn. If retrieval used an invalid property value, I fix domain validation rather than rewrite the PM prompt. If a source is unavailable, the system may return a partial result only when the remaining evidence supports one. If context is too large, the next attempt must reduce it. Provider credit failure stops rather than retries. An unresolved paid call resumes only through explicit checkpoint recovery. The operating record should identify affected investigations, whether completed reports may be wrong, the corrective case, and any remaining limitation.

**Deep-dive points.** Severity follows user and decision impact, not whether the bug is labelled AI or software. Preserve failed artifacts and traces. Do not weaken a rubric or expected result simply to make a release pass.

**Repository evidence/source.** [Incident response](07_AI_OPERATING_AND_SAFE_RELEASE_PLAN.md#incident-response), [failure-specific response rules](07_AI_OPERATING_AND_SAFE_RELEASE_PLAN.md#failure-specific-response-rules).

**Likely follow-ups.** When do you disable live investigations? How do you find affected reports? When is a retry safe? How does a failure enter the regression library?

### 36. Why is the held-out set empty, and when would you create it?

**30-second answer.** The existing 15 cases are development regressions and the independently reviewed five-case sample is a calibration pilot. I did not relabel either as held out. A genuine held-out set requires new unseen cases, independent review, adjudication, and a sealed version, so I deferred it until the system is stable and a reviewer is available.

**2-minute answer.** A held-out case is more than a question. It includes a frozen evidence packet, required source coverage, expected findings, acceptable conclusions, prohibited claims, criterion-level expectations, severity, and review provenance. If I inspect those labels and tune the system against them, the cases become development regressions. The held-out set is not necessary for local development or an honest portfolio demonstration. It becomes strongly recommended for a design-partner pilot and required before a production-readiness claim. When the time comes, I would freeze the system, commission approximately 8 to 15 new cases, obtain blind independent review, seal the version, approve one bounded paid run, and report failures without silently excluding them.

**Deep-dive points.** An empty held-out set is more credible than manufactured independence. Development, calibration, and held-out sets answer different questions. Once a failed held-out case is used for repair, it belongs in the development regression library.

**Repository evidence/source.** [Held-out policy](07_AI_OPERATING_AND_SAFE_RELEASE_PLAN.md#gate-6-evaluation-evidence), [evaluation strategy](../evaluation/EVALUATION_STRATEGY.md#held-out-set).

**Likely follow-ups.** Who should write the cases? Why not use the current independent sample? Can a public repository contain a held-out set? How often should it be refreshed?

## Closing narrative

The strongest way to describe this project is not “I built a multi-agent app.” It is:

> I built a decision-support system for product managers, then used evaluation and profiling to discover where the architecture was overconfident, expensive, slow, or operationally fragile. I preserved provenance and human control, corrected the quality gates, reduced context waste, introduced durable identity and ownership when the product required them, and remained explicit about what synthetic evaluation does not prove.

That narrative demonstrates product judgement and technical credibility without pretending the project is already a production-proven enterprise platform.
