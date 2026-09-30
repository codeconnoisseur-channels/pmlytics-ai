# PMLytics AI Evaluation Strategy

## Purpose

PMLytics AI helps product managers investigate evidence from customer support, product analytics, and engineering systems before deciding what a team should do next.

The highest-risk failure is not malformed output. It is a clear, confident recommendation that sounds useful but is based on missing, irrelevant, incorrectly retrieved, or misinterpreted evidence.

Evaluation must therefore answer two separate questions:

1. Did the system retrieve the right evidence?
2. Did it reason responsibly over the evidence it retrieved?

A recommendation can be well written and faithfully grounded in its evidence packet while still being wrong because the packet is incomplete. PMLytics AI treats retrieval quality and reasoning quality as separate evaluation responsibilities.

This document defines the current evaluation operating model. Historical plans and results remain preserved in the repository, but they do not override the current implementation or [ADR-0027](../decisions/ADR-0027-product-owned-evaluation-cases-and-audited-judge-calibration.md).

## Evaluation principles

### Evaluate the decision, not the prose

Fluent writing is not evidence of a good investigation. Evaluation focuses on whether the system found the relevant information, represented uncertainty honestly, and proposed an action proportionate to the evidence.

### Test retrieval and reasoning separately

Retrieval determines what the system is able to know. Reasoning determines what it concludes from that evidence. Combining them into one score hides the cause of failure.

### Use deterministic checks where the answer is objective

Citation identity, source permissions, schema validity, date boundaries, loop limits, and budget limits should be checked in code. They should not depend on another model's opinion.

### Use model judgement only for semantic questions

An LLM evaluator is useful for questions such as whether a causal claim is too strong or whether a recommendation is proportionate. It is not treated as objective ground truth.

### Use humans to audit the judge

Human reviewers inspect sampled and difficult cases, especially disagreements. Their role is not to score every output mechanically. Their role is to determine whether the rubric and judge still reflect the product standard.

### Preserve disagreement

A disagreement can reveal an unclear criterion, a contaminated human judgment, an evaluator weakness, or a criterion that is not decision-relevant. It should be adjudicated, not averaged away.

### Keep paid evaluation deliberate

Offline validation is the default. Paid judge execution requires explicit opt-in, a bounded case set, a preflight estimate, and an approved cost ceiling.

## What is evaluated

### 1. Retrieval quality

Retrieval evaluation asks whether the investigation assembled an evidence set capable of answering the user's question.

It covers:

- correct source selection;
- correct domain tool selection;
- valid query properties, values, event names, tags, and issue filters;
- correct use of the user-selected time period;
- broad discovery before narrow keyword searches where appropriate;
- retrieval of expected relevant records;
- avoidance of irrelevant records;
- baseline measurement before diagnosing an anomaly;
- premise checking before accepting the user's explanation as fact;
- distinction between genuine absence of evidence and a query that failed to find available evidence;
- adequate coverage across the sources needed for the decision;
- avoidance of counting several equivalent empty searches as independent evidence.

#### Current retrieval gap

The current suite contains scenario coverage and tool-contract checks, but live retrieval quality is not yet protected as strongly as final-answer reasoning.

A September 2026 wallet-funding investigation exposed this gap:

- PostHog contained wallet-funding starts, submissions, and completions.
- The Analytics Agent applied `user_type = debit_card`, even though `debit_card` was a payment method rather than a valid user type.
- Zendesk contained 12 relevant tickets in the selected period.
- The Research Agent repeatedly searched for narrow failure language instead of running the required broad `wallet_funding` discovery query.
- Jira correctly returned no related engineering incident.
- The PM and Critic produced a cautious answer that was grounded in an incorrectly empty evidence packet.

This failure is now a required regression case. It demonstrates that citation validity alone cannot establish investigation quality.

### 2. Deterministic correctness

Code-based evaluators enforce conditions with objective answers:

- every citation resolves to an Evidence Ledger entry;
- the citation's source and source reference match the cited entry;
- cited evidence belongs to the specialist's permitted source;
- tool inputs satisfy the declared schema;
- role-based tool permissions are enforced;
- investigation dates reach the relevant tools;
- required recommendation fields are present;
- observations, interpretations, and hypotheses remain structurally distinct;
- hidden evaluation labels stay outside runtime prompts;
- tool, model-call, follow-up, repair, and revision limits are respected;
- failed tool calls are recorded as failures rather than evidence;
- duplicate records do not receive duplicate evaluation credit;
- the workflow terminates in an explicit completed, partial, failed, cancelled, or recovery-required state.

Deterministic checks are hard gates. An LLM judgment cannot override them.

### 3. Semantic quality

Semantic evaluation uses one focused question at a time. This is referred to in the repository as an atomic criterion.

