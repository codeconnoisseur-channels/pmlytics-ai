# ADR-0017: Truthful investigation lifecycle and PM-selected time scope

## Status

Accepted — 2026-09-20

## Context

The workspace could display an investigation as completed when LangGraph had
actually returned a partial or failed state. This made the result endpoint fail
after the user had already been told the report was ready. Investigations also
always examined the available dataset, leaving a PM unable to state the period
they wanted analysed.

## Decision

- The LangGraph terminal state is authoritative. `completed` is only emitted
  after a report has been assembled successfully.
- A `partial` state is preserved when it contains a qualified recommendation;
  it is presented as a decision with follow-up items, never as a completed
  report.
- A terminal state without a recommendation is `failed` and exposes a
  user-safe error rather than an internal exception.
- A typed `InvestigationScope` carries a PM-selected primary time window and
  optional comparison window from the API through state, planning, specialist
  tasks, and follow-up work.
- The analytics tool boundary overrides model-proposed dates with the selected
  primary window, so a bounded analytics investigation cannot silently query
  all available data.

## Consequences

The frontend treats `partial` as terminal and report-bearing, while polling and
SSE stay consistent with the backend. The launch form offers an optional date
range. Support and engineering sources are explicitly instructed to honour the
same scope; their adapters need native date-filter support before enforcement
can be made equivalent to analytics.

## Invariants preserved

- LangGraph remains the sole orchestration layer.
- Specialist roles and their read-only tool permissions are unchanged.
- Evidence provenance and the evidence ledger remain authoritative.
- No new service, agent, memory system, RAG, or MCP capability is introduced.
