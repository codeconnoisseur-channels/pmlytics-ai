# ADR-0020: Nested evidence audit records

## Status

Accepted — 2026-09-21

## Context

The decision brief intentionally presents one concise evidence summary per source so
product managers can understand the recommendation without reading operational data.
Those summaries are sufficient for the main report but not for a reviewer who needs to
trace a conclusion back to the customer conversations, engineering work items, or
aggregated product measurements that support it.

Flattening every underlying record into the report would create a noisy issue log. A
second investigation or an additional model call would waste time and inference credit,
while exposing raw event-level PostHog data would add privacy and usability risk.

## Decision

1. Keep the report's canonical evidence ledger at one source summary per relevant source.
2. Add an optional, backward-compatible `supporting_records` collection to each evidence
   summary returned by the investigation result API.
3. Project these records from the typed payload already retained in the authoritative
   evidence ledger. This projection performs no new external request and no LLM call.
4. Present the records only in the Evidence Ledger drawer, behind an explicit expand
   action. Search covers both source summaries and their supporting records.
5. Zendesk projections may include customer conversations and public comments. Jira
   projections may include issues and issue comments. PostHog projections contain only
   aggregated metric rows; individual user events are not exposed.
6. Remove requester IDs, distinct IDs, transaction IDs, failure codes, raw query syntax,
   transport errors, and prompt-like implementation detail from the customer-facing
   projection.
7. Bound the projection to 20 support or engineering records and 12 analytics rows per
   source summary.
8. Supporting records remain read-only and retain a customer-safe source reference,
   title, excerpt, status, timestamp, and small set of useful display attributes.

## Consequences

- The main report remains concise while reviewers gain a deeper, attributable audit path.
- Existing clients remain compatible because `supporting_records` defaults to an empty
  collection.
- Historical investigations whose persisted typed payloads contain record detail gain the
  audit view without rerunning the investigation; payloads that contain only a summary
  honestly show that no additional records were returned.
- The drawer is not a replacement Zendesk, Jira, or PostHog interface. It exposes the
  bounded evidence needed to assess a product decision.
- Agent topology, tool permissions, orchestration, source systems, and model behavior are
  unchanged.
