# Pocket AI Product Discovery Team
## Architecture Decision Records

**Version:** 1.0  
**Status:** Draft  
**Related documents:**  
- Product Requirements Document
- Product Specification
- System Architecture
- Agent Specification
- Data & API Specification
- Evaluation Strategy
- Implementation Plan

---

# ADR-001 — Use LangGraph for Agent Orchestration

**Status:** Accepted

**Date:** 2026-09-14

## Context

Pocket requires a stateful investigation workflow involving:

- investigation planning
- conditional routing
- specialist agent execution
- evidence aggregation
- evidence sufficiency checks
- PM synthesis
- critic review
- bounded revision
- workflow termination

The workflow therefore needs explicit state transitions and conditional control rather than a collection of independent LLM calls.

## Decision

Use **LangGraph** as the orchestration layer.

LangGraph will manage:

- workflow state
- node execution
- routing
- parallel specialist execution
- conditional branches
- revision loops
- termination conditions

LangGraph is not responsible for defining product logic. Product and agent requirements remain defined in the project specifications.

## Alternatives Considered

### Plain Python control flow

Could orchestrate the workflow directly.

**Rejected because:** state transitions and agent workflow logic would become increasingly difficult to inspect and maintain as the system grows.

### CrewAI

Provides multi-agent abstractions.

**Rejected for MVP because:** the workflow is fundamentally a controlled state graph rather than an open-ended autonomous team conversation.

### n8n

Familiar for workflow orchestration.

**Rejected for this project because:** the objective is to demonstrate a code-first AI product architecture and make the agent workflow version-controlled and testable within the application codebase.

## Consequences

### Positive

- explicit workflow graph
- typed state can be maintained
- conditional routing is straightforward
- bounded revision loops are easy to represent
- workflow execution is inspectable
- suitable for evaluation and experimentation

### Negative

- introduces an orchestration dependency
- requires developers to understand graph/state concepts
- adds some abstraction compared with a simple sequential script

---

# ADR-002 — Mock Zendesk Instead of Using a Live Zendesk Account

**Status:** Accepted

**Date:** 2026-09-14

## Context

The Research Agent requires a customer-support data source with realistic API interaction.

A live Zendesk environment would introduce:

- account/setup requirements
- external service dependency
- trial limitations
- less control over the fictional dataset
- reproducibility challenges

The project does not require an actual Zendesk organisation.

## Decision

Use a **local HTTP mock implementing the subset of the Zendesk API required by the product**.

The mock will expose API-compatible operations for:

- ticket search
- ticket retrieval
- ticket comments
- ticket creation for seeding

The agent will communicate with the mock through the same application tool boundary it would use for an external service.

## Alternatives Considered

### Live Zendesk account

**Rejected because:** unnecessary dependency and operational friction.

### Static JSON files

**Rejected because:** agents would not interact with a realistic API boundary.

### Direct database access

**Rejected because:** it couples the agent layer to storage implementation and bypasses the external-system boundary we want to simulate.

## Consequences

### Positive

- deterministic
- reproducible
- controllable
- inexpensive
- API-oriented
- easier to test failure scenarios

### Negative

- the mock will not reproduce the full Zendesk platform
- API compatibility must be maintained deliberately
- some real-world Zendesk behaviour will be simplified

## Boundary

The mock is explicitly a **Zendesk-compatible subset**, not a complete Zendesk implementation.

---

# ADR-003 — Mock Jira Instead of Using a Live Jira Cloud Instance

**Status:** Accepted

**Date:** 2026-09-14

## Context

The Engineering Agent requires engineering issues, comments and issue relationships.

A live Jira environment would create unnecessary account and environment dependencies similar to Zendesk.

## Decision

Use a **local HTTP mock implementing the subset of Jira REST API v3 required by the product**.

The mock will support:

- JQL-based issue search
- issue retrieval
- issue comments
- issue relationships
- seeding operations

## Alternatives Considered

### Live Jira Cloud

