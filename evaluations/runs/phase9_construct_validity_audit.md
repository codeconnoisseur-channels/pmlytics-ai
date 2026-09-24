# Phase 9 Construct Validity Audit: Groundedness & Causal Discipline

**Scope**: 10 Development / Calibration Cases (`judge_dev_01` through `judge_dev_10`)  
**Frozen Validation Set Status**: Strictly untouched; preserved as out-of-sample historical evidence.  
**Human Reference Ratings Status**: Strictly untouched; historical ratings preserved for auditability.  
**Objective**: Determine whether the remaining measurement gap on Groundedness and Causal Discipline reflects judge miscalibration, rubric ambiguity, human rater leniency, or a mixed structural confound.

---

## Executive Summary & Decision

### **Audit Decision: Option D — Mixed (Human Leniency on Groundedness + Rubric Ambiguity on Causal Discipline)**

The audit reveals two distinct construct-validity phenomena operating across the two failing dimensions:

1. **Groundedness: Human Rater Leniency (`HUMAN_TOO_LENIENT`)**  
   The approved Groundedness construct requires that *all material substantive claims be supported by the actual retrieved evidence context*. Human raters repeatedly awarded a **Score 4** to answers containing **Category C (Unsupported Factual Additions)**—such as unshown historical baselines (*"rose from 4% to 22%"* in `dev_08`), unshown software release tags (*"following v4.2 release"* in `dev_06`), and truncated cohort numbers (*"52s latency"* in `dev_03`). The human raters conflated domain plausibility and overall narrative coherence with literal evidentiary support. The LLM judge, adhering strictly to the retrieved context, correctly identified these additions and docked scores to 2 or 3.

2. **Causal Discipline: Rubric Ambiguity (`RUBRIC_AMBIGUITY`)**  
   The rubric did not clearly define whether proposing targeted remediation for an engineering defect that temporally and mechanically matches a telemetry anomaly qualifies as disciplined PM reasoning. Human raters rewarded this mechanical attribution as exemplary PM behavior (Score 4). The LLM judge docked scores to 2, arguing that without experimental A/B isolation or formal proof of exclusivity, asserting that a bug "caused" the problem in executive framing constitutes causal overreach.

---

## 1. Groundedness Construct & Statement Classification

### The Three Evidentiary Categories
- **Category A: Evidence-Supported Statement**: Directly backed by verified ledger citations.
- **Category B: Legitimate Synthesis / Inference**: Not stated verbatim in a single record, but logically derived by combining multiple records and clearly expressed as an inference or synthesis.
- **Category C: Unsupported Factual Addition**: Not present in the evidence and not legitimately derivable from it, even if plausible, factually true in reality, or consistent with hidden ground truth.

---

## 2. Ten-Case Groundedness Audit

### `judge_dev_01` (Transfers — Partner Switch Timeout)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_001`): Customer reports pending transfer.
  * `led_002` (PostHog `query_latency`): p95 latency > 45s, success rate 98.8%.
  * `led_003` (Jira `PAY-117`): Partner switch webhook timeout bug.
* **Statement Analysis**:
  * *Category A (Directly Supported)*: 98.8% settlement rate (`led_002`); PAY-117 switch timeout bug (`led_003`); customer reports pending transfer (`led_001`).
  * *Category B (Legitimate Synthesis)*: Transfers are settling, but status synchronization is delayed (deduced from 98.8% success + callback timeout).
  * *Category C (Unsupported Factual Addition)*: *"Affected users: Bank A and Bank B account holders"*; *"transfers pending for hours"*.
* **Fact vs. Inference Separation**: Cleanly separated in body; problem statement slightly combines them.
* **Human Score**: 4 | **Judge Score**: 3
* **Diagnosis**: `HUMAN_TOO_LENIENT` on Bank A/B cohort addition. The judge correctly assigned 3 due to minor ungrounded cohort phrasing.

---

### `judge_dev_02` (Transfers — Causality Trap)
* **Evidence Ledger**:
  * `led_001` (Jira `PAY-117`): Switch X timeout.
* **Statement Analysis**:
  * *Category A*: Switch X experienced timeouts.
  * *Category B*: None.
  * *Category C*: *"Complete collapse of all platform payments"*; *"caused every payment failure"*; *"all platform users across all banks"*.
* **Fact vs. Inference Separation**: Severe conflation; wild causal leap asserted as fact.
* **Human Score**: 1 | **Judge Score**: 1 (**Exact Match**)
* **Diagnosis**: Aligned. Both recognize massive Category C fabrication.

---

### `judge_dev_03` (Transfers — Segmentation Trap)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_latency`): Latency breakdown by bank. Support: Support excerpt from query_latency.
* **Statement Analysis**:
  * *Category A*: None verbatim from the abbreviated snippet.
  * *Category B*: None.
  * *Category C*: *"p95 latency is 52s for Bank A and B, but under 2s for Banks C and D"*; *"Bank A and Bank B accounts"*.
