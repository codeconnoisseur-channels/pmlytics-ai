# Pocket AI Product Discovery Team
## Product Requirements Document (PRD)

**Document status:** Draft v1.0  
**Product:** Pocket AI Product Discovery Team  
**Product type:** AI-powered product discovery and decision-support system  
**Primary user:** Product managers  
**Initial fictional company:** Pocket, a Nigerian consumer fintech  
**Document owner:** Product  
**Implementation environment:** To be defined in the technical design documents

---

# 1. Product Overview

Pocket AI Product Discovery Team is an AI-powered product discovery system that helps product managers investigate product problems by gathering and synthesising evidence from multiple product systems.

The system investigates three different perspectives of a product problem:

- **Customer voice:** what customers are reporting through support conversations
- **User behaviour:** what customers are actually doing in the product
- **Engineering context:** what the engineering team knows about related technical issues

The system then produces an evidence-backed product assessment and subjects that assessment to a critical review before presenting the final recommendation.

The product is intended to support, rather than replace, product-manager judgment.

The central product hypothesis is:

> A coordinated AI workflow that combines customer feedback, behavioural analytics and engineering context can help a PM reach a more evidence-backed product decision than relying on a single source of information or a single general-purpose LLM response.

The project will also test whether the additional complexity of a multi-agent architecture is justified by measurable improvements in decision quality.

---

# 2. Background and Context

Product teams routinely have relevant information distributed across different systems.

A customer-support platform may show customers complaining about a problem. Product analytics may show a behavioural drop-off. Engineering tickets may reveal a technical issue that could explain the behaviour.

These sources often contain:

- incomplete information
- different terminology
- conflicting signals
- irrelevant information
- symptoms rather than causes
- evidence of different magnitudes of impact

A PM therefore has to perform an investigation across systems before deciding:

- whether a problem is real
- how significant it is
- who is affected
- what is likely causing it
- whether it is worth prioritising
- what additional information is needed

Pocket AI Product Discovery Team is designed to assist with this investigation.

---

# 3. Problem Statement

Product managers spend significant time manually connecting information across customer support, analytics and engineering systems when investigating product problems.

Current investigation workflows can make it difficult to:

1. identify relevant customer evidence quickly
2. quantify whether a reported problem appears in actual user behaviour
3. connect product symptoms to known engineering issues
4. distinguish correlation from plausible explanation
5. recognise contradictory evidence
6. identify gaps in the available evidence
7. turn fragmented evidence into a clear product recommendation

A system that merely summarises each data source independently would not solve this problem.

The product must instead help the PM **connect evidence, identify uncertainty and make a defensible recommendation**.

---

# 4. Product Vision

Build an AI product-discovery teammate that helps a PM move from:

> "Something seems wrong with this part of the product."

to:

> "Here is what customers are experiencing, here is what the behavioural data shows, here is what engineering knows, here is where those sources agree or disagree, here is our best-supported interpretation, and here is what we should consider doing next."

The long-term vision is a system that becomes a reliable first-pass product investigation layer for PMs.

The initial product will remain decision support. It will not autonomously make or execute production decisions.

---

# 5. Target Users

## Primary User: Product Manager

The primary user is a PM responsible for understanding product problems and deciding what deserves further investigation or prioritisation.

The PM may ask questions such as:

- Why are users abandoning transfers?
- What is driving the increase in support complaints?
- Are transfer failures a technical problem?
- Which customer problem should we prioritise?
- What evidence supports this recommendation?
- What information are we missing?

The PM needs an answer that is:

- evidence-backed
- traceable to source information
- appropriately uncertain
- useful for decision-making
- clear enough to act on

---

# 6. User Needs

The PM needs to be able to:

### Understand customer problems

See what customers are reporting, how frequently themes appear, and what specific examples support the finding.

### Understand actual product behaviour

Determine whether the behaviour described by customers is reflected in product analytics.

### Understand technical context

Determine whether engineering has identified bugs, incidents or technical conditions related to the reported problem.

### Compare evidence

Understand where the systems agree and where they disagree.

### Avoid premature conclusions

Distinguish between:

- observed facts
- interpretations
- hypotheses
- confirmed causes

### Make decisions with appropriate confidence

Receive a recommendation that explicitly communicates uncertainty and identifies unresolved questions.

---

# 7. Product Goals

## Goal 1: Reduce investigation effort

Help a PM collect relevant evidence from multiple product systems without manually performing each investigation step.

## Goal 2: Improve evidence quality

