# PMLytics AI Operating and Safe Release Plan

## Purpose

This document explains how PMLytics AI should be operated, changed, evaluated, and released without treating a successful model response as sufficient proof of safety or usefulness.

It covers the current portfolio application and the controls that would be required before a private pilot or production use. It does not claim that the current system is production ready.

PMLytics AI is the product. Pocket is the fictional fintech company represented by synthetic demonstration data.

## Current operating posture

PMLytics AI currently operates as a read-only product investigation and decision-support application.

It includes:

- authenticated users and owner-scoped investigations;
- a FastAPI application boundary;
- a LangGraph workflow with bounded specialist, follow-up, repair, and revision paths;
- role-bound Zendesk, PostHog, and Jira tools;
- an append-only Evidence Ledger;
- PM synthesis and Critic review;
- PostgreSQL persistence and LangGraph checkpoints through Supabase;
- SSE progress with polling fallback;
- LangSmith tracing and application telemetry;
- deterministic evaluation, development stress cases, and an independently reviewed calibration pilot.

It has not been validated with real customer production data, sustained production traffic, enterprise tenancy, or a qualified held-out evaluation set. End-to-end retrieval correctness is still an incomplete release gate.

## Operating principles

1. **Retrieval comes before reasoning.** A careful recommendation cannot compensate for evidence that was not found.
2. **Hard guarantees belong in code.** Authentication, permissions, schemas, budgets, citations, and terminal states must not depend on a prompt.
3. **Model output is fallible.** Fluency is never treated as evidence of correctness.
4. **Source failure is not absence of evidence.** Failed, empty, and semantically incorrect queries are different states.
5. **Uncertainty is a valid product outcome.** Partial results and investigate-further decisions are preferable to manufactured certainty.
6. **Consequential decisions remain human-owned.** The product recommends; the PM decides.
7. **Retries require a failure theory.** The system should retry only when the next attempt can plausibly differ.
8. **Paid work must be bounded.** Live model and judge calls require explicit budgets, observable usage, and fail-closed ceilings.
9. **Failures become permanent learning.** Material failures should become regression cases after their cause is understood.
10. **Release evidence must match the claim.** Portfolio demonstration, private pilot, and production use require different proof.

## Maturity stages

| Stage | Purpose | Required evidence | Current position |
| --- | --- | --- | --- |
| Local development | Build and diagnose the system | Focused tests, source fixtures, traces, documented limitations | Supported |
| Controlled portfolio demo | Demonstrate the product and decision experience | Stable reference reports, protected live calls, core regression checks, transparent synthetic-data disclosure | Supported with documented limitations |
| Private design-partner pilot | Test usefulness with authorised users and production-shaped data | Retrieval gate, data-governance review, pilot metrics, incident process, independent evaluation sample | Not ready |
| Limited production pilot | Serve a bounded customer cohort | Qualified release evidence, tenant controls, operational ownership, monitoring, rollback, support commitments | Not ready |
| Broader production release | Support repeatable commercial use | Proven value, reliability, governance, scalable execution, validated economics | Not ready |

Public deployment and autonomous write actions are outside the current plan.

## Ownership model

One person may hold several roles in a portfolio project, but the responsibilities should remain distinct.

| Role | Owns | Must not self-approve |
| --- | --- | --- |
| Product Owner | User problem, scope, outcome measures, acceptable limitations, release decision | A material quality exception without documented evidence |
| AI/System Owner | Workflow, prompts, model routing, state, tools, failure handling, observability | Semantic quality of a material change based only on personal inspection |
| Evaluation Owner | Case library, deterministic checks, judge configuration, regression reports | A rubric change introduced only to make a failing result pass |
| Independent Reviewer | Blind review of selected semantic cases and material disagreements | Cases where prior labels or judge results were visible |
| Data/Integration Owner | Source credentials, mappings, schemas, query validity, data-readiness checks | A source declared reliable without representative validation |
| Security/Privacy Reviewer | Identity, authorization, secrets, data minimisation, retention, trace exposure | A security exception affecting other users or sensitive data |
| Release Approver | Confirms required gates and accepts documented limitations | A blocked critical gate without explicit risk ownership |

