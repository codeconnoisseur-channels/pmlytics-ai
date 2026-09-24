# Pocket AI Product Discovery Team
## System Architecture

**Version:** 1.0  
**Status:** Draft  
**Related documents:**  
- Pocket AI Product Discovery Team — PRD v1.0
- Pocket AI Product Discovery Team — Product Specification v1.0

---

# 1. Architecture Purpose

This document defines the technical architecture for Pocket AI Product Discovery Team.

It translates the product requirements into an implementable system design covering:

- application components
- agent topology
- orchestration
- state management
- tool architecture
- external integrations
- data flow
- failure handling
- observability
- evaluation boundaries
- security boundaries
- deployment considerations

This document defines **how the system works**.

It does not define detailed agent prompts, exact seed records, or individual implementation tasks. Those belong in the Agent Specification, Data & API Specification, and Implementation Plan.

---

# 2. Architecture Principles

The system should follow the following principles.

## 2.1 Product-first architecture

Technical complexity must exist to satisfy a product requirement.

A component should not be added simply because it is popular in agentic AI development.

---

## 2.2 Explicit responsibility boundaries

Each specialist agent has a narrow domain and only the tools required for that domain.

The system should avoid giving every agent access to every data source.

---

## 2.3 Structured communication

Agents should exchange structured objects rather than unconstrained prose wherever practical.

This makes the system:

- easier to validate
- easier to evaluate
- easier to debug
- less vulnerable to prompt drift
- easier to modify

---

## 2.4 Evidence traceability

Every meaningful conclusion should retain a path back to source evidence.

The system must preserve enough metadata to determine:

> Where did this claim come from?

---

## 2.5 Bounded autonomy

The system may make decisions about investigation sequencing, but agent loops must be bounded.

There must be explicit termination conditions.

---

## 2.6 Read-oriented MVP

The MVP is primarily a read-and-analyse system.

External systems should not receive consequential write actions from agents.

---

## 2.7 Simple where possible

We should not introduce:

- RAG
- long-term memory
- MCP
- distributed task queues
- microservices
- Kubernetes
- autonomous planning frameworks

unless a demonstrated product or technical requirement justifies them.

---

## 2.8 Evaluation-driven architecture

The architecture must make it possible to compare:

- single-agent
- multi-agent
- multi-agent + critic

without rebuilding the entire application.

---

# 3. High-Level Architecture

```text id="v6p4wr"
                         ┌─────────────────────┐
                         │        User         │
                         │       (PM)          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Application UI   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Investigation API   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ LangGraph Runtime   │
                         │                     │
                         │   Orchestrator      │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
        │   Research   │   │  Analytics   │   │ Engineering  │
        │    Agent     │   │    Agent     │   │    Agent     │
        └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
               │                  │                   │
               ▼                  ▼                   ▼
        ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
        │ Mock Zendesk │   │   PostHog    │   │   Mock Jira  │
        └──────────────┘   └──────────────┘   └──────────────┘
               │                  │                   │
               └──────────────────┼───────────────────┘
                                  ▼
                         ┌─────────────────────┐
                         │    Evidence State   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      PM Agent       │
                         │ Synthesis/Decision  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Critic Agent     │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┴────────────┐
                       │                         │
                    PASS                       REVISE
                       │                         │
                       ▼                         ▼
                   Complete                 PM revision
                                                 │
                                                 └──────► Critic
```

---

# 4. Architectural Components

The system consists of the following logical components:

1. Presentation layer
2. Investigation API
3. Orchestration layer
4. Specialist agents
5. Tool layer
6. Data-source adapters
7. State store
8. Evaluation layer
9. Observability layer
10. Configuration and secrets management

---

# 5. Presentation Layer

The presentation layer provides the PM-facing experience.

For MVP it requires:

- investigation submission
- investigation progress
- completed investigation
- investigation history
- source/evidence inspection

The UI should communicate application state received from the backend.

It should not contain agent orchestration logic.

---

# 6. Investigation API

The backend exposes an application-level API between the UI and the agent runtime.