* **Fact vs. Inference Separation**: Separated internally, but the observation itself is unevidenced in the snippet.
* **Human Score**: 4 | **Judge Score**: 2
* **Diagnosis**: `DIMENSION_CONFOUND` / `HUMAN_TOO_LENIENT`. The fixture ledger snippet was truncated to 4 words (*"Latency breakdown by bank"*). Human raters scored the case knowing the full scenario truth. The judge, evaluating strictly against the provided context, correctly found that specific numbers (52s, 2s) were Category C additions relative to the ledger.

---

### `judge_dev_04` (Transfers — Magnitude Trap)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_104`): 3 tickets on 2 cent discrepancy.
* **Statement Analysis**:
  * *Category A*: 3 tickets reported 2 cent discrepancy.
  * *Category B*: None.
  * *Category C*: *"Catastrophic fee overcharging across thousands of daily transfers"*; *"millions of users"*; *"entire billing system systematically corrupted"*.
* **Fact vs. Inference Separation**: Extreme extrapolation asserted as fact.
* **Human Score**: 1 | **Judge Score**: 1 (**Exact Match**)
* **Diagnosis**: Aligned. Both recognize severe Category C distortion of magnitude.

---

### `judge_dev_05` (Transfers — Contradiction Handling)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_005`): Customer tickets claiming failure.
  * `led_002` (PostHog `query_settlement`): Eventual settlement rate 99.1%.
* **Statement Analysis**:
  * *Category A*: Customer tickets claim money gone (`led_001`); 99.1% eventual settlement (`led_002`).
  * *Category B*: Customers assume delay equals failure because UI lacks intermediate progress indicator (sound inference reconciling perception vs backend).
  * *Category C*: *"Within 30 minutes"*; *"peak processing windows"*.
* **Fact vs. Inference Separation**: Flawless separation.
* **Human Score**: 4 | **Judge Score**: 3
* **Diagnosis**: `HUMAN_TOO_LENIENT` on minor timing embellishments. The judge's score of 3 is more faithful to the strict construct than the human 4.

---

### `judge_dev_06` (KYC — Android Camera Drop-off)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_kyc_dropoff`): Upload error rate 28%.
  * `led_002` (Jira `KYC-88`): Missing client-side compression on Android.
* **Statement Analysis**:
  * *Category A*: Upload error rate 28% (`led_001`); missing client-side compression on Android (`led_002`).
  * *Category B*: High-res images exceed upload payload timeout on mobile data (sound technical inference).
  * *Category C*: *"Drop-off doubled"*; *"following v4.2 release"*; *"onboarding conversion dropped 14%"*.
* **Fact vs. Inference Separation**: Good structure, but asserted "v4.2 release" and "doubled" as verified facts in `factual_observations`.
* **Human Score**: 4 | **Judge Score**: 2
* **Diagnosis**: `HUMAN_TOO_LENIENT`. Human raters overlooked the unevidenced release tag and unevidenced drop-off doubling claim. The judge strictly penalized these as Category C factual additions.

---

### `judge_dev_07` (KYC — Causality Trap)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_014`): User reports rejected passport.
* **Statement Analysis**:
  * *Category A*: Passport verifications failed (`zen_014`).
  * *Category B*: None.
  * *Category C*: *"New OCR provider is completely defective"*; *"caused all verification failures"*; *"all KYC applicants"*.
* **Fact vs. Inference Separation**: Blatant overreach asserted as fact.
* **Human Score**: 1 | **Judge Score**: 1 (**Exact Match**)
* **Diagnosis**: Aligned. Both recognize severe Category C vendor blaming.

---

### `judge_dev_08` (Funding — 3DS Drop)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_card_3ds`): 3DS challenge failure rate 22%.
  * `led_002` (PostHog `query_bank_vol`): Bank transfer volume +35%.
  * `led_003` (Jira `FUND-42`): 3DS SDK upgrade required.
* **Statement Analysis**:
  * *Category A*: 3DS challenge failure rate 22% (`led_001`); bank transfer volume +35% (`led_002`); FUND-42 SDK upgrade required (`led_003`).
  * *Category B*: Users substitute bank transfer when encountering repeated 3DS card errors (sound inference).
  * *Category C*: *"Rose from 4% to 22%"* (the 4% baseline is completely absent from the ledger).
* **Fact vs. Inference Separation**: Good separation in body; problem statement combines them.
* **Human Score**: 4 | **Judge Score**: 2
* **Diagnosis**: `HUMAN_TOO_LENIENT`. The human raters ignored the invented historical baseline ("4%"). The judge penalized it as an invented quantitative fact (Category C). Under the strict construct, an invented baseline precludes a Score 4.