For the current project, the author can operate the first three roles. Independent claims still require an independent reviewer.

## Change classification

Every material change should be classified before testing.

| Change class | Examples | Minimum evidence |
| --- | --- | --- |
| Documentation | Copy, diagrams, explanatory material | Link and consistency checks |
| Presentation | Report ordering, evidence display, progress language | Frontend tests and product review; no AI evaluation unless meaning changes |
| Deterministic application logic | Status rules, ownership filters, progress reconciliation | Unit, integration, API, and affected workflow tests |
| Source adapter or tool | Query parameters, response parsing, time scoping | Contract tests, source fixture tests, retrieval regressions |
| Prompt | Planning, specialist, PM, Critic instructions | Affected development cases and semantic evaluation where meaning changes |
| Model routing | Provider, model, token ceiling, role allocation | Quality, latency, cost, and structured-output comparison |
| Evidence contract | Ledger fields, citation identity, support projection | Provenance tests, evaluator packet tests, report projection tests |
| Workflow topology | New node, routing condition, follow-up or revision behaviour | Workflow termination, budget, recovery, and end-to-end regression tests |
| Evaluation method | Rubric, judge prompt, severity, packet construction | Versioned evaluator tests and independent audit where claims depend on it |
| Authentication or persistence | Tokens, ownership, RLS, migrations, checkpoints | Security, cross-user access, migration, recovery, and deletion tests |
| Source data | Seed records, event taxonomy, expected scenario evidence | Reproducibility report and affected retrieval/evaluation cases |

Changing several high-risk classes at once should be avoided because it makes attribution difficult.

## Release evidence package

A release decision should point to a small evidence package containing:

- release identifier or commit;
- change summary and change classification;
- intended product effect;
- affected agents, tools, sources, and schemas;
- focused and broader test results;
- retrieval regression result where relevant;
- semantic evaluation result where relevant;
- latency, call, and cost impact where relevant;
- known limitations;
- unresolved incidents or evaluator disagreements;
- rollback or disablement path;
- final gate decision and owner.

The package should reference existing reports rather than copy every result into another document.

## Release gates

### Gate 1: Identity, authorization, and secrets

**Purpose:** Prevent unauthorised access and credential exposure.

**Pass conditions:**

- authentication is required for investigation APIs;
- the verified Supabase subject is the trusted user identifier;
- investigation reads, events, retry, rename, and delete operations are owner scoped;
- one user cannot read or mutate another user's investigation;
- unauthenticated users cannot start a live investigation;
- service-role and provider credentials never reach the browser;
- secrets are absent from committed files, logs, traces, and report content;
- authentication failure produces an explicit non-success state.

**Current status:** Implemented at application level, but enterprise organisations, delegated roles, SSO, and production security review are not implemented.

### Gate 2: Source connectivity and retrieval correctness

**Purpose:** Establish that the investigation queried the right sources and assembled evidence capable of answering the question.

**Pass conditions:**

- required sources are selected for the question;
- the user's complete date range reaches relevant tools;
- tool inputs pass structural and domain-value validation;
- broad discovery occurs before narrow wording is treated as evidence of absence;
- claimed anomalies are compared with an appropriate baseline where possible;
- expected scenario evidence is retrieved;
- irrelevant records do not dominate the packet;
- suspicious zero results trigger validation or a bounded recovery path;
- transport failure, valid empty results, and semantically wrong queries are distinguishable;
- source-specific limitations are recorded;
- the Evidence Ledger represents the successful retrieval results accurately.

**Current status:** Blocked for production claims. The wallet-funding investigation showed that a structurally valid analytics filter and narrow support searches could hide evidence that existed. The four demo scenarios do not yet have a complete offline retrieval release gate.

### Gate 3: Evidence integrity and provenance

