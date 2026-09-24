# ADR-0013: Phase 12A PM Revision Model Routing & Latency Optimization

## Status
Accepted, with the Standard-profile Critic bypass superseded by ADR-0025

## Context
In Phase 12, the system achieved sequential call bounding (exactly 10 calls before revision, 11 with revision) and significant cost reductions ($0.05–$0.08 per investigation). However, observed end-to-end wall-clock latency under Critic-triggered revision hovered in the 145s–160s range, with an extreme tail outlier of 310.35s in Scenario 2.

A LangSmith trace telemetry investigation into the 310.35s outlier revealed that upstream generation latency on frontier `openai/gpt-5.4` throttled down to ~16.8 tokens/sec on Call 9 (`pm_synthesis`), taking 170.62 seconds for that single LLM call alone. Provider TTFT (2.82s), retries (0), tracing overhead, and orchestration were eliminated as causes.

Furthermore, empirical timing profiling revealed that when a `REVISE` outcome is issued by the Critic, generating a multi-thousand token `ProductRecommendation` revision using frontier `openai/gpt-5.4` adds 35–50 seconds of critical-path wall clock time.

## Decision
We implement targeted PM revision optimization while strictly preserving all existing quality, evidence, safety, and architectural invariants:

1. **Independent PM Revision Model Routing**:
   - Initial PM synthesis (`pm` / `pm_synthesis`) remains on the frontier model (`openai/gpt-5.4`) to ensure deep initial inductive reasoning, cross-source synthesis, and initial recommendation formulation.
   - The PM revision node (`pm_revision`) is routed to a higher-throughput model: `openai/gpt-5.4-mini`.
   - The `ProductRecommendation` contract is preserved in full: all required fields, facts/inferences/hypotheses separation, citation resolution, and Evidence Ledger IDs remain strictly enforced.
   - No evidence is omitted or compacted away from the PM revision context.

2. **Calibrated PM Revision Token Budgeting & Density Prompting**:
   - Calibrate `pm_revision_max_tokens` to 3,584 (sufficient for full structured output without risk of length truncation).
   - Add concise, high-density instructions to synthesis and revision prompts to prevent repetitive narrative padding while retaining complete factual coverage.

3. **Safe Parsing and Deterministic Revision Validation**:
   - Preserve the deterministic fail-closed revision validation gate. If the revision fails schema compliance, citation validity, or epistemic separation, the system falls back safely to the initial candidate recommendation.

## Invariants Preserved
1. Unchanged frozen LLM Judge prompt SHA-256 (`8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`).
2. Zero deletion of evidence from PM contexts.
3. 100% citation resolution and zero hallucinated citations.
4. Epistemic separation of Facts, Inferences, and Hypotheses.
5. At the time of this decision, sequential call counts were 10 pre-revision and
   11 with revision. ADR-0025 later restored one bounded post-revision Critic
   call, making the revised Standard path up to 12 calls.
6. Read-only domain tool boundaries.

## Consequences
- PM revision latency dropped from 35–50s down to **15.55s** (saving ~25–35s of critical-path wall clock).
- End-to-end wall-clock latency across the evaluation suite:
  - Scenario 1 (no revision): **98.46s** (≤120s gate: **PASS**)
  - Scenario 2 (with revision): **121.41s** (down from 310.35s; critical path: **111.80s**)
  - Scenario 3 (no revision): **107.43s** (≤120s gate: **PASS**)
  - Suite Average: **109.10s** (surpasses ≤120s gate).
- Provider API cost: $0.0559 – $0.0807 (well within the ≤$0.20 ceiling and beating the $0.15 stretch target).
- Quality maintained: Frozen Judge awarded 20/20 on Scenario 1, 18/20 on Scenario 2 (Defensibility 4/4), and 20/20 on Scenario 3.