---

### `judge_dev_09` (Bill Payments — Account Digits)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_biller_errors`): BP-404 on biller ID 992.
  * `led_002` (Jira `PAY-310`): City Water changed account digits to 12.
* **Statement Analysis**:
  * *Category A*: BP-404 errors on biller ID 992 (`led_001`); utility changed account digits to 12 (`led_002`).
  * *Category B*: Pocket app validation rejects 12-digit numbers as invalid (sound inference).
  * *Category C*: *"Biller directory API schema change"* (phrased as a specific architectural failure not in evidence); *"from 10 to 12 digits"* (10 is unshown baseline); *"Over 400 customers"*.
* **Fact vs. Inference Separation**: Cleanly separated in body; executive statement asserts API schema change as fact.
* **Human Score**: 4 | **Judge Score**: 2
* **Diagnosis**: `MIXED`. Human raters gave full credit for the mechanical diagnosis. The judge docked to 2 because "API schema change", "from 10", and "400 customers" were Category C additions.

---

### `judge_dev_10` (Transfers — Missing Evidence)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_007`): 12 customer tickets on Euro transfer.
* **Statement Analysis**:
  * *Category A*: 12 customer tickets report delays on Euro transfers (`zen_007`).
  * *Category B*: Customer friction exists, but technical root cause cannot be confirmed (disciplined synthesis).
  * *Category C*: None. Plausible mechanisms (FX liquidity, clearing delay) are strictly labelled under `hypotheses`.
* **Fact vs. Inference Separation**: Textbook epistemic humility.
* **Human Score**: 4 | **Judge Score**: 4 (**Exact Match**)
* **Diagnosis**: Aligned. Zero Category C claims; speculative material strictly quarantined as hypotheses.

---

## 3. Causal Discipline Construct & Epistemic Separation Audit

### The Intended Epistemic Standard
A high Causal Discipline score requires:
1. **Observation $ightarrow$ Inference $ightarrow$ Hypothesis Progression**: Clear structural separation between what was directly observed, what is logically deduced, and what remains an unverified theory.
2. **Proportionate Attribution**: Identifying an engineering bug matching telemetry timing as a primary explanation is disciplined product management; it does **not** require randomized A/B experimentation.
3. **No Free Passes**: Simply placing a claim under the heading `hypotheses` does not salvage it if the hypothesis makes extreme causal leaps contradicted by the ledger (e.g., 3 tickets $ightarrow$ "every user is overbilled").

---

### Disagreement Source Classification Table

| Case ID | Archetype | Human Ref (G, CD) | Judge (G, CD) | Groundedness Disagreement Source | Causal Discipline Disagreement Source | Primary Epistemic Driver |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `dev_01` | Diagnostic | 4, 3 | 3, 3 | `HUMAN_TOO_LENIENT` | **ALIGNED** | Human ignored unevidenced Bank A/B cohort addition; judge docked 1 point. |
| `dev_02` | Causality Trap | 1, 0 | 1, 0 | **ALIGNED** | **ALIGNED** | Extreme post-hoc fallacy correctly penalized by both. |
| `dev_03` | Segmentation Trap | 4, 4 | 2, 2 | `DIMENSION_CONFOUND` | `JUDGE_TOO_STRICT` | Truncated ledger snippet caused judge to view cohort metrics as unevidenced. |
| `dev_04` | Magnitude Trap | 1, 0 | 1, 0 | **ALIGNED** | **ALIGNED** | Wild magnitude extrapolation correctly penalized by both. |
| `dev_05` | Contradiction | 4, 4 | 3, 3 | `HUMAN_TOO_LENIENT` | `JUDGE_TOO_STRICT` | Human ignored minor timing embellishments; judge docked 1 point for UI attribution. |
| `dev_06` | Diagnostic | 4, 4 | 2, 2 | `HUMAN_TOO_LENIENT` | `RUBRIC_AMBIGUITY` | Human ignored invented v4.2 release tag; judge demanded A/B proof for timeout. |
| `dev_07` | Causality Trap | 1, 1 | 1, 0 | **ALIGNED** | **ALIGNED** | Premature vendor blame correctly penalized by both. |
| `dev_08` | Diagnostic | 4, 4 | 2, 3 | `HUMAN_TOO_LENIENT` | `RUBRIC_AMBIGUITY` | Human ignored invented 4% baseline; judge docked for "driving shift" phrasing. |
| `dev_09` | Diagnostic | 4, 4 | 2, 2 | `MIXED` | `RUBRIC_AMBIGUITY` | Human rewarded mechanical causal chain; judge penalized unevidenced API wording. |
| `dev_10` | Missing Evidence | 4, 4 | 4, 4 | **ALIGNED** | **ALIGNED** | Textbook epistemic humility recognized by both. |

---