Conceptually:

```text id="v4xqk8"
POST /investigations
GET  /investigations/{id}
GET  /investigations
```

### POST /investigations

Creates a new investigation.

Input:

```json
{
  "question": "Why are users abandoning transfers?"
}
```

Output:

```json
{
  "investigation_id": "inv_001",
  "status": "submitted"
}
```

---

## GET /investigations/{id}

Returns investigation state and, when complete, the final result.

The exact response schema belongs in the application API contract.

---

# 7. Orchestration Layer

LangGraph is the workflow orchestration layer.

The graph is responsible for:

- routing
- state transitions
- parallel specialist execution
- aggregation
- synthesis
- critic evaluation
- bounded revision
- termination
- error routing

LangGraph is used as a **workflow/state orchestration mechanism**, not as a substitute for product design.

---

# 8. Core Graph

The initial graph should follow this topology:

```text id="g4j6qs"
START
  │
  ▼
planner
  │
  ▼
route_investigation
  │
  ├─────────────┐
  │             │
  ▼             ▼
research     analytics
  │             │
  └──────┬──────┘
         │
         ▼
   engineering
         │
         ▼
   evidence_check
         │
         ├───────────────┐
         │               │
      sufficient       insufficient
         │               │
         ▼               ▼
      synthesis       targeted_research
         │               │
         │               └──────► evidence_check
         ▼
      pm_review
         │
         ▼
       critic
         │
     ┌───┴────┐
     ▼        ▼
   PASS     REVISE
     │        │
     ▼        ▼
 COMPLETE    PM_REVISION
                │
                └──────► critic
```

A more precise implementation may execute the specialist investigations in parallel rather than sequentially.

---

# 9. Planning Node

The planner receives the user's question and creates an investigation plan.

Inputs:

```text id="0kof8w"
user_question
```

Potential output:

```json
{
  "question_type": "diagnostic",
  "required_sources": [
    "customer",
    "analytics",
    "engineering"
  ],
  "investigation_tasks": [
    "identify transfer complaints",
    "measure transfer funnel drop-off",
    "find relevant transfer issues"
  ]
}
```

The planner should not produce a product recommendation.

Its responsibility is determining the investigative work required.

---

# 10. Routing

Routing determines which specialist tasks should execute.

Possible routes:

```text id="1x4dl1"
customer
analytics
engineering
```

The routing layer may execute multiple tasks concurrently.

For example:

> "Why are users abandoning transfers?"

would likely route to all three specialists.

A question such as:

> "What are customers complaining about regarding transfers?"

may only require customer-support evidence.

The system should therefore support conditional investigation.

---

# 11. Specialist Agent Architecture

The three specialists are isolated by domain.

```text id="u1d44o"
Research Agent
    │
    └── Customer tools only

Analytics Agent
    │
    └── PostHog tools only

Engineering Agent
    │
    └── Jira tools only
```

This provides:

- constrained tool selection
- lower tool confusion
- clear ownership
- easier testing
- clearer failure attribution

---

# 12. Research Agent

## Responsibilities

- search customer-support records
- identify recurring themes
- inspect relevant conversations
- identify representative evidence
- identify affected user descriptions
- communicate evidence limitations

## Permitted data source

Mock Zendesk.

## Permitted operations

```text id="m6jz9t"
search_tickets
get_ticket
get_ticket_comments
```

## Prohibited behaviour

The Research Agent must not:

- query PostHog
- query Jira
- invent ticket information
- infer causality from support volume alone
- claim all customers experience a problem based on a small sample

---

# 13. Analytics Agent

## Responsibilities

- query product analytics
- inspect funnels and behaviour
- identify meaningful drop-offs
- compare segments
- inspect changes across time
- validate or challenge customer claims

## Permitted data source

PostHog.

## Primary operation

```text id="8d3yga"
query_analytics
```

## Prohibited behaviour

The Analytics Agent must not:

- infer customer sentiment from behavioural data
- claim causal relationships without supporting evidence
- fabricate metrics
- query Zendesk or Jira

