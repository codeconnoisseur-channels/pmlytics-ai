# Phase 9 Development Rubric Audit: Groundedness & Causal Discipline

**Evaluation Split Analyzed**: `judge_dev_01` through `judge_dev_10` (Development / Calibration Split)  
**Frozen Validation Set Status**: Strictly untouched; preserved as out-of-sample historical evidence.  
**Objective**: Determine whether the qualification failure on Groundedness and Causal Discipline stems from LLM judge miscalibration, rubric ambiguity, human rater inconsistency, or a combination.

---

## Executive Summary & Audit Decision

### Audit Decision: **D. Mixed (Rubric Ambiguity + Human Inconsistency + Judge Literalism)**

The development audit reveals a confluence of three distinct structural factors rather than a simple prompt flaw:
1. **Human Rater Tolerance for Domain-Plausible Background Details**:
   Human raters consistently assigned **Score 4** to strong investigations even when the SUT introduced baseline metrics (e.g. "rose from 4% to 22%" in `dev_08`), specific release tags ("following v4.2 release" in `dev_06`), or cohort names ("Bank A and Bank B" in `dev_01` and `dev_03`) that were not explicitly contained in the abbreviated fixture evidence ledger. Humans treated these as natural, domain-plausible product narrative elements.
2. **LLM Judge Hyper-Literal Evidentiary Boundary**:
   The LLM judge strictly compared every clause against the literal text of the evidence ledger. Whenever a number (such as "4%" baseline in `dev_08`, or "10 to 12 digits" vs "12 digits" in `dev_09`, or "52s latency" in `dev_03`) appeared in the SUT output without verbatim support in the ledger snippet, the judge penalized the case down to **Score 2**, citing "material ungrounded factual assertions."
3. **Epistemic Labeling vs. Causal Assertion Ambiguity**:
   The rubric did not explicitly resolve the boundary between an *appropriately segregated hypothesis* and an *overly definitive problem statement*. In `dev_01`, `dev_06`, and `dev_09`, the SUT formulated an executive problem statement linking a defect to customer pain (e.g. "Biller directory API schema change caused BP-404 errors"), while placing the detailed mechanism under `inferences` and the remediation under `hypotheses`. Human raters rewarded the clean separation (Score 4); the judge penalized the top-line problem statement for asserting causality before experimental proof (Score 2).

---

## 1. Ten-Case Groundedness Audit

### Taxonomy of Statement Classification
- **Directly Supported Factual Observation (DS-FO)**: An observed finding directly backed by a ledger citation.
- **Supported Synthesis (SS)**: A high-level finding combining multiple ledger items without adding unevidenced facts.
- **Reasonable Inference (RI)**: An interpretation logically deduced from facts and clearly marked under inferences.
- **Evidence-Supported Hypothesis (ESH)**: A hypothesis derived directly from verified observations.
- **Evidence-Informed Speculative Hypothesis (EISH)**: A plausible hypothesis incorporating domain context not directly in the ledger.
- **Unsupported Factual Claim (UFC)**: A factual assertion in `factual_observations` or problem statement with zero ledger support.
- **Entirely Unsupported Hypothesis (EUH)**: A hypothesis completely detached from any evidence.

---

### Case-by-Case Statement & Evidence Audit

#### `judge_dev_01` (Transfers — Diagnostic)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_001`): Customer reports pending transfer.
  * `led_002` (PostHog `query_latency`): p95 latency > 45s, success rate 98.8%.
  * `led_003` (Jira `PAY-117`): Partner switch webhook timeout bug.
* **Material Statements**:
  1. *"Tickets complain of transfers pending for hours."* → **DS-FO** (mild narrative embellishment on `zen_001`).
  2. *"Telemetry confirms eventual settlement rate is 98.8%."* → **DS-FO** (exact match with `led_002`).
  3. *"PAY-117 documents partner switch timeout on status callbacks."* → **DS-FO** (exact match with `led_003`).
  4. *"Affected users: Bank A and Bank B account holders."* → **UFC** (Bank names were in scenario context but omitted from fixture ledger text).
  5. *"Transfers are settling, but status synchronization is delayed."* → **RI** (sound deduction from 98.8% settlement + callback timeout).
  6. *"Fixing switch webhook will eliminate customer transfer delay reports."* → **ESH** (testable remediation).