**Purpose:** Ensure every material claim can be traced to the evidence the system actually retrieved.

**Pass conditions:**

- successful tool results receive immutable evidence identifiers;
- failed tool attempts are recorded as errors, not evidence;
- citation identifier, source type, and source reference match;
- agents can cite only evidence from their permitted source;
- duplicate records do not create duplicate support;
- source summaries retain deeper record references;
- evidence visible to synthesis, evaluation, persistence, and the report remains consistent;
- instructions embedded in retrieved records are treated as untrusted data.

**Current status:** Implemented with deterministic checks and development stress coverage. Production source shapes remain unvalidated.

### Gate 4: Recommendation quality and uncertainty

**Purpose:** Prevent a polished brief from overstating what its packet can support.

**Pass conditions:**

- observations, interpretations, and hypotheses remain distinct;
- causal language matches evidence strength;
- contradictions affect confidence, recommendation, or follow-up;
- affected customers are not inferred from unsupported segmentation;
- success measures do not invent baselines or targets;
- missing sources and evidence gaps are disclosed;
- the action is proportionate and reversible where uncertainty remains;
- a revised PM candidate receives the required final Critic review;
- unresolved material Critic issues prevent a completed status.

**Current status:** Covered by deterministic validation, the 15-case development stress suite, and a five-case independent calibration pilot. This does not prove universal judge reliability or compensate for incomplete retrieval.

### Gate 5: Workflow termination, failure, and recovery

**Purpose:** Make paid, stateful execution predictable and recoverable.

**Pass conditions:**

- tool, model-call, follow-up, repair, and revision budgets are enforced;
- every graph path terminates in an explicit state;
- source failure cannot silently become successful evidence;
- retry policy distinguishes transient, semantic, budget, and insufficient-evidence failures;
- final state is durable before completion is announced;
- streaming reconnection does not restart an investigation;
- polling reconciliation cannot move progress backward;
- a process restart resumes only from a safe durable checkpoint;
- an ambiguous in-flight paid call requires explicit recovery rather than silent replay;
- cancellation and deletion produce consistent durable state.

**Current status:** Implemented for the current single-service application with PostgreSQL checkpoints and lease-based recovery. Substantial concurrent workload and external worker execution are not validated.

### Gate 6: Evaluation evidence

**Purpose:** Ensure a material AI change is supported by the right kind of evaluation.

**Pass conditions:**

- relevant deterministic tests pass;
- affected development regression cases pass;
- semantic changes use the declared evaluator version;
- humans and the judge receive identical packets when calibration is claimed;
- reviewer provenance and attestation are recorded;
- disagreements are adjudicated rather than averaged away;
- no unresolved critical false pass remains;
- results identify case population, model, phase, and limitations;
- paid evaluation was explicitly approved and remained within its ceiling.

**Held-out policy:** A qualified held-out set is not required for local development or a portfolio demonstration. It is strongly recommended for a private design-partner pilot and required before a production-readiness claim. The actual cases remain deferred until an independent reviewer is available and the system is stable enough to freeze.

**Current status:** Development and calibration evidence exists. The held-out set remains intentionally empty.

### Gate 7: Performance and provider economics

**Purpose:** Confirm that the workflow's speed and cost are appropriate for its use case and do not fail unpredictably.

**Pass conditions:**

- expected model and tool call ranges are understood;
- per-run and evaluation budgets are configured;
- provider credit or quota failure stops without wasteful retry;
- latency and cost are measured by scenario and configuration;
- repeated context and unnecessary re-execution are investigated;
- model routing changes preserve required quality;
- a rollback path exists for a model or provider change;
- published figures distinguish historical measurements from current expectations.

**Current status:** Historical optimisation reduced a matched run from 558.08 to 98.46 seconds and from $0.788899 to $0.0559. Later safety changes altered the path, so those figures are evidence of an optimisation result, not a current service-level promise. A new controlled benchmark is deferred until retrieval corrections are complete and paid testing is approved.