---

# 14. Engineering Agent

## Responsibilities

- identify relevant engineering issues
- inspect issue status
- inspect comments
- identify related issues
- identify technical context relevant to the product problem

## Permitted data source

Mock Jira.

## Operations

```text id="lu1m5v"
search_issues
get_issue
get_issue_comments
get_linked_issues
```

## Prohibited behaviour

The Engineering Agent must not:

- infer user impact from Jira alone
- query Zendesk or PostHog
- claim an issue is the root cause without evidence
- present an old or resolved issue as a current incident without qualification

---

# 15. Tool Architecture

Agents should interact with stable application-level tools.

The architecture should separate:

```text id="ec6qhd"
Agent
  ↓
Domain Tool
  ↓
API Adapter
  ↓
External/Mock Service
```

Example:

```text id="xg8hfq"
Research Agent
      ↓
search_tickets()
      ↓
Zendesk Adapter
      ↓
Mock Zendesk API
```

This prevents the agent from becoming tightly coupled to the underlying API implementation.

---

# 16. Tool Contracts

Tools should have:

- explicit input schemas
- explicit output schemas
- validation
- bounded parameters
- timeout behaviour
- structured errors

Example concept:

```python
search_tickets(
    query: str,
    page: int = 1,
    limit: int = 20
) -> TicketSearchResult
```

The model should never construct arbitrary raw HTTP requests.

The application controls available operations.

---

# 17. Data-Source Adapters

Each source gets an adapter layer.

```text id="rmsqpx"
ZendeskClient
JiraClient
PostHogClient
```

The agents and tools should not know:

- storage implementation
- database implementation
- mock internals
- authentication implementation details

They should interact with a stable domain interface.

---

# 18. Mock Zendesk Architecture

The mock Zendesk system should behave as an API service rather than as a local JSON file directly queried by agents.

Conceptually:

```text id="c72m8u"
Zendesk Tool
     ↓
HTTP Client
     ↓
Mock Zendesk API
     ↓
Mock Data Store
```

This preserves the system boundary found in a real enterprise integration.

The mock should implement only the API surface needed by the product.

---

# 19. Mock Jira Architecture

The same architectural pattern applies.

```text id="z0xlqv"
Engineering Tool
      ↓
HTTP Client
      ↓
Mock Jira API
      ↓
Mock Data Store
```

The mock should support the subset of Jira behaviour required by the Engineering Agent.

---

# 20. PostHog Architecture

PostHog remains an external service.

```text id="5kgj0l"
Analytics Tool
      ↓
PostHog Client
      ↓
PostHog API
      ↓
Pocket Project
```

The project should use PostHog for the behavioural analytics source rather than creating a custom analytics service.

---

# 21. State Architecture

The LangGraph state is the shared execution state for an investigation.

Conceptually:

```python
InvestigationState = {
    "investigation_id": str,
    "user_question": str,

    "plan": InvestigationPlan | None,

    "customer_findings": list[CustomerFinding],
    "analytics_findings": list[AnalyticsFinding],
    "engineering_findings": list[EngineeringFinding],

    "evidence_assessment": EvidenceAssessment | None,

    "pm_recommendation": ProductRecommendation | None,

    "critic_review": CriticReview | None,

    "revision_count": int,

    "status": InvestigationStatus,

    "errors": list[InvestigationError]
}
```

The actual implementation should use typed schemas rather than an unvalidated dictionary.

---

# 22. State Ownership

Different nodes should own different state fields.

### Planner

Writes:

```text id="pgz3v4"
plan
```

### Research

Writes:

```text id="hws4md"
customer_findings
```

### Analytics

Writes:

```text id="ssve87"
analytics_findings
```

### Engineering

Writes:

```text id="c5sc9j"
engineering_findings
```

### Evidence assessment

Writes:

```text id="94a2v7"
evidence_assessment
```

### PM

Writes:

```text id="2v1n4i"
pm_recommendation
```

### Critic

Writes:

