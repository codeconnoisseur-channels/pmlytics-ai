# PMLytics AI Product Strategy

## Purpose

This document explains the product strategy behind PMLytics AI: who it is for, which decision problem it addresses, why AI is useful, how the product could create measurable value, how it could reach users, and what might make it defensible.

PMLytics AI is the product. Pocket is the fictional fintech company represented in the synthetic demonstration data.

## Executive product thesis

Product managers are expected to make evidence-based decisions, but the evidence behind one decision often lives in several systems. Customer support describes what people say. Product analytics records what they do. Engineering tracking shows defects, incidents, constraints, and work already underway. Each source is useful, but none independently answers the product question:

> Given the evidence available now, what should the team do next?

PMLytics AI is designed to reduce the work required to investigate that question. It gathers evidence through source-specific tools, preserves provenance, reconciles disagreement, and produces a decision brief with a recommendation, confidence, success measures, risks, unresolved questions, and supporting records.

The strategic bet is not that AI should make product decisions autonomously. The bet is that a controlled AI investigation layer can help product teams reach a defensible decision faster while making the evidence and uncertainty easier to inspect.

## Product opportunity

### The current problem

A PM investigating a conversion decline, transaction failure, complaint surge, or adoption problem may need to:

1. define the behaviour and time period in PostHog;
2. search Zendesk using language that may differ from event names;
3. inspect Jira for related defects or incidents;
4. align dates, cohorts, terminology, and source limitations;
5. distinguish association from cause;
6. decide whether to fix, contain, instrument, test, or investigate further;
7. explain that decision to other stakeholders.

The cost is not only tab switching. The difficult work is determining whether records from different systems describe the same problem, whether contradictory signals can be reconciled, and whether the available evidence is strong enough to justify action.

### Why existing categories do not fully solve it

| Alternative | What it does well | Remaining gap for this job |
| --- | --- | --- |
| Product analytics dashboard | Measures known events, funnels, cohorts, and trends | Does not naturally connect behavioural change with customer language and engineering context. |
| Business intelligence | Supports governed reporting and flexible analysis | Usually requires predefined models, analyst time, and a known analytical question. |
| Search across company tools | Retrieves potentially relevant records | Does not establish whether records support the same explanation or what action follows. |
| Generic chatbot | Interprets open-ended language and produces fluent summaries | Can blend evidence and interpretation, has weak source boundaries, and may not preserve provenance. |
| Manual PM investigation | Applies context, judgement, and organisational knowledge | Is slow, difficult to reproduce, and vulnerable to confirmation bias and inconsistent evidence handling. |

PMLytics AI is positioned between retrieval and decision-making. It does not replace source systems, analytics practice, or PM judgement. It creates a controlled first-pass investigation that a PM can inspect and challenge.

## Target market hypothesis

### Primary user

**Implemented product audience:** product managers and product leads who investigate product behaviour and decide what a team should do next.

The strongest initial user profile is a PM who:

- works with support, analytics, and engineering systems;
- investigates recurring product questions rather than one-off document research;
- needs to explain decisions to engineering, support, design, data, or leadership;
- values an evidence trail rather than a conversational answer;
- can tolerate a deliberate investigation when the question has material decision value.

### Initial economic-buyer hypothesis

The likely buyer is not yet validated. Plausible buyers include:

- Head or VP of Product seeking more consistent product decisions;
- Product Operations leader standardising investigation practice;
- product or business unit leader responsible for a high-volume digital journey;
- founder or product-led organisation without dedicated analysts for every squad.

### Influencers and blockers

Adoption would also depend on:

- engineering teams responsible for source access and operational credibility;
- data teams responsible for event quality and metric definitions;
- support operations responsible for ticket taxonomy and privacy;
- security and legal teams responsible for credentials, data handling, retention, and vendors.

### Market focus

The demonstration uses fintech scenarios because payment and identity journeys create evidence across customer, behavioural, and engineering systems. The architecture is not inherently limited to fintech, but cross-industry demand has not been validated. The initial strategy should prioritise one repeatable product-investigation workflow before claiming a broad horizontal market.

## Job to be done

> When an important product question appears, help me assemble and reconcile customer, behavioural, and engineering evidence so I can make and explain a defensible next decision without manually stitching together several disconnected systems.

### Decisions the product should help with

- whether the premise of a reported problem is supported;
- which part of a journey appears most affected;
- whether customer reports and behavioural data describe the same issue;
- whether engineering context is a confirmed cause, a plausible contributor, or merely related;
- whether to prioritise remediation, improve the experience, instrument a gap, run a test, or investigate further;
- what should be measured after acting;
- what evidence would change the decision.

### Decisions outside the current scope