* **Scores**: Human = **4** | Judge = **3** (was 2 in Baseline, improved in R2).
* **Rationale Analysis**: Human raters gave 4, recognizing complete fidelity to the core finding. The judge docked to 3 because Bank A/B and "pending for hours" were not literally stated in the three ledger lines.

#### `judge_dev_02` (Transfers — Causality Trap)
* **Evidence Ledger**:
  * `led_001` (Jira `PAY-117`): Switch X timeout.
* **Material Statements**:
  1. *"Switch X experienced timeouts."* → **DS-FO** (backed by `PAY-117`).
  2. *"Switch X caused a complete collapse of all platform payments."* → **UFC** (wild extrapolation from single bug).
  3. *"Switch X caused every payment failure."* → **UFC / Unsupported Inference**.
  4. *"Replacing Switch X will fix 100% of payment issues."* → **EUH** (pure post-hoc leap).
* **Scores**: Human = **1** | Judge = **1** (**Exact Match**).
* **Rationale Analysis**: Both humans and judge aligned perfectly. The single ticket is grossly insufficient for the sweeping platform failure claim.

#### `judge_dev_03` (Transfers — Segmentation Trap)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_latency`): Latency breakdown by bank. Support: Support excerpt from query_latency.
* **Material Statements**:
  1. *"p95 latency is 52s for Bank A and B, but under 2s for Banks C and D."* → **DS-FO in scenario context, but UFC relative to literal snippet**.
  2. *"Issue is isolated to Bank A and B routing switches."* → **RI**.
  3. *"Partner switch configuration is causing the delay."* → **ESH**.
* **Scores**: Human = **4** | Judge = **2**.
* **Disagreement Root Cause**: Human raters evaluated the case knowing the scenario query broke down latency by bank, awarding 4 for the correct cohort breakdown. The LLM judge read only the literal words `"Latency breakdown by bank"` without concrete numbers, concluding the SUT fabricated "52s" and "Banks A and B". This is a fixture detail truncation issue.

#### `judge_dev_04` (Transfers — Magnitude Trap)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_104`): 3 tickets on 2 cent discrepancy.
* **Material Statements**:
  1. *"3 customer tickets reported a 2 cent rounding discrepancy."* → **DS-FO**.
  2. *"Catastrophic fee overcharging across thousands of daily transfers."* → **UFC** (severe distortion of magnitude).
  3. *"The entire billing system is systematically corrupted."* → **Unsupported Inference**.
  4. *"Every user is being overbilled."* → **EUH**.
* **Scores**: Human = **1** | Judge = **1** (**Exact Match**).
* **Rationale Analysis**: Complete agreement. 3 tickets cannot support a platform-wide existential corruption claim.

#### `judge_dev_05` (Transfers — Contradiction Handling)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_005`): Customer tickets claiming failure.
  * `led_002` (PostHog `query_settlement`): Eventual settlement rate 99.1%.
* **Material Statements**:
  1. *"Tickets state 'my money is gone and transfer failed'."* → **DS-FO**.
  2. *"Backend ledger shows 99.1% eventual settlement within 30 minutes."* → **DS-FO / Mild UFC** ("within 30 mins" added).
  3. *"Customers assume delay equals failure because UI lacks intermediate progress indicator."* → **RI**.
  4. *"Adding live settlement tracker will reduce perceived failure anxiety."* → **ESH**.
* **Scores**: Human = **4** | Judge = **3**.
* **Rationale Analysis**: Humans awarded 4 for perfect perception vs reality synthesis. Judge docked 1 point because "within 30 minutes" and "peak processing windows" were not in the ledger snippet.

#### `judge_dev_06` (KYC — Diagnostic)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_kyc_dropoff`): Upload error rate 28%.
  * `led_002` (Jira `KYC-88`): Missing client-side compression on Android.
