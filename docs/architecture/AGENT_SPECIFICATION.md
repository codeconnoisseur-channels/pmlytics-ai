# Pocket AI Product Discovery Team
## Agent Specification

**Version:** 1.0  
**Status:** Draft  
**Related documents:**  
- Pocket AI Product Discovery Team — PRD v1.0
- Pocket AI Product Discovery Team — Product Specification v1.0
- Pocket AI Product Discovery Team — System Architecture v1.0

---

# 1. Purpose

This document defines the behaviour and contract of every AI agent in Pocket AI Product Discovery Team.

It specifies:

- agent responsibilities
- scope boundaries
- inputs
- outputs
- tools
- tool permissions
- decision rules
- evidence requirements
- failure behaviour
- handoffs
- stopping conditions
- validation requirements
- evaluation requirements

The objective is to prevent agents from becoming generic LLMs with broad access to the entire system.

Each agent should have a **specific job**.

---

# 2. Agent Topology

The MVP contains six AI roles:

```text
                      USER QUESTION
                            │
                            ▼
                     ┌─────────────┐
                     │  PLANNER /  │
                     │ORCHESTRATOR │
                     └──────┬──────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌────────────┐
        │ Research │  │Analytics │  │Engineering │
        │  Agent   │  │  Agent   │  │   Agent    │
        └────┬─────┘  └────┬─────┘  └─────┬──────┘
             │             │              │
             └─────────────┼──────────────┘
                           ▼
                    ┌─────────────┐
                    │ PM SYNTHESIS │
                    │    AGENT     │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │   CRITIC    │
                    │    AGENT     │
                    └──────┬──────┘
                           │
                     ┌─────┴─────┐
                     ▼           ▼
                   PASS        REVISE
                                 │
                                 ▼
                              PM AGENT
```

The six roles are:

1. Investigation Planner
2. Research Agent
3. Analytics Agent
4. Engineering Agent
5. PM Synthesis Agent
6. Critic Agent

The Planner/Orchestrator is responsible for workflow control. It is not a seventh "general-purpose researcher."

---

# 3. Agent Design Principles

## 3.1 Least-privilege tool access

An agent should only receive the tools required for its responsibility.

Example:

The Research Agent must not have an analytics tool simply because another agent has one.

---

## 3.2 Structured communication

Agents communicate through typed state and schemas rather than informal agent-to-agent conversations.

---

## 3.3 Evidence before recommendation

Specialists gather evidence.

The PM Agent makes a recommendation based on evidence already collected.

---

## 3.4 Facts must remain distinguishable from interpretation

Every specialist output must distinguish:

- observation
- interpretation
- hypothesis
- uncertainty

---

## 3.5 No fabricated evidence

If information cannot be found, the agent must report that it could not establish the claim.

---

## 3.6 Bounded tool use

Every agent has limits on:

- number of searches
- number of retrieval calls
- retries
- investigation loops

These limits prevent runaway execution.

---

## 3.7 Bounded revision

The PM/Critic loop cannot run indefinitely.

MVP maximum:

**2 revisions.**

---

# 4. Common Agent Context

Every agent receives a minimal shared context.

```python
class AgentContext(BaseModel):
    investigation_id: str
    user_question: str
    investigation_plan: InvestigationPlan | None
```

Specialists additionally receive the specific task relevant to them.

They should not automatically receive the entire investigation history.

---

# 5. Shared Evidence Model

All specialist agents use a common evidence representation.

```python
class Evidence(BaseModel):
    source_type: Literal["zendesk", "posthog", "jira"]
    source_reference: str
    finding: str
    support: str
    interpretation: str | None
    confidence: Literal["high", "medium", "low"]
    limitations: list[str]
```

The purpose is to ensure evidence remains attributable after it leaves the specialist agent.

---

# 6. Investigation Planner

## 6.1 Role

The Planner determines what investigation work is required to answer the user's question.

It is responsible for:

- understanding the question
- classifying the question
- identifying required evidence
- defining investigation tasks
- determining which specialists are needed
- identifying potential evidence gaps

It is **not** responsible for making the final product recommendation.

---

## 6.2 Input

```python
class PlannerInput(BaseModel):
    user_question: str
```

---