PMLytics AI does not currently:

- make roadmap decisions without human ownership;
- replace governed financial, risk, or regulatory analysis;
- execute production actions;
- establish causality from observational evidence alone;
- search arbitrary enterprise documents through RAG;
- retain long-term agent memory across investigations;
- support enterprise organisations, SSO, or delegated administration;
- prove market demand or willingness to pay.

## Product value proposition

PMLytics AI should create value in four ways.

### 1. Reduce investigation effort

Bring the first pass across support, analytics, and engineering into one controlled workflow.

### 2. Improve decision discipline

Separate observed facts, interpretations, and hypotheses. Require causal language and confidence to match the available evidence.

### 3. Make decisions auditable

Connect findings and recommendations to an Evidence Ledger that preserves source identity and allows deeper record inspection.

### 4. Expose uncertainty early

Identify missing sources, contradictory signals, instrumentation gaps, and unsupported premises before a team commits to the wrong remedy.

The product should be judged by whether it improves a PM's decision process, not by whether it produces an impressive volume of prose.

## Why AI is part of the solution

AI contributes where the task contains ambiguity:

- turning an open-ended question into source-specific objectives;
- recognising related customer language and engineering terminology;
- selecting relevant operations from an allowlisted tool set;
- interpreting patterns across narrative and structured evidence;
- reconciling sources that disagree or operate at different levels;
- expressing uncertainty and alternative explanations;
- synthesising a product recommendation;
- critiquing whether a candidate answer goes beyond its evidence.

Deterministic application code remains responsible for:

- identity and ownership;
- tool permissions;
- schemas and evidence identity;
- date boundaries where they can be enforced;
- budgets and loop limits;
- persistence and recovery;
- terminal investigation status;
- release gates with objective answers.

This hybrid design is a strategic choice. The product uses model judgement without treating the model as the authority for security, provenance, or workflow correctness.

## Positioning

### Positioning statement

For product managers who need to understand an important product problem across several operational systems, PMLytics AI is an evidence-driven product investigation workspace that gathers customer, behavioural, and engineering context, then produces an auditable recommendation. Unlike a dashboard, search product, or generic chatbot, it preserves provenance, separates evidence from interpretation, and can explicitly recommend further validation when the available data cannot support a stronger decision.

### What the product should be known for

- defensible recommendations rather than generic summaries;
- transparent evidence rather than hidden reasoning claims;
- useful uncertainty rather than forced confidence;
- source-specific investigation rather than unrestricted browsing;
- controlled agent behaviour rather than autonomy for its own sake.

## Product experience strategy

The core experience should remain decision-led:

```text
Question and time period
→ Visible investigation progress
→ Recommendation and confidence
→ Executive finding and affected customers
→ Key evidence and interpretation
→ Success measures, risks, and open questions
→ Deeper source-level audit when needed
```

The main brief should help a PM decide. The evidence layer should support trust and challenge without turning the primary report into a raw technical log.

The product should preserve three distinct experiences:

- **decision view:** concise enough for a PM or product lead;
- **evidence view:** detailed enough to inspect source records;
- **system trace:** detailed enough for builders and operators, but not exposed as customer report content.

## Adoption strategy

### Entry point

The recommended entry point is a recurring, high-friction investigation class rather than organisation-wide replacement of analytics or product operations.

An initial team could begin with questions such as:

- why did a core funnel deteriorate;
- what explains a complaint surge;
- is a suspected incident visible in user behaviour;
- which evidence is missing before prioritising a fix.

### Trust-building sequence

1. Start with read-only source access.
2. Let users inspect every material evidence source.
3. Compare the brief with the team's normal investigation.
4. Track whether the brief reduced investigation time or changed the decision.
5. Turn incorrect or incomplete investigations into permanent regression cases.
6. Expand usage only when retrieval reliability and decision usefulness are demonstrated.

### Activation hypothesis

A user is meaningfully activated when they complete an investigation, inspect the evidence, and report that the brief either accelerated a decision, changed a decision, or identified a missing validation step that prevented premature action.

Merely generating a report is not sufficient activation.

### Retention hypothesis

Retention should come from repeated trust in the investigation process, not novelty. A team is more likely to return when:

- source connections remain reliable;
- the product understands recurring product terminology;
- evidence is easy to verify;
- previous decisions remain available as records;
- the system is honest when it cannot support a conclusion;
- the time saved exceeds the cost and waiting time.

## Go-to-market hypothesis

The go-to-market model has not been validated. A credible sequence would be:

### Stage 1: portfolio and problem validation

- demonstrate the workflow with synthetic evidence;
- interview PMs about recent cross-source investigations;
- test whether the decision brief matches how they communicate decisions;
- identify the investigation classes with the highest frequency and cost.

