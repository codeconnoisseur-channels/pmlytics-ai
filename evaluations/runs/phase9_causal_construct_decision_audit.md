# Phase 9 Targeted Causal Discipline Construct Decision Audit

**Evaluation Dataset**: 10 Development Calibration Cases (`judge_dev_01` through `judge_dev_10`)  
**Frozen Validation Status**: Strictly untouched; preserved as out-of-sample historical evidence.  
**Human Reference Status**: Strictly untouched; historical ratings preserved for auditability.  
**Target Dimension**: `causal_discipline`  
**Core Purpose**: Audit the epistemic boundary of Causal Discipline, classify every candidate causal statement across fields, answer the justified causal language standard, resolve the decision taxonomy, and determine protocol amendment requirements.

---

## 1. Formal Decision

### **Decision: RUBRIC_AMBIGUOUS**

### Justification from Development Cases:
The 10 development cases demonstrate that the disagreement between human raters and the LLM judge on Causal Discipline is fundamentally driven by **unresolved ambiguity in the scoring rubric**:
1. **Silence on Executive Summary Framing**: The rubric instructs the judge to evaluate whether the system *"resists premature causal conclusions and correlation traps"*, but does not specify how the executive `problem_statement` interacts with the structured fields. When a candidate uses an unhedged causal verb in its executive title (*"due to"* in `dev_06`, *"caused"* in `dev_09`), human raters treat this as an executive summary of the investigation's focus and award **Score 4** because the detailed mechanism is properly segregated under `inferences` and `hypotheses`. Conversely, the LLM judge penalizes the unhedged executive title as a fatal causal overreach, docking the entire case to **Score 2**.
2. **Ambiguity on Mechanical Engineering Attribution**: In diagnostic investigations (`dev_06`, `dev_08`, `dev_09`), an engineering bug (e.g. Jira issue documenting missing client-side compression or account digits changed to 12) temporally and mechanically matches a telemetry failure spike (28% upload error or BP-404 errors). The rubric did not define whether identifying this bug as the primary explanatory mechanism and proposing remediation constitutes *disciplined PM attribution* or an *unsupported causal leap*. Human raters regarded this as textbook PM root-cause analysis (Score 4), while the judge demanded component-level proof of exclusivity (Score 2).

---

## 2. Statement-by-Statement Causal Classification Across the 10 Development Cases

### Taxonomy of Causal Statements
- **Class A: Directly Evidenced Causal Relationship**: Causal link explicitly established and measured by the evidence record itself.
- **Class B: Legitimate Evidence-Based Inference**: Causal relationship logically deduced from concurrent, matching multi-source evidence and framed with appropriate epistemic qualifiers (*"consistent with"*, *"indicates"*, *"associated with"*).
- **Class C: Evidence-Informed Hypothesis**: Proposed causal mechanism or testable theory explicitly framed as a hypothesis (*"hypothesize that"*, *"may resolve"*).
- **Class D: Unsupported Causal Assertion**: Definitive, unhedged causal claim (*"caused"*, *"due to"*, *"drove 100%"*) where evidence establishes only association or plausible mechanics.
- **Class E: Post-Hoc or Contradicted Causal Claim**: Blatant post-hoc ergo propter hoc fallacy, vendor blaming, or causal claim contradicted by available data.

---

### Case-by-Case Causal Statement Inventory

#### `judge_dev_01` (Transfers — Diagnostic)
* **Evidence**: Zendesk pending transfer (`zen_001`); PostHog latency >45s, 98.8% settlement (`query_latency`); Jira webhook timeout bug (`PAY-117`).
* **Causal Statements by Field**:
  * `executive_summary`: *"Partner switch callback timeouts causing perceived transfer failures."* -> **Class D** (unhedged "causing" in title).
  * `factual_observations`: Purely observational (settlement 98.8%, timeout bug noted). -> **Class A**.
  * `inferences`: *"Transfers are settling, but status synchronization is delayed."* -> **Class B** (properly qualified deduction).
  * `hypotheses`: *"Fixing switch webhook will eliminate customer transfer delay reports."* -> **Class C** (testable remediation hypothesis).
  * `recommendation`: Deploy timeout fix and add UI status banner. -> Disciplined, proportionate action.
* **Scores**: Human = **3** | Judge = **3** (**Exact Agreement**).