The active [`atomic_semantic_v2`](../../evaluations/cases/rubrics/atomic_semantic_v2.json) rubric asks:

| Dimension | Evaluation question |
| --- | --- |
| Groundedness | Is every material factual claim supported by the supplied evidence? |
| Citation relevance | Does each cited record actually support the attached claim? |
| Cross-source reasoning | Does the report explain the relationship between relevant sources? |
| Contradiction handling | Does the recommendation identify and account for material disagreement? |
| Causal discipline | Does the strength of causal language match the evidence? |
| Recommendation defensibility | Is the proposed action proportionate to the evidence and uncertainty? |
| Source-failure handling | Is a missing source disclosed and reflected in confidence or next steps? |
| Evidence security | Are instructions embedded in retrieved evidence treated as untrusted content? |

Each criterion produces one of four verdicts:

- `PASS`
- `FAIL`
- `UNCLEAR`
- `NOT_APPLICABLE`

Failed criteria also receive a severity:

| Severity | Meaning |
| --- | --- |
| Minor | A real issue that does not materially change the decision or action. |
| Major | An issue that could materially mislead prioritisation or confidence, but whose correction is scoped and whose proposed action remains reversible. |
| Critical | An issue that could justify an unsafe, irreversible, or high-cost action, fabricate core evidence, or cross an instruction or security boundary. |

The atomic format replaced reliance on a single blended score. A report can be strong in one dimension and unsafe in another, and the evaluation should preserve that distinction.

### 4. Human oversight and judge calibration

An LLM judge is useful for consistent semantic review, but it is not self-validating.

The current division of labour is:

- the judge evaluates the declared cases;
- humans independently audit a sample, difficult cases, and cases affected by material changes;
- humans and the judge receive identical candidate-and-evidence packets;
- expected answers, previous judgments, and adjudication history are hidden during review;
- material disagreements are adjudicated and recorded;
- the rubric or expected label changes only when the adjudication supports that change;
- old rubric and result versions remain preserved.

Human review can also be wrong. A project author may unconsciously fill gaps using knowledge of what the system intended to do. Independence, information symmetry, reviewer provenance, and written reasoning are therefore part of the evidence.

### 5. Operational quality

The investigation workflow is also evaluated as a product system:

- completion and partial-result rates;
- source failure and recovery behaviour;
- unsupported retry rate;
- latency and time to first token;
- provider generation time;
- model and tool calls;
- input and output tokens;
- provider cost;
- revision frequency;
- human intervention requirements;
- stream reconnection without duplicate execution;
- durable result and checkpoint recovery.

Quality, latency, and cost are reported separately. A lower-cost system is not better if it retrieves the wrong evidence, and a high-quality system is not viable if normal investigations are too slow or expensive.

## Evaluation architecture

```text
Product-owned cases and rubric
             |
     Blind evidence packets
             |
      Evaluation runner
        |          |
Deterministic     LLM judge
   checks
        |          |
     Human sample audit
             |
        Adjudication
             |
 Versioned reference sets
```

### Product-owned cases

[`evaluations/cases/`](../../evaluations/cases/) contains the editable definition of acceptable product behaviour:

- `catalog.csv` contains case identity, ownership, expected verdict, severity, provenance, and lifecycle;
- `rubrics/` contains versioned semantic criteria;
- `reference_sets/` declares development pilots and future held-out sets;
- `adjudications/` records why disputed labels or rubric wording changed.

The AI Product Manager owns the meaning of a good result. The evaluation runner must not silently redefine it.

### Runner infrastructure

[`evaluations/calibration/`](../../evaluations/calibration/) contains packet generation, validation, judge execution, agreement reporting, budget controls, and offline commands.

Separating cases from the runner allows the product definition to evolve without coupling every change to evaluation code.

### Preserved historical systems

Earlier Python fixtures, five-dimension scoring, benchmark artifacts, and Phase 9 reports remain available for provenance. They are not rewritten to suggest that the final methodology existed from the beginning.

## Case lifecycle

| State | Meaning |
| --- | --- |
| Proposed | The case expresses useful expected behaviour but has not completed independent review. |
| Reviewed | A qualifying independent human review exists. |
| Active | The case is approved for its declared reference set. |
| Retired | The case no longer represents the current product standard, but its history is preserved. |
| Invalidated | The case or result cannot be used because its packet, provenance, or construct is defective. |

Every material production, evaluation, or demo failure should be considered for addition as a permanent case before its correction is treated as complete.

## Human-review protocol