Produce recommendations grounded in identifiable customer, behavioural and engineering evidence.

## Goal 3: Surface contradictions

Prevent the system from treating one source as definitive when other sources provide conflicting evidence.

## Goal 4: Improve decision quality

Help PMs distinguish symptoms from likely causes and understand who is actually affected.

## Goal 5: Make uncertainty explicit

The system should clearly identify evidence gaps, assumptions and unresolved questions.

## Goal 6: Evaluate the value of agentic architecture

Measure whether specialist agents and a critic/revision workflow produce meaningfully better results than simpler alternatives.

---

# 8. Non-Goals

The initial product will **not**:

- autonomously modify production systems
- automatically deploy code
- automatically create or close production Jira tickets
- automatically change product roadmaps
- make final prioritisation decisions without PM oversight
- claim definitive causal inference from observational evidence
- act as a general-purpose company assistant
- use long-term personal memory about individual users
- provide voice or vision capabilities
- ingest arbitrary enterprise documents as a general RAG system
- replace product analytics, customer-support or engineering platforms
- attempt to simulate an entire fintech company

The product is a **product investigation and decision-support system**, not an autonomous product manager.

---

# 9. Product Concept

The user provides a product question.

The system investigates the question across multiple sources and produces a structured assessment.

Conceptually:

User question

↓

Investigation

↓

Customer evidence

+

Behavioural evidence

+

Engineering evidence

↓

Evidence synthesis

↓

Critical review

↓

Final product assessment

The user should be able to understand both the conclusion and the evidence behind it.

---

# 10. Core User Journey

## Step 1: Ask a product question

The PM enters a question such as:

> Why are users abandoning transfers?

The question should be expressed naturally rather than through a fixed form.

---

## Step 2: Investigation begins

The system determines which evidence is relevant.

The investigation may require:

- customer-support evidence
- product analytics
- engineering information
- segmentation or additional investigation

The system should not query every system unnecessarily when the question can be answered with less investigation.

---

## Step 3: Specialist investigations

The system investigates through specialist capabilities.

### Customer investigation

Determines:

- what customers are reporting
- recurring complaint themes
- representative examples
- affected customer types
- limitations in the support evidence

### Behavioural investigation

Determines:

- relevant user behaviour
- funnel or event changes
- affected segments
- magnitude of observed behaviour
- relevant time periods
- limitations in the analytics evidence

### Engineering investigation

Determines:

- relevant engineering issues
- incident or bug context
- issue status
- comments and technical context
- links between technical issues and the product problem

---

# 11. Evidence Synthesis

After the individual investigations, the system should combine the evidence.

The synthesis should answer:

### What is happening?

A concise description of the observed product problem.

### What evidence supports it?

Relevant evidence from customer, behavioural and engineering sources.

### Who is affected?

The users or segments for which evidence exists.

### What might explain it?

Potential causes or contributing factors, clearly separated from confirmed facts.

### Where do sources agree?

Evidence that converges across systems.

### Where do sources disagree?

Contradictions, inconsistent signals or competing explanations.

### What remains unknown?

Questions that cannot currently be answered with available evidence.

---

# 12. Product Recommendation

The system should produce a recommendation that answers:

> Given the evidence we currently have, what should the product team do next?

The recommendation may include:

- prioritise a problem
- investigate further
- run an experiment
- fix a technical issue
- improve a product flow
- collect additional evidence
- defer action because evidence is insufficient

The system should not assume that every investigation must result in "build a feature."

A valid recommendation may be:

> We do not yet have enough evidence to justify a product change.

---

# 13. Critical Review

Before a final recommendation is presented, the system should subject the proposed conclusion to critical review.

The review should test for:

- unsupported claims
- weak evidence
- causal overreach
- conflicting evidence
- missing segmentation
- alternative explanations
- overstatement of confidence
- recommendations that do not follow from the evidence

The purpose is to reduce plausible-sounding but poorly supported conclusions.

Where significant weaknesses are identified, the system should revise the assessment before returning the final result.

---

# 14. Final Output

The final investigation should use a consistent structure.

## Product Problem

What appears to be happening.

## Evidence

The strongest supporting evidence, separated by source.

## Affected Users

Who appears to be affected and what evidence supports that conclusion.

## Likely Causes

Potential explanations, clearly distinguished from established facts.

## Conflicting Evidence

Important evidence that weakens, qualifies or challenges the main conclusion.

## Recommendation

What the PM should consider doing next.

## Success Metrics

What metrics could indicate whether the recommended action worked.

## Risks

