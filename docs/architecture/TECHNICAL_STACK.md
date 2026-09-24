# Pocket AI Product Discovery Team
## Locked Technical Baseline

**Version:** 1.0  
**Status:** Accepted  
**Date:** 2026-09-15

---

# 1. Purpose

This document freezes the technical choices that the implementation must use unless they are intentionally changed through an Architecture Decision Record.

The purpose is to prevent the implementation agent from making major technology choices during coding.

---

# 2. Locked Stack

| Concern | Decision |
|---|---|
| Primary language | Python |
| Orchestration | LangGraph |
| LLM gateway | OpenRouter |
| Initial default model | OpenAI GPT-5.4 |
| First benchmark challenger | Anthropic Claude Sonnet 4.6 |
| AI observability | LangSmith |
| Product analytics source | PostHog |
| Customer-support source | Mock Zendesk |
| Engineering source | Mock Jira via MockServer |
| Agent communication | Typed structured schemas |
| Agent tool interface | Domain tools |
| Long-term memory | None |
| RAG | None |
| MCP | None in MVP |
| Agent write actions | None in MVP |

---

# 3. LLM Gateway

## Decision

Use **OpenRouter** for all model inference.

All agent model calls must go through OpenRouter.

The application must not contain provider-specific inference logic inside individual agents.

Architecture:

```text
Agent
  ↓
Application LLM abstraction
  ↓
OpenRouter
  ↓
Selected model
```

OpenRouter currently documents tool calling as a common interface where application code defines tools, receives tool-call requests and returns tool results. Its LangChain integration also supports tool binding and structured outputs. 

---

# 4. Initial Model

## Decision

Use:

```text
openai/gpt-5.4
```

as the initial default model for all agents.

GPT-5.4 currently supports:

- function/tool calling
- structured outputs
- large context
- multi-provider routing

OpenRouter currently lists it at $2.50/M input tokens and $15/M output tokens on the standard pricing tier, with a 1.05M-token context window. 

This is the **initial model**, not the final model decision.

---

# 5. Benchmark Model

The first alternative model to benchmark is:

```text
anthropic/claude-sonnet-4.6
```

Sonnet 4.6 currently supports tool calling and structured outputs and has a 1M-token context window.

The benchmark should determine whether it provides materially better:

- investigation quality
- tool selection
- cross-source reasoning
- critic performance

relative to GPT-5.4.

The final architecture may use:

```text
GPT-5.4 everywhere
```

or:

```text
GPT-5.4 for some agents
+
Claude Sonnet 4.6 for others
```

based on evaluation.

---

# 6. Model Selection Policy

Do not select models based purely on benchmark reputation.

Evaluate them on the actual Pocket workload.

Evaluation dimensions:

```text
tool calling
structured output adherence
evidence grounding
cross-source reasoning
contradiction handling
recommendation quality
critic effectiveness
cost
latency
```

The evaluation strategy remains the authority for model comparison.

---

# 7. OpenRouter Configuration

Conceptual environment:

```env
OPENROUTER_API_KEY=
DEFAULT_MODEL=openai/gpt-5.4

PLANNER_MODEL=
RESEARCH_MODEL=
ANALYTICS_MODEL=
ENGINEERING_MODEL=
PM_MODEL=
CRITIC_MODEL=
JUDGE_MODEL=
```

The final agent-specific model configuration should default to GPT-5.4 but remain overrideable for experiments.

---

# 8. Observability Platform

## Decision

Use **LangSmith** as the primary AI observability and tracing platform.

LangSmith currently provides tracing for agent execution and supports monitoring of latency, cost, errors, tool/agent trajectories and quality metrics. It is also framework-agnostic and supports LangGraph workflows.

---

# 9. LangSmith Responsibilities

LangSmith is responsible for AI execution observability.

Track:

- investigation traces
- LangGraph nodes
- agent runs
- model calls
- tool calls
- latency
- errors
- token/cost metadata where available
- evaluation runs where appropriate

The application's own persistence remains the source of truth for investigation records.

---

# 10. LangSmith Configuration

Current LangSmith Python configuration uses:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=Pocket-AI-Product-Discovery
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

The exact endpoint may follow account/region configuration.

LangSmith currently supports project-level trace grouping and environment-based tracing configuration.

---

# 11. Investigation Trace Correlation

Every application investigation must have a stable ID.

Example:

```text
inv_01J...
```

The same investigation ID should be attached to relevant LangSmith metadata/tags.

This gives us:

```text
Application investigation
        ↕
LangSmith trace
```

and allows a reviewer to move from a product result into its technical execution trace.

---

# 12. Zendesk Mock

## Decision