---

#### `judge_dev_02` (Transfers — Causality Trap)
* **Evidence**: Jira switch timeout (`PAY-117`).
* **Causal Statements by Field**:
  * `executive_summary`: *"Switch X caused a complete collapse of all platform payments."* -> **Class E** (wild post-hoc leap).
  * `factual_observations`: *"Switch X experienced timeouts."* -> **Class A**.
  * `inferences`: *"Therefore Switch X caused every payment failure."* -> **Class E** (blatant fallacy).
  * `hypotheses`: *"Replacing Switch X will fix 100% of payment issues."* -> **Class E** (extreme overreach).
  * `recommendation`: Terminate partner Switch X contract platform-wide. -> Dangerous overreach.
* **Scores**: Human = **0** | Judge = **0** (**Exact Agreement**).

---

#### `judge_dev_03` (Transfers — Segmentation Trap)
* **Evidence**: PostHog latency breakdown by bank (`query_latency`).
* **Causal Statements by Field**:
  * `executive_summary`: *"Transfer delays selectively impacting Bank A and Bank B accounts."* -> **Class B** (valid cohort association).
  * `factual_observations`: Latency numbers cited by bank. -> Observational.
  * `inferences`: *"Issue is isolated to Bank A and B routing switches."* -> **Class B / Class D** (routing switch inferred without engineering evidence).
  * `hypotheses`: *"Partner switch configuration is causing the delay."* -> **Class C** (acceptable as hypothesis, but unhedged "causing").
  * `recommendation`: Target partner switch routing patch for Banks A and B only. -> Premature fix without engineering ticket.
* **Scores**: Human = **4** | Judge = **2** (Disagreement: 2 points).
* **Audit Finding**: SUT lacked engineering evidence for a "routing switch" defect. The inference overreached from telemetry correlation to an unevidenced hardware component. Human raters were too lenient (Score 4); the judge correctly noted the gap between bank correlation and switch root cause (Score 2).

---

#### `judge_dev_04` (Transfers — Magnitude Trap)
* **Evidence**: Zendesk 3 tickets on 2 cent discrepancy (`zen_104`).
* **Causal Statements by Field**:
  * `executive_summary`: *"Catastrophic fee overcharging across thousands of daily transfers."* -> **Class E**.
  * `factual_observations`: 3 customer tickets cited. -> **Class A**.
  * `inferences`: *"The entire billing system is systematically corrupted."* -> **Class E**.
  * `hypotheses`: *"Every user is being overbilled."* -> **Class E**.
  * `recommendation`: Halt platform billing and refund historical fees. -> Destructive overreach.
* **Scores**: Human = **0** | Judge = **0** (**Exact Agreement**).

---

#### `judge_dev_05` (Transfers — Contradiction Handling)
* **Evidence**: Zendesk customer claims money gone (`zen_005`); PostHog 99.1% eventual settlement (`query_settlement`).
* **Causal Statements by Field**:
  * `executive_summary`: *"Perceived transfer failures contrast with confirmed backend settlement."* -> **Class B** (sound tension framing).
  * `factual_observations`: Purely observational (tickets vs settlement). -> **Class A**.
  * `inferences`: *"Customers assume delay equals failure because UI lacks intermediate progress indicator."* -> **Class B** (sound behavioural inference).
  * `hypotheses`: *"Adding live settlement tracker will reduce perceived failure anxiety."* -> **Class C**.
  * `recommendation`: Add real-time progress state in mobile app. -> Proportionate product fix.
* **Scores**: Human = **4** | Judge = **3** (1-point difference).
* **Audit Finding**: Minor disagreement. SUT reasoned cleanly. Judge docked 1 point because the UI explanation lacked explicit survey evidence.

---

#### `judge_dev_06` (KYC — Diagnostic)
* **Evidence**: PostHog upload error rate 28% (`query_kyc_dropoff`); Jira KYC-88 missing Android compression.
* **Causal Statements by Field**:
  * `executive_summary`: *"Document verification drop-off doubled due to uncompressed camera uploads failing timeout."* -> **Class D** (unhedged "due to" asserting causal chain in title).
  * `factual_observations`: Upload error rate 28%; KYC-88 documents lack of compression. -> **Class A** (plus unevidenced release tag).
  * `inferences`: *"High-res images exceed upload payload timeout on mobile data."* -> **Class B** (highly plausible mechanical deduction).
  * `hypotheses`: *"Client-side compression before upload will restore conversion rate."* -> **Class C** (properly qualified expectation).
  * `recommendation`: Implement client-side JPEG compression and increase API timeout threshold. -> Best-practice technical fix.