Important risks associated with the recommendation.

## Confidence

An assessment of how strongly the available evidence supports the conclusion.

## Open Questions

Information that would materially improve the decision.

---

# 15. Evidence Principles

The product must follow several core principles.

## Evidence before conclusion

The system should investigate before making a recommendation.

## Facts before interpretation

Observed data should be distinguishable from interpretation.

## Source traceability

Important claims should be traceable to their underlying source records or analytics queries.

## No false certainty

The system must not present a hypothesis as an established fact.

## Contradictions must be visible

Conflicting evidence should not be silently discarded.

## Absence of evidence is not evidence of absence

A source failing to contain evidence should not automatically be interpreted as proof that something does not exist.

## Relevance over volume

A large number of weakly relevant records should not outweigh a small amount of highly relevant evidence.

---

# 16. Initial Product Scenarios

The initial Pocket environment will contain several product situations designed to test the investigation workflow.

## Scenario A: Transfer delays

Customers report transfers remaining pending.

Behavioural data indicates degradation somewhere in the transfer journey.

Engineering records contain relevant transfer-status issues.

The system should determine whether these signals converge and what the strongest supported explanation is.

---

## Scenario B: KYC abandonment

Customers report difficulty completing verification.

Analytics show a drop-off in the KYC process.

Engineering records contain some KYC-related issues.

The system must determine whether the evidence supports a primarily technical explanation or whether alternative explanations should remain open.

---

## Scenario C: Wallet funding abandonment

Users begin funding their wallets but some fail to complete the process.

The system must investigate whether the problem appears to be technical, behavioural, pricing-related or related to another factor.

---

## Scenario D: Bill-payment abandonment

Users initiate bill payments but a proportion fail to complete them.

The system must identify the strongest evidence and determine whether the issue is significant enough to warrant further action.

---

# 17. Deliberate Ambiguity

The product must be tested against scenarios where the answer is **not obvious**.

Examples include:

- customers using "failed" to describe transactions that are merely delayed
- high ticket volume but low overall user impact
- a large analytics drop that has no corresponding engineering issue
- an engineering issue that exists but affects very few users
- multiple plausible causes
- a problem concentrated in a specific segment rather than the entire user base

This is a core product requirement.

The system should not succeed simply by finding matching keywords across systems.

---

# 18. User Experience Requirements

The user experience should make the investigation understandable.

The PM should be able to see:

### Investigation status

Which areas have been investigated and whether additional investigation was required.

### Evidence

The important findings discovered by the system.

### Source attribution

Where findings came from.

### Conflicting signals

Evidence that challenges the leading interpretation.

### Recommendation

The resulting product assessment.

### Confidence and uncertainty

How strong the evidence is and what remains unresolved.

The interface should prioritise clarity over visual complexity.

---

# 19. Transparency Requirements

The system should expose enough information for the PM to understand how a recommendation was formed without requiring the PM to inspect internal model reasoning.

The product should show:

- tools or data sources consulted
- key evidence retrieved
- relevant source identifiers
- analytics queries or metric definitions where appropriate
- important assumptions
- critic feedback that materially changed the conclusion
- unresolved evidence gaps

The system should **not** expose private chain-of-thought reasoning.

Instead, it should provide concise, auditable evidence and rationale.

---

# 20. Human-in-the-Loop Requirements

The PM remains the decision-maker.

The system should therefore support human review of:

- evidence
- recommendation
- confidence
- open questions

The initial version does not require a mandatory approval workflow for every investigation.

However, the product architecture should allow a future workflow in which a recommendation requires explicit PM approval before being used to trigger downstream actions.

---

# 21. Functional Requirements

## FR-01: Submit investigation

The user must be able to submit a natural-language product question.

## FR-02: Plan investigation

The system must determine which evidence sources and investigative steps are relevant.

## FR-03: Retrieve customer evidence

The system must retrieve relevant customer-support records.

## FR-04: Retrieve behavioural evidence

The system must retrieve relevant product analytics.

## FR-05: Retrieve engineering evidence

The system must retrieve relevant engineering issues and context.

## FR-06: Combine evidence

The system must synthesise findings from multiple sources.

## FR-07: Identify contradictions

The system must identify important conflicts between evidence sources.

## FR-08: Produce recommendation

The system must produce a structured product recommendation.

## FR-09: Critically review recommendation

The system must review the recommendation for unsupported or weakly supported conclusions.

## FR-10: Revise when necessary

The system must be able to revise a recommendation when critical review identifies material weaknesses.