**Rejected because:** unnecessary external dependency for the MVP.

### Small Jira-specific open-source mock

**Rejected as the architectural foundation because:** relying on an obscure third-party implementation provides less control over the required behaviour than owning the small API surface ourselves.

### Generic database access

**Rejected because:** it breaks the API boundary we want to simulate.

## Consequences

### Positive

- reproducible
- controllable
- easier scenario injection
- easier failure testing
- no external Jira account required

### Negative

- not a complete Jira implementation
- we must maintain the supported subset ourselves

---

# ADR-004 — Use Real PostHog for Product Analytics

**Status:** Accepted

**Date:** 2026-09-14

## Context

The Analytics Agent needs to investigate actual product analytics through an external service.

Unlike customer-support and engineering systems, the analytics integration is important to demonstrate a genuine product-analytics workflow.

PostHog provides:

- event ingestion
- product analytics
- funnel analysis
- breakdowns and segmentation
- query capabilities

## Decision

Use a **real PostHog project** containing fictional Pocket data.

The seed process will send synthetic events into the PostHog project.

The Analytics Agent will query the same project through an application-level analytics tool.

## Alternatives Considered

### Build a custom analytics database

**Rejected because:** significant engineering effort would be spent recreating product analytics infrastructure rather than demonstrating the AI product.

### Mock PostHog

**Rejected because:** using a real analytics service creates a more credible external integration and allows us to demonstrate querying actual analytics infrastructure.

## Consequences

### Positive

- realistic external integration
- genuine analytics querying
- useful demonstration of API/tool integration
- avoids building unnecessary analytics infrastructure

### Negative

- requires a PostHog account/project
- requires credential management
- introduces an external service dependency
- query behaviour may need adjustment as PostHog APIs evolve

## Boundary

PostHog is used as an external analytics service, not as the system of record for the fictional company's entire application.

---

# ADR-005 — Do Not Use RAG in MVP

**Status:** Accepted

**Date:** 2026-09-14

## Context

The project could be implemented using a vector database and retrieval pipeline.

However, the core information sources are structured product systems:

- Zendesk
- PostHog
- Jira

The product requirement is primarily to investigate structured operational evidence, not to search a large document corpus.

## Decision

Do not introduce RAG or a vector database in the MVP.

Agents will query structured systems through tools.

## Alternatives Considered

### Pinecone / Qdrant / Weaviate

**Rejected because:** this introduces infrastructure to solve a problem that the product does not currently have.

### RAG over exported tickets/issues

**Rejected because:** exporting API data into another retrieval system creates an additional source of truth and reduces the realism of directly integrating with product systems.

## Consequences

### Positive

- simpler architecture
- fewer infrastructure components
- clearer data lineage
- more realistic product-system integration
- easier evaluation

### Negative

- no generic semantic retrieval layer
- large-scale unstructured knowledge use cases are not covered

## Revisit Condition

Introduce retrieval infrastructure only if the product later needs substantial unstructured sources such as:

- product documentation
- customer research transcripts
- Slack discussions
- strategy documents
- long-form incident reports

---

# ADR-006 — Constrain Each Specialist Agent to Its Own Data Source

**Status:** Accepted

**Date:** 2026-09-14

## Context

A general-purpose agent could be given every available tool.

However, this creates:

- larger tool selection space
- weaker responsibility boundaries
- more difficult evaluation
- potential source misuse
- less predictable behaviour

## Decision

Use least-privilege data access.

```text
Research → Zendesk
Analytics → PostHog
Engineering → Jira
PM → no external data tools
Critic → no external data tools in MVP
```

The application will enforce these permissions.

## Alternatives Considered

### One agent with all tools

**Rejected as the primary architecture because:** it weakens specialization and makes tool-use behaviour harder to evaluate.

It remains **Baseline A** for architecture comparison.

### All agents receive read-only access to all sources

**Rejected because:** read-only access does not solve the responsibility-boundary problem.

## Consequences