## 6.3 Output

```python
class InvestigationTask(BaseModel):
    specialist: Literal["research", "analytics", "engineering"]
    objective: str
    questions: list[str]
    priority: Literal["required", "useful"]

class InvestigationPlan(BaseModel):
    question_type: Literal[
        "diagnostic",
        "behavioural",
        "customer",
        "technical",
        "prioritisation",
        "comparative",
        "other"
    ]
    objectives: list[str]
    tasks: list[InvestigationTask]
    required_sources: list[str]
    success_condition: str
```

---

## 6.4 Planning Rules

The Planner should:

1. translate the user's question into investigable objectives
2. identify what evidence is necessary
3. invoke only relevant specialists
4. include cross-source investigation where the question requires causal or prioritisation reasoning
5. avoid specifying a conclusion before evidence is collected

---

## 6.5 Example

User:

> Why are users abandoning transfers?

Planner:

```text
Required:
Research → identify customer complaints
Analytics → identify transfer funnel drop-off
Engineering → identify relevant technical issues

Success condition:
Determine whether customer reports, behavioural data and
engineering evidence converge on a plausible explanation.
```

The planner must not conclude:

> Transfers are failing because of provider delays.

That is an investigation result, not a planning result.

---

## 6.6 Tool Access

The Planner has no external product-data tools.

It operates on the user question and available system capabilities.

---

## 6.7 Failure Behaviour

If the question is too ambiguous to create a meaningful investigation plan, the Planner should request clarification only where the application genuinely cannot proceed.

Otherwise it should create a best-effort plan and record uncertainty.

---

# 7. Research Agent

## 7.1 Role

The Research Agent answers:

> **What are customers saying and experiencing?**

It investigates customer-support records.

---

## 7.2 Authorised Source

Mock Zendesk only.

---

## 7.3 Tools

```text
search_tickets
get_ticket
get_ticket_comments
```

---

## 7.4 Input

```python
class ResearchTask(BaseModel):
    user_question: str
    objective: str
    questions: list[str]
```

---

## 7.5 Output

```python
class CustomerFinding(BaseModel):
    finding: str
    evidence: list[Evidence]
    observed_pattern: str
    affected_users: str | None
    frequency_context: str | None
    limitations: list[str]
    confidence: Literal["high", "medium", "low"]

class ResearchResult(BaseModel):
    findings: list[CustomerFinding]
    unanswered_questions: list[str]
    investigation_complete: bool
```

---

# 8. Research Agent Investigation Strategy

The Research Agent should use a progressive retrieval strategy.

### Stage 1: Broad discovery

Use `search_tickets()` to identify candidate ticket groups.

### Stage 2: Relevance filtering

Determine which tickets are actually relevant.

### Stage 3: Deep inspection

Use `get_ticket()` and `get_ticket_comments()` for representative or ambiguous cases.

### Stage 4: Pattern extraction

Identify:

- recurring complaint themes
- customer-described symptoms
- affected user groups
- language customers use
- important exceptions

### Stage 5: Evidence limitations

Determine whether the retrieved sample is sufficient to make a claim.

---

# 9. Research Agent Rules

The Research Agent must:

- distinguish customer statements from its interpretation
- preserve ticket references
- avoid treating individual anecdotes as population-level evidence
- inspect comments where context materially changes interpretation
- report meaningful uncertainty

It must not:

- claim an exact frequency without adequate data
- infer root cause from support language alone
- claim that a problem affects all customers
- query analytics or Jira
- make product recommendations

---

# 10. Research Agent Stopping Rules

The agent should stop when:

- relevant ticket themes are sufficiently identified
- representative supporting evidence exists
- further searches are unlikely to materially change the finding
- the tool-call budget is reached

MVP should use a configurable maximum number of tool calls.

Recommended initial budget:

**10 tool calls per research task.**

---

# 11. Analytics Agent

## 11.1 Role

The Analytics Agent answers:

> **What are users actually doing in the product?**

It investigates PostHog behavioural data.

---

## 11.2 Authorised Source

PostHog only.

---

## 11.3 Tool

```text
query_analytics
```

---

## 11.4 Input

```python
class AnalyticsTask(BaseModel):
    user_question: str
    objective: str
    questions: list[str]
```

