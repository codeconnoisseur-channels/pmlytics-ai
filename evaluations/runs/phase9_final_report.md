# Phase 9 Final Report: Evaluation Framework & Benchmark Disposition

**Project**: Pocket AI Product Discovery Team  
**Phase**: Phase 9 — Evaluation System  
**Date**: `2026-09-16`  
**Phase Status**: `EVALUATION_FRAMEWORK_COMPLETE`  
**Benchmark Status**: `LARGE_BENCHMARK_DEFERRED`  
**Evaluator Status**: `FROZEN_SEMANTIC_EVALUATOR_WITH_DOCUMENTED_LIMITATIONS`  
**Frozen Judge Prompt SHA256**: `8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`  

---

## 1. Executive Summary & Core Decisions

Phase 9 is officially closed as **`EVALUATION_FRAMEWORK_COMPLETE`** with benchmark status **`LARGE_BENCHMARK_DEFERRED`**.

The purpose of Phase 9 was to establish a rigorous, credible, two-layer evaluation framework capable of detecting grounding, citation, causal, contradiction, and recommendation failures in multi-agent product discovery investigations—not to maximize the volume of paid benchmark executions.

In accordance with project governance:
- The benchmark is **not** described as completed.
- No statistical architectural superiority is claimed.
- The LLM judge is **not** claimed to be objectively validated or gold-standard validated.
- The large 204-run benchmark was intentionally halted and deferred due to disproportionate infrastructure cost and token reservation dynamics.

### Primary Project Principle
> “Evaluation should be proportionate to the decision it supports. Pocket's evaluation framework is intended to detect grounding, evidence, causal, contradiction, and recommendation failures and to make system behaviour auditable. It is not intended to become a large-scale research benchmark at the expense of completing the product.”

---

## 2. Completed Evaluation Framework

The approved evaluation framework consists of two strictly segregated evaluation layers:

### Layer 1: Deterministic Evaluation Layer (Objective Programmatic Gate)
Operates independently of LLM inference, calculating programmatic invariants directly from investigation state and ground-truth scenario definitions:
1. **Structural Citation Validity**: 100% verification that every cited ledger ID in the recommendation resolves to a valid, non-hallucinated record in `state.evidence_ledger_entries`.
2. **Citation-to-Evidence Consistency**: Verifies that cited text matches the underlying evidence records without semantic contradiction or ID fabrication.
3. **Evidence Record Existence & Provenance**: Enforces that all retrieved evidence originated from authorized mock tools (Zendesk, PostHog, Jira) with immutable source references.
4. **Schema Completeness & Epistemic Separation**: Programmatically verifies structural fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `recommendation`) and confirms clear separation between observed facts and speculative hypotheses.
5. **Scenario-Aware Evidence Coverage**: Assesses context recall and precision against expected support tickets, Jira issue keys, and PostHog analytics observations without pseudo-replication.
6. **Contradiction Fidelity**: Programmatically verifies that identified contradictions match explicitly encoded ground-truth discrepancies in contradiction scenarios.
7. **Tool Iteration & Execution Bounds**: Confirms that specialist tool calls, LLM invocations, and PM revision cycles respect strict budget ceilings (`max_revisions <= 2`).

### Layer 2: Frozen Semantic LLM Evaluator (Calibrated Subjective Layer)
Evaluates nuanced reasoning dimensions on an anchored 0–4 scale via `v3.0-frozen-calibrated`:
- **Groundedness (0–4)**: Verifies that material assertions are anchored in retrieved evidence.
- **Cross-Source Reasoning (0–4)**: Evaluates tripartite synthesis across customer support, product analytics, and engineering context.
- **Contradiction Handling (0–4)**: Tests reconciliation of opposing signals without erasing tensions.
- **Causal Discipline (0–4)**: Enforces conservative causal language and penalizes correlation-causation conflations.
- **Recommendation Defensibility (0–4)**: Measures alignment between synthesized evidence and proposed product remediations.

