# Human Review Bundle

`human_review_form.csv` is the committed blank template. Do not fill it directly.

Create a personal working copy first:

```powershell
.\.venv\Scripts\python.exe -m evaluations.calibration.offline_cli start-human-review --reviewer-id project_author --reviewer-type author
```

This creates `evaluations/reviews/workspace/human_review_project_author.csv`. Open that file in Excel and save your answers normally. The entire workspace folder is Git-ignored, so your edits do not change the committed template or appear in `git status`.

Use [`review_packets.json`](review_packets.json) to inspect the candidate answer and supplied evidence for each matching `review_case_id`. The packets use neutral IDs and do not contain the expected verdict or internal case rationale.

## Fields to fill

- `reviewer_id`: use your name or a stable reviewer pseudonym.
- `reviewer_attestation`: enter `author_human_review` if you built or previously reviewed the system. Enter `independent_human_review` only if you are an outside reviewer who made the judgment without seeing an expected answer.
- `reviewed_at_utc`: ISO 8601 time, for example `2026-09-29T14:30:00Z`.
- `verdict`: `PASS`, `FAIL`, `UNCLEAR`, or `NOT_APPLICABLE`.
- `severity`: use `none` for `PASS`; use `minor`, `major`, or `critical` for `FAIL`.
- `reason`: explain the decision in one or two concrete sentences.
- `claim_reference`: optionally quote or identify the relevant claim.
- `evidence_references`: optionally list evidence IDs separated by semicolons.

Do not edit the case ID, packet hash, criterion, dimension, question, or pass/fail definitions.

Your working copy can be validated offline after completion:

```powershell
.\.venv\Scripts\python.exe -m evaluations.calibration.offline_cli validate-human-review evaluations/reviews/workspace/human_review_project_author.csv
```

Validation makes no provider or LLM calls.

An author review is useful for improving the rubric and finding judge disagreements, but it does not qualify a case for the held-out reference set. Held-out qualification requires independent review and adjudication.