---

## 11.5 Output

```python
class AnalyticsFinding(BaseModel):
    finding: str
    evidence: list[Evidence]
    metric: str
    value: str
    comparison: str | None
    segment: str | None
    time_period: str | None
    interpretation: str
    limitations: list[str]
    confidence: Literal["high", "medium", "low"]

class AnalyticsResult(BaseModel):
    findings: list[AnalyticsFinding]
    unanswered_questions: list[str]
    investigation_complete: bool
```

---

# 12. Analytics Agent Investigation Strategy

The agent should generally follow:

```text
Question
 ↓
Define metric
 ↓
Establish baseline
 ↓
Inspect relevant behaviour
 ↓
Segment where useful
 ↓
Compare
 ↓
Interpret
```

For example:

> Why are users abandoning transfers?

The Analytics Agent should not immediately query:

> transfer_failed

It should first establish the relevant journey:

```text
transfer_started
→ transfer_submitted
→ transfer_processing
→ transfer_completed
```

Then determine where meaningful loss occurs.

---

# 13. Analytics Agent Rules

The Analytics Agent must:

- define what each reported metric represents
- distinguish counts from rates
- provide comparison periods or segments when relevant
- avoid overinterpreting small or noisy changes
- preserve the query or query description used
- identify missing data

It must not:

- infer customer sentiment
- claim that a metric proves causality
- manufacture metrics when a query fails
- query Zendesk or Jira
- make product recommendations

---

# 14. Analytics Query Discipline

The agent should prefer the simplest query capable of answering the question.

It should not perform complex exploratory querying without a reason.

Potential query sequence:

```text
1. Baseline metric
2. Funnel/event relationship
3. Relevant segmentation
4. Time comparison
5. Targeted follow-up
```

This keeps analytics usage efficient.

---

# 15. Analytics Stopping Rules

The Analytics Agent should stop when:

- the requested behaviour has been sufficiently measured
- meaningful segmentation has been checked where relevant
- further queries are unlikely to change the conclusion
- tool-call budget is reached

Recommended initial budget:

**8 analytics queries per task.**

---

# 16. Engineering Agent

## 16.1 Role

The Engineering Agent answers:

> **What technical context might explain or affect the product problem?**

---

## 16.2 Authorised Source

Mock Jira only.

---

## 16.3 Tools

```text
search_issues
get_issue
get_issue_comments
get_linked_issues
```

---

## 16.4 Input

```python
class EngineeringTask(BaseModel):
    user_question: str
    objective: str
    questions: list[str]
```

---

## 16.5 Output

```python
class EngineeringFinding(BaseModel):
    finding: str
    evidence: list[Evidence]
    issue_status: str | None
    technical_context: str
    relationship_to_problem: str
    limitations: list[str]
    confidence: Literal["high", "medium", "low"]

class EngineeringResult(BaseModel):
    findings: list[EngineeringFinding]
    unanswered_questions: list[str]
    investigation_complete: bool
```

---

# 17. Engineering Investigation Strategy

The Engineering Agent should:

1. identify relevant issues
2. inspect issue details
3. inspect comments for technical context
4. inspect linked issues where relationships matter
5. distinguish active problems from historical issues
6. assess relevance to the product question

---

# 18. Engineering Agent Rules

The Engineering Agent must:

- distinguish open, resolved and historical issues
- preserve issue identifiers
- distinguish engineering suspicion from confirmed findings
- explain how an issue relates to the product problem

It must not:

- assume an engineering issue caused a product metric
- infer customer impact from issue priority alone
- query PostHog or Zendesk
- make the final product recommendation

---

# 19. Engineering Stopping Rules

Recommended initial budget:

**8 tool calls per task.**

The agent stops once relevant engineering context is sufficiently established.

---

# 20. Evidence Assessment

Although not a separate AI agent, the system should implement a controlled evidence-assessment step after specialist investigation.

Its purpose is to determine:

> Do we have enough evidence to proceed to PM synthesis?

Inputs:

```text
Customer findings
Analytics findings
Engineering findings
Investigation plan
```

Output:

```python
class EvidenceAssessment(BaseModel):
    sufficient: bool
    missing_sources: list[str]
    evidence_gaps: list[str]
    contradictions: list[str]
    recommended_followups: list[str]
```