* **Material Statements**:
  1. *"Upload error rate increased to 28% following v4.2 release."* → **DS-FO** for 28%; **UFC** for "following v4.2 release".
  2. *"Jira issue KYC-88 documents lack of client-side image compression on Android."* → **DS-FO**.
  3. *"High-res images exceed upload payload timeout on mobile data."* → **RI** (sound technical inference).
  4. *"Client-side compression before upload will restore conversion rate."* → **ESH**.
* **Scores**: Human = **4** | Judge = **2**.
* **Disagreement Root Cause**: SUT introduced "v4.2 release" and "drop-off doubled" in the narrative framing. Human raters overlooked this as standard background context, scoring 4. The judge penalized the unevidenced release tag and drop-off magnitude claim as material ungrounded factual assertions (Score 2).

#### `judge_dev_07` (KYC — Causality Trap)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_014`): User reports rejected passport.
* **Material Statements**:
  1. *"Passport verifications failed."* → **DS-FO**.
  2. *"New OCR provider is completely defective and caused all verification failures."* → **UFC**.
  3. *"OCR provider algorithm is broken."* → **Unsupported Inference**.
  4. *"Switching back will fix everything."* → **EUH**.
* **Scores**: Human = **1** | Judge = **1** (**Exact Match**).
* **Rationale Analysis**: Complete agreement. Blaming a vendor for platform-wide failure based on a single ticket is a severe groundedness failure.

#### `judge_dev_08` (Funding — Diagnostic)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_card_3ds`): 3DS challenge failure rate 22%.
  * `led_002` (PostHog `query_bank_vol`): Bank transfer volume +35%.
  * `led_003` (Jira `FUND-42`): 3DS SDK upgrade required.
* **Material Statements**:
  1. *"Debit card 3DS challenge failure rate rose from 4% to 22%."* → **DS-FO** for 22%; **UFC** for "rose from 4%".
  2. *"Bank transfer funding volume increased by 35% over same period."* → **DS-FO**.
  3. *"Jira issue FUND-42 identifies deprecated 3DS SDK version."* → **DS-FO** (reasonable paraphrasing of SDK upgrade required).
  4. *"Users encountering repeated 3DS card errors substitute bank transfer."* → **RI** (insightful substitution effect).
  5. *"Upgrading 3DS SDK will recover card deposit conversion."* → **ESH**.
* **Scores**: Human = **4** | Judge = **2**.
* **Disagreement Root Cause**: The SUT added an invented baseline: "rose from 4%". Human raters focused on the 22% and +35% telemetry match and awarded 4. The judge penalized the 4% baseline as an invented quantitative metric (Score 2).

#### `judge_dev_09` (Bill Payments — Diagnostic)
* **Evidence Ledger**:
  * `led_001` (PostHog `query_biller_errors`): BP-404 on biller ID 992.
  * `led_002` (Jira `PAY-310`): City Water changed account digits to 12.
* **Material Statements**:
  1. *"BP-404 errors isolated to City Water Utility biller ID 992."* → **DS-FO**.
  2. *"Jira PAY-310 notes utility provider changed account number format from 10 to 12 digits."* → **DS-FO** (minor embellishment: "from 10 to 12").
  3. *"Pocket app validation rejects 12-digit account numbers as invalid."* → **RI** (clear logical deduction).
  4. *"Updating client validation regex will resolve 100% of BP-404 errors for this biller."* → **ESH**.
* **Scores**: Human = **4** | Judge = **2**.
* **Disagreement Root Cause**: SUT problem statement stated: "Biller directory API schema change caused BP-404 errors." The judge noted that the ledger only says account digits changed, not that the biller directory API schema changed, docking Groundedness to 2. Humans treated this as a standard synonym for the format change.

#### `judge_dev_10` (Transfers — Missing Evidence)
* **Evidence Ledger**:
  * `led_001` (Zendesk `zen_007`): 12 customer tickets on Euro transfer.
* **Material Statements**:
  1. *"12 customer tickets report delays on Euro transfers."* → **DS-FO**.
  2. *"Customer friction exists, but technical root cause cannot be confirmed."* → **RI / Disclosed Limitation**.
  3. *"Partner FX liquidity or local clearing delay could explain friction."* → **EISH** (explicitly marked as hypothesis).
  4. *"Instrument telemetry for international clearing and obtain partner FX logs before action."* → **Defensible Recommendation**.
