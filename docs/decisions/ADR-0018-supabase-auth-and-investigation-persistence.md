# ADR-0018: Supabase Authentication and Investigation Persistence

## Status

Accepted — 2026-09-20

## Context

The process-local `InvestigationManager` loses investigations on backend restart and cannot enforce user ownership. The approved product specifications already require durable investigation history and staged authenticated accounts. The user has selected Supabase for both managed PostgreSQL and authentication.

## Decision

1. Supabase Auth is the identity provider for basic email/password accounts.
2. Next.js uses `@supabase/ssr` and cookie-backed sessions for sign-up, sign-in, email confirmation, password reset, session refresh, and sign-out.
3. FastAPI remains the authoritative application API. It verifies Supabase access tokens against the project's public JWKS and never trusts a browser-supplied user identifier.
4. Every live investigation route requires an authenticated user. Unknown and other-user investigation IDs both return `404` to avoid resource enumeration.
5. The Supabase publishable key may be used by the browser. Secret/service-role keys are not required by the application and must not be added to frontend configuration.
6. Supabase PostgreSQL is the durable application store for investigation lifecycle records, progress events, evidence snapshots, results, and safe failure metadata.
7. Every persisted investigation record has a non-null Supabase user ID owner. Database access remains behind an application storage adapter; agents receive no database tool and cannot read historical investigations as model context.
8. Row Level Security will provide defense in depth for user-owned tables, while FastAPI authorization remains mandatory.
9. Public landing content and precomputed sample scenarios remain accessible without authentication. Starting or accessing a live investigation requires authentication.

## Security Invariants

- No Supabase secret/service-role key in the browser or repository.
- No user ID accepted from request payloads for authorization.
- JWT issuer, audience, expiry, signature, and subject are verified.
- Cross-user resource access returns `404`.
- Authentication failures occur before LLM or evidence-source calls.
- A new investigation record is persisted before the background workflow is launched.
- A completed state is durably saved before a completion event is sent to the browser.
- Lifecycle writes are serialized so a delayed progress update cannot overwrite a terminal state.
- Persistent history is not long-term agent memory and is never automatically inserted into a new investigation prompt.

## Consequences

- The prior Phase 14 deferral of authentication and persistence is superseded for these two capabilities.
- Authenticated SSE uses a fetch-based stream because native `EventSource` cannot attach a bearer token.
- Alembic owns the application schema. The initial migration creates owner-scoped investigation and event tables with Row Level Security policies.
- Completed reports survive application restarts. An active record whose process task was lost is truthfully marked interrupted; automatic workflow replay is not implied.
- Team workspaces, RBAC, social OAuth, enterprise SSO, and billing remain out of scope.
