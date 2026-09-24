# Pocket AI Product Discovery Team
## Evaluation Strategy

**Version:** 1.0  
**Status:** Draft  
**Related documents:**
- Pocket AI Product Discovery Team — PRD v1.0
- Pocket AI Product Discovery Team — Product Specification v1.0
- Pocket AI Product Discovery Team — System Architecture v1.0
- Pocket AI Product Discovery Team — Agent Specification v1.0
- Pocket AI Product Discovery Team — Data & API Specification v1.0

---

# 1. Purpose

This document defines how Pocket AI Product Discovery Team will be evaluated.

The evaluation strategy is designed to answer five questions:

1. Can the system retrieve the right evidence?
2. Can the system correctly interpret evidence from different sources?
3. Can the system handle ambiguity and conflicting evidence?
4. Can the system produce defensible product recommendations?
5. Does the multi-agent architecture provide enough value to justify its additional complexity, cost and latency?

The evaluation must measure both **component-level quality** and **end-to-end product quality**.

---

# 2. Evaluation Philosophy

The product should not be evaluated solely on final-answer quality.

An investigation can produce a correct-looking recommendation for the wrong reasons.

For example:

> "Transfer failures are increasing because Provider X is having issues."

This might sound reasonable.

But if:

- PostHog shows that actual failure rates are stable
- Zendesk shows customers describing delayed transactions as "failed"
- Jira only shows a callback-delay issue

then the answer is poorly grounded even if it sounds convincing.

Therefore evaluation must inspect the chain:

```text
Question
   ↓
Investigation planning
   ↓
Tool selection
   ↓
Evidence retrieval
   ↓
Evidence interpretation
   ↓
Cross-source synthesis
   ↓
Recommendation
   ↓
Critical review
   ↓
Final recommendation
```

---

# 3. Evaluation Objectives

## Objective 1: Retrieval quality

Determine whether agents retrieve the evidence required to answer the question.

## Objective 2: Grounded reasoning

Determine whether conclusions are supported by the retrieved evidence.

## Objective 3: Cross-source reasoning

Determine whether the system correctly connects customer, behavioural and engineering evidence.

## Objective 4: Contradiction handling

Determine whether the system notices and appropriately handles conflicting evidence.

## Objective 5: Recommendation quality

Determine whether the proposed action follows from the evidence.

## Objective 6: Critic effectiveness

Determine whether the critic identifies genuine problems in the PM recommendation.

## Objective 7: Efficiency

Measure the cost and latency of each architecture.

## Objective 8: Architecture value

Determine whether specialist agents and critic loops materially outperform simpler alternatives.

---

# 4. Evaluation Pyramid

Evaluation will operate at four levels.

```text
                    END-TO-END
                 Product Decision
                       ▲
                       │
                 Workflow Level
             Orchestration + Handoffs
                       ▲
                       │
                 Agent Level
              Specialist Performance
                       ▲
                       │
                 Tool / API Level
             Retrieval + Data Access
```

A failure at a lower level should not be confused with an agent reasoning failure.

For example:

> The Research Agent cannot find the correct ticket because the search tool is broken.

is an integration failure, not evidence that the Research Agent is incapable of research.

---

# 5. Evaluation Dataset

The evaluation dataset will consist of carefully designed product-investigation scenarios.

Initial target:

**40–50 scenarios**

The dataset should represent the types of reasoning the product is intended to perform.

---

# 6. Evaluation Scenario Structure

Each scenario should contain:

```python
class EvaluationScenario(BaseModel):
    scenario_id: str
    question: str
    product_area: str

    required_sources: list[str]

    expected_findings: list[str]
    required_evidence: list[str]

    contradictions: list[str]
    known_traps: list[str]

    acceptable_conclusions: list[str]
    unacceptable_conclusions: list[str]

    expected_recommendation_type: str

    critical_issues: list[str]
```

The evaluation ground truth must remain separate from the runtime application.

---

# 7. Scenario Categories

The evaluation dataset should contain several archetypes.

## Direct Investigation

