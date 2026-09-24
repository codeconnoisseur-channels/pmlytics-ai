# Pocket AI Product Discovery Team
## Implementation Plan

**Version:** 1.0  
**Status:** Draft  
**Related documents:**
- Pocket AI Product Discovery Team — PRD v1.0
- Pocket AI Product Discovery Team — Product Specification v1.0
- Pocket AI Product Discovery Team — System Architecture v1.0
- Pocket AI Product Discovery Team — Agent Specification v1.0
- Pocket AI Product Discovery Team — Data & API Specification v1.0
- Pocket AI Product Discovery Team — Evaluation Strategy v1.0

---

# 1. Purpose

This document defines how Pocket AI Product Discovery Team will be built from an empty repository to a production-grade portfolio implementation.

It establishes:

- implementation order
- phase boundaries
- epics
- engineering tasks
- dependencies
- acceptance criteria
- testing requirements
- quality gates
- architectural constraints
- documentation requirements
- release criteria

The implementation must proceed sequentially.

The existence of later phases must not be treated as permission to prematurely implement them.

---

# 2. Implementation Philosophy

The project will follow a real-world product development flow:

```text
Product definition
      ↓
Technical design
      ↓
Foundation
      ↓
Data/integrations
      ↓
Agent capabilities
      ↓
Orchestration
      ↓
Evaluation
      ↓
Optimisation
      ↓
Interface
      ↓
Release
```

The project should **not** follow:

```text
Prompt Antigravity
     ↓
Generate lots of code
     ↓
Fix whatever breaks
     ↓
Add more dependencies
     ↓
Patch architecture
```

The second approach is explicitly prohibited.

---

# 3. Source of Truth

The following hierarchy applies:

```text
PRD
  ↓
Product Specification
  ↓
System Architecture
  ↓
Agent Specification
  ↓
Data & API Specification
  ↓
Evaluation Strategy
  ↓
Implementation Plan
```

The implementation plan may explain how to satisfy the earlier documents, but it must not silently redefine product requirements.

If implementation reveals a conflict with a specification:

1. stop the affected work
2. document the conflict
3. create or update an Architecture Decision Record
4. resolve the decision
5. update the affected specification
6. continue implementation

Antigravity must not silently change the product contract.

---

# 4. Development Rules

## Rule 1: One phase at a time

A phase must satisfy its acceptance criteria before the next phase begins.

## Rule 2: Tests are part of implementation

A phase is not complete because code exists.

Code + tests + documentation + acceptance criteria are required.

## Rule 3: No speculative infrastructure

Do not add infrastructure because it "may be useful later."

## Rule 4: No uncontrolled dependencies

Every meaningful dependency must have an identifiable purpose.

## Rule 5: No hidden manual configuration

A clean environment should be able to reproduce the project setup from documented steps.

## Rule 6: No architectural drift

Changes affecting system boundaries, agent responsibilities or external interfaces require documentation.

## Rule 7: No premature UI work

The backend workflow must demonstrate value before substantial interface work begins.

## Rule 8: Evaluation begins early

Evaluation infrastructure must be built before the system becomes too complex to diagnose.

---

# 5. Overall Phase Map

```text
PHASE 0  Project Governance & Repository Foundation
   ↓
PHASE 1  Pocket Data Model & Scenario Design
   ↓
PHASE 2  Mock Zendesk
   ↓
PHASE 3  Mock Jira
   ↓
PHASE 4  PostHog Integration & Analytics Dataset
   ↓
PHASE 5  Domain Tool Layer
   ↓
PHASE 6  Specialist Agents
   ↓
PHASE 7  LangGraph Orchestration
   ↓
PHASE 8  PM + Critic Decision Loop
   ↓
PHASE 9  Evaluation System
   ↓
PHASE 10 Observability & Optimisation
   ↓
PHASE 11 Product Interface
   ↓
PHASE 12 Hardening, Documentation & Release
   ↓
PHASE 12B Authentication, Durable Execution & Recovery Hardening
```

Evaluation capabilities begin earlier than Phase 9, but **formal architecture comparison begins there**.

---

# 6. Phase 0 — Project Governance & Repository Foundation

## Objective