```text id="qrxp1s"
critic_review
```

This explicit ownership reduces accidental state mutation.

---

# 23. Evidence Object Model

Evidence is a first-class object.

Conceptually:

```python
Evidence = {
    "source_type": "zendesk",
    "source_reference": "1047",
    "finding": "...",
    "support": "...",
    "interpretation": "...",
    "confidence": "high",
    "limitations": []
}
```

Evidence must preserve its source identity throughout the workflow.

The system should not convert evidence into anonymous prose and lose its provenance.

---

# 24. Evidence Assessment Node

The evidence assessment node determines whether the information gathered so far is sufficient for synthesis.

It should consider:

- source coverage
- evidence relevance
- evidence quality
- contradictions
- missing information
- question requirements

Possible outputs:

```text id="n3kj82"
SUFFICIENT
INSUFFICIENT
```

If insufficient, the system may initiate targeted additional research.

---

# 25. Targeted Research

The system should not automatically restart the entire investigation when a gap is found.

Example:

The Analytics Agent says:

> Transfer abandonment is concentrated in a specific transaction segment, but we do not know whether customers in that segment are reporting the same problem.

The orchestrator can request:

> Research Agent: investigate support tickets for that segment/problem.

This creates adaptive investigation while keeping the workflow bounded.

---

# 26. Synthesis Architecture

The synthesis stage consumes:

```text id="b0jij5"
Customer Findings
Analytics Findings
Engineering Findings
Evidence Assessment
```

and produces a consolidated evidence model.

It should identify:

```text id="kknjrw"
converging_evidence
contradictory_evidence
likely_explanations
affected_users
evidence_gaps
```

This output feeds the PM Agent.

---

# 27. PM Agent Architecture

The PM Agent receives synthesized evidence.

It should not independently query external systems in the MVP.

This is deliberate.

Its responsibility is:

> Turn the available evidence into a product recommendation.

Inputs:

```text id="1lkm46"
user_question
evidence_assessment
customer_findings
analytics_findings
engineering_findings
```

Output:

```text id="m8bq1u"
ProductRecommendation
```

---

# 28. Critic Agent Architecture

The Critic receives:

```text id="lzy7w8"
user_question
evidence
pm_recommendation
```

and produces:

```python
CriticReview = {
    "decision": "PASS | REVISE",
    "issues": [...],
    "missing_evidence": [...],
    "unsupported_claims": [...],
    "alternative_explanations": [...],
    "required_changes": [...]
}
```

The critic is intentionally independent from the PM's generation process.

---

# 29. Revision Loop

The PM/Critic loop is bounded.

```text id="85h8nu"
PM
 ↓
Critic
 ↓
PASS ─────────► Complete

REVISE
 ↓
PM Revision
 ↓
Critic
```

Maximum MVP revisions:

**2**

After the maximum is reached, the system should return the best available recommendation with unresolved issues clearly marked.

It should not loop indefinitely.

---

# 30. Why the PM Does Not Directly Access the APIs

This is an intentional design decision.

The PM Agent receives evidence rather than querying the underlying systems directly.

Benefits:

- clearer separation of discovery and synthesis
- fewer tool calls
- easier evaluation
- smaller PM context
- reduced risk of selectively querying evidence to support its own conclusion
- easier reproducibility

The specialist agents effectively act as evidence collectors.

The PM acts as the decision synthesiser.

---

# 31. Why the Critic Does Not Browse Everything by Default

The initial Critic should primarily challenge the recommendation against the evidence already collected.

This avoids turning every critique into another expensive investigation.

However, the architecture should allow a later version to permit targeted verification when the critic identifies a specific evidence gap.

---

# 32. Agent Communication

Agents should communicate through structured state rather than direct agent-to-agent chat.

Preferred:

```text id="0yp4mu"
Research Agent
      ↓
CustomerFinding[]
      ↓
Shared Investigation State
      ↓
PM Agent
```

Avoid:

```text id="rr15i9"
Agent A → natural-language message → Agent B
```

unless a direct handoff is necessary.