The evidence is relatively clear.

Purpose:

Test whether the system can perform basic investigation correctly.

Example:

> Is there evidence of increased bill-payment failures?

---

## Diagnostic

The PM asks why a problem may be occurring.

Example:

> Why are users abandoning transfers?

These require cross-source reasoning.

---

## Ambiguous

Multiple explanations remain plausible.

Example:

> Why are users abandoning KYC?

The system should resist premature conclusions.

---

## Contradictory

Different systems provide apparently conflicting signals.

Example:

> Customers report more failed transfers, but analytics show stable failure rates.

---

## False Lead

The most obvious interpretation is wrong.

Example:

> A large number of tickets exists, but the affected population is small.

---

## Prioritisation

The user asks which problem deserves attention.

Example:

> Which of these product problems should we prioritise?

This requires combining impact, evidence strength and business relevance.

---

## Evidence Gap

The available data is genuinely insufficient.

Example:

> What caused the decline in wallet funding?

The correct output may be:

> The available evidence does not establish a clear cause.

---

## Adversarial / Trap

The question encourages a tempting but unsupported conclusion.

Example:

> Did Provider X cause the transfer failures?

The system should not accept the premise without sufficient evidence.

---

# 8. Evaluation Split

The initial dataset should be divided into:

```text
Development set
Validation set
Final holdout set
```

Recommended starting distribution:

```text
25 scenarios → development
10 scenarios → validation
10 scenarios → holdout
```

The holdout set should not be used during prompt tuning or architecture iteration.

---

# 9. Ground Truth Design

Ground truth should not be treated as a single exact wording.

There may be multiple acceptable recommendations.

For each scenario define:

### Required observations

What the system must recognise.

### Required evidence

What evidence it must use.

### Forbidden conclusions

Conclusions that contradict the data.

### Acceptable interpretations

The range of defensible interpretations.

### Expected recommendation type

For example:

```text
prioritise
investigate_further
experiment
technical_remediation
monitor
deprioritise
```

This allows semantic evaluation rather than exact-string matching.

---

# 10. Agent-Level Evaluation

Each agent is evaluated independently before evaluating the complete workflow.

---

# 11. Planner Evaluation

The Planner is evaluated on whether it correctly determines the investigative work required.

## Metrics

### Source Selection Accuracy

Did it identify the sources needed?

```text
selected_required_sources
/
required_sources
```

### Unnecessary Source Rate

How often did it invoke sources that were not materially relevant?

### Task Decomposition Score

Human or LLM evaluation of whether the investigation tasks adequately answer the question.

### Planning Failure Rate

Percentage of scenarios where the plan makes it impossible to obtain the required evidence.

---

# 12. Research Agent Evaluation

The Research Agent should be tested against known relevant tickets.

## Metrics

### Evidence Recall

Of the required customer evidence, how much did the agent retrieve?

```text
relevant evidence retrieved
/
required relevant evidence
```

### Evidence Precision

Of the evidence retrieved, how much was actually relevant?

```text
relevant retrieved evidence
/
all evidence retrieved
```

### Attribution Accuracy

Does the finding correctly correspond to the cited ticket?

### Interpretation Accuracy

Does the agent accurately characterise what customers said?

### Overgeneralisation Rate

How often does the agent turn a small sample into a population-level claim?

---

# 13. Analytics Agent Evaluation

The Analytics Agent should be evaluated on whether it asks the right analytical question and interprets the result correctly.

## Metrics

### Query Intent Accuracy

Does the query measure the intended behaviour?

### Metric Accuracy

Does the reported metric correspond to the requested concept?

### Segmentation Accuracy

Does the agent identify relevant affected segments?

### Interpretation Accuracy

Does it correctly interpret the analytical result?

### Causal Overreach Rate

How often does it treat correlation or association as causal evidence?

---

# 14. Engineering Agent Evaluation

## Metrics

### Issue Retrieval Recall

Did it identify required Jira issues?

### Issue Retrieval Precision

How much irrelevant engineering material did it retrieve?

