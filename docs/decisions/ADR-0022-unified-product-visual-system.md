# ADR-0022: Unified product visual system

## Status

Accepted, 2026-09-21

## Context

ADR-0021 introduced a new public landing-page direction and deliberately kept it isolated
until product review. The product owner approved that direction and explicitly requested
that it be extended across authentication, the investigation launchpad, the workspace,
and the evidence drawer.

The rollout must not change investigation state, evidence contracts, orchestration,
authentication rules, or report content. An earlier product requirement also established
blue as the live investigation progress signal.

## Decision

1. Use the same warm neutral canvas, near-black ink, rounded geometry, restrained lime
   accents, grid texture, and translucent surfaces across the full Next.js product.
2. Keep source provenance and epistemic colours semantic. Lime must not replace Zendesk,
   PostHog, Jira, fact, inference, hypothesis, warning, or failure colours.
3. Keep the live investigation progress bar blue so that it remains a stable operational
   signal distinct from the broader visual identity.
4. Use the strongest dark surface for the primary recommendation so the decision remains
   the first element users read in a completed brief.
5. Preserve all existing product behavior and accessibility requirements. This decision
   changes presentation only.
6. Avoid em dashes in customer-facing product and marketing copy.
7. Keep the application header and sidebar visible while the report scrolls. Investigation
   history belongs in a separately scrollable sidebar region, not beneath the inquiry form.
8. Use explicit labels for private copied links and for the full evidence audit layer.

## Consequences

- Public, authentication, launchpad, workspace, and evidence-audit surfaces now read as
  one product family.
- Shared Tailwind tokens change from cool slate and blue branding to warm neutrals and
  ink-led branding.
- Blue remains reserved for investigation progress and existing semantic uses.
- No backend, model, prompt, workflow, or data-source behavior changes.
