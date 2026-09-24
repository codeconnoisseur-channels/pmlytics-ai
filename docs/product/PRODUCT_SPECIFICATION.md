# Pocket AI Product Discovery Team
## Product Specification

**Version:** 1.0  
**Status:** Draft  
**Related PRD:** Pocket AI Product Discovery Team PRD v1.0  
**Primary User:** Product Manager  
**Product Type:** AI-powered product investigation and decision-support application

---

# 1. Purpose

This specification translates the Product Requirements Document into a concrete product experience.

It defines:

- how a PM interacts with the system
- what happens after a question is submitted
- what the system investigates
- how evidence is presented
- how recommendations are challenged
- how failures and uncertainty are communicated
- what constitutes acceptable behaviour for the MVP

This document does **not** define the implementation technology in detail. LangGraph, Python, model providers, API implementation and infrastructure decisions belong in the System Architecture and Agent Specification documents.

---

# 2. Product Experience

The product is an investigation workspace.

The core interaction is:

```text
Ask a product question
        ↓
Investigation is planned
        ↓
Evidence is collected
        ↓
Evidence is synthesised
        ↓
Recommendation is challenged
        ↓
Recommendation is revised when necessary
        ↓
Final investigation is presented
```

The product should feel like the PM has delegated the first-pass investigation to a small product team.

It should **not** feel like a generic chatbot answering from memory.

---

# 3. Primary User Journey

## 3.1 Enter Investigation

The user opens the application and sees an investigation prompt.

Example:

> What would you like to investigate?

The PM enters:

> Why are users abandoning transfers?

The PM submits the investigation.

### Acceptance criteria

- The system accepts natural-language questions.
- The question does not need to follow a predefined template.
- Empty submissions are rejected.
- The system displays that the investigation has started.
- The submitted question becomes the immutable question for that investigation run.

---

# 4. Investigation Lifecycle

Every investigation moves through explicit states.

```text
DRAFT
  ↓
SUBMITTED
  ↓
PLANNING
  ↓
INVESTIGATING
  ↓
SYNTHESISING
  ↓
CRITIQUING
  ↓
REVISING (if necessary)
  ↓
COMPLETED
```

Failure states may occur from any active stage:

```text
FAILED
CANCELLED
```

---

# 5. State Definitions

## DRAFT

The user has entered a question but has not submitted it.

### Behaviour

The user may edit the question.

No agents or external tools should run.

---

## SUBMITTED

The investigation has been accepted for processing.

### Behaviour

The system creates an investigation ID and starts processing.

---

## PLANNING

The system determines what evidence is required.

The planning step should identify likely investigation areas such as:

- customer feedback
- product behaviour
- engineering context

It may also determine that a narrower investigation is sufficient.

### Example

Question:

> Are users abandoning transfers because of technical failures?

Potential investigation plan:

```text
Customer evidence
Behavioural evidence
Engineering evidence
Transaction failure segmentation
```

The plan should be driven by the question rather than always invoking every possible source.

---

## INVESTIGATING

The system executes the investigation plan.

The user should see progress at a high level.

Example:

```text
Investigation

✓ Investigation plan created
✓ Customer evidence collected
⟳ Analysing product behaviour
○ Checking engineering context
```

The UI should communicate meaningful progress without exposing internal model reasoning.

---

## SYNTHESISING

The system combines findings from the specialist investigations.

The synthesis should identify:

- major findings
- supporting evidence
- affected users
- relationships between findings
- potential explanations
- contradictions
- evidence gaps

---

## CRITIQUING

The proposed recommendation is reviewed.

The critical review should determine whether the recommendation:

- is adequately supported
- overstates the evidence
- ignores contradictory evidence
- confuses correlation with causation
- misses relevant segmentation
- recommends action unsupported by the evidence

---

## REVISING

Revision occurs only when the critic identifies a material issue.

The system should return to synthesis/recommendation generation rather than restarting the entire investigation unnecessarily.

A bounded number of revision cycles must be enforced.

MVP default:

**Maximum: 2 revisions.**

---

## COMPLETED

The system has produced a final investigation.

The user sees:

- conclusion
- evidence
- contradictions
- recommendation
- confidence
- open questions

---

## FAILED

The investigation could not be completed reliably.

Possible causes include:

- external service failure
- invalid analytics query
- tool timeout
- malformed tool response
- unrecoverable agent error