### Stage 2: design-partner validation

- work with a small number of product teams;
- connect read-only, authorised data sources;
- compare PMLytics AI with the team's existing process;
- measure time, decision usefulness, retrieval failures, and trust;
- avoid broad self-serve positioning until integration and data mapping are understood.

### Stage 3: limited commercial offering

- focus on a defined customer profile and source configuration;
- provide guided onboarding and source validation;
- price around demonstrated product value and operational cost;
- add team governance only when real adoption requires it.

### Sales and adoption risks

- integration setup may be more difficult than the investigation itself;
- customers may not trust an AI-generated recommendation with sensitive product data;
- weak event or ticket taxonomy may limit output quality;
- product teams may prefer existing analysts or internal workflows;
- long investigation latency may be unacceptable for routine questions;
- a single confidently wrong recommendation may damage trust disproportionately.

## Packaging and pricing hypothesis

The landing page currently shows Starter, Team, and Enterprise packages. Those packages are product-design hypotheses, not validated commercial offers.

Potential pricing units include:

| Model | Advantage | Risk |
| --- | --- | --- |
| Per user | Familiar and predictable | Weak relationship to provider cost and team-wide value. |
| Per team | Matches collaborative product work | Requires team ownership and administration not currently implemented. |
| Investigation allowance | Connects price with usage | May discourage exploration and creates anxiety about expensive questions. |
| Platform fee plus usage | Reflects fixed integration value and variable inference cost | More complex to explain and forecast. |
| Enterprise contract | Supports governance, onboarding, and custom integrations | Requires capabilities and service commitments not currently implemented. |

Before treating any displayed price as real, the product would need evidence about:

- investigation frequency;
- value of time saved;
- acceptable latency;
- source onboarding cost;
- model and infrastructure cost at realistic usage;
- willingness to pay by buyer type;
- whether usage is individual or collaborative.

## Business outcome validation

### Strategic outcome

The product succeeds if it helps teams reach better-supported product decisions faster, not simply if it completes investigations.

### North-star candidate

> Percentage of investigations that help a product team reach a defensible decision faster than its existing process.

This is a candidate, not a validated north-star metric. It combines usefulness and speed, but it requires careful user research and baseline measurement.

### Measurement hierarchy

#### Product-value measures

- time from question to defensible decision;
- percentage of briefs that materially clarify or change a decision;
- recommendation adoption or explicit rejection with rationale;
- follow-up action completion;
- decision reversal after new evidence;
- user-reported trust and usefulness;
- repeat investigation rate;
- retention among activated teams.

#### Investigation-quality measures

- expected evidence coverage;
- false no-evidence rate;
- citation validity and relevance;
- unsupported-claim rate;
- contradiction-handling success;
- critical false-pass rate;
- percentage of outputs appropriately returning partial or investigate-further outcomes.

#### Operational measures

- completion, partial, failure, cancellation, and recovery-required rates;
- end-to-end and critical-path latency;
- model and tool calls;
- provider cost per investigation;
- source failure rate;
- retry, revision, and repair rate;
- recovery success rate.

#### Commercial measures for future validation

- source-connection completion;
- time to first useful investigation;
- pilot-to-paid conversion;
- expansion from individual to team use;
- gross margin by investigation class;
- onboarding and support cost;
- renewal and churn reasons.

### Validation approach

Business outcome validation should compare PMLytics AI with the team's existing process. A useful pilot would record:

1. the original question and its decision importance;
2. how long the normal investigation would take;
3. what sources the team would inspect;
4. the PMLytics AI brief and evidence inspected;
5. whether the brief changed, accelerated, or failed to help the decision;
6. what action followed;
7. what later evidence confirmed or overturned the decision.

The product should not claim decision improvement from report completion, citation clicks, or evaluator scores alone.

## Defensibility thesis

### What is not a moat

The following are reproducible implementation choices rather than durable defensibility:

- using LangGraph;
- connecting to popular SaaS APIs;
- having multiple agents;
- using a particular model;
- prompt wording;
- generating a decision brief.

### Potential sources of defensibility

If the product earned sustained usage, defensibility could develop through:

1. **Organisation-specific source mappings.** Reliable understanding of each customer's events, properties, ticket language, issue taxonomy, and metric definitions.
2. **A high-value evaluation library.** Real investigation failures converted into independently reviewed regression cases and release gates.
3. **Decision-to-outcome feedback.** Evidence about which recommendations were accepted, rejected, or later overturned and why.
4. **Workflow embedding.** Integration into recurring product reviews, incident learning, prioritisation, and evidence-sharing practices.
5. **Trust and governance.** Proven provenance, ownership, auditability, privacy controls, and disciplined handling of uncertainty.
6. **Question routing and economics.** Learning which questions need a full investigation and which can be answered through a cheaper deterministic or single-source path.