### Positive

- clearer agent roles
- easier testing
- smaller tool spaces
- better failure attribution
- easier security reasoning

### Negative

- cross-source investigations require orchestration
- additional handoffs exist
- multiple agents may increase latency and cost

---

# ADR-007 — PM Agent Does Not Directly Query External Systems in MVP

**Status:** Accepted

**Date:** 2026-09-14

## Context

The PM Agent could have access to Zendesk, PostHog and Jira and independently perform additional research.

However, this would blur the boundary between:

> evidence collection

and:

> evidence synthesis.

It would also make it harder to determine whether the PM selectively queried sources to support an emerging conclusion.

## Decision

The PM Agent receives structured specialist findings and does not directly query external systems in MVP.

The orchestrator may trigger additional targeted research through the appropriate specialist when an evidence gap is identified.

## Alternatives Considered

### PM has all tools

**Rejected because:** weaker separation of responsibilities and harder evaluation.

### PM can request arbitrary additional searches

**Rejected for MVP because:** increases complexity and potentially creates uncontrolled investigation behaviour.

## Consequences

### Positive

- clearer role separation
- smaller context
- easier evaluation
- greater auditability

### Negative

- additional orchestration is required for missing evidence
- PM cannot independently verify every claim

## Revisit Condition

Allow controlled PM verification tools later if evaluation demonstrates that the restriction materially harms decision quality.

---

# ADR-008 — Use a Dedicated Critic + Bounded Revision Loop

**Status:** Accepted

**Date:** 2026-09-14

## Context

LLMs can produce plausible recommendations that overstate evidence, ignore contradictions or make unsupported causal claims.

A dedicated critical-review stage can identify these weaknesses before a recommendation reaches the user.

However, an unrestricted critic loop could create:

- infinite cycles
- high latency
- excessive cost
- repeated stylistic criticism

## Decision

Use a dedicated Critic Agent with:

```text
PASS
REVISE
```

as its top-level decision.

Revision is bounded to a maximum of **2 cycles**.

The Critic focuses on material issues including:

- unsupported claims
- causal overreach
- contradiction handling
- evidence gaps
- segmentation gaps
- magnitude errors
- confidence mismatch

## Alternatives Considered

### No critic

**Rejected as the candidate architecture**, but retained as part of Baseline B.

### Unbounded self-reflection

**Rejected because:** unpredictable cost and termination behaviour.

### Deterministic rules only

**Rejected because:** some reasoning errors cannot be identified reliably through simple rules.

## Consequences

### Positive

- explicit quality-control step
- measurable critic effectiveness
- supports adversarial evaluation
- bounded cost

### Negative

- extra model call(s)
- additional latency
- possibility of false-positive criticism

---

# ADR-009 — Use Structured Agent Inputs and Outputs

**Status:** Accepted

**Date:** 2026-09-14

## Context

Unstructured agent-to-agent prose makes validation, evaluation and debugging difficult.

## Decision

Agent interfaces will use typed schemas for:

- inputs
- outputs
- evidence
- recommendations
- critic reviews
- failures

The implementation should use a schema system such as Pydantic or an equivalent validated approach.

## Alternatives Considered

### Free-form text between agents

**Rejected because:** difficult to validate and evaluate reliably.

### JSON without schema validation

**Rejected because:** syntactically valid JSON can still violate the expected contract.

## Consequences

### Positive

- predictable interfaces
- easier testing
- improved observability
- easier evaluation
- explicit contracts

### Negative

- schemas require maintenance
- model outputs may require repair/retry when validation fails

---

# ADR-010 — Separate Runtime Data from Evaluation Ground Truth

**Status:** Accepted

**Date:** 2026-09-14

## Context

The system needs ground truth to evaluate whether it correctly discovers the underlying product problems.

If the ground truth is stored with runtime data, the agents could inadvertently receive the answers.

## Decision

Maintain two separate domains:

```text
Runtime
Pocket data

Evaluation
Ground truth + expected evidence + known traps
```

