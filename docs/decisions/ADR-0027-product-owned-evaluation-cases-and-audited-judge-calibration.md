# ADR-0027 Product Owned Evaluation Cases and Audited Judge Calibration

## Status

Accepted

## Context

The original evaluation implementation placed scenarios, behavioural expectations, judge fixtures, and runner logic inside Python modules. This made the suite reproducible, but made product quality definitions harder to inspect or change without editing code.

The Phase 9 calibration work also showed that human and automated judgments are not interchangeable. Some comparison packets were informationally asymmetric and a later rating artifact failed provenance review. Those artifacts cannot support a human-qualified judge claim.

Paid evaluation runs created a separate risk. A benchmark retried provider-credit failures and consumed time without producing a valid comparison. Evaluation infrastructure therefore needs to be useful offline and paid execution must require deliberate opt-in.

## Decision

1. Product-owned case definitions and rubrics live as editable data under `evaluations/cases/`.
2. Runner infrastructure lives separately under `evaluations/calibration/`.
3. Existing Python scenarios stress fixtures and historical run artifacts remain preserved. They are not rewritten as if the final methodology existed from the beginning.
4. The initial external case catalog is seeded from the 15 behavioural stress fixtures and labelled as predeclared system expectations rather than independent human ground truth.
5. The held-out reference set remains empty until genuinely unseen cases receive blind independent human review, verified provenance, identical evaluation packets, and documented adjudication.
6. Human reviewers audit sampled judge decisions and adjudicate disagreements. They do not need to assign a 0 to 4 score to every output.
7. Atomic verdicts and severity supplement the historical five-dimension ordinal scores. Deterministic checks remain hard gates.
8. Live provider evaluation is disabled by default. It requires explicit live opt-in, a selected run or case limit, a preflight estimate, and an approved estimate-based provider-cost ceiling.

## Consequences

- A product owner can revise expected behaviour without editing runner code.
- Case provenance lifecycle and ownership become inspectable.
- The project no longer needs to present invalid historical human labels as a calibration standard.
- A valid held-out result requires new cases that were not used to develop the rubric or pilot the judge, followed by independent review and adjudication.
- The repository gains more schemas validation and governance files.
- Spreadsheet synchronization remains deferred until multiple non-technical contributors need it. The versioned CSV is the current product-owned source of truth.
- The atomic judge pilot uses a content-addressed cache keyed by packet, rubric, criterion, prompt, and model so an unchanged successful judgment is not purchased twice. Historical stress-run checkpoints remain separate.
- LangSmith remains the observability system. A future trace-to-case workflow can promote sanitized failures into proposed cases without migrating platforms.

## First adjudication outcome

The first author review did not qualify held-out ground truth, but it proved useful as a rubric audit. It corrected two severity labels, reversed one predeclared contradiction-handling verdict, and exposed that the embedded-instruction question was written from the evaluator's perspective rather than the candidate's. `atomic_semantic_v2` records the clarified candidate-focused construct.

The subsequent five-case judge pilot ran only after explicit cost preflight and approval. One packet incorrectly omitted the structured source failure described by its candidate answer. The judge returned `NOT_APPLICABLE`, which exposed the fixture defect. After the packet was corrected, only that case was purchased again because the other four judgments were content-addressed cache hits. A blind independent product-manager review then matched the final GPT-5.4 verdict and severity on all five cases, with zero false passes, critical false passes, or false failures. The sample remains a development calibration pilot, not a held-out benchmark or a claim of universal judge reliability.