### Claim-Level Evidence Audit
Every material assertion in the candidate output is extracted, localized, and mapped to supporting ledger entries with explicit support classifications (`FULLY_SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED_ADDITION`, `CONTRADICTED`) and causal classifications (`DIRECT_CAUSAL_EVIDENCE`, `LEGITIMATE_INFERENCE`, `EVIDENCE_INFORMED_HYPOTHESIS`, `UNSUPPORTED_CAUSAL_ASSERTION`).

### Context-Integrity Fix (`v3.0-context-integrity-patch`)
A context-integrity defect in the evaluator context assembly was identified during stress testing: `_assemble_judge_context` previously omitted `entry.support`, causing the judge to evaluate claims against a truncated representation of evidence. The context assembly was upgraded to serialize all evidence fields (`ledger_entry_id`, `source_type`, `source_reference`, `finding`, `support`, `confidence`, `limitations`).

### Behavioral Stress Suite (15/15 PASS)
The evaluation framework was validated against a 15-case behavioral stress suite targeting edge-case invariants:
- Fabricated metrics, unevidenced baselines, valid multi-record synthesis, unsupported causal assertions, qualified causal hypotheses, explicit contradictions, absent contradictions, and prompt injections.
- **Result**: **15/15 PASS** (`BEHAVIORAL_EVALUATOR_SANITY_PASS`).

---

## 3. Evaluator-Development History & Methodological Audits

The evaluation system underwent multiple rigorous development iterations and audits:

```text
Phase 9.1 Initial Human Calibration
  ↓
Phase 9.2 Human Rating Asymmetry Discovery (Contamination in validation packet)
  ↓
Phase 9.3 Clean Validation Requalification & Provenance Audit
  ↓
Phase 9.4 Postmortem: Human Raters Unsuitable as Quantitative Oracle
  ↓
Phase 9.5 Permanent Prompt Freeze (v3.0-frozen-calibrated)
  ↓
Phase 9.6 Behavioral Stress Suite & Context-Integrity Patch (15/15 PASS)
```