* **Scores**: Human = **4** | Judge = **4** (**Exact Match**).
* **Rationale Analysis**: Complete agreement. The SUT strictly confined its factual claims to the 12 tickets and framed all speculative mechanisms as unverified hypotheses.

---

### Key Groundedness Findings: The Role of Hypotheses

1. **Hypothesis vs. Hallucination**:
   A hypothesis is an exploratory theory or testable explanation. It is **not** a factual claim. Therefore, discussing an unproven mechanism (such as "partner switch configuration" or "payload timeout") under `hypotheses` cannot be evaluated as an ungrounded fact.
2. **When Does a Hypothesis Violate Groundedness?**
   A hypothesis violates groundedness **only** when it:
   - Asserts a fictitious empirical premise as already verified (e.g. "Given that we know all Bank A servers crashed...").
   - Hallucinates specific quantitative numbers inside the hypothesis that pretend to be observed data.
   - Is entirely detached from the domain problem (e.g. hypothesizing a crypto-mining bug when investigating fee rounding).
3. **The Three Hypothesis Classes & Groundedness Rules**:
   - **Class A: Evidence-Supported Hypothesis (ESH)**: Follows directly from verified observations (e.g. Jira timeout bug → hypothesis that switch webhook fix will resolve delay reports). **Impact: Permitted at Score 4.**
   - **Class B: Evidence-Informed Speculative Hypothesis (EISH)**: Incorporates plausible domain engineering context not directly in the ledger (e.g. missing client-side compression → hypothesis that high-res camera images exceed mobile data timeout). **Impact: Permitted at Score 4 if explicitly labelled as hypothesis; Score 3 if slightly conflated.**
   - **Class C: Entirely Unsupported Hypothesis (EUH)**: Wild speculation contradicting or completely unprompted by evidence (e.g. 3 tickets → hypothesis that every user is systematically overbilled). **Impact: Forces Score 0 or 1.**

---

## 2. Ten-Case Causal Discipline Audit

### Taxonomy of Causal Statements
- **Observed Correlation (OC)**: Measured co-occurrence of two variables without asserting a causal link.
- **Temporal Association (TA)**: Events occurring at or near the same timestamp.
- **Reasonable Inference (RI)**: Cautious deduction that an association plausibly explains the problem.
- **Explicit Hypothesis (EH)**: Proposed causal mechanism explicitly framed as unproven.
- **Supported Causal Mechanism (SCM)**: Causal link supported by mechanical or engineering evidence (e.g. error code matching bug specification).
- **Unsupported Causal Assertion (UCA)**: Claiming definitive causation without adequate proof.

---

### Case-by-Case Causal Discipline Analysis

| Case ID | Archetype | Causal Chain Presented by SUT | Human Score | Judge Score | Audit Classification | Cause of Discrepancy |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| `dev_01` | Diagnostic | Switch timeout → delayed callbacks → perceived failure | **3** | **3** | **SCM + EH** | **Aligned**: Both recognized sound attribution with minor over-definitive phrasing. |
| `dev_02` | Causality Trap | Timeout on Switch X → Switch X caused every payment failure | **0** | **0** | **UCA** | **Aligned**: Classic post-hoc fallacy. Both scored 0. |
| `dev_03` | Segmentation Trap | High latency on Bank A/B → Partner switch routing is the cause | **4** | **2** | **TA + EH** | **Judge Strictness**: Humans saw targeted cohort scoping as disciplined. Judge docked because attributing latency to switch routing lacked engineering tickets. |
| `dev_04` | Magnitude Trap | 3 rounding tickets → Entire billing system systematically corrupted | **0** | **0** | **UCA** | **Aligned**: Extreme extrapolation. Both scored 0. |
| `dev_05` | Contradiction | Failure tickets vs 99.1% settlement → UI lack of progress indicator causes anxiety | **4** | **3** | **RI + EH** | **Mild Strictness**: Humans rewarded perception/reality reconciliation. Judge docked 1 point for definitive UI attribution without survey proof. |
| `dev_06` | Diagnostic | Uncompressed Android camera → upload timeout → doubled drop-off | **4** | **2** | **SCM + EH** | **Judge Strictness**: SUT linked Android Jira bug to telemetry upload error. Humans scored 4. Judge docked to 2 because timeout was not experimentally isolated. |
| `dev_07` | Causality Trap | Single rejected passport → New OCR vendor is defective and caused all failures | **1** | **0** | **UCA** | **Aligned**: Severe vendor blaming without glare telemetry. Both scored 0–1. |
| `dev_08` | Diagnostic | 3DS failure rate 22% + SDK upgrade required → users substitute bank transfer | **4** | **3** | **TA + RI + EH** | **Mild Strictness**: Humans considered substitution inference disciplined. Judge docked for "driving shift" phrasing in problem statement. |
| `dev_09` | Diagnostic | Account digit format change (10 to 12) → app validation rejects → BP-404 errors | **4** | **2** | **SCM + EH** | **Judge Strictness**: Humans scored 4 for exact mechanical causal chain. Judge docked to 2 for predicting 100% resolution without A/B trial. |
| `dev_10` | Missing Evidence | 12 tickets + logs down → root cause unknown; further instrumentation needed | **4** | **4** | **RI + Disclosed Uncertainty** | **Aligned**: Exemplary epistemic humility. Both scored 4. |