### Status Accuracy

Did it correctly distinguish:

- open
- in progress
- blocked
- done

### Technical Interpretation Accuracy

Did it correctly interpret the engineering context?

### Historical/Current Distinction

Did it avoid treating historical issues as active problems?

---

# 15. Evidence Groundedness

This metric applies across specialists and PM synthesis.

For every substantive claim:

> Can the claim be supported by the evidence available to the system?

Each claim can be classified as:

```text
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
CONTRADICTED
```

A weighted groundedness score can then be calculated.

Example:

```text
weighted supported claims
/
total substantive claims
```

Claims with high decision impact should receive greater weight.

---

# 16. Source Attribution Accuracy

The system should correctly map claims to sources.

Example:

> "Customers frequently report pending transfers."

must have valid Zendesk evidence.

A claim such as:

> "Transfer completion dropped 18%."

must point to a valid analytics result.

Attribution errors should count separately from general groundedness errors.

---

# 17. Cross-Source Reasoning Evaluation

This is one of the most important evaluation dimensions.

The system should be assessed on whether it correctly combines:

```text
Zendesk
+
PostHog
+
Jira
```

For each scenario define expected relationships.

Example:

```text
Zendesk:
customer complaints ↑

PostHog:
actual failure rate stable

Jira:
callback delays ↑
```

Expected interpretation:

> Customers may perceive delayed transactions as failures.

A system that independently summarises all three sources but misses this relationship should not receive a high cross-source reasoning score.

---

# 18. Contradiction Detection

The system receives explicit scenarios containing conflicting evidence.

The evaluator determines whether the final result:

1. noticed the conflict
2. represented it accurately
3. adjusted confidence appropriately
4. avoided ignoring inconvenient evidence

### Metric

```text
contradictions correctly identified
/
material contradictions present
```

---

# 19. Causal Discipline

The evaluation should specifically measure causal overreach.

Examples of problematic conclusions:

> "The Jira issue caused the decline."

when the evidence only establishes that:

> The issue and decline occurred during the same period.

Each evaluation scenario should identify whether causal language is justified.

---

# 20. Affected-User Accuracy

The system should correctly describe who is affected.

Example:

Ground truth:

> High-value transfers are disproportionately affected.

Bad output:

> All transfer users are affected.

The evaluator should compare:

- affected population
- segment
- relative impact

against ground truth.

---

# 21. Recommendation Evaluation

The PM recommendation should be evaluated independently of writing quality.

Key dimensions:

### Evidence alignment

Does the recommendation follow from the evidence?

### Decision appropriateness

Is the chosen recommendation type defensible?

### Impact consideration

Does the recommendation account for user impact?

### Evidence strength

Does the recommendation match the strength of evidence?

### Uncertainty

Does it appropriately identify what remains unknown?

### Actionability

Is the proposed next step useful?

---

# 22. Recommendation Outcome Classes

Each recommendation is classified as:

```text
CORRECT
PARTIALLY_CORRECT
UNSUPPORTED
CONTRADICTED
```

A scenario may allow multiple valid recommendations.

Therefore evaluation should use semantic criteria rather than exact text matching.

---

# 23. Critic Evaluation

The Critic should be evaluated separately.

The question is not:

> Did the critic produce a long critique?

The question is:

> **Did the critic catch the problems that matter?**

Each test scenario can contain known weaknesses.

Example:

```text
known issue:
causal overreach
```

The critic should detect it.

---

# 24. Critic Detection Metrics

### True Positive Rate

How often does the Critic catch genuine recommendation problems?

```text
true issues detected
/
true issues present
```

### False Positive Rate

How often does the Critic reject a sound recommendation?

```text
false issues
/
valid recommendation opportunities
```

### Issue Relevance

How often are critic objections materially relevant rather than stylistic?

### Required-Change Accuracy

Does the proposed correction actually address the underlying problem?

---

# 25. Revision Quality

When the Critic returns `REVISE`, the revised PM recommendation should be evaluated.

The key question:

> Did the revision actually resolve the critic's concern?

Metrics:

- critique resolution rate
- remaining unsupported claims
- remaining causal errors
- recommendation stability
- regression rate

A revision that merely changes wording should not count as successful.

---

# 26. Critic Overreach

The Critic itself can create problems.

For example:

> "We cannot conclude anything because we don't have data from every user."

That is unreasonable.

The Critic should challenge material weaknesses, not demand impossible certainty.

Therefore evaluation must penalise:

- irrelevant criticism
- impossible evidence requirements
- excessive caution
- rejection of adequately supported conclusions

---

# 27. End-to-End Evaluation

The full investigation workflow is evaluated as a product.

For each scenario:

```text
Question
 ↓
Plan
 ↓
Specialists
 ↓
Evidence synthesis
 ↓
PM
 ↓
Critic
 ↓
Revision
 ↓
Final result
```

The evaluator scores the complete result.

---

# 28. End-to-End Scorecard

Recommended dimensions:

| Dimension | Weight |
|---|---:|
| Evidence retrieval | 20% |
| Groundedness | 20% |
| Cross-source reasoning | 20% |
| Contradiction handling | 10% |
| Recommendation quality | 20% |
| Uncertainty / confidence | 10% |

Overall score:

```text
Weighted End-to-End Score
```

The weights can be adjusted after pilot evaluation.

---

# 29. Tool-Use Evaluation

Tool usage should also be evaluated.

The system should not receive full credit for an answer that happens to be correct if it used inappropriate tools or ignored necessary evidence.

Measure:

### Correct tool

Did it call the appropriate source?

### Correct arguments

Did it search/query appropriately?

### Tool efficiency

Did it use a reasonable number of calls?

### Unnecessary calls

Did it repeatedly query irrelevant sources?

### Recovery

Did it correctly handle failed tool calls?

---

# 30. Tool-Call Accuracy

Each scenario should define expected tool families.

Example:

```text
Question:
"Why are customers reporting failed transfers?"

Expected:
Zendesk
PostHog
Jira
```

A system that only queries Zendesk should lose points for incomplete investigation.

---

# 31. Efficiency Metrics

AI product quality is not only accuracy.

Record:

### Latency

- total investigation latency
- planning latency
- retrieval latency
- synthesis latency
- critic latency

### Cost

- input tokens
- output tokens
- model cost
- total cost per investigation

### Tool usage

- total calls
- calls per agent
- retries
- failed calls

### Revision count

- average revisions
- percentage requiring revision

---

# 32. Cost-Quality Tradeoff

Every architecture should be evaluated as:

```text
quality
vs
cost
vs
latency
```

A more accurate architecture that costs 5× as much may not be a better product.

Similarly, a cheap architecture that produces materially worse recommendations may not be acceptable.

---

# 33. Architecture Comparison

This is a central experiment.

We will evaluate three versions.

---

## Architecture A: Single Agent

```text id="x7cxnq"
Question
   ↓
Single Agent
   ↓
Zendesk + PostHog + Jira
   ↓
Recommendation
```

One agent receives all relevant tools.

This establishes the baseline.

---

## Architecture B: Specialist Agents

```text id="gkq8zc"
Question
   ↓
Planner
   ↓
Research + Analytics + Engineering
   ↓
PM
   ↓
Recommendation
```

No critic.

---

## Architecture C: Specialist Agents + Critic

```text id="j8p2wc"
Question
   ↓
Planner
   ↓
Research + Analytics + Engineering
   ↓
PM
   ↓
Critic
   ↓
Revision
   ↓
Recommendation
```

This is the proposed full architecture.

---

# 34. Primary Architecture Hypotheses

## H1

Specialist agents improve evidence retrieval and cross-source reasoning compared with a single agent.

## H2

Specialist tool boundaries reduce irrelevant tool usage.

## H3

The critic reduces unsupported claims and causal overreach.

## H4

The quality improvement from specialization and criticism justifies the additional cost and latency.

These hypotheses must be tested rather than assumed.

---