The system should explain the failure at a useful product level and identify which part of the investigation could not be completed.

---

# 6. Investigation Planning Behaviour

The system should determine what evidence is necessary before querying external systems.

The planner should consider:

### Question type

Examples:

- diagnostic question
- prioritisation question
- behavioural question
- customer-problem question
- technical-problem question

### Evidence requirements

For example:

> "What are customers complaining about?"

may primarily require customer-support evidence.

Whereas:

> "Are transfer failures causing users to abandon transfers?"

requires multiple sources.

### Investigation scope

The system should avoid unnecessary calls when they would not materially improve the answer.

---

# 7. Specialist Investigation Behaviour

Each specialist should have a clearly bounded responsibility.

## Customer Investigation

The system investigates customer-support evidence.

### Questions it should answer

- What are customers reporting?
- What themes recur?
- How common does the theme appear within the retrieved sample?
- What examples directly support the finding?
- What types of users appear affected?
- Are customers describing symptoms, causes or both?

### Output

```text
Customer Findings

Finding
Supporting tickets
Observed pattern
Affected users
Limitations
Open questions
Confidence
```

---

## Behavioural Investigation

The system investigates product analytics.

### Questions it should answer

- Where does the relevant user journey break down?
- How large is the drop-off?
- When does the problem occur?
- Which segments are affected?
- Has the behaviour changed over time?
- Do the analytics support the customer narrative?

### Output

```text
Behavioural Findings

Finding
Metric
Observed value
Comparison
Segment
Time period
Interpretation
Limitations
Confidence
```

The system should distinguish between:

**metric observation**

and

**interpretation of the metric.**

---

## Engineering Investigation

The system investigates engineering records.

### Questions it should answer

- Are there relevant bugs or incidents?
- Are they open or resolved?
- Do issue comments provide additional context?
- Are multiple issues connected?
- Does engineering evidence support or contradict other findings?

### Output

```text
Engineering Findings

Issue
Status
Relevant evidence
Technical context
Relationship to product problem
Limitations
Confidence
```

---

# 8. Evidence Model

All specialist findings must use an evidence-oriented structure.

Each finding should contain:

```text
source_type
source_reference
finding
support
interpretation
confidence
limitations
```

### Source types

```text
zendesk
posthog
jira
```

### Example

```text
Source:
Zendesk

Reference:
Ticket #1047

Finding:
Customer reports that a transfer remained pending.

Interpretation:
This supports the existence of transfer-status complaints.

Confidence:
High
```

The system should not turn this into:

> "The transfer failed."

unless the evidence actually establishes that.

---

# 9. Evidence Hierarchy

The product should distinguish three categories.

## Observed

Directly supported by source data.

Example:

> 17 tickets mention transfers remaining pending.

## Inferred

A reasonable interpretation of observed evidence.

Example:

> Customers may be experiencing uncertainty about transfer status.

## Hypothesised

A possible explanation that requires further validation.

Example:

> Delayed provider callbacks may be contributing to the status issue.

These categories should remain conceptually distinct throughout the investigation.

---

# 10. Cross-Source Synthesis

The most important product behaviour is combining evidence rather than simply displaying three separate summaries.

The synthesis should classify findings into:

### Converging evidence

Multiple independent sources support the same conclusion.

Example:

```text
Zendesk:
Customers report pending transfers.

PostHog:
Drop-off occurs after transfer submission.

Jira:
Open issue regarding delayed transfer callbacks.
```

### Partial support

Some evidence supports a conclusion but important information is missing.

### Contradictory evidence

Different sources point toward different interpretations.

Example:

```text
Zendesk:
Users describe transfers as failed.

PostHog:
Actual failure rate is stable.
```

### Unresolved

Available evidence does not support a confident conclusion.

---

# 11. Affected User Analysis

The product should avoid describing a problem as universal when the evidence indicates concentration in a particular segment.

Where data supports it, the system should consider:

- transaction size
- bank
- app version
- user cohort
- transaction type
- time period
- user lifecycle stage

The system should explicitly distinguish:

> "Users are affected"

from:

> "A subset of users appears disproportionately affected."

---

# 12. Root Cause Handling

The product must not claim that an issue is the cause of a metric movement merely because the two appear together.

The output should use language appropriate to the evidence.

### Strong evidence

> Engineering evidence directly identifies delayed callbacks affecting the relevant flow.