Create a clean, reproducible development foundation before implementing product functionality.

---

## Epic 0.1 — Repository setup

### Tasks

- initialise Git repository
- establish branch strategy
- create project directory structure
- add README
- establish Python project configuration
- establish dependency management
- establish formatting/linting
- establish test framework
- establish environment configuration pattern
- add `.gitignore`
- add environment template

---

## Epic 0.2 — Documentation structure

Create:

```text
docs/
├── product/
├── architecture/
├── agents/
├── api/
├── evaluation/
├── decisions/
└── implementation/
```

Store approved project specifications here.

---

## Epic 0.3 — Development quality controls

Set up:

- linting
- formatting
- type checking
- unit test execution
- basic CI checks where practical

---

## Acceptance Criteria

- clean checkout can install project dependencies
- test runner works
- linting works
- type checking works
- environment variables are documented
- no secrets exist in repository
- documentation directory is structured
- README explains how to start development

---

## Test Gate

A clean environment should successfully run:

```text
install
lint
typecheck
tests
```

with no application functionality required yet.

---

## Definition of Done

Phase 0 is complete when a second developer can clone the repository and understand how to configure and validate the project without undocumented steps.

---

# 7. Phase 1 — Pocket Data Model & Scenario Design

## Objective

Define and validate the fictional company's data world before building the APIs that expose it.

This phase prevents the common failure of generating unrelated synthetic data independently for each system.

---

## Epic 1.1 — Domain models

Define models for:

### Users

```text
user_id
user_type
signup_date
bank
app_version
```

### Transfers

```text
transaction_id
user_id
amount_ngn
bank
timestamp
status
```

### Support tickets

Core Zendesk-compatible fields.

### Engineering issues

Core Jira-compatible fields.

### Analytics events

Core PostHog event fields.

---

## Epic 1.2 — Scenario definitions

Implement machine-readable scenario definitions for:

- transfer status delays
- KYC abandonment
- wallet funding abandonment
- bill-payment failure

Also encode:

- supporting evidence
- contradictory evidence
- misleading signals
- affected segments
- expected interpretations

---

## Epic 1.3 — Seed generator architecture

Define:

```text
base data
+
scenario injections
+
noise injection
```

Do not yet optimise volume.

The priority is **coherence**.

---

## Epic 1.4 — Data validation

Build checks for:

- referential integrity
- valid timestamps
- scenario integrity
- expected relationships
- absence of prohibited real-world PII
- valid enum values

---

## Acceptance Criteria

- every scenario is machine-readable
- scenario ground truth is separate from runtime data
- shared user and transaction entities are consistent
- seeded records can be traced back to scenarios
- validation detects deliberately broken relationships
- no evaluation answers are available to runtime agents

---

## Test Gate

At least one fully generated scenario must pass:

```text
schema validation
referential validation
scenario validation
```

---

## Definition of Done

The fictional environment can be regenerated deterministically without any agent implementation.

---

# 8. Phase 2 — Mock Zendesk

## Objective

Build an API-shaped customer-support service that behaves like the subset of Zendesk required by the Research Agent.

The actual Zendesk API provides ticket retrieval, search and ticket comments; our mock should implement only the relevant subset. 

---

## Epic 2.1 — Mock data store

Implement storage for:

- tickets
- comments

The underlying storage implementation should remain replaceable.

---

## Epic 2.2 — API endpoints

Implement:

```text
GET  /api/v2/search
GET  /api/v2/tickets/{ticket_id}
GET  /api/v2/tickets/{ticket_id}/comments
GET  /api/v2/tickets
POST /api/v2/tickets
```

Optionally:

```text
POST /api/v2/tickets/create_many
```

for efficient seeding.

The endpoint surface should be documented as a **Zendesk-compatible subset**, not as a complete Zendesk implementation.

---

## Epic 2.3 — Search behaviour

Support:

- keyword search
- relevant filters needed by the Research Agent
- pagination
- not-found behaviour

---

## Epic 2.4 — Seed integration

Connect the scenario-driven seed generator to the mock service through HTTP.

Do not write directly into mock storage from the seed generator.

---

## Acceptance Criteria