Use:

```text
allan-simon/http-zendesk-mock
```

as the initial customer-support test double.

Repository:

https://github.com/allan-simon/http-zendesk-mock

The repository describes itself as an HTTP service intended to replicate the Zendesk API and supports ticket creation, ticket retrieval and comment retrieval.

---

# 13. Zendesk Pinning Rule

Do not depend on an unpinned branch.

At implementation kickoff:

1. clone the repository
2. verify the required API operations
3. run smoke tests
4. record the exact commit SHA
5. document that SHA in the project configuration

The application must subsequently use the pinned revision.

If the mock fails our contract tests, replace it only through an ADR.

---

# 14. Zendesk Boundary

The mock implements only the subset needed by Pocket.

Required runtime surface:

```text
GET /api/v2/search
GET /api/v2/tickets/{id}
GET /api/v2/tickets/{id}/comments
```

Seed-only operations:

```text
POST /api/v2/tickets
```

and optionally:

```text
POST /api/v2/tickets/create_many
```

Agents do not receive seed/write operations.

---

# 15. Jira Mock

## Decision

Use **MockServer 7.6.0** as the HTTP mocking foundation for Jira.

MockServer currently publishes an explicit `7.6.0` release and supports Docker deployment, HTTP request matching, response configuration, OpenAPI-driven mock generation and verification of requests.

---

# 16. Jira Mock Architecture

MockServer will emulate the required Jira REST surface.

Conceptually:

```text
Engineering Tool
      ↓
Jira Adapter
      ↓
MockServer
      ↓
Configured Jira expectations
```

We do not implement a full Jira server.

We implement the exact contract required by our Engineering Agent.

---

# 17. Jira Mock Version

Pin:

```text
mockserver/mockserver:7.6.0
```

Do not use:

```text
mockserver/mockserver:latest
```

for the reproducible project environment.

MockServer's current documentation explicitly provides the `7.6.0` Docker image and recommends explicit versioning for reproducible deployments.

---

# 18. Jira Mock API Surface

Runtime:

```text
POST /rest/api/3/search/jql

GET /rest/api/3/issue/{issueIdOrKey}

GET /rest/api/3/issue/{issueIdOrKey}/comment

GET /rest/api/3/issue/{issueIdOrKey}?fields=issuelinks
```

Seed/setup:

```text
POST /rest/api/3/issue
POST /rest/api/3/issue/{issueIdOrKey}/comment
POST /rest/api/3/issueLink
```

The implementation should model the current Jira API contract required by these workflows, not reproduce Jira's entire feature set.

---

# 19. Why MockServer Rather Than a Jira-Specific Mock

MockServer is preferred because the requirement is:

> We need a controlled HTTP test double implementing a small Jira-compatible surface.

MockServer gives us:

- active project
- explicit versioning
- Docker support
- API-driven expectations
- request verification
- OpenAPI support
- controllable failure injection

This is a better fit than depending on a small Jira-specific repository with an uncertain maintenance trajectory.

---

# 20. PostHog

## Decision

Use a real PostHog project for Pocket.

Official platform:

https://posthog.com/

The seed generator sends fictional Pocket events into the project.

The Analytics Agent queries that same project.

---

# 21. PostHog Boundary

PostHog is external infrastructure.

Architecture:

```text
Seed generator
      ↓
PostHog
      ↓
Pocket project
      ↓
Analytics Tool
      ↓
Analytics Agent
```

The agent does not receive the PostHog API key.

---

# 22. PostHog Configuration

Conceptual configuration:

```env
POSTHOG_HOST=
POSTHOG_PROJECT_ID=
POSTHOG_API_KEY=
```

The exact credential type should be confirmed against the account's current API configuration during setup.

---

# 23. PostHog Responsibilities

PostHog is responsible for:

- event storage
- behavioural analysis
- funnel analysis
- segmentation
- time comparisons
- analytics querying

The seed system remains responsible for creating the fictional event population.

---

# 24. Tool Layer

Agents do not access any external service directly.

Required architecture:

```text
Agent
  ↓
Domain Tool
  ↓
Adapter
  ↓
Service
```

Examples:

```text
Research Agent
  ↓
search_tickets()
  ↓
Zendesk Adapter
  ↓
Mock Zendesk
```

```text
Analytics Agent
  ↓
query_analytics()
  ↓
PostHog Adapter
  ↓
PostHog
```

```text
Engineering Agent
  ↓
search_issues()
  ↓
Jira Adapter
  ↓
MockServer
```

---

# 25. Observability Does Not Become Agent Logic

LangSmith is observability infrastructure.

Agents should not:

- query LangSmith
- use LangSmith as memory
- use LangSmith as a knowledge source
- depend on LangSmith availability to generate their product answer

Tracing failure should not cause investigation failure.

---

# 26. Evaluation Platform Boundary

LangSmith and the application's evaluation runner have different responsibilities.

### Application evaluation layer

Owns:

- scenarios
- ground truth
- deterministic checks
- score aggregation
- benchmark comparison

### LangSmith

Provides:

- execution traces
- model/tool visibility
- run metadata
- observability
- optional evaluation support

Do not make LangSmith the only evaluation mechanism.

---

# 27. Initial Development Environment

The intended local environment is:

```text
┌──────────────────────────┐
│      Pocket App          │
│      Python              │
│      LangGraph           │
└────────────┬─────────────┘
             │
      ┌──────┼───────┐
      │      │       │
      ▼      ▼       ▼
 Mock       PostHog  Mock
 Zendesk             Jira
                    (MockServer)

External:
OpenRouter
LangSmith
PostHog
```

Mock Zendesk and Mock Jira run locally.

OpenRouter, LangSmith and PostHog are external services.

---

# 28. Local Service Isolation

Each mock should have its own configuration and health check.

Example:

```env
ZENDESK_BASE_URL=http://localhost:<zendesk-port>
JIRA_BASE_URL=http://localhost:<jira-port>
```

The application must not hard-code local ports throughout the codebase.

---

# 29. Required `.env.example`

The repository must eventually contain a template resembling:

```env
# LLM
OPENROUTER_API_KEY=
DEFAULT_MODEL=openai/gpt-5.4

# LangSmith
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=Pocket-AI-Product-Discovery

# PostHog
POSTHOG_HOST=
POSTHOG_PROJECT_ID=
POSTHOG_API_KEY=

# Local mocks
ZENDESK_BASE_URL=
JIRA_BASE_URL=
```

No real values.

---

# 30. Final Locked Architecture

```text
                         USER
                           │
                           ▼
                    Pocket Application
                           │
                           ▼
                       LangGraph
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
         Research      Analytics    Engineering
          Agent          Agent          Agent
             │             │             │
             ▼             ▼             ▼
       Zendesk Tool    Analytics Tool  Jira Tools
             │             │             │
             ▼             ▼             ▼
       Mock Zendesk     PostHog      MockServer
                                      Jira API
             └─────────────┼─────────────┘
                           ▼
                       PM Agent
                           │
                           ▼
                      Critic Agent
                           │
                           ▼
                      Final Result


All LLM calls
       ↓
   OpenRouter
       ↓
 GPT-5.4 initially


All AI execution tracing
       ↓
    LangSmith
```

---

# 31. Locked-vs-Experimental Decisions

## Locked

- Python
- LangGraph
- OpenRouter
- LangSmith
- PostHog
- Mock Zendesk approach
- MockServer for Jira
- domain-tool architecture
- structured agent contracts
- no RAG
- no long-term memory
- read-only agents

## Initial but experimentally revisable

- GPT-5.4 as default model
- Claude Sonnet 4.6 as benchmark challenger
- exact agent-to-model assignment
- final model routing strategy
- exact seed-data volume
- exact evaluation thresholds

This distinction is intentional.

---

# 32. What Antigravity Must Not Decide

Antigravity must not independently choose:

- another LLM gateway
- another orchestration framework
- another observability platform
- another analytics platform
- another mock strategy
- RAG
- MCP
- long-term memory
- a new agent
- external write capabilities

unless the corresponding architecture decision is explicitly changed.

---

# 33. Technology Change Process

If implementation discovers that a locked technology cannot satisfy a requirement:

```text
Problem identified
       ↓
Evidence collected
       ↓
Alternative evaluated
       ↓
ADR created
       ↓
Architecture decision changed
       ↓
Specifications updated
       ↓
Implementation continues
```

Never silently substitute technology.

---

# 34. Technical Baseline Definition of Done

Before substantive application implementation begins:

- OpenRouter account/API access is configured
- GPT-5.4 can complete a basic tool-calling smoke test
- LangSmith tracing works
- PostHog project exists and accepts test events
- Mock Zendesk passes its API smoke tests
- MockServer 7.6.0 starts successfully
- the required Jira expectations can be exercised
- all external URLs are environment-configured
- `.env.example` exists
- no secrets are committed

---

# 35. Final Technology Principle

The project should use technology to support the product architecture.

The intended chain is:

```text
Product requirement
      ↓
Architecture
      ↓
Technology
      ↓
Implementation
      ↓
Evaluation
```

not:

```text
Interesting technology
      ↓
Find a reason to use it
      ↓
Build around it
```