### Moderate evidence

> Delayed callbacks are a plausible contributor to the observed status problem.

### Weak evidence

> The available data does not establish a clear cause.

The system should not produce definitive causal language unless the evidence justifies it.

---

# 13. PM Synthesis

The PM synthesis transforms evidence into a product assessment.

The PM synthesis must answer:

### Problem

What product problem appears to exist?

### Impact

How significant does the problem appear to be?

### Affected users

Who appears to be affected?

### Causes

What explanations are supported or plausible?

### Evidence quality

How strong is the evidence?

### Recommendation

What should the product team do next?

### Metrics

How should the recommendation be evaluated?

### Risks

What could make the recommendation wrong or ineffective?

### Open questions

What information is still needed?

---

# 14. Recommendation Types

The system must be allowed to produce different kinds of recommendations.

## Prioritise

Evidence is sufficiently strong to justify treating the problem as a priority.

## Investigate further

The problem appears meaningful, but evidence is insufficient to decide what to do.

## Experiment

A product or experience hypothesis should be tested.

## Technical remediation

There is sufficient evidence that technical remediation deserves attention.

## Monitor

The signal exists but does not currently justify intervention.

## Deprioritise

Evidence does not support treating the issue as a significant current priority.

The system must not force every investigation toward a feature recommendation.

---

# 15. Critic Behaviour

The critic should evaluate the recommendation against the evidence.

It should ask:

### Evidence support

Does the evidence actually support the claim?

### Completeness

Are important sources missing?

### Causality

Is the recommendation making an unjustified causal assumption?

### Contradictions

Were contradictory signals considered?

### Segmentation

Is the problem actually concentrated in a smaller population?

### Magnitude

Is the problem significant enough to justify the proposed action?

### Alternatives

Are there competing explanations?

### Confidence

Does the stated confidence match the evidence?

---

# 16. Critic Outcomes

The critic must return one of:

```text
PASS
REVISE
```

### PASS

The recommendation is sufficiently supported.

### REVISE

The critic identifies a material weakness.

The PM synthesis must then be revised.

Minor stylistic disagreement should not trigger revision.

---

# 17. Revision Behaviour

When the critic requests revision, it must identify the reason.

Example:

```text
Issue:
The recommendation assumes that payment failures increased.

Evidence:
PostHog shows the failure rate remained stable.

Required revision:
Separate actual payment failures from delayed transaction
status experienced by customers.
```

The revised recommendation should directly address the critique.

The system must not simply regenerate the same answer with different wording.

---

# 18. Final Investigation View

The completed investigation should be organised into the following sections:

```text
Investigation
[Question]

Executive conclusion

Problem

Why it matters

Evidence

Customer evidence
Behavioural evidence
Engineering evidence

Where the evidence converges

Where the evidence conflicts

Likely explanations

Recommendation

Success metrics

Risks

Confidence

Open questions
```

---

# 19. Executive Conclusion

The first section should provide a concise decision-oriented summary.

Example:

> Transfer-status reliability appears to be a meaningful product problem. Customer complaints, behavioural drop-off and engineering records provide converging evidence of delays after transfer submission. However, the available analytics do not indicate a broad increase in actual transfer failures. The strongest next step is to address and measure status synchronisation before treating transfer failure itself as the primary problem.

This summary should not introduce claims that do not appear in the supporting evidence.

---

# 20. Evidence Presentation

Evidence should be concise.

The product should avoid displaying every retrieved record.

Instead, it should show:

- representative evidence
- material quantitative findings
- important source references
- evidence that changes the decision

The interface should make it possible to inspect supporting records where available.

---

# 21. Source References

Every important source-backed finding should identify its origin.

Examples:

```text
Zendesk ticket #1047
Zendesk ticket #1062
Jira PAY-117
PostHog query: transfer funnel, last 30 days
```

For analytics findings, the product should preserve the query or query description used to derive the metric.

---

# 22. Confidence Model

Confidence should reflect evidence quality rather than model certainty.

The MVP may use:

```text
High
Medium
Low
```

### High

Multiple independent evidence sources converge and there are few unresolved contradictions.

### Medium

Evidence supports the conclusion but gaps or contradictions remain.

### Low

Evidence is incomplete, weak or substantially conflicting.

Confidence must not be calculated solely from the language-model's subjective confidence.

The eventual technical design should define a more explicit scoring approach where practical.