* **Scores**: Human = **4** | Judge = **2** (Disagreement: 2 points).
* **Audit Finding**: Key disagreement case. SUT had a strong mechanical and temporal match (Android compression bug + upload error spike). The body maintained proper epistemic separation (mechanism under inferences, recovery under hypotheses). However, the executive problem statement asserted definitive causation (*"due to"*). Human raters gave 4 for the sound engineering chain. The judge gave 2 for the definitive executive claim.

---

#### `judge_dev_07` (KYC — Causality Trap)
* **Evidence**: Zendesk 1 user rejected passport (`zen_014`).
* **Causal Statements by Field**:
  * `executive_summary`: *"New OCR provider is completely defective and caused all verification failures."* -> **Class E**.
  * `factual_observations`: Passport verifications failed. -> **Class A**.
  * `inferences`: *"OCR provider algorithm is broken."* -> **Class E**.
  * `hypotheses`: *"Switching back will fix everything."* -> **Class E**.
  * `recommendation`: Immediately roll back OCR vendor integration. -> Unjustified vendor blame.
* **Scores**: Human = **1** | Judge = **0** (**Aligned**).

---

#### `judge_dev_08` (Funding — Diagnostic)
* **Evidence**: PostHog 3DS challenge failure 22% (`query_card_3ds`); PostHog bank volume +35% (`query_bank_vol`); Jira FUND-42 SDK upgrade required.
* **Causal Statements by Field**:
  * `executive_summary`: *"3DS authentication failures on debit cards driving shift to bank transfers."* -> **Class B / Class D** ("driving shift" is slightly strong for association).
  * `factual_observations`: 22% failure rate; +35% bank volume; SDK upgrade required. -> **Class A** (plus unevidenced 4% baseline).
  * `inferences`: *"Users encountering repeated 3DS card errors substitute bank transfer."* -> **Class B** (insightful substitution inference).
  * `hypotheses`: *"Upgrading 3DS SDK will recover card deposit conversion."* -> **Class C**.
  * `recommendation`: Upgrade 3DS mobile SDK to v2.2 and add fallback notice. -> Defensible remediation.
* **Scores**: Human = **4** | Judge = **3** (1-point difference).
* **Audit Finding**: SUT reasoned well. Judge docked 1 point for "driving shift" phrasing.

---

#### `judge_dev_09` (Bill Payments — Diagnostic)
* **Evidence**: PostHog BP-404 on biller ID 992 (`query_biller_errors`); Jira PAY-310 City Water changed account digits to 12.
* **Causal Statements by Field**:
  * `executive_summary`: *"Biller directory API schema change caused BP-404 errors for water utility."* -> **Class D** (unhedged "caused" + unevidenced "biller directory API" phrasing).
  * `factual_observations`: BP-404 on biller 992; format changed to 12 digits. -> **Class A**.
  * `inferences`: *"Pocket app validation rejects 12-digit account numbers as invalid."* -> **Class B** (exact logical deduction).
  * `hypotheses`: *"Updating client validation regex will resolve 100% of BP-404 errors for this biller."* -> **Class D inside Hypothesis** (unhedged "resolve 100%").
  * `recommendation`: Update biller account regex in configuration service. -> Safe, scoped fix.
* **Scores**: Human = **4** | Judge = **2** (Disagreement: 2 points).
* **Audit Finding**: The mechanical causal match between 12-digit account change and validation 404 is exact. However, the SUT framed the executive summary as definitive ("caused") and claimed "100%" certainty in its hypothesis. Human raters awarded 4 for the correct diagnosis. The judge docked to 2 for unhedged causal assertions.

---

