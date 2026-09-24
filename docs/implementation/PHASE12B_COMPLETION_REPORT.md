# Phase 12B completion report

## Phase

Phase 12B — Authentication, durable execution, and recovery hardening.

## Implemented

- Supabase authentication entry points on the public landing page.
- Protected investigation routes with return-path preservation.
- Sign-out in the authenticated application shell.
- Owner-scoped API access and durable investigation history.
- LangGraph `AsyncPostgresSaver` checkpoints in the configured Supabase database.
- Database leases and 30-second heartbeats for active workflow ownership.
- Startup recovery from the latest completed graph node.
- A distinct `recovery_required` state for ambiguous in-flight paid work.
- Explicit user-controlled retry of only the checkpointed step.
- Windows selector-loop API launcher required by Psycopg asynchronous connections.
- Default test isolation for live LLM and LangSmith smoke validation.

## Tests

- Backend API and orchestration gate: 27 passed.
- Recovery persistence regression gate: 6 passed.
- Frontend unit suite: 59 passed.
- Frontend type check: passed.
- Next.js production build: passed.
- Live startup: API and frontend healthy on ports 8000 and 3000.
- Supabase: application migration `0002` applied; four LangGraph checkpoint tables verified.
- Full Python suite before stale-test correction: 340 passed, 8 failed, 2 skipped.
- Final full Python suite: 347 passed, 3 skipped, 0 failed.
- Ruff on all Phase 12B files: passed.
- Mypy on the changed application/runtime files: passed.

No investigation was started as part of recovery verification. Live LLM smoke
tests now require `RUN_LIVE_LLM_TESTS=1` so routine validation cannot consume
model credit.

## Acceptance criteria

- Authentication entry and exit are clear: **PASS**.
- Investigation history is owner-scoped and durable: **PASS**.
- Completed graph nodes survive process restart: **PASS**.
- Ambiguous paid work is never retried silently: **PASS**.
- Live workflow ownership is protected against false interruption: **PASS**.
- Local Windows startup supports PostgreSQL checkpoints: **PASS**.
- Frontend renders without console errors: **PASS**.

## Documentation

- Added ADR-0019 for checkpointed investigation recovery.
- Updated the implementation phase map.
- Updated local startup and live-test instructions in the README.

## ADRs

- ADR-0019: accepted.

## Known limitations

- Recovery occurs at LangGraph node boundaries. If the process dies while a
  paid request is unresolved, the UI pauses and asks the user before retrying
  that step; it does not claim that the request was never billed.
- Local mock Zendesk integration is intentionally slower than unit tests because
  it exercises 51 HTTP-created demo tickets.
- Repository-wide static analysis still contains inherited issues in older agent
  tests, observability fixtures, and empirical-validation scripts. They do not
  fail the functional suite and were not broadly rewritten during this phase.

## Next phase

The end-to-end investigation workflow can now be exercised with one intentional
live query. Performance and response quality should be evaluated separately so
model, prompt, and latency changes remain attributable.

## Demo-readiness follow-up — 2026-09-21

### Implemented

- Separated initial stream connection from a genuine reconnection, so a new
  investigation never opens with a misleading reconnect warning.
- Restored the blue progress bar as a verified six-step lifecycle indicator.
  It begins at the left edge, advances only on backend lifecycle state, and
  cannot move backwards after a stale snapshot or reconnect.
- Rebuilt all four completed scenario previews from the active seeded evidence,
  with decision-first recommendations, measurable targets, attributable
  evidence, and no raw implementation language.
- Corrected the wallet-funding preview to reject the false outage premise and
  corrected the bill-payment preview to isolate the incident to electricity.
- Updated landing-page evidence copy to match the canonical transfer dataset.
- Corrected live PostHog scenario tests to use dataset version `2.0` and the
  canonical August 28–31 bill-payment incident window. Runtime analytics were
  already version-scoped, so old records cannot contaminate an investigation.

### Tests

- Frontend unit suite: 65 passed.
- Frontend type check and Next.js production build: passed.
- Live PostHog scenarios: 5 passed.
- Full Python suite: 347 passed, 3 skipped, 0 failed.
- Landing page, investigation launchpad, and all four preview URLs: HTTP 200.

### Acceptance criteria

- A new run starts at lifecycle step zero: **PASS**.
- Initial connection is not described as reconnection: **PASS**.
- Navigation/reconnection cannot regress progress: **PASS**.
- Four preview briefs reflect the active seeded evidence: **PASS**.
- Preview reports avoid internal implementation leakage: **PASS**.
- Routine validation consumes no LLM credit: **PASS**.

### ADRs

- None. The changes preserve the approved lifecycle, data boundaries, and
  frontend architecture.

## Authentication and hydration follow-up — 2026-09-21

### Implemented

- Replaced locale-dependent investigation-period formatting with explicit
  `en-GB` UTC formatting so server and browser output are identical.
- Removed the requested sign-in and sign-up descriptive copy.
- Aligned sign-up and password-reset validation with the configured policy:
  at least eight characters, one uppercase letter, one lowercase letter, and
  one digit.
- Added live password requirement feedback, accessible validation messaging,
  and a show/hide password control. The server independently enforces the same
  policy.

### Tests

- Frontend unit suite: 69 passed.
- Targeted desktop browser checks: 2 passed, including a console assertion for
  hydration errors.
- Frontend type check and Next.js production build: passed.

### Acceptance criteria

- Investigation scope has deterministic server/client text: **PASS**.
- Requested authentication copy is absent: **PASS**.
- Password guidance and backend enforcement match: **PASS**.

### ADRs

- None.