This should preferably be implemented as deterministic validation plus structured model assessment rather than another unrestricted agent.

---

# 21. Targeted Investigation

If evidence is insufficient, the orchestrator may issue a targeted task.

Example:

```text
Analytics:
"Drop-off appears concentrated among high-value transactions."

Evidence gap:
"No corresponding customer evidence has been checked for this segment."

Targeted task:
Research Agent → investigate support evidence related to high-value transfers.
```

The targeted investigation must have a specific objective.

The system should not restart every specialist from scratch.

---

# 22. PM Synthesis Agent

## 22.1 Role

The PM Agent converts evidence into a product assessment.

This is the first agent whose primary responsibility is **product judgment** rather than evidence retrieval.

---

## 22.2 Inputs

```text
user_question
investigation_plan
customer_findings
analytics_findings
engineering_findings
evidence_assessment
```

---

## 22.3 Tool Access

**None in MVP.**

The PM Agent receives evidence through state.

---

# 23. PM Output

```python
class ProductRecommendation(BaseModel):
    problem_statement: str
    why_it_matters: str
    affected_users: str
    evidence: list[Evidence]
    likely_causes: list[str]
    conflicting_evidence: list[str]
    recommendation: str
    recommendation_type: Literal[
        "prioritise",
        "investigate_further",
        "experiment",
        "technical_remediation",
        "monitor",
        "deprioritise"
    ]
    success_metrics: list[str]
    risks: list[str]
    confidence: Literal["high", "medium", "low"]
    open_questions: list[str]
```

---

# 24. PM Agent Decision Rules

The PM Agent must:

### Separate facts from hypotheses

Example:

**Fact:**

> 18 support tickets report transfers remaining pending.

**Hypothesis:**

> Delayed callbacks may be contributing to the perceived transfer-status problem.

These must not be presented as equivalent.

---

### Consider all material evidence

The PM Agent should not select only evidence supporting the most convenient conclusion.

---

### Weigh evidence by relevance

Not all evidence deserves equal weight.

A direct analytics measurement may be more informative for behavioural impact than a handful of anecdotes.

Likewise, a detailed engineering issue may be stronger technical evidence than a generic support complaint.

---

### Consider affected-user magnitude

A severe problem affecting 0.5% of users may deserve a different recommendation from a moderate problem affecting 40%.

---

### Avoid forced action

The system may recommend:

> Investigate further.

when evidence is insufficient.

---

# 25. PM Recommendation Rules

A recommendation should answer:

> Given what we know now, what is the most defensible next product decision?

The PM Agent should not simply repeat:

> "We should investigate further."

unless the evidence genuinely warrants it.

The recommendation should contain a concrete next step.

---

# 26. PM Confidence Rules

### High

Use only when:

- evidence from multiple relevant sources converges
- material contradictions are absent
- important evidence gaps are limited

### Medium

Use when:

- evidence supports the conclusion
- meaningful uncertainty or gaps remain

### Low

Use when:

- evidence is sparse
- sources materially conflict
- causal explanation remains weak

Confidence must be tied to evidence quality.

---

# 27. Critic Agent

## 27.1 Role

The Critic acts as an adversarial reviewer of the PM recommendation.

Its job is:

> **Find reasons the recommendation may be wrong, overstated or insufficiently supported.**

It is not a second PM.

---

# 28. Critic Inputs

```text
user_question
investigation_plan
evidence_assessment
customer_findings
analytics_findings
engineering_findings
pm_recommendation
```

---

# 29. Critic Output

```python
class CriticIssue(BaseModel):
    category: Literal[
        "unsupported_claim",
        "causal_overreach",
        "missing_evidence",
        "contradiction",
        "segmentation_gap",
        "magnitude_gap",
        "alternative_explanation",
        "confidence_mismatch",
        "recommendation_mismatch"
    ]
    claim: str
    problem: str
    supporting_evidence: list[str]
    required_change: str

class CriticReview(BaseModel):
    decision: Literal["PASS", "REVISE"]
    issues: list[CriticIssue]
    overall_assessment: str
    required_changes: list[str]
```

---