This makes the workflow deterministic and inspectable.

---

# 33. Model Abstraction

The system should not hard-code a single model throughout the architecture.

A model interface/configuration layer should allow:

```text id="4uwh45"
planner_model
research_model
analytics_model
engineering_model
pm_model
critic_model
```

Different agents may initially use the same model.

However, model choice should remain configurable so evaluation can compare models without redesigning the graph.

---

# 34. Model Strategy

The initial implementation should optimise for reliability rather than minimum cost.

A suitable baseline architecture should use one capable tool-calling model for all agents.

Then evaluation can test:

- smaller models for specialist agents
- stronger model for PM/critic
- different providers
- single-model vs mixed-model architectures

Model selection should therefore be an experimental variable rather than a permanent architectural assumption.

---

# 35. No RAG

The system does not require a vector database in MVP.

The primary data sources are structured APIs.

The architecture is:

```text id="08o6vz"
APIs
 ↓
Tools
 ↓
Agents
```

rather than:

```text id="i71x46"
Documents
 ↓
Embeddings
 ↓
Vector Database
 ↓
Retriever
 ↓
Agent
```

RAG may be introduced later if the product gains an unstructured knowledge requirement.

---

# 36. No Long-Term Memory

The system requires investigation state, not conversational memory.

Each investigation is a self-contained unit.

Historical investigations may be persisted as application records but should not automatically become model context for future investigations.

This prevents accidental contamination between independent investigations.

---

# 37. Persistence

The MVP should persist completed investigations and relevant metadata.

At minimum:

```text id="yb6v0f"
investigation_id
question
status
timestamps
final recommendation
confidence
source findings
critic outcome
```

The exact database choice is a technical implementation decision.

The application should not depend on agent state existing indefinitely in process memory.

---

# 38. Caching

Caching may be used for deterministic external requests where appropriate.

However:

- analytics results may become stale
- support/engineering data may change
- investigation reproducibility requires recording what was actually retrieved

Therefore cached responses should not overwrite the original evidence record.

The system should preserve investigation-time evidence.

---

# 39. Failure Handling

Failures must be treated as first-class workflow outcomes.

## Tool failure

Example:

> Zendesk API unavailable.

The specialist should return a structured error.

The orchestrator determines whether the investigation can continue.

---

## Partial failure

Example:

```text id="m7n7wo"
Customer evidence ✓
Analytics ✓
Engineering ✗
```

The system may continue if the remaining evidence is sufficient, but the final result must identify the missing source.

---

## Complete failure

If the system cannot produce a minimally valid investigation, it should return a clear failure state rather than a fabricated result.

---

# 40. Timeouts and Retries

External tool calls should have bounded timeouts.

Retries should be limited and should distinguish between:

- transient errors
- invalid requests
- authentication errors
- unavailable services

The system should not retry indefinitely.

---

# 41. Invalid Tool Arguments

Tools should validate arguments before making requests.

Examples:

- invalid ticket ID
- invalid Jira issue key
- malformed analytics query
- unsupported query parameter

The agent should receive a structured tool error that it can use to correct the request when appropriate.

---

# 42. Hallucination Controls

The architecture should reduce hallucination risk through:

### Constrained tools

Agents can only access relevant sources.

### Structured outputs

Agents must return typed objects.

### Source identifiers

Claims must retain source references.

### Evidence-first synthesis

The PM receives evidence rather than a blank context.

### Critic review

Recommendations are explicitly challenged.

### No-evidence behaviour

Missing evidence cannot silently become fabricated information.

---

# 43. Security Architecture

Secrets must remain outside source code.

Credentials should be injected through environment configuration or the chosen secrets-management mechanism.

The model should never receive:

- API keys
- service credentials
- secret configuration values

Tools operate with application-managed credentials.

---

# 44. External Write Boundary

MVP agents should not have production write capabilities.

The mock environments may support seeding endpoints for development, but those endpoints are not agent tools.

This distinction is important:

```text id="fk1w9p"
Seed script
   ↓
Write APIs
   ↓
Mock systems
```

versus:

```text id="u1z1u3"
Agent
   ↓
Read tools
   ↓
Systems
```

Agents remain read-oriented.

---

# 45. Observability Architecture

Every investigation should produce an observable execution trace.

At minimum, record:

```text id="6t7s3c"
investigation_id
agent
model
node
tool
tool input metadata
tool duration
tool result status
tokens
latency
errors
revision count
final status
```

Sensitive data should not be unnecessarily copied into telemetry.

---

# 46. Evaluation Architecture

Evaluation should operate independently of the production UI.

Conceptually:

```text id="bxcs3x"
Evaluation Dataset
       ↓
Investigation Runner
       ↓
Architecture Under Test
       ↓
Structured Output
       ↓
Evaluation Engine
       ↓
Metrics
```

This allows the same test scenarios to evaluate multiple architecture variants.

---

# 47. Baseline Architecture Support

The application should make it possible to implement alternative execution modes.

### Baseline A

```text
Question
 ↓
Single Agent
 ↓
All tools
 ↓
Recommendation
```

### Baseline B

```text
Question
 ↓
Specialist Agents
 ↓
Synthesis
 ↓
Recommendation
```

### Baseline C

```text
Question
 ↓
Specialist Agents
 ↓
Synthesis
 ↓
Critic
 ↓
Revision
 ↓
Recommendation
```

The core tool and data layers should be reusable across all three.

---

# 48. Testability

Each major layer should be testable independently.

### Unit tests

Test:

- tool validation
- parsers
- schemas
- routing logic
- state transitions

### Integration tests

Test:

- tool → mock API
- tool → PostHog
- complete specialist investigations

### Workflow tests

Test:

- successful investigation
- partial source failure
- insufficient evidence
- critic revision
- revision limit

### Evaluation tests

Test:

- end-to-end product questions
- answer quality
- evidence grounding
- contradiction handling

---

# 49. Determinism and Reproducibility

The system must retain sufficient metadata to understand how an investigation was produced.

Store:

- model name/version where available
- configuration
- investigation question
- tool requests
- relevant source evidence
- evaluation scenario ID where applicable
- revision count

Exact model determinism cannot always be guaranteed, but the run should remain auditable.

---

# 50. Project Structure

The implementation should maintain clear separation between product logic, agents, integrations and tests.

A recommended conceptual structure:

```text
project/
│
├── app/
│   ├── api/
│   ├── domain/
│   ├── orchestration/
│   ├── agents/
│   ├── tools/
│   ├── integrations/
│   ├── models/
│   ├── storage/
│   └── config/
│
├── mocks/
│   ├── zendesk/
│   └── jira/
│
├── seed/
│   └── ...
│
├── evaluations/
│   ├── scenarios/
│   ├── runners/
│   └── metrics/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── workflow/
│
├── docs/
│   └── ...
│
└── README.md
```

Exact package structure may change during implementation if a documented decision justifies it.

---

# 51. Development Environment

The system should be runnable locally with a documented setup.

A developer should be able to:

1. install dependencies
2. configure environment variables
3. start mock services
4. seed the fictional environment
5. start the application
6. run tests
7. execute an investigation

The environment should not require hidden manual configuration.

---

# 52. Runtime Sequence

A typical investigation should follow:

```text id="qkhd4q"
1. User submits question
2. API creates investigation
3. Orchestrator initialises state
4. Planner creates investigation plan
5. Required specialist nodes execute
6. Tools query their permitted data sources
7. Findings are written to state
8. Evidence sufficiency is assessed
9. Targeted research occurs if necessary
10. PM synthesises recommendation
11. Critic evaluates recommendation
12. PM revises if required
13. Investigation completes
14. Result is persisted
15. UI displays final investigation
```

---

# 53. Architectural Invariants

The following rules should remain true unless explicitly changed through an architecture decision.

### Invariant 1

Specialist agents only access their authorised data sources.

### Invariant 2

The PM Agent does not independently browse all underlying systems in MVP.