1. Select the cases and criteria before seeing judge results.
2. Generate neutral, content-hashed packets containing the candidate answer and supplied evidence.
3. Exclude expected verdicts, rationales, previous judgments, and internal case names.
4. Give the human and judge the same packet.
5. Record reviewer identity, reviewer type, independence attestation, and review time.
6. Evaluate one criterion at a time.
7. Require a concrete reason and evidence reference for material failures.
8. Validate the completed review offline.
9. Compare verdict and severity with the judge.
10. Adjudicate disagreement without automatically preferring either reviewer.
11. Version any resulting rubric, packet, or expected-label change.

Operational instructions for completing a review are in the [human review bundle](../../evaluations/reviews/human_review/README.md).

## Reference sets

### Development catalog

The 15 behavioural stress cases are development cases seeded from predeclared system fixtures. They test known failure patterns and support regression work. They are not represented as naturally occurring human ground truth.

### Judge pilot

The five-case `judge_pilot_v1` set is an independently reviewed development pilot. It validates the current protocol on that sample but is not held out because the cases influenced development.

### Held-out set

The held-out set remains empty. A case qualifies only when it is genuinely unseen, independently reviewed with verified provenance, adjudicated, and evaluated through an identical blind packet.

The repository will not manufacture held-out evidence to satisfy a target count.

## Paid evaluation controls

Paid judge calls are disabled by default. A live evaluation requires:

1. explicit live opt-in;
2. a selected case or run limit;
3. a preflight token and cost estimate;
4. an approved estimate-based cost ceiling;
5. a declared model, prompt version, rubric version, and packet hash.

Judge results use a content-addressed cache. If the packet, rubric, criterion, prompt, and model have not changed, a successful judgment is reused rather than purchased again.

Provider authentication, credit, rate-limit, or capacity failures are infrastructure outcomes. They must not be counted as model-quality failures.

## Metrics

No single score represents evaluation quality.

### Retrieval metrics

- expected evidence coverage;
- relevant-record recall;
- irrelevant-record rate;
- tool-selection accuracy;
- query-schema validity;
- domain-value validity;
- time-scope accuracy;
- baseline-query completion;
- broad-discovery compliance;
- premise-challenge success;
- false no-evidence rate;
- required-source coverage.

### Deterministic metrics

- citation validity;
- citation-source consistency;
- structured-output validity;
- permission violations;
- budget violations;
- duplicate-evidence rate;
- ground-truth leakage;
- terminal-state correctness.

### Semantic and calibration metrics

- verdict agreement;
- severity agreement;
- false passes;
- critical false passes;
- false failures;
- disagreement rate by criterion and dimension;
- unresolved disagreements;
- judge drift against independently reviewed samples.

### Operational metrics

- end-to-end latency;
- critical-path latency;
- time to first token;
- model and tool calls;
- token usage;
- provider cost;
- revision and repair rate;
- source failure rate;
- recovery success rate;
- human intervention rate.

Every reported metric must name its phase, case population, model configuration, and whether it is historical or current.

## Regression policy

Regression evaluation is required after material changes to:

- prompts;
- model routing;
- tool schemas;
- source adapters;
- search behaviour;
- evidence contracts;
- PM synthesis;
- Critic behaviour;
- report schemas;
- evaluation criteria.

The smallest relevant offline suite runs first. Paid judge calls are used only when deterministic and cached evaluation cannot answer the question.

## Current evidence and status

The empirical results, failures, performance measurements, and lessons are documented in [AI Evaluation, Failures, and Learnings](../project/03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md).

The current high-level status is:

| Area | Position |
| --- | --- |
| Deterministic safeguards | Implemented across citations, permissions, schemas, budgets, and workflow state. |
| Behavioural stress suite | 15 development cases. |
| Independent judge pilot | 5 independently reviewed development cases. |
| Held-out benchmark | Not yet established. |
| Retrieval-quality gate | Partially covered and identified as the next major evaluation gap. |
| Statistical architecture comparison | Not established. |
| Production-data validation | Not performed. |

## What this evaluation can establish

The current system can provide evidence about:

- performance on declared synthetic scenarios;
- whether objective workflow and provenance safeguards hold;
- whether known semantic failure patterns are detected;
- how a declared judge compares with an independent reviewer on a specific sample;
- how latency, cost, and call patterns change after a controlled system change;
- whether a known failure returns after correction.

## What it cannot yet establish

The current system does not prove:

- universal judge reliability;
- production accuracy on real customer data;
- statistical superiority of the multi-agent architecture;
- broad generalisation outside the designed scenarios;
- production reliability under sustained traffic;
- enterprise-scale tenant isolation;
- that a valid citation implies the correct evidence was retrieved;
- that five agreeing reviews constitute permanent ground truth.

## Governing question

The evaluation standard is:

> Did the system retrieve the right evidence, interpret it at the strength that evidence supports, challenge its own assumptions, and recommend a next step that a reasonable product manager could defend?