---

# 23. Open Questions

The final investigation must explicitly state what remains unknown.

Examples:

- Does the problem disproportionately affect larger transfers?
- Is Provider X responsible for most affected transactions?
- Does the issue occur only on certain app versions?
- Are users abandoning because of the delay or because of a different checkout issue?

Open questions should be limited to questions that could materially change the decision.

---

# 24. Error Handling

## External source unavailable

The system should state:

> Customer-support data could not be retrieved, so the investigation is incomplete.

It should not invent customer findings.

## Analytics query failure

The system should identify that behavioural evidence could not be established.

## No relevant evidence

The system should say:

> No strong supporting evidence was found in the available sources.

It should not interpret this as proof that the problem does not exist.

## Partial investigation

If one source is unavailable but the remaining sources provide useful evidence, the system may continue with a clearly stated limitation.

---

# 25. No-Evidence Behaviour

When evidence is insufficient, the expected product behaviour is:

> "There is not enough evidence to support a confident recommendation."

The system should then state:

- what was investigated
- what was found
- what could not be established
- what additional information would be useful

This is a successful outcome, not a failure, when evidence genuinely does not support a conclusion.

---

# 26. Unrelated Question Behaviour

The product is intended for product investigation.

For questions unrelated to the available product environment, the system should clearly state that the question is outside its intended scope.

Example:

> "What is the weather in Lagos?"

The system should not attempt to answer using Pocket's product data.

---

# 27. Investigation Progress UI

The interface should communicate progress without exposing internal reasoning.

Recommended representation:

```text
Investigation in progress

✓ Understanding the question
✓ Reviewing customer feedback
⟳ Analysing user behaviour
○ Reviewing engineering context
○ Synthesising evidence
○ Critiquing recommendation
```

The UI should not display:

- chain-of-thought
- hidden model reasoning
- internal system prompts
- private agent deliberation

---

# 28. Investigation History

MVP should support viewing completed investigations during the current application session.

A history item should contain:

```text
Investigation ID
Question
Date/time
Status
Final recommendation
Confidence
```

Long-term persistent memory is not required for MVP.

Historical investigations are stored as product records, not as agent "memory."

---

# 29. Re-running an Investigation

The PM should be able to run the same question again.

A new investigation should receive a new investigation ID.

The system should preserve the distinction between separate runs so changes in evidence or model behaviour can be evaluated.

This is especially important for evaluation and benchmarking.

---

# 30. Investigation Detail

Each investigation should have a stable internal representation containing:

```text
investigation_id
user_question
status
investigation_plan
customer_findings
analytics_findings
engineering_findings
synthesis
critic_reviews
revisions
final_recommendation
confidence
open_questions
timestamps
```

The exact storage representation belongs to the technical design.

---

# 31. Acceptance Criteria for the Core Workflow

The MVP core workflow is considered complete when:

### AC-01

A PM can submit a natural-language product question.

### AC-02

The system generates an investigation plan appropriate to the question.

### AC-03

The system can obtain customer evidence when customer evidence is relevant.

### AC-04

The system can obtain behavioural evidence when behavioural evidence is relevant.

### AC-05

The system can obtain engineering evidence when engineering evidence is relevant.

### AC-06

Specialist outputs remain attributable to their source.

### AC-07

The system combines findings across sources rather than producing three unrelated summaries.

### AC-08

The system distinguishes observed facts from inferred explanations.

### AC-09

The system identifies material contradictions.

### AC-10

The PM synthesis produces a structured recommendation.

### AC-11

The critic can reject an inadequately supported recommendation.

### AC-12

The PM synthesis can revise a recommendation in response to substantive criticism.

### AC-13

The final result contains source-backed evidence.

### AC-14

The final result communicates confidence and open questions.

### AC-15

The system does not invent evidence when a source is unavailable or contains no relevant information.

### AC-16

The system terminates after a bounded number of revision cycles.

---

# 32. Product Quality Acceptance Criteria

A technically functioning system is not sufficient.

The investigation must also satisfy quality expectations.

### Evidence quality

Important conclusions should be supported by relevant evidence.

### Relevance

The system should avoid filling the report with unrelated records.

### Reasoning quality

Conclusions should follow reasonably from the evidence presented.

### Contradiction awareness

Material counter-evidence should not be omitted.

### Uncertainty

The system should avoid unjustified certainty.