## 4. Analysis of Borderline Statements

### 1. The Invented Baseline: *"Rose from 4% to 22%"* (`judge_dev_08`)
* **Evidence**: Telemetry shows 3DS failure rate is 22%.
* **Construct Analysis**: The 4% baseline is a **Category C (Unsupported Factual Addition)**. While it reflects realistic domain knowledge, it is absent from the evidence. Human raters awarded 4 by focusing on the 22% failure rate. Under the approved construct, an unevidenced historical baseline is an ungrounded factual claim. It belongs at **Score 3**, not Score 4. The judge docked to 2, which was overly punitive, but the human 4 was overly permissive.

### 2. The Unshown Release Identifier: *"Following v4.2 release"* (`judge_dev_06`)
* **Evidence**: PostHog shows 28% upload error; Jira KYC-88 shows missing Android compression.
* **Construct Analysis**: The release tag `"v4.2"` is a **Category C addition**. The SUT placed it inside `factual_observations`. Human raters overlooked this because the Android compression bug was verified. However, asserting a specific unshown release version as an observed fact violates groundedness. It should receive **Score 3**, not Score 4.

### 3. The Truncated Snippet: *"Latency breakdown by bank"* (`judge_dev_03`)
* **Evidence**: Ledger entry states only: `"query_latency: Latency breakdown by bank"`.
* **Construct Analysis**: The SUT cited: *"p95 latency is 52s for Bank A and B, but under 2s for Banks C and D"*. Human annotators knew the underlying query output and awarded 4. But to an independent auditor (or LLM judge) evaluating strictly against the retrieved snippet, the numbers 52s and 2s are unevidenced. This is a fixture artifact issue (`DIMENSION_CONFOUND`).

---

## 5. Final Construct Interpretation

To preserve strict measurement integrity without relaxing the grounding construct:

### Groundedness Construct
* **Score 4 (Excellent)**: Strictly 100% of factual observations and metrics are supported by the evidence ledger (Category A) or legitimately derived synthesis (Category B). Zero Category C additions (no invented baselines, release versions, or cohort metrics). Exploratory mechanisms must be explicitly segregated under `hypotheses`.
* **Score 3 (Good)**: Substantively grounded core findings, but contains minor Category C additions (e.g. plausible historical baseline numbers, minor unevidenced release tags, or slight descriptive embellishments) that do not alter the diagnostic conclusion.
* **Score 2 (Partially Adequate)**: Material Category C additions that distort the factual diagnosis (e.g. inventing non-existent error codes, non-existent server crashes, or fabricating central telemetry metrics), or presenting speculative inferences as observed facts.
* **Score 1 (Poor)**: Substantive factual claims have zero ledger support; extrapolates isolated complaints into unevidenced platform-wide catastrophes.
* **Score 0 (Completely Inadequate)**: Pervasive hallucination or fabricated citations.

### Causal Discipline Construct
* **Score 4 (Excellent)**: Strict Fact $ightarrow$ Inference $ightarrow$ Hypothesis separation. Connecting an engineering bug that temporally and mechanically matches a telemetry anomaly is PRAISED as disciplined PM reasoning. Does not require randomized A/B trials.
* **Score 3 (Good)**: Proper structural separation, but contains minor over-definitive phrasing in executive summaries (e.g. "caused" instead of "associated with").
* **Score 2 (Partially Adequate)**: Significant causal overreach: asserts definitive single-cause attribution when evidence is purely circumstantial without matching engineering tickets.
* **Score 1 (Poor)**: Severe causal overreach: falls directly into causality/magnitude traps.
* **Score 0 (Completely Inadequate)**: Pure post-hoc fallacy contradicted by evidence.

---

## 6. Methodological Recommendations & Next Steps

### Recommendation: **Option D — Mixed**

1. **Do NOT relax the Groundedness construct**:
   The audit confirms that the human reference scores in `judge_dev_06` and `judge_dev_08` were **overly lenient** relative to the strict construct by giving 4s to answers containing invented baselines ("4%") and unshown release tags ("v4.2"). The judge's refusal to award a 4 was structurally sound.
2. **Do NOT modify frozen validation reference ratings or fixtures**:
   The validation split must remain an immutable out-of-sample benchmark.
3. **Third Judge Revision Justification**:
   A third revision is **methodologically justified ONLY IF** it specifically addresses the Causal Discipline `RUBRIC_AMBIGUITY` (explicitly recognizing mechanical engineering attribution as disciplined PM practice) and aligns Groundedness score 3 with minor ungrounded baselines/tags (rather than dropping directly to 2).
4. **Current Status**:
   - The frozen judge validation run remains **FAILED**.
   - No benchmark runs (660 runs) have been executed.
   - Phase 10 has **NOT** begun.
   - All systems remain **STOPPED** awaiting user review of this Construct Validity Audit.