- tickets can be created through HTTP
- tickets can be searched through HTTP
- ticket details can be retrieved
- ticket comments can be retrieved
- pagination works
- invalid IDs produce structured errors
- seed records appear through the same API the agent will use

---

## Test Gate

Contract tests covering:

```text
create
search
retrieve
comments
pagination
not found
invalid request
```

must pass.

---

## Definition of Done

A Research Agent could be written against the API without knowing anything about the underlying mock storage.

---

# 9. Phase 3 — Mock Jira

## Objective

Build the engineering-system equivalent.

Jira Cloud REST v3 supports the current JQL search flow, issue retrieval, comments and issue links. The mock will implement only the required subset. 

---

## Epic 3.1 — Issue data store

Implement:

- issues
- comments
- issue links

---

## Epic 3.2 — Search

Implement:

```text
POST /rest/api/3/search/jql
```

with the subset of JQL functionality required by our scenarios.

Avoid implementing a full Jira query engine.

---

## Epic 3.3 — Issue retrieval

Implement:

```text
GET /rest/api/3/issue/{issueIdOrKey}
GET /rest/api/3/issue/{issueIdOrKey}/comment
```

---

## Epic 3.4 — Linked issues

Support retrieval of issue links.

---

## Epic 3.5 — Seed integration

Seed through HTTP APIs.

---

## Acceptance Criteria

- issues can be created
- issues can be searched
- issue details can be retrieved
- comments can be retrieved
- linked issues can be represented
- invalid requests are handled
- API responses are structured
- seed data is discoverable through agent-facing operations

---

## Test Gate

Contract tests cover:

```text
create issue
JQL search
retrieve issue
retrieve comments
retrieve links
not found
invalid search
```

---

## Definition of Done

Engineering tools can treat Mock Jira like an external service boundary.

---

# 10. Phase 4 — PostHog Integration & Analytics Dataset

## Objective

Connect the fictional product to a real PostHog project and create a coherent event environment.

PostHog provides product analytics and query APIs appropriate for the behavioural-analysis use case. 

---

## Epic 4.1 — PostHog project configuration

Configure:

- project credentials
- environment variables
- test project
- data isolation strategy

Credentials must never enter source control.

---

## Epic 4.2 — Event seeding

Implement ingestion for the defined event taxonomy.

Seed:

- account events
- KYC events
- wallet events
- transfer events
- bill-payment events

---

## Epic 4.3 — Analytics query adapter

Create the application-level PostHog client.

The adapter should hide vendor-specific API mechanics from the Analytics Agent.

---

## Epic 4.4 — Query validation

Verify that expected scenarios produce the intended analytical patterns.

For example:

```text
transfer started
→ submitted
→ processing
→ completed
```

should produce meaningful funnel data.

---

## Acceptance Criteria

- PostHog project is configured
- events can be ingested
- event properties are consistent
- scenario patterns exist in analytics
- the analytics adapter returns structured results
- credentials are not exposed to the model

---

## Test Gate

At least one end-to-end analytics query must successfully recover a known seeded pattern.

---

## Definition of Done

PostHog can function as the Analytics Agent's external behavioural evidence source.

---

# 11. Phase 5 — Domain Tool Layer

## Objective

Create stable tools between agents and external systems.

This is a critical abstraction boundary.

---

## Epic 5.1 — Zendesk tools

Implement:

```text
search_tickets
get_ticket
get_ticket_comments
```

---

## Epic 5.2 — Analytics tool

Implement:

```text
query_analytics
```

---

## Epic 5.3 — Jira tools

Implement:

```text
search_issues
get_issue
get_issue_comments
get_linked_issues
```

---

## Epic 5.4 — Tool schemas

Define typed inputs and outputs.

---

## Epic 5.5 — Tool error handling

Normalise:

- timeouts
- authentication failures
- invalid requests
- missing records
- server failures

---

## Epic 5.6 — Tool observability

Record:

- tool name
- execution duration
- success/failure
- relevant non-sensitive metadata

---

## Acceptance Criteria

- agents never make raw HTTP requests
- every tool has a typed input
- every tool has a typed output
- errors are structured
- tool calls are testable independently
- tool implementations can change without changing agent contracts

---

## Test Gate