#### `judge_dev_10` (Transfers — Missing Evidence)
* **Evidence**: Zendesk 12 tickets on Euro transfer delays (`zen_007`).
* **Causal Statements by Field**:
  * `executive_summary`: *"Insufficient evidence to determine root cause of international transfer delays."* -> **Class B** (disciplined uncertainty).
  * `factual_observations`: 12 customer tickets report delays. -> **Class A**.
  * `inferences`: *"Customer friction exists, but technical root cause cannot be confirmed."* -> **Class B**.
  * `hypotheses`: *"Partner FX liquidity or local clearing delay could explain friction."* -> **Class C** (properly qualified exploratory theories).
  * `recommendation`: Instrument telemetry and obtain partner FX logs before action. -> Exemplary PM humility.
* **Scores**: Human = **4** | Judge = **4** (**Exact Agreement**).

---

## 3. Core Construct Question Answered

> **“When engineering evidence and telemetry provide a strong temporal and mechanical match, what level of causal language is justified, and how should the score change depending on whether the relationship is presented as an observation, inference, hypothesis, or definitive fact?”**

### The Approved Evidentiary Boundary:
1. **In `factual_observations`**:
   - **Justified Language**: Strictly observational. What was measured, logged, or reported.
   - **Forbidden Language**: Causal link words (*"caused"*, *"because"*, *"due to"*).
   - **Scoring Impact**: Placing a causal conclusion inside `factual_observations` conflates observation with interpretation, warranting a penalty (precludes Score 4).
2. **In `inferences`**:
   - **Justified Language**: Evidence-supported deductions expressing explanatory connection with appropriate epistemic qualification (*"indicates that X contributes to Y"*, *"is consistent with X explaining Y"*, *"suggests X is the primary driver"*).
   - **Forbidden Language**: Unqualified declarations of absolute causality that rule out all unmeasured factors without evidence.
   - **Scoring Impact**: Formulating a mechanically plausible explanation from matching engineering and telemetry evidence under `inferences` is disciplined PM reasoning and is **fully compatible with Score 4**.
3. **In `hypotheses`**:
   - **Justified Language**: Testable operational theories and expected remediation outcomes (*"Hypothesize that deploying patch X will reduce failure rate Y"*, *"Mechanism may be uncompressed payload timeout"*).
   - **Forbidden Language**: Predictions of unconditional 100% resolution, or wild speculative storytelling detached from verified facts.
   - **Scoring Impact**: Evidence-informed hypotheses are **fully compatible with Score 4**. Over-certain predictions (*"resolve 100%"*) warrant a 1-point deduction to Score 3.
4. **In `problem_statement` / Executive Summary**:
   - **Justified Language**: Framing the investigation's focus using associative or explanatory language (*"Transfer delay reports linked to partner callback timeouts"*, *"Investigation into 3DS failure impact on card deposits"*).
   - **Language Tolerance & Scoring**: If an executive summary uses a shorthand causal verb (*"due to"*, *"caused by"*), but the underlying body strictly segregates the mechanism into `inferences` and `hypotheses`:
     * This constitutes a minor executive over-statement, NOT a collapse of causal discipline.
     * **Score Impact: Score 3 (Good)**. It should be docked 1 point from 4, but must **NOT** be collapsed to Score 2.
     * A score of **2 (Partially Adequate)** is reserved for cases where the body itself conflates correlation with causation or asserts definitive causality without matching engineering/telemetry evidence.

---

## 4. Evaluation of the Eight Construct Invariants

| Invariant | Description | Audit Finding Across Dev Cases |
| :---: | :--- | :--- |
| **1** | A/B/C receive high scores when epistemic status is represented correctly. | **Confirmed**: `dev_01`, `dev_05`, `dev_10` scored 3 or 4 when A/B/C were properly placed. |
| **2** | Mechanically plausible mechanism does not automatically become an established causal fact. | **Confirmed**: SUT in `dev_06` and `dev_09` had a plausible mechanism, but treating it as established fact in executive framing required qualification. |
| **3** | "Hypothesis" is not a loophole for unsupported storytelling. | **Confirmed**: In `dev_02` and `dev_04`, labeling wild leaps as "hypotheses" did not prevent Score 0. |
| **4** | Definitive causal language in factual observations must be penalized. | **Confirmed**: Factual observations must remain strictly observational. |
| **5** | Recommending remediation for an engineering defect does not require randomized A/B evidence. | **Confirmed**: Recommending an SDK update (`dev_08`) or regex fix (`dev_09`) is sound PM action without A/B trials. |
| **6** | Causal language strength must remain proportional to evidence. | **Confirmed**: Proportionality separates Score 4 (fully hedged), Score 3 (minor over-definitive phrasing), and Score 2 (unsupported assertion). |
| **7** | Post-hoc correlation, vendor blame, and contradicted claims remain low-scoring. | **Confirmed**: `dev_02` (0), `dev_04` (0), `dev_07` (0) correctly scored at the bottom. |
| **8** | Do not redefine Causal Discipline so broadly that any plausible explanation gets a 4. | **Confirmed**: Plausible explanations with unhedged executive claims belong at Score 3, not Score 4. |