# 30. Critic Evaluation Rules

The critic should challenge:

### Unsupported claims

> What evidence supports this statement?

### Causal assumptions

> Does the evidence establish cause or merely association?

### Missing evidence

> Was an important evidence source or segment ignored?

### Contradictions

> Is there evidence that weakens this conclusion?

### Magnitude

> Is the problem large enough to justify the recommendation?

### Alternative explanation

> Is another explanation at least as plausible?

### Confidence

> Does the confidence level match the evidence?

---

# 31. Critic Behaviour Example

PM:

> Transfer failures have increased because of Provider X.

Critic:

```text
Decision: REVISE

Issue:
causal_overreach

Problem:
PostHog does not show a material increase in actual transfer
failure rate. Jira provides evidence of delayed callbacks but
does not establish that Provider X caused the observed customer
complaints.

Required change:
Distinguish delayed transaction status from actual transfer
failure and reduce causal certainty.
```

This is the desired behaviour.

---

# 32. Critic Non-Goals

The Critic must not:

- criticise purely stylistic choices
- create objections merely to appear adversarial
- invent contradictory evidence
- demand evidence irrelevant to the user's question
- rewrite the entire recommendation unnecessarily
- perform unlimited additional research

---

# 33. PM Revision

When Critic returns `REVISE`, the PM receives:

```text
Original recommendation
Critic issues
Required changes
Original evidence
```

The PM should produce a revised recommendation.

The PM should explicitly address every material critic issue.

---

# 34. Revision Integrity

The revised recommendation must not:

- silently ignore the critique
- remove inconvenient evidence without justification
- introduce unsupported evidence
- change the underlying question
- exceed the evidence available

The revised output must remain grounded in the original evidence unless targeted new research was explicitly requested.

---

# 35. Revision Limit

Maximum:

**2 PM revision cycles per investigation.**

If the recommendation still has material weaknesses after the maximum:

```text
Investigation status:
COMPLETED_WITH_LIMITATIONS
```

The final output must preserve the unresolved issues.

---

# 36. Orchestrator Responsibilities

The orchestrator is responsible for workflow control.

It should:

- initialise state
- invoke the Planner
- route specialist work
- collect outputs
- trigger evidence assessment
- initiate targeted research
- invoke PM synthesis
- invoke Critic
- route revision
- enforce limits
- terminate the workflow
- handle failures

It should not independently invent product findings.

---

# 37. Orchestrator Decision Rules

The orchestrator can decide:

### Continue

Evidence is still incomplete.

### Synthesis

Evidence meets the minimum requirement.

### Targeted research

A specific evidence gap can materially affect the conclusion.

### Revise

Critic identifies material weaknesses.

### Complete

Investigation meets completion criteria.

### Fail

The system cannot produce a trustworthy investigation.

---

# 38. Agent Failure Contracts

Every agent must return structured failures rather than throwing unhandled prose into shared state.

Example:

```python
class AgentError(BaseModel):
    agent: str
    error_type: Literal[
        "tool_failure",
        "invalid_output",
        "timeout",
        "insufficient_data",
        "configuration_error",
        "unknown"
    ]
    message: str
    recoverable: bool
```

---

# 39. Invalid Structured Output

If an agent generates output that does not validate against its schema:

1. attempt bounded structured-output repair
2. retry generation where appropriate
3. fail the node if the output remains invalid
4. never silently coerce missing critical fields

The exact retry count belongs in implementation configuration.

---

# 40. Agent Tool Security

Agents never receive raw credentials.

Tool execution occurs through application-controlled functions.

Conceptually:

```text
Agent
 ↓
Tool
 ↓
Application integration
 ↓
Credential
 ↓
API
```

not:

```text
Agent
 ↓
API key
 ↓
Internet
```

---

# 41. Tool-Call Constraints

Every tool invocation should have:

- schema validation
- timeout
- retry policy
- call limit
- structured response validation

The model should not construct arbitrary URLs or HTTP requests.

---

# 42. Prompt Architecture

Each agent should have a dedicated system instruction defining:

1. role
2. objective
3. allowed evidence sources
4. available tools
5. prohibited actions
6. evidence rules
7. output schema
8. stopping conditions
9. failure behaviour