# 35. Controlled Comparison

All architectures should use:

- the same data
- same evaluation scenarios
- same underlying tools
- comparable model settings
- same output requirements

Only the architecture should change.

This allows meaningful comparison.

---

# 36. Experimental Matrix

Example:

| Architecture | Retrieval | Groundedness | Recommendation | Cost | Latency |
|---|---:|---:|---:|---:|---:|
| Single Agent | — | — | — | — | — |
| Specialist | — | — | — | — | — |
| Specialist + Critic | — | — | — | — | — |

The actual values will be populated after evaluation.

---

# 37. Statistical Considerations

Results should not rely on one successful or failed run.

For scenarios involving nondeterministic model behaviour:

- run multiple trials where practical
- report mean and variance
- report failure counts
- retain individual traces

For example:

```text
Architecture A
30 scenarios
3 runs each
90 total evaluations
```

This gives a more reliable comparison than one pass through the dataset.

---

# 38. Repeatability

Every evaluation run should record:

```text
dataset version
scenario version
architecture version
prompt version
model
model configuration
timestamp
run identifier
```

This allows results to be reproduced or explained later.

---

# 39. LLM-as-Judge

An LLM evaluator may be used for semantic dimensions such as:

- evidence relevance
- reasoning quality
- recommendation quality
- contradiction handling

However, LLM judging should not be the only evaluation mechanism.

---

# 40. Deterministic Evaluation

Where possible, use deterministic checks.

Examples:

### Source references

Does cited Zendesk ticket exist?

### Metric values

Does the reported number correspond to query results?

### Issue identifiers

Does Jira issue referenced by the answer exist?

### Recommendation type

Does the output match an allowed recommendation class?

### Required evidence

Were mandatory evidence items included?

### Unsupported claims

Can a claim be mapped to available evidence?

---

# 41. Hybrid Evaluation Model

The preferred evaluation architecture is:

```text
Deterministic checks
        +
Structured rule checks
        +
LLM semantic judge
        +
Human review of a sample
```

This reduces dependence on any single evaluation mechanism.

---

# 42. LLM Judge Input

The judge should receive:

```text
user question
ground truth
retrieved evidence
agent output
final recommendation
```

It should not receive hidden implementation information unless required.

---

# 43. LLM Judge Output

Use structured scoring.

Example:

```python
class JudgeResult(BaseModel):
    evidence_relevance: int
    groundedness: int
    cross_source_reasoning: int
    contradiction_handling: int
    recommendation_quality: int
    uncertainty: int
    overall: int

    errors: list[str]
    supporting_reasons: list[str]
```

Use a fixed score scale.

Recommended:

**0–4**

```text
0 = unacceptable
1 = major problems
2 = partially correct
3 = good
4 = excellent
```

---

# 44. Judge Calibration

Before relying on an LLM judge:

1. create a small set of human-reviewed examples
2. have the judge score them
3. compare judge decisions with human ratings
4. refine the rubric
5. repeat until judge behaviour is sufficiently aligned

Human review should remain the reference standard for calibration.

---

# 45. Human Evaluation

A smaller subset of scenarios should receive human review.

Recommended initial sample:

**10–15 end-to-end investigations.**

Reviewers assess:

- factual correctness
- evidence usage
- reasoning
- usefulness
- recommendation defensibility

The human sample should include difficult scenarios rather than only easy successes.

---

# 46. Error Taxonomy

Every failed evaluation should be classified.

Recommended categories:

```text
PLANNING_ERROR
TOOL_SELECTION_ERROR
TOOL_ARGUMENT_ERROR
RETRIEVAL_MISS
IRRELEVANT_RETRIEVAL
DATA_INTERPRETATION_ERROR
CROSS_SOURCE_REASONING_ERROR
CONTRADICTION_MISS
CAUSAL_OVERREACH
SEGMENTATION_ERROR
UNSUPPORTED_CLAIM
RECOMMENDATION_ERROR
CRITIC_MISS
CRITIC_FALSE_POSITIVE
REVISION_FAILURE
SYSTEM_FAILURE
```