Unit and integration tests cover every tool.

---

## Definition of Done

The AI layer has clean, stable product-domain tools independent of vendor-specific API details.

---

# 12. Phase 6 — Specialist Agents

## Objective

Build and validate specialist agents independently before introducing multi-agent orchestration.

Agents:

```text
Research
Analytics
Engineering
```

The Planner may be implemented here as a standalone component or in the following orchestration phase, but its schema and behaviour must already be defined.

---

## Epic 6.1 — Research Agent

Implement:

- prompt
- input schema
- output schema
- tool binding
- tool-call limits
- evidence extraction
- failure handling

---

## Epic 6.2 — Analytics Agent

Implement:

- analytical task interpretation
- query tool usage
- metric interpretation
- segmentation
- output validation

---

## Epic 6.3 — Engineering Agent

Implement:

- issue search
- issue inspection
- comments
- linked issue retrieval
- technical evidence synthesis

---

## Epic 6.4 — Specialist test suite

Create deterministic and scenario-based tests.

---

## Acceptance Criteria

Each specialist can independently:

- receive a task
- select appropriate tools
- retrieve evidence
- return a valid structured output
- preserve provenance
- stop within configured limits
- handle missing evidence
- avoid unauthorised data sources

---

## Test Gate

Each specialist must pass its minimum independent evaluation set before orchestration begins.

---

## Definition of Done

The three specialist agents are individually reliable enough to be composed into the broader workflow.

---

# 13. Phase 7 — LangGraph Orchestration

## Objective

Connect the specialist capabilities into the investigation workflow.

---

## Epic 7.1 — Investigation state

Implement typed workflow state.

Minimum state:

```text
investigation_id
question
plan
customer_findings
analytics_findings
engineering_findings
evidence_assessment
pm_recommendation
critic_review
revision_count
status
errors
```

---

## Epic 7.2 — Planner

Implement the Investigation Planner.

---

## Epic 7.3 — Routing

Implement conditional specialist routing.

---

## Epic 7.4 — Parallel execution

Where independent investigations have no dependency on one another, execute them concurrently.

---

## Epic 7.5 — Evidence assessment

Implement evidence sufficiency checking.

---

## Epic 7.6 — Targeted research

Implement bounded additional research.

---

## Epic 7.7 — Workflow failure states

Implement:

```text
FAILED
PARTIAL
COMPLETED
```

and appropriate recovery paths.

---

## Acceptance Criteria

- question creates an investigation
- planner creates a task plan
- relevant specialists execute
- findings enter typed state
- evidence sufficiency is assessed
- targeted research is bounded
- workflow reaches a valid terminal state
- failures do not produce fabricated results
- revision loops cannot become infinite

---

## Test Gate

End-to-end workflow tests must cover:

1. successful investigation
2. source failure
3. insufficient evidence
4. targeted research
5. invalid specialist output
6. workflow timeout
7. terminal completion

---

## Definition of Done

A PM can submit a question and receive a specialist evidence package without PM/critic synthesis yet.

---

# 14. Phase 8 — PM + Critic Decision Loop

## Objective

Transform specialist evidence into a defensible product recommendation and add the adversarial review loop.

---

## Epic 8.1 — PM Agent

Implement:

- structured input
- recommendation schema
- evidence-grounding rules
- confidence model
- recommendation types

---

## Epic 8.2 — Critic Agent

Implement:

- critique schema
- issue categories
- pass/revise decision
- materiality rules

---

## Epic 8.3 — Revision loop

Implement:

```text
PM
 ↓
Critic
 ↓
PASS → complete

REVISE → PM revision
```

---

## Epic 8.4 — Revision limits

Enforce:

```text
MAX_REVISIONS = 2
```

---

## Epic 8.5 — Final result assembly

Build the final investigation representation.

---

## Acceptance Criteria

- PM can synthesise specialist evidence
- PM recommendation has valid schema
- critic can identify material issues
- critic can pass sound recommendations
- critic can reject weak recommendations
- revisions address critic feedback
- revision limit is enforced
- final recommendation retains source evidence
- confidence reflects evidence strength

---

## Test Gate

Test at minimum:

```text
valid recommendation → PASS

causal overreach → REVISE

missing evidence → REVISE

contradiction ignored → REVISE

adequately supported recommendation → PASS
```

---

## Definition of Done

The complete AI decision workflow functions:

```text
question
→ evidence
→ PM recommendation
→ critic
→ revision if required
→ final result
```

---

# 15. Phase 9 — Evaluation System

## Objective

Build the formal evaluation framework needed to determine whether the product and architecture actually work.

This phase is not where evaluation begins; rather, this is where the evaluation system becomes a first-class product capability.

---

## Epic 9.1 — Evaluation dataset

Implement:

- scenarios
- ground truth
- expected evidence
- acceptable conclusions
- known traps

---

## Epic 9.2 — Evaluation runner

The runner should:

1. load scenario
2. execute selected architecture
3. collect outputs
4. run deterministic checks
5. run semantic evaluation
6. store results

---

## Epic 9.3 — Deterministic evaluators

Implement checks for:

- source references
- required evidence
- valid metrics
- issue IDs
- recommendation type
- schema validity

---

## Epic 9.4 — LLM judge

Implement structured evaluation of:

- evidence relevance
- groundedness
- cross-source reasoning
- contradiction handling
- recommendation quality
- uncertainty

---

## Epic 9.5 — Human calibration set

Create a small human-reviewed benchmark.

Use it to calibrate the LLM judge.

---

## Epic 9.6 — Error taxonomy

Implement classification of failures using the predefined error categories.

---

## Acceptance Criteria

- evaluation scenarios are versioned
- runtime cannot access ground truth
- complete investigations can be evaluated automatically
- deterministic checks run
- semantic judge runs
- results are stored with model/config metadata
- failures are categorised
- human-reviewed examples exist

---

## Test Gate

The evaluation runner must correctly execute a known scenario and reproduce expected evaluation results.

---

## Definition of Done

A single command or documented workflow can run the evaluation suite and produce a structured report.

---

# 16. Phase 10 — Architecture Benchmarking, Observability & Optimisation

## Objective

Determine whether the proposed architecture is actually worth its complexity.

This is where the project moves from:

> "We built a multi-agent system."

to:

> "We tested whether this architecture was the right product decision."

---

## Epic 10.1 — Baseline A

Implement:

```text
single agent
+
all relevant tools
```

Reuse existing tools and data sources.

---

## Epic 10.2 — Baseline B

Benchmark:

```text
specialists
+
PM
```

---

## Epic 10.3 — Candidate C

Benchmark:

```text
specialists
+
PM
+
Critic
```

---

## Epic 10.4 — Observability

Track:

- model
- tokens
- tool calls
- latency
- errors
- cost
- revisions

---

## Epic 10.5 — Benchmark runner

Run the same evaluation scenarios against all architectures.

---

## Epic 10.6 — Failure analysis

Group failures by:

```text
planning
tool selection
retrieval
interpretation
cross-source reasoning
causal overreach
recommendation
critic
revision
system
```

---

## Epic 10.7 — Model experiments

Test model alternatives where justified.

Possible dimensions:

- specialist model
- PM model
- critic model
- single vs multiple models

Do not change model and architecture simultaneously unless the experiment explicitly intends to test both.

---

## Acceptance Criteria

The benchmark report includes:

- quality scores
- failure rates
- cost
- latency
- tool-call counts
- revision counts
- architecture comparison
- failure analysis

---

## Architecture Decision Gate

At the end of this phase, explicitly decide:

### Keep full multi-agent architecture

if quality improvement justifies complexity.

### Simplify

if additional agents do not create sufficient value.

### Modify

if a specific component provides value but another does not.

The decision must be documented in an ADR.

---

## Definition of Done

There is a measured basis for the final architecture.

---

# 17. Phase 11 — Product Interface

## Objective

Wrap the validated AI workflow in a lightweight PM-facing product.

This phase intentionally comes late.

---

## Epic 11.1 — Investigation home

Implement:

- question input
- submit action
- recent investigations

---

## Epic 11.2 — Investigation progress

Display:

- current state
- completed evidence areas
- active investigation status

Do not expose hidden reasoning.

---

## Epic 11.3 — Investigation result

