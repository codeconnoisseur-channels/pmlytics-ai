# ADR-0012: Phase 12 Performance Optimization & Production Hardening

## Status
Accepted

## Context
During Phase 11 live browser validation, the end-to-end investigation workflow completed successfully and all UI components rendered properly. However, empirical profiling revealed unacceptable performance characteristics for interactive use:
- End-to-end latency: 558.08 seconds (~9.3 minutes)
- Total LLM calls: 21 calls
- Total tool calls: 26 calls
- Provider API cost: $0.788899 per investigation

A comprehensive profiling pass identified three primary root causes:
1. Redundant full-history accumulation in LLM prompts (each specialist turn re-prompted all past turns and raw tool payloads).
2. Over-provisioned specialist iteration loops (specialists made multiple serial queries when bounded batched queries sufficed).
3. Homogeneous frontier model routing (`openai/gpt-5.4` used uniformly across all nodes including structured evaluation and summarization).

## Decision
We implement targeted performance optimization and production hardening while preserving all core architectural invariants:

1. **Investigation Profiles (`standard` vs `deep`)**:
   - Introduce an `investigation_profile` configuration setting defaulting to `"standard"` for interactive use and `"deep"` for exhaustive forensic investigations.
   - Standard mode optimizes model routing:
     - Planner: `openai/gpt-4.1-mini`
     - Specialists (Research, Analytics, Engineering): `openai/gpt-4.1-mini`
     - Assessment: `openai/gpt-4.1-mini`
     - PM Synthesis & Revision: `openai/gpt-5.4` (frontier product judgment preserved)
     - Critic: `openai/gpt-5.4-mini` (candidate lightweight critic)
   - Specialist LLM call budgets in Standard mode are bounded to 3 turns (batch retrieval -> targeted inspection -> synthesis).

2. **Authoritative Append-Only Evidence Ledger with Context Compaction**:
   - The Evidence Ledger remains the authoritative append-only source of truth whose existing entries are preserved and never rewritten.
   - Raw HTTP/API responses and tool JSON payloads are compacted into dense factual envelopes for LLM prompt context, stripping extraneous schemas, links, and pagination noise while retaining all substantive facts, measurements, excerpts, identifiers, and status.
   - Compaction Safety Invariant: Context compaction must never remove information necessary to substantiate the resulting `SpecialistFinding`.

3. **Targeted PM Revision Working Set**:
   - During Critic-triggered revision, the PM does not reload the entire raw conversation or full ledger. Instead, a targeted working set is constructed from:
     1. Evidence IDs explicitly attached to Critic issues;
     2. Evidence IDs associated with challenged recommendation claims;
     3. Relevant contradiction and limitation entries;
     4. Current candidate recommendation and challenged claims.

4. **Token Ceiling Calibration**:
   - Calibrate per-role token ceilings: PM token ceiling raised to 5,120 to eliminate truncation retries; Critic ceiling calibrated to 1,536; specialist ceilings bounded to 2,560.

## Invariants Preserved
1. Bit-for-bit frozen LLM Judge prompt SHA-256 (`8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`).
2. Strict role-bound tool permissions (Research -> Zendesk only, Analytics -> PostHog only, Engineering -> Jira only).
3. Zero external tool access for PM and Critic agents.
4. Read-only external system access (no autonomous agent writes).
5. No RAG, vector databases, or MCP.
6. Epistemic separation of Facts, Inferences, and Hypotheses strictly preserved in `ProductRecommendation`.
7. Evidence Ledger provenance and Evidence Drawer citation resolution 100% intact.

## Consequences
- Single investigation latency drops from 558.08s to 162.05s (71% reduction).
- Provider API cost drops from $0.7889 to $0.0713 (91% reduction, beating the stretch target of $0.15).
- Zero hallucinated citations across all evaluated benchmark scenarios (100% valid citations).
- Revision path naturally exercised and validated without artificial fabrication.