---

## 5. Replacement Causal Discipline Rubric

Because the audit establishes that **`RUBRIC_AMBIGUOUS`** is the primary driver of the 2-point disagreements in `dev_06` and `dev_09`, the following replacement rubric resolves the ambiguity while strictly upholding all eight invariants:

```markdown
### DIMENSION 4: `causal_discipline` (0 to 4)
Evaluates epistemic discipline in distinguishing correlation from causation, properly categorizing claims across fields, and qualifying uncertainty.

- **Score 4 (Excellent)**: Exemplary epistemic discipline. Strict structural separation across fields:
  * `factual_observations` contains strictly empirical, non-causal data.
  * Explanatory mechanisms linking engineering defects to telemetry anomalies are placed under `inferences` using appropriately qualified language (e.g. "consistent with", "indicates", "plausibly explains").
  * Testable remediation outcomes and potential failure theories are explicitly placed under `hypotheses`.
  * Executive framing avoids unhedged causal declarations.
  * Recommending targeted remediation or operational investigation based on matching engineering and telemetry evidence is fully disciplined and does NOT require randomized A/B trials or formal experimental causal identification.

- **Score 3 (Good)**: Sound epistemic discipline. The core analysis properly places mechanisms under `inferences` and solutions under `hypotheses`, and the causal link is well-supported by matching engineering and telemetry evidence. Contains minor over-definitive phrasing (e.g. executive problem statement uses shorthand causal phrasing like "due to" or "caused by", or hypothesis expresses overly optimistic certainty like "resolve 100%").

- **Score 2 (Partially Adequate)**: Material causal overreach. Conflates correlation with causation in core analytical conclusions; asserts definitive single-cause attribution when evidence is purely circumstantial without matching engineering tickets or timing signatures; or asserts unproven causal mechanisms as verified observations in `factual_observations`.

- **Score 1 (Poor)**: Severe causal overreach. Extrapolates isolated anecdotal complaints into platform-wide root causes; engages in premature vendor blaming without supporting telemetry; or falls directly into a known causality/magnitude trap.

- **Score 0 (Completely Inadequate)**: Blatant post-hoc ergo propter hoc fallacy; wild causal leaps completely contradicted by available evidence.
```

---

## 6. Protocol Amendment Requirement

### Mandatory Governance Check:
The Phase 9 operating contract specifies:
> **"Maximum calibration iterations: 2 prompt/rubric revisions after the current baseline."**

Both approved development revisions have already been executed:
* **Revision 1**: Introduced positive/negative anchors and basic epistemic rules.
* **Revision 2**: Refined Groundedness cohort anchors and Contradiction handling schema rules.

### **Formal Statement on Calibration Limits**:
1. **A protocol amendment IS required before any third calibration revision can be performed.**
2. Coding agents working in this repository are strictly bound by `AGENTS.md` and Phase 9 rules: they cannot unilaterally grant themselves additional calibration iterations.
3. Therefore, **no third prompt revision has been applied, no code has been modified, and the frozen judge remains untouched.**
4. Any third revision to implement the replacement rubric proposed in Section 5 must be preceded by an explicit, documented instruction amending the calibration iteration limit.

---

## 7. Current Project Status

* **LLM Judge Qualification**: **FAILED** (Pre-calibration baseline and post-Revision 2 validation qualification preserved).
* **660-Run SUT Benchmark**: **BLOCKED** (Not launched).
* **Phase 10**: **NOT BEGUN**.
* **Integrity Invariants**:
  - `evaluations/dataset/judge_cases.py` is strictly unmodified.
  - All frozen human ratings and validation reference ratings are strictly unmodified.
  - Full evaluation test suite passes (`35 passed in 1.39s`).

**Awaiting user decision on the audit report and protocol amendment status.**
