# Evaluation Case Library

This directory contains the product-owned definition of evaluation quality. Runner code lives under `evaluations/calibration/` and must not define expected product behaviour.

## Source of truth

`catalog.csv` is the editable case catalog. A product owner can add or revise a case without changing Python. Nested criteria live in the versioned rubric JSON.

The current catalog is seeded from the 15 preserved behavioural stress fixtures. These entries are labelled `predeclared_system_fixture`. They are development cases, not independent human ground truth.

The earlier Python judge cases and historical human-rating artifacts remain in place for provenance. They are not imported into this case library as qualified human labels because the Phase 9 provenance audit invalidated that claim.

## Ownership

- Product owner: AI Product Manager
- Technical maintainer: evaluation runner maintainer
- Review triggers: material product failure, model change, prompt change, evidence-contract change, tool change, report-schema change, or judge change

Every material failure must be considered for addition as a permanent case before its correction is considered complete.

## Case lifecycle

`proposed` means the case expresses a useful expected behaviour but has not completed independent human adjudication.

`reviewed` means an independent human audit exists with verified provenance.

`active` means the case is approved for the declared reference set.

`retired` and `invalidated` require a documented reason. Historical results are not rewritten when a case or rubric changes.

## Held-out policy

The held-out set is intentionally empty. Cases must not be moved into it merely to satisfy a target count. Qualification requires identical human and judge packets, blind independent human review, an adjudication record, and a content hash.

## Editing workflow

1. Add or revise a row in `catalog.csv`.
2. Keep the case ID stable after results exist.
3. Point `packet_source` to a fixed packet or preserved fixture.
4. Run the offline validator.
5. Complete independent review before changing lifecycle or reference-set membership.
6. Never describe AI-generated labels as human judgments.

## Human review

The fillable worksheet is [`../reviews/human_review/human_review_form.csv`](../reviews/human_review/human_review_form.csv). Its matching blind evidence packets are in [`../reviews/human_review/review_packets.json`](../reviews/human_review/review_packets.json). Follow the instructions in the review bundle README and do not inspect the case catalog while rating.

Author reviews are diagnostic and remain outside the qualified held-out set. Differences between a human review and the catalog are recorded under [`adjudications/`](adjudications/) before expected labels change. A disagreement is evidence that the case, severity scale, or rubric wording may be wrong; it is not automatically resolved in favour of either side.

The rubric defines explicit severity anchors. `critical_when_failed` identifies a criterion whose failure can become critical, but the concrete case still determines whether the observed impact is minor, major, or critical.

The first author-review adjudication produced `atomic_semantic_v2`. It clarified that the embedded-instruction criterion evaluates the candidate recommendation, not the human or automated reviewer. The v1 rubric remains preserved as retired history.

## Provider budget

Case validation, deterministic checks, agreement reports, and human audit records run offline. Paid judge execution is a separate opt-in action and is blocked unless live use and a maximum provider budget are both explicitly supplied.

The completed five-case paid pilot is defined in [`reference_sets/judge_pilot_v1.json`](reference_sets/judge_pilot_v1.json), with its audited result in [`reference_sets/judge_pilot_v1_result.json`](reference_sets/judge_pilot_v1_result.json). An independent product manager and the GPT-5.4 judge matched on all five verdicts and severities, with no false passes or false failures. These were development cases, so the result is an independently reviewed calibration pilot rather than a held-out benchmark.
