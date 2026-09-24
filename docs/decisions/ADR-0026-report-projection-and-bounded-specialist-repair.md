# ADR-0026: Customer-Safe Report Projection and Bounded Specialist Repair

## Status

Accepted

## Context

Live demo investigations exposed two reliability failures.

First, the API report projection rejected an entire evidence sentence whenever
it contained an internal term or a ledger citation. Multiple distinct facts,
metrics, and risks then collapsed into repeated generic placeholders. The raw
recommendation could be materially better than the report presented to users.

Second, the Standard specialist path allowed exactly 2 model calls: one
retrieval-selection call and one structured synthesis call. A single malformed
structured response therefore discarded otherwise valid retrieved evidence and
created a deterministic fallback report. Users still paid for the failed call
but received a substantially degraded decision brief.

## Decision

1. Customer-facing report projection translates known technical terminology,
   preserves verified citations, filters internal workflow failures, removes
   duplicates, and bounds secondary lists. It no longer replaces a complete
   useful sentence merely because the sentence contains a ledger citation.
2. Standard specialists retain one retrieval batch and one normal synthesis
   call. They receive one additional synthesis-repair call only when the first
   structured result is invalid.
3. The normal-path specialist call count remains unchanged. The failure path is
   bounded at 3 calls per specialist.
4. Search-result ledger summaries retain representative ticket and issue
   content already returned by the source so synthesis does not mistake
   available evidence for unanalysed data.

## Consequences

- Paid investigations no longer degrade immediately after one repairable schema
  failure.
- Report wording remains grounded in the stored recommendation while hiding
  implementation details from the default decision view.
- The worst-case cost increases by one small-model call for each specialist that
  actually returns invalid structured output.
- The Evidence Ledger remains the deeper audit surface for source-specific and
  technical detail.

## Superseded Detail

This amends the exact 2-call specialist failure bound documented in the Phase
12A latency baseline. It does not change the normal 2-call specialist path,
agent topology, permissions, source boundaries, or read-only behavior.