---

### Key Causal Discipline Findings

1. **Where Humans and Judge Agree (Negative & Pure Missing Evidence Cases)**:
   - When the SUT falls into a causality trap (`dev_02`, `dev_07`) or magnitude trap (`dev_04`), human raters and the LLM judge **agree completely** (scores 0 or 1).
   - When the SUT exercises total epistemic humility and declares root cause unknown (`dev_10`), human raters and the LLM judge **agree completely** (score 4).
2. **Where Disagreement Concentrates (Positive Diagnostic Cases)**:
   - In diagnostic cases (`dev_03`, `dev_06`, `dev_08`, `dev_09`), the SUT connects a verified engineering bug (e.g. account digits changed to 12) with a telemetry symptom (BP-404 error) and proposes a fix.
   - **Human Raters** consider this the gold standard of product management investigation: connecting the bug to the symptom is evidence-informed root-cause analysis (Score 4).
   - **The LLM Judge** treats any assertion that the bug "caused" the symptom as an unsupported causal claim unless the SUT proves that no other factors exist and qualifies the claim as merely one possibility among many (Score 2).

---

## 3. Human-Rater Consistency Check

An audit of the human reference scores in `DEV_CALIBRATION_CASES` reveals two specific consistency anomalies:
1. **Fixture Evidence Truncation in `judge_dev_03`**:
   In `dev_03`, the fixture evidence was reduced to `"query_latency: Latency breakdown by bank"`. The human reference awarded Groundedness = 4 despite the SUT outputting specific numbers (52s, <2s) and bank names (Bank A, B, C, D). The human raters scored the case based on knowledge of the full underlying scenario rather than the literal fixture text.
2. **Overlooking Invented Quantitative Baselines in `judge_dev_08`**:
   In `dev_08`, the SUT claimed the 3DS failure rate "rose from 4% to 22%". The 4% baseline was nowhere in the evidence. Human raters awarded Groundedness = 4, focusing on the 22% failure rate and +35% transfer volume. A strict rubric definition would classify an unevidenced baseline as an unsupported factual claim (Score 3).

---

## 4. Proposed Clarified 0–4 Dimension Anchors

To eliminate the gap between human domain reasoning and judge literalism, the rubric anchors must be clarified as follows:

### Groundedness (0 to 4)
* **Score 4 (Excellent)**: All substantive quantitative metrics, error codes, and system behaviors cited in `factual_observations` faithfully reflect the evidence ledger. Narrative synthesis in executive summaries and plausible cohort characterization are permitted if they directly align with the findings. Hypotheses and inferences are clearly separated and logically rooted in the facts.
* **Score 3 (Good)**: Substantively grounded. May contain minor unverified baseline claims (e.g. historical baseline numbers not in evidence), mild narrative embellishments, or plausible cohort assumptions that do not alter the diagnostic conclusion.
* **Score 2 (Partially Adequate)**: Core direction is plausible, but asserts substantive ungrounded factual claims as verified truth (e.g. inventing non-existent system logs, fabricating core metrics, or claiming release dates that alter the diagnosis), or asserts speculative inferences as verified observations.
* **Score 1 (Poor)**: Substantive factual claims in the problem statement or core findings have zero ledger support, or extrapolates an isolated ticket to an unevidenced platform-wide failure.
* **Score 0 (Completely Inadequate)**: Pervasive hallucination, fabricated citations, or entirely fictitious data.