## FR-11: Communicate uncertainty

The system must expose confidence, limitations and open questions.

## FR-12: Provide traceable evidence

Important claims must be traceable to supporting evidence.

---

# 22. Quality Requirements

A successful system must be evaluated on more than whether the final response sounds convincing.

Evaluation should cover:

### Evidence retrieval

Did the system find the information necessary to answer the question?

### Tool selection

Did the system use appropriate sources and tools?

### Groundedness

Are conclusions supported by retrieved evidence?

### Cross-source reasoning

Did the system correctly connect evidence from different systems?

### Contradiction handling

Did the system notice important conflicting evidence?

### Recommendation quality

Does the recommendation follow reasonably from the evidence?

### Critic effectiveness

Does critical review identify genuine weaknesses rather than producing generic objections?

### Efficiency

How much time, model usage and cost are required to produce a useful investigation?

---

# 23. Success Metrics

Initial success should be assessed through a controlled evaluation set rather than subjective impressions alone.

The project should establish baseline measurements for:

- investigation success rate
- evidence retrieval accuracy
- tool-call accuracy
- groundedness
- recommendation correctness
- contradiction detection
- critic detection rate
- unsupported-claim rate
- average investigation cost
- average investigation latency

The project should also compare alternative architectures.

At minimum:

### Baseline A

Single general-purpose agent with access to all relevant tools.

### Baseline B

Specialist investigation agents + synthesis.

### Baseline C

Specialist agents + synthesis + critic/revision.

The product should not assume that the most complex architecture is automatically the best one.

---

# 24. Product Hypotheses

## Hypothesis 1

Specialist agents with constrained tool access will produce more reliable source-specific findings than a single agent operating across all systems.

## Hypothesis 2

Combining customer, behavioural and engineering evidence will produce better product recommendations than relying on a single source.

## Hypothesis 3

A dedicated critic/revision step will reduce unsupported conclusions and causal overreach.

## Hypothesis 4

The quality improvement from additional agents will be large enough in important scenarios to justify their additional latency and model cost.

## Hypothesis 5

Structured evidence and recommendations will make the system easier to evaluate and debug than unconstrained natural-language agent outputs.

These hypotheses will be tested during implementation and evaluation.

---

# 25. Constraints

The initial system will operate within a controlled fictional environment.

The system will use:

- a mock customer-support environment
- a mock engineering environment
- a real product-analytics service containing seeded fictional data

The underlying fictional data must be coherent across systems.

For example, a product issue represented in customer support should have the possibility of corresponding behavioural or engineering evidence, but the systems should not be artificially identical.

The dataset must contain both relevant information and realistic noise.

---

# 26. Data Requirements

The product environment should contain:

### Customer-support records

Examples:

- customer complaints
- questions
- incident reports
- normal support requests
- ticket metadata
- conversation history

### Engineering records

Examples:

- bugs
- incidents
- improvement tickets
- issue status
- comments
- linked issues

### Product analytics

Examples:

- user events
- conversion steps
- drop-offs
- transaction outcomes
- relevant user and transaction properties
- temporal patterns
- meaningful segments

The initial environment should contain enough background data that the system must investigate rather than simply search for a pre-labelled answer.

---

# 27. Data Integrity Requirements

The seeded environment must preserve realistic relationships between systems.

For example:

A support complaint about transfer delays may correspond to:

- a measurable behavioural change
- an engineering issue
- a particular time period
- a specific user segment

However, not every complaint must have a corresponding engineering issue.

Not every engineering issue must produce a measurable customer impact.

Not every analytics anomaly must generate support complaints.

This asymmetry is intentional.

It allows the system to reason about evidence instead of performing record matching.

---

# 28. Security and Credential Requirements

Credentials used to access external services must:

- be stored outside source code
- use environment variables or an equivalent secure configuration mechanism
- never be included in evaluation data
- never be committed to version control

The system should use the minimum external permissions necessary for its function.

The product must not expose credentials to end users or model output.

---

# 29. Operational Boundaries

The agents will initially have **read-oriented product investigation capabilities**.

They may retrieve and analyse information.

They should not autonomously perform consequential write actions in production systems.

This boundary is intentional.

The project is evaluating AI decision support before autonomous execution.

---

# 30. Definition of Product Success

The MVP is successful when a PM can provide a product question and receive an investigation that:

1. examines the relevant evidence sources
2. retrieves meaningful evidence
3. distinguishes evidence from inference
4. connects information across sources
5. identifies important contradictions
6. avoids unsupported certainty
7. produces a defensible recommendation
8. identifies remaining evidence gaps
9. provides traceable support for important claims
10. performs measurably better than an appropriate baseline on the evaluation set, or clearly demonstrates where the added complexity does not provide sufficient benefit

The final criterion is important.

A successful product outcome does not require proving that a multi-agent architecture always wins.

A valid outcome may be:

> The multi-agent architecture materially improves specific high-value investigation tasks but is unnecessary for simpler questions.

That finding would still be useful and product-relevant.

---

# 31. MVP Scope

The MVP consists of:

### Product

A PM-facing product investigation workflow.

### Data sources

Customer support, product analytics and engineering systems.

### AI capabilities

- investigation planning
- specialist investigation
- evidence synthesis
- recommendation generation
- critical review
- bounded revision

### Evaluation

A controlled evaluation dataset comparing multiple architectural approaches.

### Observability

Basic tracing, model usage, latency, tool usage and cost measurement.

### Interface

A lightweight interface suitable for demonstration and evaluation.

---

# 32. Out of Scope for MVP

The following are deliberately deferred:

- autonomous execution of product decisions
- automatic Jira ticket creation
- automatic roadmap updates
- complex enterprise permissions
- multi-user collaboration
- long-term memory
- generic document RAG
- voice interface
- mobile application
- complex visual analytics dashboards
- production-scale infrastructure
- arbitrary external data connectors

---

# 33. Product Risks

## Risk 1: The system becomes a search-and-summarise tool

If each agent simply retrieves records and summarises them, the product will not demonstrate meaningful product reasoning.

**Mitigation:** Design evaluations around ambiguity, conflicting evidence and decision quality.

## Risk 2: Multi-agent complexity adds cost without meaningful benefit

Multiple agents may produce more latency and model calls without better outcomes.

**Mitigation:** Compare against simpler baselines.

## Risk 3: Synthetic data is too clean

If all signals are perfectly aligned, the system will appear more capable than it really is.

**Mitigation:** Include noise, irrelevant records, ambiguous language and contradictory evidence.

## Risk 4: Agents overstate causality

A correlation between a metric and an engineering issue does not prove that the issue caused the metric change.

**Mitigation:** Explicitly separate observations, hypotheses and conclusions.

## Risk 5: The output is persuasive but unsupported

A fluent recommendation may appear correct despite weak evidence.

**Mitigation:** Require traceable evidence and dedicated critical review.

## Risk 6: The project becomes an engineering demo rather than an AI product

The system could accumulate infrastructure without producing a meaningful PM workflow.

**Mitigation:** Keep the user problem and evaluation criteria as the primary design anchors.

---

# 34. Future Opportunities

Potential future capabilities include:

- historical investigation tracking
- comparison of product problems over time
- PM approval workflows
- experiment recommendation
- automatic creation of draft Jira tickets
- product opportunity scoring
- Slack or collaboration-tool integration
- broader product-system integrations
- recurring product health investigations
- human feedback loops for improving recommendations

These are intentionally excluded from the MVP.

---

# 35. Final Product Principle

The system should behave less like:

> "An AI that knows everything about the company."

and more like:

> "A disciplined product investigation team that gathers evidence, challenges assumptions and helps a PM make a better-informed decision."

That distinction defines the product.

---

# 36. Next Documents Derived From This PRD

This PRD is the source of truth for the product requirements.

The next project documents should translate these requirements into implementation detail:

1. **Product Specification**
   - detailed user experience
   - screens/states
   - workflows
   - output structures
   - acceptance criteria

2. **System Architecture**
   - application architecture
   - LangGraph workflow
   - components
   - state management
   - service boundaries
   - model/runtime design

3. **Agent Specification**
   - agent roles
   - responsibilities
   - tool permissions
   - inputs/outputs
   - instructions
   - failure handling
   - handoff rules

4. **Data & API Specification**
   - Pocket data model
   - Zendesk mock API contract
   - Jira mock API contract
   - PostHog integration
   - seed-data relationships

5. **Evaluation Strategy**
   - evaluation scenarios
   - ground truth
   - metrics
   - baselines
   - scoring methodology

6. **Implementation Plan**
   - development phases
   - tasks
   - dependencies
   - acceptance criteria
   - testing requirements
   - definition of done

7. **Architecture Decision Records**
   - important implementation decisions
   - alternatives considered
   - rationale
   - consequences

These documents should be produced before implementation begins so that the Antigravity workspace receives a coherent specification rather than a collection of disconnected prompts.