1. **Initial Human Calibration**: Two independent human raters evaluated development cases (`dev_01` to `dev_07`). Analysis revealed significant inter-rater divergence and ceiling effects on subjective dimensions.
2. **Contamination & Packet Asymmetry Discovery**: An audit identified that human raters had been exposed to an extra synthetic `Critic Outcome` field not provided to the LLM judge, rendering the Revision 3 comparison informationally asymmetric.
3. **Clean-Reference Requalification**: Re-running human ratings with strictly identical inputs exposed that human raters systematically gave high marks (e.g. 4/4 Groundedness) to outputs that contained clear factual extrapolations, proving human ratings were unreliable as a quantitative calibration gold standard.
4. **Decision on Human Calibration**: Formal human-reference calibration (e.g., Cohen's kappa qualification gates) was permanently deprecated. Human ratings remain preserved as historical research artifacts but are **not** treated as ground truth.
5. **Frozen Prompt Revision 3**: The prompt was frozen with SHA256 `8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63` and enforced by automated CI tests (`test_judge_prompt_frozen_sha.py`).
6. **Stress Testing & Fixture Refinement**: Initial stress testing achieved 14/15 PASS, revealing (a) the context serialization omission, and (b) an over-extrapolated fixture assertion in `stress_04`. After applying `v3.0-context-integrity-patch` and refining `stress_04_v2`, the stress suite achieved **15/15 PASS**.

---

## 4. Final Evaluator Result & Formal Declaration

> “The frozen semantic evaluator passed 15/15 predefined behavioral stress checks after correcting an evidence-context serialization defect. Human-reference calibration was not retained as a benchmark ground truth because the analytical nature of the task and defects in the reference process made it unsuitable as an objective oracle.”

The evaluator status is recorded as:
```text
FROZEN_SEMANTIC_EVALUATOR_WITH_DOCUMENTED_LIMITATIONS
```

---

## 5. Interrupted Benchmark & OpenRouter Cost Issue

### Benchmark Decision
> “The originally planned large benchmark was intentionally deferred because its cost and scope were disproportionate to the portfolio objective. The interrupted execution is preserved as historical evidence and is not treated as a completed benchmark.”

### Checkpoint Status
- **Artifact**: `phase9_benchmark_checkpoint.json` (generated raw checkpoint retained locally and excluded from the public repository)
- **Marked Status**: `PHASE9_LARGE_BENCHMARK_ABORTED_INFRASTRUCTURE_COST`
- **Execution Breakdown**:
  * **Legitimate Exploratory Executions**: 13 runs (`scn_001` through `scn_004` across architectures A, B, and C).
  * **HTTP 402 Infrastructure Failures**: 57 runs (`scn_005` through `scn_041`).
  * **Unattempted Executions**: 134 runs.
  * **Statistical Calculation**: No benchmark statistics were calculated from the incomplete run.
  * **Interpretation Rule**: The 57 HTTP 402 failures are **infrastructure defects**, not SUT quality or architectural results.
  * **Disposition**: The checkpoint is permanently closed; it will not be resumed and will not be merged into future benchmarks.

### Root Cause of OpenRouter Cost Issue
1. **Unbounded Max Tokens Reservation**: The benchmark configuration did not explicitly bound `max_tokens` per completion request. For `openai/gpt-5.4`, OpenRouter defaults to reserving balance for the maximum potential output capacity (65,536 tokens).
2. **Credit Threshold Rejection (HTTP 402)**: At 20:50:49 UTC, the account balance fell below the reservation threshold (sufficient for 62,788 tokens, but short of 65,536). OpenRouter rejected all subsequent requests with `402 Payment Required`.
3. **Retry Amplification**: The retry logic attempted 5 backoff retries per call, burning execution time before logging failures.
4. **Resolution**: No additional funds will be spent on the large benchmark. The token-bounding logic and JSON outer-object decoding fallback (`json.JSONDecoder().raw_decode`) are preserved in code for future controlled evaluations.

---

## 6. LangSmith Observability Policy

LangSmith is the designated primary observability platform for the actual Pocket product application.

During subsequent application implementation (Phase 10 & Phase 11), application queries will expose:
- Top-level LangGraph workflow traces;
- Planner/Orchestrator decision nodes;
- Research, Analytics, and Engineering specialist agent runs;
- PM Synthesis and Critic review rounds;
- Tool invocations and payloads;
- Model names, latencies, and token counters;
- Classified tool and system errors;
- Scenario/query metadata.

A normal end-to-end smoke query is sufficient to verify live tracing without incurring benchmark-scale token consumption.

---

## 7. Evaluator Invariant Commitments

For the remainder of the project:
1. No fourth judge calibration revision will be conducted.
2. The frozen judge prompt and rubric remain bit-for-bit immutable.
3. No further human ratings will be collected.
4. No additional stress suite cases or benchmark tiers will be created.
5. The 15/15 behavioral stress result stands as the final evaluator stress gate for this repository.

---

## 8. Verification & Test Gate Summary

All 42 automated evaluation unit and integration tests are passing:

```text
============================= test session starts =============================
tests/evaluations/test_baselines.py ..                                   [  4%]
tests/evaluations/test_behavioral_stress_suite_structure.py ...          [ 11%]
tests/evaluations/test_candidate_c_evaluation.py ..                      [ 16%]
tests/evaluations/test_deterministic_evaluators.py .......               [ 33%]
tests/evaluations/test_error_taxonomy.py .....                           [ 45%]
tests/evaluations/test_eval_schemas.py .....                             [ 57%]
tests/evaluations/test_evaluation_runner.py ...                          [ 64%]
tests/evaluations/test_holdout_isolation.py ...                          [ 71%]
tests/evaluations/test_judge_calibration.py .......                      [ 88%]
tests/evaluations/test_judge_context_integrity.py .                      [ 90%]
tests/evaluations/test_judge_frozen_validation.py ...                    [ 97%]
tests/evaluations/test_judge_prompt_frozen_sha.py .                      [100%]
============================= 42 passed in 3.98s ==============================
```

Phase 9 is formally closed.
