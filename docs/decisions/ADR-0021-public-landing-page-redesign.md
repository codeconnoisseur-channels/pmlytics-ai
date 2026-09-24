# ADR-0021: Public landing-page redesign

## Status

Accepted — 2026-09-21

## Context

ADR-0016 froze the earlier landing-page visual direction while the production Next.js
frontend was being established. Subsequent product review explicitly rejected that landing
experience as too plain, repetitive, and insufficiently representative of the product now
implemented. The product owner approved a new visual reference and a focused copy revision
before authorizing implementation.

The investigation workspace, backend workflow, evidence contracts, and agent architecture
are outside this redesign.

## Decision

1. Supersede the landing-page visual freeze in ADR-0016 for the production Next.js root
   route only. The legacy vanilla prototype remains unchanged.
2. Adopt an editorial SaaS visual language using a warm neutral canvas, high-contrast ink,
   a restrained chartreuse marketing accent, source-specific evidence colours, asymmetric
   bento compositions, and generous spacing.
3. Use the product interface as the primary visual. Do not introduce stock AI imagery,
   fabricated customer logos, testimonials, pricing, or vanity performance figures.
4. Preserve the five customer-visible investigation stages: Ask, Gather, Synthesize,
   Challenge, and Decide.
5. Lead with the recommendation in the product preview and retain source traceability,
   measurable success criteria, and the four completed sample investigations.
6. Keep the redesign isolated to landing components and landing-specific CSS tokens until
   the product owner approves extending the visual system into the application workspace.
7. Use Server Components for static marketing sections. Keep client-side state limited to
   the accessible mobile navigation.
8. Meet WCAG-oriented keyboard, focus, contrast, reduced-motion, responsive, and semantic
   markup requirements.

## Approved positioning

- Headline: “Turn scattered product signals into a clear next move.”
- Core promise: combine customer support, product analytics, and engineering context to
  explain what is happening, recommend what to do next, and show the evidence behind the
  decision.
- Primary signed-out action: “Create Account.”
- Primary authenticated action: “Start an Investigation.”
- Secondary action: “View a Sample Brief.”

## Consequences

- The public landing page can evolve independently of the approved workspace while the
  latter awaits a separate visual review.
- Marketing content remains demonstrably grounded in the seeded sample investigations.
- The earlier Next.js landing design is no longer the visual acceptance baseline.
- No backend endpoint, LLM prompt, orchestration flow, or external data integration changes.
