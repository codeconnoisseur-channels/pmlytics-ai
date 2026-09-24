# Phase 9 Validation Input Equivalence Audit

**Date**: 2026-09-16  
**Objective**: Verify information equivalence between the evaluation context visible to human raters vs. the evaluation payload visible to the frozen LLM Judge (`v3.0-frozen-calibrated`) across all 10 frozen validation fixtures (`judge_val_01` to `judge_val_10`).  
**Status**: COMPLETE - DISCREPANCIES IDENTIFIED AND CATALOGUED  

---

## 1. Audit Methodology and Boundary Definitions

For each of the 10 validation cases, we audited:
1. **Information Visible to the Frozen Judge**:
   - `User Query`
   - `Product Area`
   - `Verified Evidence Ledger Available to Agent`: Entry ID, Source Type, Source Reference, Finding, Support Excerpt
   - `Candidate Product Recommendation`: Serialized Pydantic `ProductRecommendation` model in standard JSON format
2. **Information Visible in the Original Human-Rating Packet** (`phase9_human_rating_packet.md`):
   - Markdown sections: Investigation Metadata, Evidence Provided, Candidate Recommendation Output, Human Rating Sheet
3. **Prohibited Contaminants Checked**:
   - Presence of `Critic Outcome` or reviewer evaluation
   - Exposure of `human_ground_truth_scores` or `human_gold_rationale`
   - Exposure of underlying scenario gold metadata (archetype label, scenario expectations)
   - Evaluator commentary or post-hoc correctness confirmations
   - Differences in evidence findings, support strings, or citations

---

## 2. Global Equivalence Findings

### A. Critical Information Asymmetries Identified in Original Packet
1. **Synthetic `Critic Outcome` Field Exposed to Humans**:
   - Across all 10 cases in `phase9_human_rating_packet.md`, Section 3 contained an authoritative `Critic Outcome` line (`PASS` or `REVISE` with an accompanying explanatory justification).
   - Example (`judge_val_01`): `Critic Outcome: PASS (No material issues identified; causal link between lock contention and timeouts is technically supported)`.
   - Example (`judge_val_09`): `Critic Outcome: PASS (Appropriately reported missing evidence boundary; maintained high epistemic caution)`.
   - **Severity**: FATAL DEFECT. This commentary served as an authoritative validation stamp, priming human raters to rate candidate causal logic as sound, whereas the frozen judge received only the raw candidate recommendation JSON.
2. **Evidence Support Incompleteness / Narrative Gap**:
   - In several cases (`judge_val_08`, `judge_val_09`, `judge_val_10`), the `support` excerpt was a minimal placeholder (`Support excerpt from query_biller_grid`), while human raters brought external scenario knowledge (e.g., 504 timeouts, specific biller names, 10-cent hike) into their evaluations.
3. **No Hidden Gold Leakage**:
   - The original packet successfully hid the gold scores (`human_ground_truth_scores`) and archetype labels from the human raters. The contamination was purely narrative/evaluative priming via the Critic field and external scenario recall.

---

## 3. Case-by-Case Equivalence Matrix

### Case `judge_val_01` (Transfers)
- **User Query**: *"Why did automated batch transfers fail at midnight?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (No material issues identified; causal link between lock contention and timeouts is technically supported).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 2 records in both.
  - `[led_001]` (posthog) query_batch_time: Finding and Support match verbatim between Judge context and Human packet.
  - `[led_002]` (jira) DB-22: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_02` (Transfers)
- **User Query**: *"Did the iOS update cause transfer failures across all platforms?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``REVISE` (Critic noted that client iOS rollback cannot remediate Android platform failures without backend causality).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 1 records in both.
  - `[led_001]` (jira) IOS-501: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_03` (KYC)
- **User Query**: *"Which country applicants are suffering KYC verification delays?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (Targeted segmentation supported by country telemetry).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 1 records in both.
  - `[led_001]` (posthog) query_kyc_country: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_04` (KYC)
