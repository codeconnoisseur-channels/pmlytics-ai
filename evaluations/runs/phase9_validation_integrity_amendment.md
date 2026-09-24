# Phase 9 Protocol Amendment: Validation Integrity Correction

**Date**: 2026-09-16  
**Status**: APPROVED & EXECUTED  
**Scope**: LLM-as-Judge Frozen Validation Integrity Correction  
**Target File**: `evaluations/runs/phase9_validation_integrity_amendment.md`  

---

## 1. Protocol Amendment Statement

> **The original Revision 3 validation comparison is preserved as historical evidence but is not used for final qualification because human and judge evaluation contexts were not equivalent. A clean rerating and single requalification run are authorized solely to restore evaluation validity. No judge calibration revision is authorized by this amendment.**

---

## 2. Rationale & Defect Discovery

During the diagnostic postmortem following the Revision 3 validation qualification run, a material evaluation-design defect was identified in the human rating packet (`phase9_human_rating_packet.md`):

1. **Information Asymmetry (Critic Field Exposure)**:
   - The original human-rating workbook exposed an additional synthetic `Critic Outcome` field (e.g., `PASS (No material issues identified; causal link between lock contention and timeouts is technically supported)`) in Section 3 for each candidate output.
   - This field was **not** supplied to the frozen LLM Judge, which evaluated the candidate `ProductRecommendation` as raw JSON without external evaluation.
   - The exposed critic text provided an authoritative validation stamp, priming human raters to view candidate reasoning as verified and sound.

2. **Outside Scenario Ground Truth Leakage**:
   - Multiple human raters awarded Score 4 to unevidenced candidate claims (such as specific HTTP 504 timeouts, third-party vendor names, and unevidenced fee hike dates) because they recognized those facts as true within the broader product scenario design, rather than evaluating strictly against the retrieved evidence ledger records.

3. **Incomplete Support Excerpts**:
   - In several validation fixtures, the support text was a minimal placeholder string (`Support excerpt from ...`), creating a narrative gap between human recall and what was literally provided in the evidence ledger.

This was an **evaluation-reference contamination problem**, not a judge calibration failure. Modifying the judge prompt or making the judge more permissive would have degraded measurement rigor.

---

## 3. Scope of Authorized Actions

1. **Frozen Judge Remains Immutable**:
   - Judge Version: `v3.0-frozen-calibrated`
   - Prompt SHA256: `8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`
   - Model: `openai/gpt-5.4` via OpenRouter at `temperature: 0.0`
   - No prompt modifications, model changes, or threshold relaxations permitted.

2. **Preservation of Historical Artifacts**:
   - The original Rater 1, Rater 2, consensus reference ratings, and Revision 3 results are preserved in the repository as immutable historical evidence, marked as `CONTAMINATED / INVALID FOR FINAL JUDGE QUALIFICATION`.

3. **Validation Input Equivalence Audit**:
   - Conducted an audit comparing the exact information visible to human raters vs. the frozen judge across all 10 validation fixtures (`evaluations/runs/phase9_validation_input_equivalence_audit.md`).

4. **Clean Human-Rating Packet & Fresh Ratings**:
   - Built a clean workbook (`evaluations/human_ratings/phase9_clean_validation_rating_packet.md`) containing zero critic commentary, zero gold annotations, and strict instructions to evaluate Groundedness and Causal Discipline strictly against the supplied evidence ledger.
   - Obtained two fresh independent ratings (`evaluations/human_ratings/phase9_clean_validation_ratings_rater1.json` and `rater2.json`).
   - Reconstructed the clean human reference (`evaluations/human_ratings/phase9_clean_validation_reference.json`) using the approved consensus rule.

5. **Single Requalification Run**:
   - Executed exactly ONE fresh validation requalification run of `v3.0-frozen-calibrated` against the clean reference (`evaluations/runs/phase9_clean_validation_requalification_results.json`).

---

## 4. Requalification Empirical Outcome

Comparing the unchanged frozen judge against the clean human reference:

| Dimension | Weighted Cohen's $\kappa_w$ | 95% Bootstrap CI | Exact Agreement | 1-pt Diff | >1-pt Diff | Mean Signed Diff | MAE | Qualification Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Groundedness** | **0.8333** | `[0.5455, 1.0000]` | 8 / 10 | 2 / 10 | 0 / 10 | 0.00 | 0.20 | **QUALIFIED** |
| **Cross-Source Reasoning** | **0.7755** | `[-0.0674, 1.0000]` | 7 / 10 | 2 / 10 | 1 / 10 | +0.10 | 0.50 | **QUALIFIED** |
| **Contradiction Handling** | **0.9038** | `[-0.1538, 1.0000]` | 8 / 10 | 2 / 10 | 0 / 10 | 0.00 | 0.20 | **QUALIFIED** |
| **Causal Discipline** | **0.8235** | `[0.0909, 0.9565]` | 7 / 10 | 3 / 10 | 0 / 10 | -0.30 | 0.30 | **QUALIFIED** |
| **Recommendation Defensibility** | **0.9231** | `[0.5833, 1.0000]` | 8 / 10 | 2 / 10 | 0 / 10 | -0.20 | 0.20 | **QUALIFIED** |

**Overall Qualification Decision**: **QUALIFIED** ($\kappa_w \ge 0.75$ on all 5 required dimensions).

---

## 5. Governance Gate Status

1. **Judge Qualification**: **QUALIFIED** (Judge `v3.0-frozen-calibrated` is officially frozen and certified for downstream evaluation).
2. **Benchmark Status**: The 660-run SUT benchmark is now **ELIGIBLE TO PROCEED** under approved Phase 9 evaluation protocols, pending explicit user command.
3. **Phase 10 Status**: Remains **BLOCKED** until the 660-run benchmark and evaluation report are complete.