These are defensibility hypotheses. The current portfolio implementation does not establish a competitive moat.

## Strategic risks and responses

| Risk | Why it matters | Strategic response |
| --- | --- | --- |
| Incorrect retrieval | A well-grounded answer can still be based on the wrong packet. | Make retrieval quality a separate release gate and permanent regression layer. |
| Weak customer data | Poor tagging and instrumentation can limit the answer. | Diagnose data readiness, disclose gaps, and avoid promising certainty. |
| Trust failure | One confident unsupported decision can outweigh many useful reports. | Preserve citations, calibrate confidence, and fail visibly rather than fabricate. |
| Latency and cost | Full multi-agent investigation may be too slow for routine questions. | Route by question complexity and reserve stronger models for high-value judgement. |
| Integration burden | Source mapping may slow adoption and increase service cost. | Start with a narrow source profile and guided onboarding. |
| Incumbent response | Analytics and support vendors may add cross-source AI features. | Compete on source-neutral investigation quality, governance, and decision workflow rather than generic summarisation. |
| Security and privacy | Real support and product data may contain sensitive information. | Require least privilege, tenant isolation, minimisation, retention controls, and trace redaction before production use. |
| Unclear buyer | PM interest may not translate into budget. | Validate economic buyer, decision frequency, and measurable value before expanding packaging. |
| Over-engineering | Agent complexity may exceed the problem's value. | Retain simpler baselines and remove roles or paths that do not improve decisions. |

## Strategic roadmap

The roadmap should follow evidence, not novelty.

### Horizon 1: Make the investigation trustworthy

- complete retrieval regression coverage for the four demo scenarios;
- validate important query semantics and suspicious zero results;
- preserve current provenance, permission, and bounded-loop controls;
- run a new paid validation only after offline gates pass.

### Horizon 2: Prove user value

- interview PMs about recent investigations;
- test the brief with realistic questions and source structures;
- measure time to decision, usefulness, evidence inspection, and trust;
- identify which question classes deserve the full workflow.

### Horizon 3: Validate a design-partner operating model

- connect authorised, read-only production-shaped sources;
- establish source mapping and data-readiness checks;
- run controlled pilots with explicit release criteria;
- qualify new independent evaluation cases when a reviewer is available.

### Horizon 4: Decide whether to scale

- evaluate demand, retention, willingness to pay, onboarding cost, latency, and gross margin;
- introduce team and enterprise capabilities only when evidence supports them;
- choose whether the product remains a focused investigation layer or expands into broader product operations.

Deployment and autonomous source actions are deliberately outside this strategy phase.

## Simplify or stop criteria

The product should be simplified, repositioned, or stopped if evidence shows that:

- PMs consistently use only evidence retrieval and ignore the recommendation;
- recommendations do not change or accelerate decisions;
- a simpler search-and-summary flow performs equivalently;
- reliable retrieval requires unsustainable manual configuration;
- cost and latency exceed the value of the decisions supported;
- users cannot develop sufficient trust despite transparent evidence;
- the buyer and budget remain unclear after focused discovery;
- multi-agent complexity does not outperform a simpler controlled workflow on meaningful cases.

These criteria keep the architecture falsifiable. The product should earn its complexity.

## Current strategic position

| Question | Current answer |
| --- | --- |
| Is the product implemented? | Yes, as a working portfolio and demonstration application. |
| Is the core user problem credible? | Yes as a product hypothesis supported by the workflow design, but not yet validated through production customer research. |
| Does AI have a defined role? | Yes. Models own bounded semantic judgement while deterministic code owns hard controls. |
| Is technical feasibility demonstrated? | Partially. The end-to-end system works, but retrieval reliability remains an open gate. |
| Is product value proven? | No. Business outcome validation with real users has not been performed. |
| Is willingness to pay proven? | No. Current packages and prices are hypotheses. |
| Is a competitive moat established? | No. The document identifies a defensibility thesis, not an achieved moat. |
| Is the product production ready? | No. Production data, traffic, governance, held-out evaluation, and complete retrieval gates remain unvalidated. |

## Related documentation

- [Current state](01_CURRENT_STATE.md)
- [Architecture](02_ARCHITECTURE.md)
- [AI evaluation, failures, and learnings](03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md)
- [Decisions and evolution](04_DECISIONS_AND_EVOLUTION.md)
- [PMLytics AI Q&A](05_PMLYTICS_AI_Q_AND_A.md)
- [Portfolio case study](../PMLYTICS_AI_PORTFOLIO_CASE_STUDY.md)