- **User Query**: *"Are KYC failures widespread or isolated?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (Reconciled support ticket volume with overall population base rate).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 2 records in both.
  - `[led_001]` (zendesk) zen_016: Finding and Support match verbatim between Judge context and Human packet.
  - `[led_002]` (posthog) query_kyc_rate: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_05` (Funding)
- **User Query**: *"Why do customers claim card deposits were charged twice?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (Reconciled customer perception contradiction against ledger settlement reality).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 2 records in both.
  - `[led_001]` (zendesk) zen_025: Finding and Support match verbatim between Judge context and Human packet.
  - `[led_002]` (posthog) query_ledger_settle: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_06` (Funding)
- **User Query**: *"What explains the sudden drop in instant bank deposits on Monday morning?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (Causal link between credential expiration and API handshake failures is supported).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 2 records in both.
  - `[led_001]` (posthog) query_instant_fund: Finding and Support match verbatim between Judge context and Human packet.
  - `[led_002]` (jira) FUND-109: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_07` (Bill Payments)
- **User Query**: *"Did the UI redesign cause bill payment processing timeouts?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``REVISE` (Critic flagged post hoc fallacy: CSS frontend styling changes cannot explain backend server timeouts without network or architectural proof).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 1 records in both.
  - `[led_001]` (jira) UI-400: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_08` (Bill Payments)
- **User Query**: *"Are electricity bill payment failures affecting all providers?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (Recommendation appropriately isolates failing vendor without affecting healthy billers).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 1 records in both.
  - `[led_001]` (posthog) query_biller_grid: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_09` (Bill Payments)
- **User Query**: *"Why did mobile top-up payments fail when telco adapter logs are wiped?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (Appropriately reported missing evidence boundary; maintained calibrated low confidence).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 1 records in both.
  - `[led_001]` (zendesk) zen_038: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

### Case `judge_val_10` (Transfers)
- **User Query**: *"Did transfer fee increases cause user churn?"*
- **Query Equivalence**: Identical between Judge context and Human packet.
- **Candidate Output Equivalence**: Structurally equivalent, EXCEPT for the inclusion of `Critic Outcome` in the human packet:
  - **Judge Visible**: Raw JSON containing 15 schema fields (`problem_statement`, `factual_observations`, `inferences`, `hypotheses`, `evidence`, `recommendation`, etc.). Zero critic commentary.
  - **Human Visible**: Markdown list containing the 15 schema fields PLUS: ``PASS` (Reconciled stated customer survey feedback against behavioral telemetry data).`.
- **Evidence Ledger Equivalence**:
  - Entry Count: 3 records in both.
  - `[led_001]` (posthog) query_churn_latency: Finding and Support match verbatim between Judge context and Human packet.
  - `[led_002]` (zendesk) zen_010: Finding and Support match verbatim between Judge context and Human packet.
  - `[led_003]` (posthog) query_fee_vol: Finding and Support match verbatim between Judge context and Human packet.
- **Prohibited Contaminants Audit**:
  - `Critic Outcome`: **PRESENT IN ORIGINAL HUMAN PACKET (CONTAMINANT)**
  - Hidden Gold / Archetype: Absent (CLEAN)
  - Evaluator Explanations: Embedded in Critic Outcome note (CONTAMINANT)
- **Equivalence Determination**: **FAILED IN ORIGINAL PACKET DUE TO CRITIC FIELD ASYMMETRY**.

---

## 4. Requirements for Clean Human-Rating Packet

To achieve 100% informational equivalence with the frozen judge:
1. **Remove `Critic Outcome` Entirely**: No case may contain any reference to Critic outcome, critic reviews, or reviewer commentary.
2. **Strict Evidence Boundary**: The clean human packet must present the exact evidence ledger records (Entry ID, source type, reference, finding, support excerpt) and instruct raters that **any fact, baseline, metric, or vendor name not explicitly present in these ledger records is UNGROUNDED**.
3. **Epistemic Classification Rules**: Explicitly provide the approved 5-level causal taxonomy (A: direct causal evidence, B: legitimate evidence-based inference, C: evidence-informed hypothesis, D: unsupported causal assertion, E: post-hoc/contradicted causal claim) and instruct raters to penalize Type D/E claims in problem framing or inferences.
4. **Isolation from Past Results**: Clean raters must have no visibility into prior Rater 1, Rater 2, consensus reference, or LLM judge outputs.

Persisted at `evaluations/runs/phase9_validation_input_equivalence_audit.md`.