Display:

- executive conclusion
- evidence
- contradictions
- affected users
- likely causes
- recommendation
- metrics
- risks
- confidence
- open questions

---

## Epic 11.4 — Source inspection

Allow users to inspect supporting source references where appropriate.

---

## Epic 11.5 — Investigation history

Show previous completed investigations.

---

## Acceptance Criteria

- PM can submit a question
- PM can monitor progress
- PM can inspect final recommendation
- supporting evidence is visible
- contradictions are visible
- confidence is visible
- failures are communicated clearly
- UI does not reveal hidden prompts or chain-of-thought

---

## Definition of Done

A PM can use the system without interacting directly with development tools or agent traces.

---

# 18. Phase 12 — Hardening, Documentation & Release

## Objective

Prepare the system for portfolio demonstration and production-style review.

---

## Epic 12.1 — Security review

Verify:

- no committed credentials
- correct secret loading
- safe logging
- no sensitive data leakage
- external write boundaries

---

## Epic 12.2 — Reliability review

Test:

- API failure
- PostHog failure
- malformed queries
- malformed model outputs
- repeated investigations
- revision limits
- partial source availability

---

## Epic 12.3 — Performance review

Measure:

- end-to-end latency
- tool latency
- model latency
- cost per investigation
- concurrency behaviour

---

## Epic 12.4 — Documentation

Finalise:

- README
- architecture diagram
- setup guide
- data setup
- API documentation
- agent documentation
- evaluation methodology
- benchmark results
- ADRs
- known limitations

---

## Epic 12.5 — Portfolio demonstration

Create a reproducible demonstration flow.

Example:

```text
1. Start services
2. Seed environment
3. Start application
4. Submit investigation
5. Observe evidence gathering
6. Review recommendation
7. Inspect critic outcome
8. Run evaluation
9. Compare architectures
```

---

## Definition of Done

A technically competent reviewer can:

- understand the architecture
- run the product
- reproduce the dataset
- reproduce evaluations
- inspect source evidence
- understand major architectural decisions
- understand known limitations

---

# 19. Phase Dependencies

The implementation must respect the following dependencies.

```text
Foundation
   ↓
Data model
   ↓
Mock services
   ↓
PostHog
   ↓
Tools
   ↓
Specialist agents
   ↓
Orchestration
   ↓
PM/Critic
   ↓
Evaluation
   ↓
Architecture optimisation
   ↓
UI
   ↓
Release
```

The following should **not** happen early:

```text
UI before backend workflow
RAG before a knowledge requirement exists
MCP before an interoperability requirement exists
production deployment before core evaluation
autonomous writes before read-only reliability
```

---

# 20. Phase Gate Model

Every phase should pass four gates.

```text
GATE 1
Implementation complete
       ↓
GATE 2
Automated tests pass
       ↓
GATE 3
Acceptance criteria pass
       ↓
GATE 4
Documentation updated
       ↓
Next phase
```

A phase cannot be considered complete simply because its code compiles.

---

# 21. Change Management

Any change to the following requires explicit review:

- agent responsibilities
- API contracts
- state schema
- workflow topology
- external services
- data model
- evaluation metrics
- architecture
- security boundaries

The change should answer:

```text
What changed?
Why?
What requirement does it affect?
What alternatives were considered?
What tests must change?
What documentation must change?
```

---

# 22. Definition of Ready

A phase is ready to start when:

- its upstream dependencies are complete
- required specifications exist
- required interfaces are defined
- acceptance criteria are known
- required credentials/configuration are available
- unresolved architectural decisions are identified

---

# 23. Definition of Done

A phase is done only when:

- implementation exists
- automated tests pass
- acceptance criteria pass
- documentation is updated
- observability exists where relevant
- no known blocking defects remain
- architectural changes are documented

---

# 24. Development Workflow Inside Antigravity

Antigravity should be instructed to work in the following loop:

```text
READ
↓
Understand the relevant specification
↓
PLAN
↓
Identify files/components affected
↓
IMPLEMENT
↓
TEST
↓
REVIEW
↓
DOCUMENT
↓
REPORT
```

Before beginning a phase, Antigravity should inspect:

- current repository state
- relevant specification
- previous phase outputs
- outstanding ADRs
- existing tests

It should not assume the repository is empty after Phase 0.

---

# 25. Antigravity Phase Handoff Contract

For each phase, Antigravity should receive:

```text
Phase objective
Required inputs
Allowed changes
Required implementation
Acceptance criteria
Tests required
Definition of done
Known constraints
Relevant source-of-truth documents
```

It should return:

```text
Implemented changes
Tests executed
Test results
Acceptance criteria status
Documentation updated
Known limitations
Recommended follow-up
```

---

# 26. Antigravity Guardrails

The workspace instructions should explicitly prohibit:

- rewriting specifications without approval
- adding agents without justification
- adding dependencies without documenting why
- bypassing tests
- hardcoding credentials
- directly coupling agents to storage
- giving agents unauthorised tools
- exposing hidden reasoning
- creating autonomous external write actions
- adding RAG without a documented requirement
- introducing infrastructure that is not required
- marking a phase complete when acceptance criteria remain unmet

---

# 27. Technical Debt Policy

Technical debt may be introduced deliberately only when:

- it is documented
- it does not compromise correctness
- it has a clear follow-up path

Temporary implementations must be labelled.

Examples:

```text
TODO
TECH-DEBT
EXPERIMENTAL
```

The project should not allow temporary shortcuts to silently become architecture.

---

# 28. Release Criteria

The MVP can be considered release-ready when:

### Product

The PM can complete the intended investigation workflow.

### Data

All source systems contain coherent seeded data.

### Agents

Specialists operate within their boundaries.

### Orchestration

Workflow is stable and bounded.

### Recommendation

PM + Critic loop produces structured output.

### Evaluation

Architecture has been benchmarked.

### Observability

Investigation traces and cost/latency data exist.

### Security

No credentials or sensitive information are exposed.

### Documentation

A reviewer can reproduce the system.

---

# 29. Final Portfolio Evidence

The final project should produce tangible evidence of the product-development process.

Recommended artefacts:

```text
PRD
Product Specification
System Architecture
Agent Specification
Data/API Specification
Evaluation Strategy
Implementation Plan
ADRs
Architecture diagrams
Evaluation dataset
Benchmark report
Error analysis
Demo
README
```

The goal is to demonstrate both:

> **what was built**

and:

> **how product and technical decisions were made.**

---

# 30. Final Build Narrative

The completed project should be explainable as:

```text
1. Identified a product-management problem:
   fragmented evidence across support, analytics and engineering.

2. Defined the user workflow and product requirements.

3. Designed an architecture around specialised evidence retrieval,
   product synthesis and adversarial review.

4. Created a controlled fictional product environment with
   API-based data sources.

5. Implemented the source integrations and domain tools.

6. Built and tested specialist agents independently.

7. Orchestrated them with bounded stateful workflows.

8. Added PM synthesis and Critic review.

9. Built a formal evaluation framework.

10. Compared simpler and more complex architectures.

11. Selected the final architecture based on quality,
    cost and latency rather than assumption.

12. Wrapped the validated workflow in a usable PM interface.

13. Documented the system, limitations and decisions.
```

This is the intended implementation story.

---

# 31. Final Implementation Principle

The implementation should optimise for:

```text
clarity
+
correctness
+
measurability
+
maintainability
+
product value
```

rather than:

```text
number of agents
+
number of frameworks
+
number of APIs
+
amount of code
```

The finished system should be something you can explain as a **product decision system you deliberately designed, tested and iterated**, not merely software that happened to contain multiple LLM calls.

---

# 32. Master Definition of Done

The project is complete when a reviewer can start from a clean environment and:

```text
1. Install the project
2. Configure credentials
3. Start local mock services
4. Seed Pocket's fictional environment
5. Start the application
6. Submit a product investigation
7. Observe evidence collection
8. Review the PM recommendation
9. Inspect critic feedback
10. Inspect source evidence
11. Run the evaluation suite
12. Compare architectures
13. Review benchmark results
14. Understand the final architecture decision
15. Read the documentation and reproduce the workflow
```

The project is therefore considered complete only when the **product, implementation, evaluation and documentation all tell the same story**.