### Invariant 3

Important evidence retains source provenance.

### Invariant 4

Critic revision is bounded.

### Invariant 5

Agents cannot perform consequential external writes in MVP.

### Invariant 6

No fabricated evidence may be introduced to fill an information gap.

### Invariant 7

The system must support evaluation against simpler baselines.

### Invariant 8

Product requirements take precedence over framework conventions.

---

# 54. Architectural Decision Candidates

The following decisions must be explicitly documented in ADRs before or during implementation:

1. Why LangGraph is being used for orchestration.
2. Why Zendesk is mocked rather than connected to a live account.
3. Why Jira is mocked rather than connected to a live account.
4. Why PostHog is used as the real analytics service.
5. Why no RAG is used in MVP.
6. Why specialist agents have constrained tool access.
7. Why the PM Agent does not directly query the underlying systems.
8. Why a critic/revision loop exists.
9. Why revision count is bounded.
10. Why the architecture supports single-agent and multi-agent evaluation modes.
11. Final model-selection strategy.
12. Final persistence and deployment strategy.

---

# 55. Expected Non-Functional Characteristics

The MVP should prioritise:

### Reliability

The system should fail clearly rather than fabricate output.

### Observability

Investigations should be inspectable through traces and structured state.

### Maintainability

Domain tools, agents and integrations should remain independently replaceable.

### Testability

Major components should be independently testable.

### Cost awareness

Model and tool usage should be measurable.

### Extensibility

Adding another evidence source should not require redesigning the entire graph.

---

# 56. Extending the Architecture

Future sources could be added using the same pattern:

```text id="5bsvfw"
New Data Source
      ↓
Integration Adapter
      ↓
Domain Tool
      ↓
Specialist Capability
      ↓
Investigation State
```

Potential future sources:

- Slack
- NPS
- survey platforms
- CRM
- feature-flag systems
- additional product analytics

The architecture should therefore make the addition of a new source incremental rather than invasive.

---

# 57. What This Architecture Deliberately Avoids

The initial system does not include:

- vector databases
- generic RAG pipelines
- long-term agent memory
- arbitrary model-generated HTTP requests
- unrestricted agent-to-agent messaging
- autonomous write actions
- microservice decomposition
- distributed queues
- complex event-driven infrastructure
- Kubernetes
- voice/vision components

These can be introduced later only when a demonstrated requirement exists.

---

# 58. Architecture Definition of Done

The architecture is considered implemented when:

1. The application can create and track an investigation.
2. The orchestrator can plan and route investigation work.
3. Specialist agents operate within defined tool boundaries.
4. Tools communicate through stable application interfaces.
5. Mock Zendesk and Mock Jira operate through HTTP APIs.
6. PostHog is accessed through a dedicated integration layer.
7. Findings retain source provenance.
8. Investigation state survives across workflow nodes.
9. Evidence sufficiency can trigger targeted research.
10. PM synthesis produces a structured recommendation.
11. Critic review can trigger bounded revision.
12. Failures are handled explicitly.
13. Investigations are traceable through observability data.
14. The workflow can be evaluated independently of the UI.
15. Alternative single-agent and multi-agent execution modes can reuse the same core integrations.

---

# 59. Architectural Summary

The architecture is intentionally built around a simple idea:

```text
                 PRODUCT QUESTION
                        ↓
                INVESTIGATION PLAN
                        ↓
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
      CUSTOMER       BEHAVIOUR    ENGINEERING
       EVIDENCE       EVIDENCE      EVIDENCE
          └─────────────┼─────────────┘
                        ↓
                 EVIDENCE CHECK
                        ↓
                    PM SYNTHESIS
                        ↓
                     CRITIC
                     ↙   ↘
                 PASS    REVISE
                   │       │
                   │       └──► PM
                   ↓
                FINAL RESULT
```

The architecture deliberately separates:

**data retrieval → evidence interpretation → product judgment → critical review.**

That separation is the core architectural decision behind Pocket AI Product Discovery Team.