A specialist agent should not receive another specialist's system instructions.

---

# 43. Context Construction

The application, not the agent, determines what context is supplied.

Example:

Research Agent receives:

```text
user question
research objective
research questions
```

It does not receive:

```text
full Jira dataset
full PostHog results
PM recommendation
```

unless a targeted workflow explicitly requires it.

This keeps context focused.

---

# 44. Information Flow

The information flow should be:

```text
Question
  ↓
Planner
  ↓
Specialist tasks
  ↓
Specialist evidence
  ↓
Evidence assessment
  ↓
PM
  ↓
Critic
  ↓
PM revision if required
  ↓
Final recommendation
```

No specialist should directly modify another specialist's findings.

---

# 45. Agent-to-Agent Communication

Direct natural-language agent conversations are not part of the MVP.

Instead:

```text
Agent A
   ↓
typed result
   ↓
shared state
   ↓
Agent B
```

This is preferable because it makes execution:

- inspectable
- reproducible
- testable
- easier to evaluate

---

# 46. Agent Stopping Conditions

Every agent must have at least one explicit stopping condition.

The system should terminate an agent when:

- its objective is satisfied
- sufficient evidence has been collected
- the remaining uncertainty cannot be resolved with available tools
- the tool budget is reached
- an unrecoverable error occurs

Agents should not continue searching merely because additional data exists.

---

# 47. Agent Quality Criteria

A specialist agent is successful when it:

1. answers its assigned investigation objective
2. uses the correct source
3. retrieves relevant evidence
4. preserves provenance
5. avoids unsupported interpretation
6. clearly communicates limitations
7. stops within its operational boundaries

---

# 48. Cross-Agent Quality Criteria

The system as a whole is successful when:

- specialist findings are compatible
- contradictions are preserved
- the PM uses evidence correctly
- the Critic catches real weaknesses
- revisions materially address criticism
- final conclusions remain grounded

---

# 49. Evaluation Targets by Agent

## Planner

Measure:

- appropriate source selection
- task decomposition quality
- unnecessary-source rate

## Research Agent

Measure:

- relevant ticket retrieval
- evidence precision
- source attribution
- theme accuracy

## Analytics Agent

Measure:

- correct metric selection
- query correctness
- interpretation accuracy
- segmentation quality

## Engineering Agent

Measure:

- relevant issue retrieval
- technical-context accuracy
- current-vs-historical distinction

## PM Agent

Measure:

- evidence grounding
- synthesis quality
- recommendation correctness
- causal discipline
- confidence calibration

## Critic Agent

Measure:

- true issue detection
- false criticism rate
- contradiction detection
- causal-overreach detection

---

# 50. Agent-Level Baselines

Each specialist should also be testable independently.

For example:

```text
Research Agent
Question
→ expected relevant tickets

Analytics Agent
Question
→ expected metric/query

Engineering Agent
Question
→ expected issues
```

This allows debugging failures without having to run the full workflow.

---

# 51. Recommended Initial Agent Count

MVP should remain at six logical roles:

```text
1. Planner
2. Research
3. Analytics
4. Engineering
5. PM
6. Critic
```

Do not add:

- dedicated summariser
- dedicated fact checker
- dedicated memory agent
- dedicated prioritisation agent
- dedicated "manager" agent

unless evaluation shows a real need.

---

# 52. Why We Are Not Adding More Agents

Additional agents increase:

- latency
- cost
- orchestration complexity
- failure modes
- debugging effort

The architecture should earn additional agents through demonstrated need.

---

# 53. Agent Permission Matrix

| Capability | Planner | Research | Analytics | Engineering | PM | Critic |
|---|---:|---:|---:|---:|---:|---:|
| Read Zendesk | No | Yes | No | No | No | No |
| Read PostHog | No | No | Yes | No | No | No |
| Read Jira | No | No | No | Yes | No | No |
| Make product recommendation | No | No | No | No | Yes | Review only |
| Critique recommendation | No | No | No | No | No | Yes |
| Trigger targeted research | No | No | No | No | No | Via orchestrator |
| External writes | No | No | No | No | No | No |

This permission boundary should be enforced by the application rather than relying solely on prompts.

---

# 54. Example Full Investigation