This is important because aggregate accuracy alone will not tell us what to fix.

---

# 47. Failure Analysis Workflow

After every evaluation cycle:

```text
Failures
   ↓
Group by error type
   ↓
Identify dominant failure modes
   ↓
Determine likely cause
   ↓
Change one variable
   ↓
Re-run evaluation
```

Potential variables:

- prompt
- tool design
- schema
- routing
- model
- agent topology
- seed data
- evaluation rubric

The project should avoid changing everything at once.

---

# 48. Regression Testing

Every significant change should run the existing evaluation suite.

Examples of changes:

- prompt update
- model update
- tool schema change
- retrieval change
- new agent
- new scenario
- orchestration change

A change should not be considered successful because it improves one previously failing example.

It must be checked for regressions across the broader test set.

---

# 49. Evaluation Gates

The implementation should define quality gates.

Example initial targets:

### Core evidence retrieval

≥ 85%

### Groundedness

≥ 90%

### Cross-source reasoning

≥ 80%

### Contradiction detection

≥ 80%

### Recommendation quality

≥ 80%

### Unsupported substantive claims

≤ 5%

These are **initial engineering targets**, not claimed project results.

They may be revised after a baseline run.

---

# 50. Architecture Acceptance Threshold

The full multi-agent architecture should not automatically become the production architecture.

We need an explicit decision rule.

For example:

> Adopt the more complex architecture only if it produces a material quality improvement on high-value scenarios without an unacceptable increase in cost or latency.

A practical threshold might be defined after baseline measurement, such as:

- ≥5 percentage-point improvement in overall quality
- or ≥10 percentage-point improvement on difficult scenarios
- with cost and latency remaining within an agreed range

The exact threshold should be finalised after initial benchmarking.

---

# 51. Critic Acceptance Threshold

The Critic should remain in the final architecture only if:

```text
quality gain
>
additional cost + latency + failure complexity
```

For example, if the critic reduces unsupported claims from 12% to 4% while adding modest latency, it may be justified.

If it changes the rate from 4% to 3.5% while doubling cost, it probably is not.

---

# 52. Agent Removal Rule

The same principle applies to individual agents.

If a specialist agent contributes no meaningful improvement over a simpler architecture, it should be reconsidered.

The goal is not to maximise the agent count.

The goal is to maximise product value.

---

# 53. Evaluation Dashboard

The project should eventually provide an evaluation summary containing:

```text
Overall Quality
Evidence Retrieval
Groundedness
Cross-Source Reasoning
Contradiction Detection
Recommendation Quality
Critic Effectiveness

Average Cost
P95 Latency
Average Tool Calls
Average Revisions

Failure Distribution
Architecture Comparison
```

The dashboard may initially be a generated report rather than a sophisticated web application.

---

# 54. Traceability

For every failed scenario, we should be able to trace:

```text
Question
 ↓
Plan
 ↓
Tool calls
 ↓
Retrieved records
 ↓
Specialist output
 ↓
Synthesis
 ↓
PM recommendation
 ↓
Critic
 ↓
Final answer
 ↓
Evaluation judgment
```

This allows failures to be diagnosed rather than simply counted.

---

# 55. Evaluation Dataset Versioning

Evaluation scenarios must be versioned.

Example:

```text
evaluation_v1
evaluation_v2
```

Changes should be documented when:

- ground truth changes
- scenario data changes
- expected evidence changes
- scoring criteria change

Results should always reference the dataset version used.

---

# 56. Data Leakage Prevention

The runtime system must not receive:

- scenario IDs that expose the answer
- expected conclusions
- ground-truth labels
- hidden evaluation metadata

Evaluation information should remain outside the application.

This is especially important when testing whether the system genuinely discovers product problems.

---

# 57. Prompt Leakage Prevention

Evaluation prompts should not contain direct hints such as:

> "You should discover that delayed callbacks are causing the issue."

The agent should receive only the legitimate investigation task.

The evaluation framework knows the correct answer; the runtime system does not.