### Gate 8: Product experience and user trust

**Purpose:** Ensure the user can understand the state, result, evidence, and recovery options.

**Pass conditions:**

- a new investigation starts from a fresh server-authoritative state;
- progress represents the current investigation and does not restart on navigation;
- completion is not shown before the durable report is available;
- partial and failed results are visually and semantically distinct from completed decisions;
- a recoverable failure offers retry rather than only navigation away;
- the recommendation, confidence, findings, measures, risks, and open questions are understandable to product users;
- internal prompts, agent identifiers, raw system errors, and implementation details are absent from customer-facing reports;
- supporting evidence is discoverable and can be inspected at source-record level;
- users are told when evidence is synthetic or incomplete.

**Current status:** The current interface implements the intended decision-brief and evidence experience, but the latest paid investigation exposed an upstream retrieval problem. Product experience cannot compensate for an incomplete evidence packet.

### Gate 9: Data governance for production-shaped use

**Purpose:** Control how customer and organisational data enters, moves through, and leaves the system.

**Pass conditions before real customer data:**

- least-privilege connector credentials;
- explicit tenant and workspace ownership;
- documented data categories and lawful use;
- PII and sensitive-data minimisation;
- retention and deletion rules;
- trace and log redaction;
- subprocessor and provider review;
- source snapshots or reproducible query context where required for audit;
- regional, contractual, and incident-notification requirements;
- audited user deprovisioning and access revocation.

**Current status:** Not satisfied for production customer data. Current evidence is synthetic and the application uses direct user ownership rather than enterprise tenancy.

## Gate decisions

Every assessed release receives one of three decisions:

| Decision | Meaning |
| --- | --- |
| `APPROVED` | All gates required for the declared stage pass. |
| `APPROVED WITH DOCUMENTED LIMITATIONS` | No critical required gate is blocked, and accepted limitations are explicit and appropriate for the stage. |
| `BLOCKED` | A required gate is failed, untested, or lacks credible evidence. |

An approval is always tied to a declared maturity stage. Approval for a portfolio demonstration is not approval for a production customer launch.

## Current readiness decision

| Gate | Current assessment |
| --- | --- |
| Identity, authorization, and secrets | Implemented for direct user ownership; not enterprise validated |
| Source connectivity and retrieval correctness | Blocked for production claims |
| Evidence integrity and provenance | Implemented with development coverage |
| Recommendation quality and uncertainty | Implemented with development and calibration evidence |
| Workflow termination, failure, and recovery | Implemented for the current application topology; concurrency not validated |
| Evaluation evidence | Partial; no qualified held-out set |
| Performance and provider economics | Historical optimisation evidence; current baseline deferred |
| Product experience and user trust | Suitable for controlled demonstration with disclosed limitations |
| Production data governance | Not implemented |

### Controlled portfolio demonstration

**Decision:** `APPROVED WITH DOCUMENTED LIMITATIONS`

The system can be demonstrated using precomputed reference investigations, the recorded video, and carefully controlled local use. Any live paid investigation should wait until the retrieval regression gate passes offline.

Required disclosures:

- Pocket is fictional;
- all source evidence is synthetic;
- Zendesk and Jira are mocked;
- PostHog is a real integration containing deterministic synthetic events;
- the held-out set is empty;
- production traffic and customer data have not been validated;
- historical latency and cost figures are not current guarantees.

### Private design-partner or production use

**Decision:** `BLOCKED`

Primary blockers:

1. incomplete end-to-end retrieval gate;
2. no production-shaped source validation;
3. no qualified held-out evaluation;
4. no enterprise tenant and governance model;
5. no sustained concurrency or external worker validation;
6. no demonstrated business-outcome evidence with target users.

## Incident model

### Severity