Question:

> Why are users abandoning transfers?

### Planner

Creates:

```text
Research:
identify transfer complaints

Analytics:
measure transfer journey and abandonment

Engineering:
identify transfer-related incidents/issues
```

### Research

Returns:

```text
Customers frequently report pending transfers.

Evidence:
Zendesk #1047
Zendesk #1062
Zendesk #1091
```

### Analytics

Returns:

```text
Largest drop occurs after transfer submission.

Actual failure rate is stable.
```

### Engineering

Returns:

```text
Open issue PAY-117 concerns delayed transfer callbacks.
```

### Evidence Assessment

```text
Sufficient: Yes
Contradiction: customer language says "failed",
analytics does not show increased actual failures.
```

### PM

Produces:

> Transfer-status reliability appears to be the primary problem rather than a broad increase in transfer failures.

### Critic

Checks:

- evidence support
- causality
- contradiction
- confidence

Returns:

```text
PASS
```

### Final output

Returned to the user.

---

# 55. Example Revision

PM initially says:

> Provider X caused the increase in failed transfers.

Critic:

```text
REVISE

Reason:
Analytics shows actual failure rate is stable.

Required change:
Distinguish delayed status updates from genuine transfer failure.
Do not attribute causation to Provider X without supporting evidence.
```

PM revises:

> Customer complaints indicate a significant transfer-status problem. Engineering evidence identifies delayed callbacks involving Provider X, but current analytics do not establish that actual transfer failures increased or that Provider X is the sole cause. The strongest next step is to investigate status synchronisation and measure the proportion of delayed transactions that eventually complete.

Critic:

```text
PASS
```

---

# 56. Agent Observability

Every agent invocation should record:

```text
investigation_id
agent
node
model
input schema
output validation status
tool calls
tool call count
tool duration
token usage
error status
revision number
```

This allows failures to be attributed to:

- planning
- retrieval
- analytics
- synthesis
- criticism
- revision

rather than treating the whole system as a black box.

---

# 57. Agent Configuration

Configuration should be externalised where practical.

Potential configuration:

```text
MAX_RESEARCH_TOOL_CALLS
MAX_ANALYTICS_QUERIES
MAX_ENGINEERING_TOOL_CALLS
MAX_TARGETED_INVESTIGATIONS
MAX_PM_REVISIONS
AGENT_MODEL
TEMPERATURE
TIMEOUT
```

Exact environment-variable names belong to implementation.

---

# 58. Prompt Versioning

Agent prompts should be version-controlled.

A prompt change should be attributable to a specific version.

Example:

```text
research_agent_v1
research_agent_v2
```

or equivalent version metadata.

This is important for evaluation.

If a prompt change improves performance, the project should be able to demonstrate which change produced it.

---

# 59. Model Swappability

The agent contract must not depend on one specific model provider.

The system should allow models to be swapped while preserving:

- input schema
- output schema
- tool contracts
- state contracts

This enables model evaluation without architectural rewrites.

---

# 60. Definition of Done

The Agent Specification is considered implemented when:

1. Every agent has a defined objective.
2. Every agent has a bounded scope.
3. Every agent has explicit tool permissions.
4. Every specialist has structured input/output schemas.
5. Evidence retains source provenance.
6. Specialists cannot access unauthorised sources.
7. The PM does not independently query data sources in MVP.
8. The Critic can issue `PASS` or `REVISE`.
9. PM revisions are bounded.
10. Agent failures are structured and recoverable where possible.
11. Tool calls are bounded and validated.
12. Agent execution is traceable.
13. Each agent can be evaluated independently.
14. The complete workflow can be evaluated end to end.
15. The architecture supports comparison against a simpler single-agent baseline.

---

# 61. Final Agent Design Principle

The agents should behave like a small product team with clearly separated responsibilities:

```text
Planner
"What do we need to find out?"

Research
"What are customers saying?"

Analytics
"What are users actually doing?"

Engineering
"What does the technical evidence tell us?"

PM
"What does the evidence mean for the product?"

Critic
"Why might that conclusion be wrong?"
```

The value of the architecture comes from **how these responsibilities interact**, not from the number of agents.

The system should therefore remain deliberately small, constrained and measurable.