Agents receive only runtime data.

The evaluation runner has access to ground truth.

## Alternatives Considered

### Store scenario truth inside records

**Rejected because:** creates a data-leakage risk.

### Hide ground truth through prompt instructions

**Rejected because:** architectural isolation is stronger than relying on prompt discipline.

## Consequences

### Positive

- cleaner evaluations
- reduced leakage risk
- more realistic discovery

### Negative

- two datasets must be kept logically consistent

---

# ADR-011 — Build a Scenario-Driven Seed System Rather Than Independent Random Data

**Status:** Accepted

**Date:** 2026-09-14

## Context

Independent random generation would create large volumes of superficially realistic but logically unrelated records.

The objective is to create realistic investigative evidence.

## Decision

Seed data will be generated from scenario definitions.

The generation pipeline is:

```text
Scenario definitions
        ↓
Base entities
        ↓
Scenario evidence
        ↓
Noise / contradictions
        ↓
System-specific records
```

## Alternatives Considered

### Pure random generation

**Rejected because:** it does not reliably create the required cross-system relationships.

### Manually authored records

**Rejected because:** difficult to scale, reproduce and modify.

### Large LLM-generated dataset without scenario controls

**Rejected because:** volume does not guarantee coherent relationships.

## Consequences

### Positive

- reproducible
- controllable
- easier evaluation
- scenario integrity
- deliberate ambiguity

### Negative

- requires upfront scenario design

---

# ADR-012 — Keep Agents Read-Only in MVP

**Status:** Accepted

**Date:** 2026-09-14

## Context

Autonomous write actions could make the system more agentic, but they also introduce significant risk and are unnecessary to demonstrate the core product value.

## Decision

MVP agents receive read-only investigation capabilities.

Seed/setup operations remain separate from agent tools.

## Alternatives Considered

### Allow Jira ticket creation

**Rejected for MVP.**

### Allow product-system changes

**Rejected for MVP.**

### Allow automated prioritisation updates

**Rejected for MVP.**

## Consequences

### Positive

- lower operational risk
- simpler permission model
- easier testing
- clear human oversight

### Future Extension

An approved recommendation may later generate a **draft** Jira ticket or experiment plan for human approval.

---

# ADR-013 — Support Single-Agent and Multi-Agent Execution Modes

**Status:** Accepted

**Date:** 2026-09-14

## Context

The project proposes a multi-agent architecture.

However, simply having multiple agents does not establish that the architecture is better.

## Decision

The core tool and data layers must be reusable across at least three evaluation modes:

```text
A. Single Agent

B. Specialist Agents + PM

C. Specialist Agents + PM + Critic
```

These architectures will use the same underlying evidence environment.

## Alternatives Considered

### Build only the final multi-agent architecture

**Rejected because:** there would be no credible evidence that the complexity is justified.

## Consequences

### Positive

- measurable architecture comparison
- stronger product decision-making
- supports portfolio discussion

### Negative

- requires additional orchestration flexibility
- increases evaluation effort

---

# ADR-014 — Evaluation Is a First-Class Product Capability

**Status:** Accepted

**Date:** 2026-09-14

## Context

AI systems can fail in ways that are not obvious from manual demonstrations.

The project therefore needs systematic evaluation during development.

## Decision

Evaluation infrastructure will be treated as a first-class component of the system.

The project will maintain:

- versioned scenarios
- ground truth
- deterministic validators
- semantic evaluation
- human calibration examples
- failure taxonomy
- benchmark reports

## Alternatives Considered

### Manual testing only

**Rejected because:** cannot reliably detect regressions or compare architectures.

### Generic LLM-as-judge only

**Rejected because:** semantic judges can themselves be wrong and should be supplemented with deterministic checks and human calibration.

## Consequences

### Positive

- measurable progress
- regression protection
- architecture comparison
- defensible project results

### Negative

- additional implementation work
- evaluation criteria require maintenance