### Actionability

The recommendation should provide a meaningful next step.

### Traceability

A reviewer should be able to identify the evidence underlying an important claim.

---

# 33. MVP Interface

The MVP interface can consist of three main views.

## View 1: Investigation Home

Contains:

- product name
- investigation prompt
- recent investigations
- submit action

Example:

```text
Pocket Product Intelligence

Investigate a product problem

[ Why are users abandoning transfers?              ]

                    [ Investigate ]
```

---

## View 2: Investigation Progress

Contains:

- question
- investigation status
- progress by evidence area
- current high-level stage

---

## View 3: Investigation Result

Contains:

- executive conclusion
- evidence
- contradictions
- recommendation
- confidence
- risks
- open questions
- source references

---

# 34. Interface Principles

The UI should:

- prioritise evidence over decoration
- make the recommendation easy to find
- clearly separate evidence from interpretation
- make uncertainty visible
- make source attribution obvious
- avoid presenting agent activity as entertainment
- avoid implying that the AI is an autonomous decision-maker

The interface is a delivery mechanism for the underlying product workflow, not the primary innovation.

---

# 35. Example End-to-End Investigation

## User question

> Why are users abandoning transfers?

### Investigation plan

```text
Customer feedback
Product behaviour
Engineering context
Transfer segment analysis
```

### Customer finding

> Customers frequently report transfers remaining pending after submission.

Supporting evidence:

- Zendesk #1047
- Zendesk #1062
- Zendesk #1091

### Analytics finding

> Transfer completion is lowest after submission, with the largest drop occurring before completion.

### Engineering finding

> Jira records indicate unresolved issues involving delayed transfer-status callbacks.

### Contradictory evidence

> The actual transfer-failure rate has not increased materially, despite customers frequently describing affected transactions as "failed."

### PM recommendation

> Prioritise investigation and remediation of transfer-status synchronisation rather than treating increased payment failure as the primary problem.

### Critic

> PASS. The recommendation distinguishes customer perception from observed failure metrics and is supported by evidence across all three sources.

### Final confidence

Medium-High.

### Open question

> What proportion of delayed statuses eventually resolve successfully?

This example represents the intended product behaviour.

---

# 36. Product Boundaries

The system should operate as a decision-support layer.

It should not:

- pretend to possess information unavailable in the connected systems
- invent missing data
- silently resolve contradictory evidence
- claim certainty from weak evidence
- perform consequential actions without explicit authorisation

The PM remains accountable for the final decision.

---

# 37. Future Product Extensions

These are explicitly outside MVP but compatible with the product model:

### Investigation comparison

Compare the same problem across different dates or runs.

### PM feedback

Allow a PM to mark findings as:

- useful
- incorrect
- incomplete

### Action planning

Generate a draft experiment or Jira ticket from an approved recommendation.

### Scheduled investigations

Run recurring checks for emerging product problems.

### Additional sources

Slack, CRM, NPS, surveys, sales feedback and other product systems.

### Human approval

Require explicit PM approval before downstream actions are taken.

---

# 38. Relationship to Technical Specification

This document establishes the product contract.

The following technical documents must derive from it rather than redefine the product independently:

**System Architecture**

Defines how the required behaviour will be implemented.

**Agent Specification**

Defines each agent's exact responsibilities, tools, instructions, inputs, outputs and constraints.

**Data & API Specification**

Defines the data models and interfaces used to satisfy the investigation requirements.

**Evaluation Strategy**

Defines how product quality and architectural hypotheses will be measured.

**Implementation Plan**

Defines the order in which the product will be built and the acceptance criteria for each implementation phase.

---

# 39. Definition of Done

The Product Specification is considered implemented for MVP when the complete investigation journey works:

```text
Question
   ↓
Investigation plan
   ↓
Relevant evidence retrieval
   ↓
Specialist findings
   ↓
Cross-source synthesis
   ↓
Critic review
   ↓
Bounded revision
   ↓
Evidence-backed recommendation
   ↓
Confidence + open questions
```

and the system can demonstrate this behaviour against the defined evaluation scenarios.

---

# 40. Product Principle

The core product experience is not:

> Ask AI a question and receive a polished answer.

It is:

> Ask a product question, investigate the available evidence, challenge the interpretation, and receive a recommendation that makes clear what is known, what is inferred, what conflicts, and what remains uncertain.