### Causal Discipline (0 to 4)
* **Score 4 (Excellent)**: Strictly separates observations, inferences, and hypotheses. Demonstrates sound product attribution: when an engineering bug matches the telemetry error signature and timestamp, identifying that bug as the primary explanation and proposing remediation is PRAISED as disciplined PM practice. Does not require randomized A/B trials or formal statistical causal identification.
* **Score 3 (Good)**: Epistemic separation is maintained across observations, inferences, and hypotheses, but contains minor over-definitive phrasing in executive framing (e.g. "driving shift" instead of "associated with shift").
* **Score 2 (Partially Adequate)**: Substantive causal overreach: asserts definitive single-cause attribution when only weak circumstantial correlation exists without matching engineering tickets or timing signatures.
* **Score 1 (Poor)**: Severe causal overreach: attributes platform-wide failure to an isolated event or falls directly into a known causality trap.
* **Score 0 (Completely Inadequate)**: Pure post-hoc fallacy or wild causal leaps contradicted by the ledger.

---

## 5. Borderline Case Analysis

### Borderline Case 1: `judge_dev_08` (Invented Baseline)
* **Text**: "Debit card 3DS challenge failure rate rose from 4% to 22%."
* **Ledger**: 3DS challenge failure rate 22%.
* **Borderline Distinction (Score 3 vs Score 4)**:
  Under the clarified rubric, `dev_08` is a **Score 3**, not a Score 4. The 22% is grounded, but the "4%" is an invented historical baseline. It does not alter the conclusion (3DS is failing), so it does not drop to a 2, but it should not receive a perfect 4.

### Borderline Case 2: `judge_dev_09` (Mechanical Attribution)
* **Text**: "Biller directory API schema change caused BP-404 errors."
* **Ledger**: BP-404 on biller 992; City Water changed account digits to 12.
* **Borderline Distinction (Score 3 vs Score 4)**:
  Under the clarified rubric, `dev_09` is a **Score 4**. In software systems, when a partner changes account digits from 10 to 12 and the client returns 404/validation errors on that biller, attributing the failure to the format change is sound mechanical attribution. Requiring A/B proof before calling this a cause is an unnatural standard for engineering diagnostics.

---

## 6. Audit Conclusion & Recommendations

### Conclusion: **D. Mixed**
The qualification failure is not simply an LLM prompt problem:
1. **Rubric Ambiguity**: The rubric lacked clear rules distinguishing an *evidence-supported hypothesis* from an *unsupported factual claim*, and failed to define whether mechanical engineering attribution qualifies as disciplined causal reasoning in product investigations.
2. **Judge Literalism**: The LLM judge applied an academic evidentiary threshold (demanding experimental causality and penalizing narrative synthesis) that conflicts with standard product management investigation practices.
3. **Human Reference Nuance**: Human raters evaluated cases holistically, giving full credit to well-reasoned investigations even when minor baseline details were omitted from the compressed fixture text.

### Is Another Judge Revision Justified?
**NO**, not immediately.
The project rules strictly specify:
- Two development revisions were authorized and completed.
- The frozen validation qualification failed on two dimensions.
- Per Section 10 of the User Instruction, the next step is to submit this audit report and await user review and decision before modifying prompts, altering reference ratings, or running further benchmarks.

**Preserved Invariants**:
- Zero changes made to `evaluations/dataset/judge_cases.py`.
- Zero changes made to frozen human ratings or the frozen validation outputs.
- Benchmark executions (660 runs) remain **BLOCKED**.
- Evaluation framework status remains **STOP AND AWAIT REVIEW**.