---

# ADR-015 — Use Domain Tools Rather Than Exposing Raw HTTP to Agents

**Status:** Accepted

**Date:** 2026-09-14

## Context

Agents need access to external APIs, but exposing raw HTTP requests would create excessive flexibility and security risk.

## Decision

Agents interact with application-level domain tools.

Examples:

```text
search_tickets()
get_ticket()

query_analytics()

search_issues()
get_issue()
```

The tools use API adapters internally.

## Alternatives Considered

### Agent-generated HTTP requests

**Rejected because:** excessive control, difficult validation and larger failure surface.

### Direct vendor SDK access from agents

**Rejected because:** couples agent behaviour to vendor-specific implementation.

## Consequences

### Positive

- stable agent contracts
- easier validation
- easier vendor replacement
- better security boundary
- better observability

### Negative

- additional abstraction layer

---

# ADR-016 — Use Workflow State Instead of Long-Term Agent Memory

**Status:** Accepted

**Date:** 2026-09-14

## Context

An investigation requires state to pass findings between workflow stages.

It does not require agents to remember users or previous conversations across unrelated sessions.

## Decision

Use explicit investigation state managed by the orchestration layer.

Do not implement long-term agent memory in MVP.

## Alternatives Considered

### Vector memory

**Rejected because:** does not solve the current product requirement.

### Persistent conversational memory

**Rejected because:** investigations should be independent and reproducible.

## Consequences

### Positive

- clearer execution model
- reduced context contamination
- easier testing
- easier reproducibility

### Negative

- repeated investigations do not automatically inherit context

---

# ADR-017 — Do Not Build a Full Microservice Architecture

**Status:** Accepted

**Date:** 2026-09-14

## Context

The product contains several conceptual components, which could tempt the implementation toward separate deployable services.

However, the MVP does not require independent scaling or organisational ownership of each component.

## Decision

Implement the application as a modular application with clear internal boundaries.

The mock Zendesk and Mock Jira services remain separate HTTP processes because they intentionally simulate external systems.

## Alternatives Considered

### Full microservices

**Rejected because:** operational complexity exceeds MVP needs.

### Single monolithic module

**Rejected because:** would blur boundaries between agents, tools, integrations and orchestration.

## Consequences

### Positive

- simpler development
- lower operational overhead
- clear code boundaries
- easier local development

### Negative

- internal components are not independently deployable

## Revisit Condition

Consider service decomposition only if real scaling or deployment requirements emerge.

---

# ADR-018 — Optimise Architecture Against Quality, Cost and Latency

**Status:** Accepted

**Date:** 2026-09-14

## Context

More agents and stronger models can potentially improve output quality but increase:

- cost
- latency
- operational complexity

## Decision

Architecture decisions will use a quality/cost/latency framework.

The most complex architecture will **not** automatically be selected.

## Alternatives Considered

### Maximum quality regardless of cost

**Rejected because:** not suitable for a product intended for real operational use.

### Minimum cost regardless of quality

**Rejected because:** poor recommendations undermine the product's purpose.

## Consequences

The final architecture will be selected from measured results rather than assumption.

---

# ADR Governance

## When an ADR is required

An ADR should be created or updated when a change materially affects:

- system architecture
- agent topology
- data boundaries
- external integrations
- security model
- evaluation methodology
- persistence strategy
- major dependencies

## When an ADR is not required

Routine implementation decisions do not require an ADR when they:

- do not alter architecture
- do not affect product behaviour
- are reversible
- remain within existing specifications

## ADR lifecycle

```text
Proposed
   ↓
Accepted
   ↓
Implemented
   ↓
Superseded (if replaced)
```

Existing ADRs should not be deleted when superseded.

The replacement decision should reference the earlier ADR.

---

# ADR Principle

The purpose of these ADRs is to preserve the reasoning behind the architecture.

A future contributor should be able to answer:

> "Why is the system built this way?"

without reconstructing the decision from old code or conversations.