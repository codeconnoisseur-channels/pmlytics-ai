# ADR-0019: Postgres-checkpointed investigation recovery

## Status

Accepted — 2026-09-20

## Context

Application records now preserve investigation history, but a running workflow is
still an in-process `asyncio` task. If that process exits, the report record can
describe the interruption but cannot reconstruct LangGraph's next executable
node. Restarting from the original question would repeat completed work and may
spend LLM credit twice.

## Decision

1. Use LangGraph's production `AsyncPostgresSaver` with the configured Supabase
   PostgreSQL database.
2. Use `investigation_id` as the LangGraph `thread_id`; checkpoint metadata also
   carries the owning user ID for operational diagnosis, never for authorization.
3. Compile the existing approved graph with the checkpointer. Agent topology,
   tool permissions, routing, and evidence contracts remain unchanged.
4. Use synchronous checkpoint durability at node boundaries. The next node is
   not allowed to begin until the previous node's state is durable.
5. On application startup, recover stale non-terminal investigations through a
   database lease. Only one process may own recovery of an investigation.
6. Resume from the latest checkpoint. Never construct a second investigation or
   reset its `created_at` timestamp.
7. If no checkpoint exists, or failure occurred inside an unresolved paid LLM
   node, mark the investigation `recovery_required` rather than automatically
   restarting the entire workflow.
8. Checkpoints are runtime execution state, not long-term agent memory. They are
   scoped to one investigation and are not injected into future investigations.

## Recovery invariants

- Completed nodes are not re-executed after process recovery.
- Recovery keeps the same investigation ID, owner, timer origin, evidence ledger,
  and event history.
- A user cancellation is terminal and must never be recovered.
- A completed or partial report is terminal and must never be recovered.
- An ambiguous in-flight paid request is not silently retried.
- Recovery failures remain explicit, customer-safe states.

## Consequences

- Add the maintained `langgraph-checkpoint-postgres` package.
- LangGraph creates and migrates its own checkpoint tables through the documented
  checkpointer setup method; Alembic continues to own application tables.
- Windows local development must start the API with a selector event loop because
  Psycopg asynchronous connections do not support the default Proactor loop.
- Recovery is in-process on application startup; no distributed queue or new
  microservice is introduced.