---

# 58. Evaluation of No-Evidence Scenarios

Some scenarios deliberately lack enough evidence.

The correct behaviour is:

> "The evidence is insufficient."

These scenarios are essential.

A model that always produces a confident answer may score well on superficial answer-quality evaluation while actually being unsafe for product decision support.

---

# 59. Calibration Evaluation

The system's confidence should be compared with correctness.

Example:

```text
High confidence
→ should usually be correct

Medium confidence
→ some uncertainty acceptable

Low confidence
→ should commonly occur when evidence is weak/conflicting
```

Measure whether confidence meaningfully correlates with correctness.

This helps determine whether confidence is useful to the PM.

---

# 60. Recommendation Stability

Run the same investigation multiple times where appropriate.

Measure:

> How often does the recommendation materially change?

A high-quality system should not randomly alternate between:

> Prioritise

and:

> Deprioritise

when the underlying evidence hasn't changed.

Some variation in wording is acceptable.

Material decision instability is not.

---

# 61. Investigation Efficiency

Measure whether the system can stop when it has enough evidence.

An inefficient system may:

- repeatedly search the same issue
- query irrelevant sources
- over-segment analytics
- retrieve excessive tickets
- invoke unnecessary revision cycles

Efficiency should therefore be part of evaluation.

---

# 62. Evaluation Success Definition

The evaluation strategy is successful when it allows us to answer, with evidence:

1. How accurately does the system retrieve relevant information?
2. How well does it reason over that information?
3. How often does it make unsupported claims?
4. How well does it recognise contradictions?
5. How often does the Critic improve the recommendation?
6. How much does the multi-agent architecture improve performance?
7. What does the improvement cost?
8. What are the dominant failure modes?
9. Which architecture should we actually ship?

---

# 63. Final Evaluation Decision Framework

At the end of evaluation, architecture selection should follow:

```text
                     Does it work?
                          │
                    ┌─────┴─────┐
                   NO           YES
                    │             │
                 Fix/test     Is it better
                              than baseline?
                                  │
                           ┌──────┴──────┐
                          NO             YES
                           │              │
                      Simplify       Is the gain
                                     worth the cost?
                                         │
                                  ┌──────┴──────┐
                                 NO             YES
                                  │              │
                             Use simpler     Adopt architecture
                               design
```

This prevents architecture decisions from becoming ideological.

---

# 64. Evaluation Deliverables

The implementation should ultimately produce:

### Evaluation Dataset

Structured scenarios and ground truth.

### Agent Evaluation Suite

Tests for individual specialist agents.

### End-to-End Evaluation Runner

Runs complete investigations.

### Judge

Scores semantic quality.

### Deterministic Validators

Check evidence, references and structured outputs.

### Benchmark Report

Compares architectures.

### Error Analysis Report

Documents failure modes.

### Final Architecture Decision

Explains which architecture is justified and why.

---

# 65. Evaluation Definition of Done

The evaluation system is considered complete when:

1. A versioned evaluation dataset exists.
2. Ground truth is separated from runtime data.
3. Specialist agents can be evaluated independently.
4. End-to-end investigations can be evaluated automatically.
5. Deterministic validation exists where possible.
6. LLM-as-judge evaluation uses a defined rubric.
7. Human-reviewed examples are used for judge calibration.
8. Failure categories are captured.
9. Cost and latency are recorded.
10. Single-agent and multi-agent architectures can be compared.
11. Regression evaluation can be run after changes.
12. Difficult, ambiguous and contradictory scenarios are represented.
13. No-evidence scenarios are represented.
14. Evaluation results are reproducible against a known dataset/configuration.
15. The system can generate an architecture recommendation based on measured quality/cost trade-offs.

---

# 66. Evaluation Principle

The ultimate evaluation question is not:

> "Did the AI give a good answer?"

It is:

> **"Did the system gather the right evidence, interpret it correctly, challenge its own assumptions, and produce a recommendation that a reasonable product manager could defend?"**

That is the standard the project should be built against.