| Severity | Definition | Example |
| --- | --- | --- |
| Critical | Privacy, ownership, security, or high-impact unsafe-decision failure | One user can access another user's investigation; fabricated evidence supports a consequential action |
| Major | Materially wrong investigation or repeated operational failure | Relevant source evidence is systematically removed by an invalid filter; revised answer bypasses final review |
| Moderate | Degraded result with a safe limitation or recovery path | One source fails and the report returns a clearly labelled partial decision |
| Minor | Localised defect that does not materially change the decision | Non-material wording issue or delayed progress event corrected by polling |

Severity should be based on user and decision impact, not on whether the failure occurred in AI code or conventional software.

### Incident classes

- authorization or data exposure;
- fabricated, misattributed, or irrelevant evidence;
- incorrect retrieval or false no-evidence conclusion;
- unsupported recommendation or causal overreach;
- missed material contradiction;
- source outage or schema change;
- provider outage, rate limit, or credit failure;
- runaway tool, model, revision, or retry cost;
- stalled, duplicated, or unrecoverable workflow;
- evaluator, rubric, or review-provenance failure;
- customer-facing exposure of internal technical content.

## Incident response

### 1. Contain

- stop or disable the affected live path when continued use could repeat harm;
- preserve existing investigation state and evidence;
- do not delete traces or failed artifacts needed for diagnosis;
- block automatic retry when the failure could duplicate paid work or unsafe output.

### 2. Classify

Determine whether the failure originated in:

- source data;
- query semantics;
- adapter or tool transport;
- specialist interpretation;
- evidence projection;
- PM synthesis;
- Critic review;
- persistence or recovery;
- authorization;
- evaluation infrastructure;
- customer-facing rendering.

### 3. Assess impact

- identify affected investigations, users, source periods, and model configurations;
- determine whether the same failure could exist in completed reports;
- distinguish an isolated case from a systematic defect;
- document whether a customer decision could have been materially affected.

### 4. Correct the smallest responsible boundary

Do not rewrite every prompt for a tool-schema error or add a retry for missing evidence. Fix the boundary that owns the failure.

### 5. Verify

- create or update the focused regression case;
- run the smallest relevant offline suite;
- run broader affected tests;
- obtain semantic or independent review when the claim requires it;
- request explicit approval before paid validation.

### 6. Learn

- record the failure, evidence, root cause, correction, and remaining limitation;
- update the relevant release gate;
- add the case to the development regression library after it is no longer held out;
- communicate affected results honestly.

## Failure-specific response rules

| Failure | Correct response | Incorrect response |
| --- | --- | --- |
| Transient provider error | Bounded retry with backoff when policy allows | Unlimited retry |
| Provider credit failure | Stop, surface configuration or budget failure | Wait and purchase the same request again |
| Invalid structured output | One permitted repair with focused instructions | Restart the full investigation automatically |
| Missing evidence | Targeted retrieval if authorised, otherwise disclose the gap | Rewrite the recommendation until it sounds complete |
| Suspicious zero result | Validate query semantics and broader discovery | Treat zero as proof that no problem exists |
| Source outage | Partial result only when remaining evidence supports it | Guess what the missing source would have shown |
| Oversized context | Reduce and focus the working set | Resend the same context repeatedly |
| Ambiguous in-flight paid call | Require explicit checkpoint recovery | Silently replay and risk duplicate spend |
| Authorization failure | Deny access and investigate | Fall back to an unscoped record lookup |

## Model, prompt, and tool change management

A material change should record:

- the observed failure or opportunity;
- the expected behavioural change;
- the smallest component that should own the correction;
- affected agents and tools;
- the cases that should change and cases that should remain stable;
- before-and-after deterministic results;
- semantic result where required;
- latency, token, and cost effect where material;
- rollback configuration;
- unresolved risks.

Model comparisons should hold the dataset, tools, architecture, and schemas constant wherever possible. Prompt changes should not be bundled with model and tool changes unless the experiment explicitly tests the combined release.

## Evaluation case lifecycle

```text
Observed failure or product requirement
→ Candidate case
→ Evidence and expected behaviour reviewed
→ Development regression case
→ Versioned suite
→ Release evidence
```

