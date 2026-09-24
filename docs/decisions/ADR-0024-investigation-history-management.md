# ADR-0024: User-managed investigation history

## Status

Accepted, 2026-09-22

## Context

Authenticated users need to rename and remove investigation history items. The original
product question is part of the investigation evidence and must remain immutable after a
run completes.

## Decision

Store an optional `display_name` separately from `user_query`. Rename changes only this
label. Deletion is owner-scoped, requires explicit confirmation in the interface, and is
blocked while an investigation is active. Deletion removes the investigation record,
its events, and its LangGraph checkpoint rows.

Retrying a failed investigation creates a new investigation ID using the original question
and scope. The failed run remains available until the user deletes it.

## Consequences

- Report evidence retains the exact question that produced it.
- History labels can be edited without changing completed reports.
- Destructive actions remain explicit and owner-scoped.
- Separate retry runs remain auditable and comparable.
