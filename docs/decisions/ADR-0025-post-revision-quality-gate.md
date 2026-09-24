# ADR-0025: Restore the Post-Revision Critic Quality Gate

## Status

Accepted

## Context

ADR-0013 optimized the Standard investigation profile by routing a PM revision
directly to finalization. This saved one Critic model call, but it created a
terminal-state defect: the finalizer evaluated the earlier `REVISE` review even
though the user-facing recommendation had since changed. A revised report could
therefore never become `completed`, and its revised claims were not semantically
reviewed by the Critic.

Deterministic schema and citation validation remains necessary, but it cannot
prove that a revision actually resolved causal overreach, confidence mismatch,
or an unsupported recommendation.

## Decision

Every PM revision returns to the Critic before finalization.

- Standard retains its single-revision limit.
- Deep retains its two-revision limit.
- A post-revision `PASS` may complete the investigation when all other finalizer
  invariants pass.
- A post-revision `REVISE` at the profile limit produces an honest `partial`
  result rather than an unreviewed success.
- Deterministic revision validation remains unchanged and fail-closed.

This supersedes only ADR-0013's Standard-profile post-revision Critic bypass.
ADR-0013's model routing, token budget, and density decisions remain accepted.

## Consequences

- A Standard investigation that requires revision uses one additional bounded
  Critic call, for up to 12 calls instead of 11.
- Reports can no longer be finalized against a review of a different candidate.
- Revision-path latency and cost increase modestly, while terminal status and
  report quality become truthful and auditable.
- Investigations that pass the first Critic review retain the existing fast path.