Held-out cases follow a different path:

```text
Stable system candidate
→ New unseen cases
→ Independent review and adjudication
→ Sealed version
→ One approved release evaluation
→ Results reported without silent exclusion
→ Failed cases move into development regression after diagnosis
```

Because an independent reviewer is not currently available, no actual held-out cases will be manufactured or labelled as qualified. The protocol remains documented for later use.

## Provider budget controls

Paid model and judge use should follow these rules:

1. Offline deterministic checks run first.
2. Cached results are reused only when content and evaluator configuration match.
3. The proposed case count, models, maximum calls, and estimated cost are shown before execution.
4. A paid run requires explicit approval.
5. The runner enforces a case limit and estimate-based cost ceiling.
6. Provider credit failures stop the run.
7. A corrected single case should not repurchase unchanged cases.
8. Actual usage is reconciled after the run.
9. Results without complete cost metadata are labelled incomplete rather than silently estimated as exact.

## Observability and operating review

The operating view should capture, where available:

- investigation and user-safe correlation identifier;
- workflow node and agent role;
- model and configuration;
- tool name and status;
- duration and time to first token;
- token usage and provider cost;
- tool, model, follow-up, repair, and revision counts;
- source failures and evidence count;
- checkpoint and recovery events;
- final status;
- evaluation and release metadata.

Operational review should look for patterns, not only individual failures:

- increasing false zero-result queries;
- a source producing more partial reports;
- model changes increasing repairs or revisions;
- cost growth without quality improvement;
- progress disconnects or recovery-required states;
- recurring unsupported claims by dimension;
- user abandonment before a brief becomes available.

LangSmith failure must not change product evidence or recommendation content. Observability is fail-open for an otherwise valid investigation, while security and ownership checks remain fail-closed.

## Business outcome review

Operational safety is necessary but not sufficient. At a design-partner stage, the release review should also ask:

- did the product reduce time to a defensible decision;
- did the brief change, clarify, or appropriately delay action;
- did users inspect and trust the supporting evidence;
- which investigations were rejected and why;
- were decisions later reversed by new evidence;
- did the product's value justify latency and provider cost;
- would a simpler workflow have produced the same result.

The measurement definitions live in the [AI Product Strategy](06_AI_PRODUCT_STRATEGY.md). This operating plan decides when those measures are strong enough for the next maturity stage.

## Safe-release checklist

Before declaring a stage-level release:

- [ ] The intended maturity stage is named.
- [ ] The change classes are recorded.
- [ ] Required tests and evaluation cases pass.
- [ ] Retrieval quality is assessed for affected questions.
- [ ] No unresolved critical security, ownership, evidence, or judge failure remains.
- [ ] Performance and cost claims name their scenario and configuration.
- [ ] Paid execution was approved and stayed within budget.
- [ ] Known limitations are visible to the release audience.
- [ ] Recovery or rollback is documented.
- [ ] An owner accepted each non-critical limitation.
- [ ] The release decision is recorded as approved, approved with limitations, or blocked.

## What this plan deliberately does not add

This plan does not introduce:

- public deployment;
- autonomous write actions;
- long-term agent memory;
- enterprise tenancy before evidence of need;
- a fabricated held-out evaluation set;
- numerical service-level objectives without representative operating data;
- a claim that the current portfolio system is production ready.

## Related documentation

- [Current state](01_CURRENT_STATE.md)
- [Product and architecture](02_PRODUCT_AND_ARCHITECTURE.md)
- [AI evaluation, failures, and learnings](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md)
- [Decisions and evolution](04_DECISIONS_AND_EVOLUTION.md)
- [PMLytics AI Q&A](05_PMLYTICS_AI_Q_AND_A.md)
- [AI Product Strategy](06_AI_PRODUCT_STRATEGY.md)
- [Evaluation strategy](../evaluation/EVALUATION_STRATEGY.md)
- [Portfolio case study](../PMLYTICS_AI_PORTFOLIO_CASE_STUDY.md)
