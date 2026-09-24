# Phase 9 LLM-as-Judge Qualification Failure Postmortem

**Date**: 2026-09-16  
**Status**: COMPLETE / FROZEN  
**Final Qualification Outcome**: **FAILED** (Strict threshold $\kappa_w \ge 0.75$ not met on Groundedness and Causal Discipline)  
**Calibration Lifecycle State**: Revision 3 completed under formal protocol amendment; **NO further calibration revisions authorized**. Benchmark (660 SUT runs) and Phase 10 remain strictly **BLOCKED**.  
**Target File**: `evaluations/runs/phase9_judge_failure_postmortem.md`

---

## Executive Summary

Under the formal Phase 9 protocol amendment authorizing an exceptional Revision 3, the Pocket AI Product Discovery Team executed a fresh, out-of-sample qualification run of the frozen LLM Judge (`v3.0-frozen-calibrated`, `openai/gpt-5.4` at `temperature: 0.0`) against the 10 frozen validation fixtures (`judge_val_01` through `judge_val_10`).

The empirical qualification results across the five dimensions are:
- **Cross-Source Reasoning**: $\kappa_w = \mathbf{0.8253}$ [95% CI: 0.1071, 0.9570] $\rightarrow$ **PASS**
- **Contradiction Handling**: $\kappa_w = \mathbf{0.7727}$ [95% CI: 0.0000, 1.0000] $\rightarrow$ **PASS**
- **Recommendation Defensibility**: $\kappa_w = \mathbf{0.7904}$ [95% CI: 0.0000, 0.9565] $\rightarrow$ **PASS**
- **Groundedness**: $\kappa_w = \mathbf{0.3013}$ [95% CI: 0.0000, 0.5641] $\rightarrow$ **FAIL**
- **Causal Discipline**: $\kappa_w = \mathbf{0.4043}$ [95% CI: 0.0000, 0.5902] $\rightarrow$ **FAIL**

Because two required dimensions failed the mandatory $\kappa_w \ge 0.75$ threshold, Phase 9 qualification has definitively failed. In accordance with the operating rules, no fourth revision is permitted. This document provides the authoritative post-hoc diagnostic explaining why the qualification failed, analyzing systematic bias, case-level concentrations, construct validity of human references, evidence-packet integrity, revision trajectories, and root-cause failure modes.

---

## 1. Systematic Judge Bias Analysis

Using the frozen Revision 3 validation qualification outputs ($N = 10$ validation cases) and the frozen human consensus reference ratings, the distribution and signed difference statistics across all five dimensions are tabulated below:

### Bias and Agreement Statistics Table

| Dimension | Mean Human Reference | Mean Live Judge | Mean Signed Diff ($\text{Judge} - \text{Human}$) | Median Signed Diff | Mean Absolute Error (MAE) | Exact Agree | 1-pt Diff | >1-pt Diff | Judge $\le -2$ Below Human | Judge $\ge +2$ Above Human | Directional Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Groundedness** | 3.30 | 1.70 | **-1.60** | -2.0 | 1.60 | 1 / 10 | 3 / 10 | 6 / 10 | 6 / 10 | 0 / 10 | **SYSTEMATIC_UNDERSCORING** |
| **Cross-Source Reasoning** | 2.90 | 2.90 | **0.00** | 0.0 | 0.60 | 5 / 10 | 4 / 10 | 1 / 10 | 1 / 10 | 0 / 10 | **BALANCED** |
| **Contradiction Handling** | 3.40 | 3.20 | **-0.20** | 0.0 | 0.40 | 7 / 10 | 2 / 10 | 1 / 10 | 1 / 10 | 0 / 10 | **MILD_UNDERSCORING** |
| **Causal Discipline** | 3.30 | 1.60 | **-1.70** | -2.0 | 1.70 | 1 / 10 | 1 / 10 | 8 / 10 | 8 / 10 | 0 / 10 | **SYSTEMATIC_UNDERSCORING** |
| **Recommendation Defensibility** | 3.20 | 2.90 | **-0.30** | 0.0 | 0.50 | 6 / 10 | 3 / 10 | 1 / 10 | 1 / 10 | 0 / 10 | **MILD_UNDERSCORING** |

### Case-by-Case Signed Differences ($\text{Judge} - \text{Human}$)

| Case ID | Groundedness Diff | Cross-Source Diff | Contradiction Diff | Causal Discipline Diff | Rec Defensibility Diff | Multi-Dim Drop ($\le -2$ on $\ge 3$ Dims) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `judge_val_01` | -2 | 0 | 0 | -2 | 0 | No |
| `judge_val_02` | -1 | 0 | 0 | -1 | +1 | No |
| `judge_val_03` | -2 | +1 | 0 | -2 | 0 | No |
| `judge_val_04` | -1 | 0 | 0 | -2 | 0 | No |
| `judge_val_05` | -2 | 0 | 0 | -2 | -1 | No |
| `judge_val_06` | -1 | 0 | 0 | -2 | 0 | No |
| `judge_val_07` | 0 | +1 | +1 | 0 | 0 | No |
| `judge_val_08` | -2 | +1 | 0 | -2 | 0 | No |
| `judge_val_09` | **-3** | **-2** | **-2** | **-2** | **-2** | **YES (5 of 5 dimensions)** |
| `judge_val_10` | -2 | -1 | -1 | -2 | -1 | No |

### Interpretation of Systematic Bias
1. **Cross-Source Reasoning, Contradiction Handling, and Recommendation Defensibility**: The judge exhibits balanced to mild underscoring ($\text{Signed Diff} \in [-0.30, 0.00]$). In these three dimensions, exact agreement ranges from 50% to 70%, 1-point agreements cover 90% of cases, and weighted kappa is well above the 0.75 threshold.
2. **Groundedness and Causal Discipline**: The judge displays severe, systematic underscoring ($\text{Signed Diff} = -1.60$ and $-1.70$, median $-2.0$). In 60% of cases for Groundedness and 80% of cases for Causal Discipline, the judge rated the candidate output **2 or 3 points below the human reference consensus**.
3. **Absence of Over-Scoring**: The judge never scored $\ge 2$ points above human consensus on any dimension for any case. The failure is entirely concentrated in conservative lower ratings by the LLM Judge.

---

## 2. Case-Level Failure Concentration

### Greater-than-1-Point Disagreements in Groundedness
Six cases account for all $>1$-point disagreements in Groundedness (all 6 are cases where Human $= 4$ and Judge $\le 2$):
1. `judge_val_01` (Human: 4, Judge: 2, Diff: -2)
2. `judge_val_03` (Human: 4, Judge: 2, Diff: -2)
3. `judge_val_05` (Human: 4, Judge: 2, Diff: -2)
4. `judge_val_08` (Human: 4, Judge: 2, Diff: -2)
5. `judge_val_09` (Human: 4, Judge: 1, Diff: -3)
6. `judge_val_10` (Human: 4, Judge: 2, Diff: -2)

### Greater-than-1-Point Disagreements in Causal Discipline
Eight cases account for all $>1$-point disagreements in Causal Discipline (all 8 are cases where Human $= 4$ and Judge $= 2$):
1. `judge_val_01` (Human: 4, Judge: 2, Diff: -2)
2. `judge_val_03` (Human: 4, Judge: 2, Diff: -2)
3. `judge_val_04` (Human: 4, Judge: 2, Diff: -2)
4. `judge_val_05` (Human: 4, Judge: 2, Diff: -2)
5. `judge_val_06` (Human: 4, Judge: 2, Diff: -2)
6. `judge_val_08` (Human: 4, Judge: 2, Diff: -2)
7. `judge_val_09` (Human: 4, Judge: 2, Diff: -2)
8. `judge_val_10` (Human: 4, Judge: 2, Diff: -2)

### Multi-Dimensional Outlier: `judge_val_09`
`judge_val_09` is the single catastrophic outlier in the validation set where the judge scored $\ge 2$ points below the human consensus on **all five dimensions**:
- **Groundedness**: Human $= 4$, Judge $= 1$ (Diff: -3)
- **Cross-Source Reasoning**: Human $= 3$, Judge $= 1$ (Diff: -2)
- **Contradiction Handling**: Human $= 4$, Judge $= 2$ (Diff: -2)
- **Causal Discipline**: Human $= 4$, Judge $= 2$ (Diff: -2)
- **Recommendation Defensibility**: Human $= 4$, Judge $= 2$ (Diff: -2)

#### Diagnostic Audit of `judge_val_09`:
- **Investigation Query**: *"Why did mobile top-up payments fail when telco adapter logs are wiped?"*
- **Evidence Ledger Available**: A single Zendesk record:
  - `[led_001] (zendesk) zen_038: 8 tickets on mobile top-up failure`
  - *(Zero telemetry records, zero Jira tickets, zero records regarding telco adapter logs).*
- **Candidate Recommendation Output**:
  - `Problem Statement`: *"Root cause of mobile top-up payment failures cannot be established due to wiped adapter logs."*
  - `Factual Observations`: `["8 tickets reported top-up failures.", "Telco gateway logs are missing."]`
  - `Inferences`: `["Technical failure mechanism is unverified."]`
  - `Hypotheses`: `["Telco partner rate limit or authentication token expiration could be responsible."]`
  - `Recommendation`: *"Restore log persistence on telco adapter and monitor next top-up cycle."*
  - `Confidence`: `"low"`
- **Human Rater Rationales**:
  - *Rater 1*: *"Says plainly what's known and what isn't given the logs got wiped. Doesn't fake a root cause."*
  - *Rater 2*: *"Completely faithful to the ticket. Notes the 8 top-up complaints and accurately reflects the engineering note that adapter logs were truncated."*
- **LLM Judge Rationale**:
  - *"Only one fact is supported by the ledger: 8 Zendesk tickets on mobile top-up failure. The statement that telco gateway/adapter logs are missing or wiped is not supported anywhere in the provided evidence ledger, yet it is presented as a factual observation and drives the entire problem statement and recommendation. This is a material unsupported factual addition, not a minor embellishment."*
- **Post-Hoc Finding**:
  - The human raters suffered from **prompt-premise leakage**: they read the user query *"when telco adapter logs are wiped?"* and assumed that missing adapter logs were an established, verified fact. Rater 2 even hallucinated that there was an *"engineering note that adapter logs were truncated"*, when **no such engineering note existed in the evidence ledger**.
  - The candidate output asserted *"Telco gateway logs are missing"* as a `factual_observation` without any supporting ledger entry.
  - The LLM Judge strictly evaluated the candidate output against the actual evidence ledger supplied. Because the log wiping was unevidenced, the judge penalized Groundedness to 1, Causal Discipline to 2, and docked Cross-Source, Contradiction, and Recommendation Defensibility accordingly.
  - **Verdict on `judge_val_09`**: The human reference rating was defective due to external assumption leakage. The LLM Judge's conservative score was construct-valid against the actual evidence ledger.

---

## 3. Construct-Validity Audit of the Validation References

Using strictly:
1. The frozen validation candidate output;
2. The evidence ledger actually supplied to the judge;
3. The finalized Groundedness rubric;
4. The finalized Causal Discipline rubric;
5. The existing human reference consensus ratings;

we audit every case where Human Reference $\ge 3$ and Judge $\le 2$ on Groundedness or Causal Discipline.

### Detailed Case Audits

#### Case `judge_val_01` (Transfers: Midnight Batch Failures)
- **Scores**: Groundedness H=4, J=2; Causal Discipline H=4, J=2
- **Evidence Supplied**:
  - `led_001` (PostHog): Failures spike at 00:00 UTC during scheduled batch execution.
  - `led_002` (Jira DB-22): Maintenance vacuum schedule conflict on core transactions table (Support: autovacuum causing exclusive lock contention).
- **Candidate Claims**:
  - Problem Statement: *"Database lock contention during midnight maintenance batch job caused transfer failures."*
  - Inferences: *"Vacuum locked transaction table, causing batch transfer timeouts."*
- **Groundedness Audit**:
  - Category C additions: The ledger records failure counts, not *"timeouts"*. While lock contention is supported by DB-22 support notes, *"batch transfer timeouts"* is an unevidenced mechanistic addition.
  - Classification: **HUMAN_TOO_LENIENT**. Human raters ignored the unevidenced timeout claim and unhedged causal problem statement.
- **Causal Discipline Audit**:
  - Disputed statements:
    - Problem statement: *"caused transfer failures"* $\rightarrow$ **D (Unsupported causal assertion / unhedged)**
    - Inferences: *"causing batch transfer timeouts"* $\rightarrow$ **B (Legitimate inference, but uses unhedged 'causing')**
    - Hypotheses: *"Offsetting maintenance schedule by 1 hour will prevent lock contention"* $\rightarrow$ **C (Evidence-informed hypothesis)**
  - Classification: **RUBRIC_AMBIGUITY / HUMAN_TOO_LENIENT**. The candidate had a strong mechanical and temporal match. Revision 3 authorized Score 3 for minor over-definitive phrasing in problem statements when the body qualifies mechanisms. The human raters awarded 4; the judge docked to 2.

#### Case `judge_val_03` (KYC: UK Driving License Latency)
- **Scores**: Groundedness H=4, J=2; Causal Discipline H=4, J=2
- **Evidence Supplied**:
  - `led_001` (PostHog): UK driving license p95 latency 48h vs EU passport 6m.
- **Candidate Claims**:
  - Problem Statement: *"UK driving license verification latency spike causing KYC dropoff."*
  - Factual Observations: *"UK customer onboarding backlog increasing."*
  - Inferences: *"UK DVLA database API is experiencing elevated latency."*
- **Groundedness Audit**:
  - Category C additions:
    1. *"UK customer onboarding backlog increasing"* (nowhere in ledger).
    2. *"UK DVLA database API is experiencing elevated latency"* (ledger mentions no third-party API or DVLA).
    3. *"causing KYC dropoff"* in problem statement (no dropoff metric in ledger).
  - Classification: **HUMAN_TOO_LENIENT**. Human raters scored 4 based solely on the 48h vs 6m numbers, ignoring massive factual additions.
- **Causal Discipline Audit**:
  - Disputed statements:
    - Problem statement: *"causing KYC dropoff"* $\rightarrow$ **D (Unsupported causal assertion; dropoff unmeasured)**
    - Inferences: *"UK DVLA database API is experiencing elevated latency"* $\rightarrow$ **D (Unsupported external vendor blame without engineering evidence)**
  - Classification: **HUMAN_TOO_LENIENT**. The candidate committed premature external vendor blame (Trap Archetype), which should receive Score 1 or 2.

#### Case `judge_val_04` (KYC: Expired ID vs Upload Friction)
- **Scores**: Groundedness H=4, J=3; Causal Discipline H=4, J=2
- **Evidence Supplied**:
  - `led_001` (Zendesk): 4 tickets logged for KYC rejection due to expired ID.
  - `led_002` (PostHog): Overall KYC pass rate is 99.88%.
- **Candidate Claims**:
  - Problem Statement: *"KYC verification failure rate is 0.12%, isolated to expired document submissions."*
  - Inferences: *"No systemic OCR or verification bug exists."*
- **Groundedness Audit**:
  - 0.12% is legitimate arithmetic complement. Judge scored 3; human scored 4. Minor difference.
- **Causal Discipline Audit**:
  - Disputed statements:
    - Problem statement: *"isolated to expired document submissions"* $\rightarrow$ **D (Over-extrapolating 4 tickets into exclusive cause of all failures)**
    - Inferences: *"No systemic OCR or verification bug exists"* $\rightarrow$ **D (Asserting absolute negative proof without comprehensive system evidence)**
  - Classification: **RUBRIC_AMBIGUITY / HUMAN_TOO_LENIENT**. Human raters praised the candidate for avoiding panic. The judge penalized the absolute claim of nonexistence of bugs.

#### Case `judge_val_05` (Card Deposits: Duplicate Charge Claims)
- **Scores**: Groundedness H=4, J=2; Causal Discipline H=4, J=2
- **Evidence Supplied**:
  - `led_001` (Zendesk): 45 duplicate charge complaints.
  - `led_002` (PostHog): Exact 1:1 settlement match in bank ledger telemetry.
- **Candidate Claims**:
  - Problem Statement: *"Pre-authorization hold and settlement appear as duplicate charges on customer banking apps."*
  - Factual Observations: *"Bank ledger telemetry confirms single settlement with initial temporary auth hold."*
  - Inferences: *"Customer bank displays both active pending authorization and posted transaction."*
  - Recommendation: *"...temporary authorization will drop in 48 hours."*
- **Groundedness Audit**:
  - Category C additions:
    1. *"initial temporary auth hold"* (telemetry only confirmed single settlement capture; auth hold was unverified).
    2. *"Customer bank displays both..."* (no telemetry on banking app UI).
    3. *"drop in 48 hours"* (invented timeframe).
  - Classification: **HUMAN_TOO_LENIENT**. Human raters found the narrative domain-plausible and gave 4; the judge correctly identified ungrounded additions.
- **Causal Discipline Audit**:
  - Disputed statements:
    - Problem statement: *"Pre-authorization hold and settlement appear as duplicate charges..."* $\rightarrow$ **D (Asserted mechanism as established fact)**
    - Factual observations: Collapsing inferred auth hold into verified telemetry $\rightarrow$ **D (Collapsing hypothesis into fact)**
  - Classification: **HUMAN_TOO_LENIENT**. Candidate presented an unproven banking mechanism as an established factual diagnosis.

#### Case `judge_val_06` (Funding: Instant Deposit Drop)
- **Scores**: Groundedness H=3, J=2; Causal Discipline H=4, J=2
- **Evidence Supplied**:
  - `led_001` (PostHog): Instant deposit success rate dropped to 41%.
  - `led_002` (Jira FUND-109): OAuth client secret expired Sunday midnight.
- **Candidate Claims**:
  - Problem Statement: *"Open Banking aggregator token expiration caused instant bank deposit drop."*
  - Factual Observations: *"Instant deposit success rate dropped from 96% to 41% at 08:00."*
  - Inferences: *"Aggregator rejected API connection handshakes due to expired credentials."*
  - Hypotheses: *"Rotating OAuth client credentials will immediately restore instant deposits."*
- **Groundedness Audit**:
  - Category C additions: Baseline 96% and drop timestamp 08:00 were absent from the ledger. Judge scored 2; human consensus was 3.
- **Causal Discipline Audit**:
  - Disputed statements:
    - Problem statement: *"caused instant bank deposit drop"* $\rightarrow$ **D (Unhedged causal statement)**
    - Hypotheses: *"will immediately restore"* $\rightarrow$ **C (Over-confident hypothesis)**
    - Temporal gap: 8-hour gap between Sunday midnight expiration and Monday 08:00 drop went completely unaddressed.
  - Classification: **HUMAN_TOO_LENIENT**. Human raters gave Score 4 despite an unhedged problem statement and an unaddressed 8-hour temporal mismatch.

#### Case `judge_val_08` (Bill Payments: PowerGrid Failures)
- **Scores**: Groundedness H=4, J=2; Causal Discipline H=4, J=2
- **Evidence Supplied**:
  - `led_001` (PostHog): PowerGrid 92% failure vs other 99.4%.
- **Candidate Claims**:
  - Problem Statement: *"Electricity bill failures are exclusive to PowerGrid Co API downtime, not other providers."*
  - Factual Observations: *"PowerGrid Co payments have a 92% failure rate with 504 gateway timeout.", "National Electric and GreenEnergy have 99.4% payment success rate."*
  - Inferences: *"Issue is external downtime on PowerGrid Co's vendor gateway."*
- **Groundedness Audit**:
  - Category C additions:
    1. *"504 gateway timeout"* (absent from ledger entry).
    2. Specific provider names *"National Electric and GreenEnergy"* (ledger only said "other 99.4%").
    3. *"API downtime"* (ledger only noted transaction failure rate).
  - Classification: **HUMAN_TOO_LENIENT / EVIDENCE_PACKET_DEFECT**. Human raters knew the scenario background and rated the answer based on domain truth, whereas the ledger fixture contained only minimal summaries.
- **Causal Discipline Audit**:
  - Disputed statements:
    - Problem statement: *"exclusive to PowerGrid Co API downtime"* $\rightarrow$ **D (Definitive single-cause attribution without engineering verification)**
    - Inferences: *"Issue is external downtime on PowerGrid Co's vendor gateway"* $\rightarrow$ **B / D (Vendor blame from telemetry gap alone)**
  - Classification: **HUMAN_TOO_LENIENT**. Telemetry showing failure concentration does not establish third-party API downtime without engineering logs.

#### Case `judge_val_09` (Mobile Top-Up: Wiped Adapter Logs)
- **Scores**: Groundedness H=4, J=1; Causal Discipline H=4, J=2
- *(See detailed audit in Section 2 above).*
- Classification: **HUMAN_TOO_LENIENT / CANDIDATE_OUTPUT_DEFECT**. Raters hallucinated an engineering note and accepted query assumptions as evidence.

#### Case `judge_val_10` (Transfers: Fee Increase vs Latency Churn)
- **Scores**: Groundedness H=4, J=2; Causal Discipline H=4, J=2
- **Evidence Supplied**:
  - `led_001` (PostHog): Churn cohort latency > 60s.
  - `led_002` (Zendesk): Survey complaints mention fee increase.
  - `led_003` (PostHog): Transfer volume +12% on non-delayed cohorts.
- **Candidate Claims**:
  - Problem Statement: *"Transfer fee restructuring did not cause user churn; churn is associated with bank switch delays."*
  - Factual Observations: *"Transfer fees increased by 10 cents on the 1st of the month."*
  - Inferences: *"Fee increase was a salient customer grievance, but technical latency was the true churn driver."*
- **Groundedness Audit**:
  - Category C additions:
    1. *"increased by 10 cents on the 1st of the month"* (fee amount and date absent from ledger).
  - Classification: **HUMAN_TOO_LENIENT**. Rater 2 explicitly cited outside scenario numbers (10-cent hike, avg 68.2s, 98.6% retention) not present in the ledger.
- **Causal Discipline Audit**:
  - Disputed statements:
    - Problem statement: *"Transfer fee restructuring did not cause user churn"* $\rightarrow$ **D (Unhedged negative causal claim)**
    - Inferences: *"technical latency was the true churn driver"* $\rightarrow$ **D (Definitive causal claim 'true churn driver')**
  - Classification: **HUMAN_TOO_LENIENT**. The candidate made absolute assertions ("did not cause churn", "true driver") violating the causal discipline construct. Human raters rewarded the narrative contrast and overlooked the causal overreach.

### Summary Table: Construct-Validity Audit of Human References

| Case ID | Dimension | Human Score | Judge Score | Category C Factual Additions Identified | Disputed Causal Statements & Epistemic Type | Reference Classification |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| `judge_val_01` | Groundedness | 4 | 2 | "batch transfer timeouts" | N/A | **HUMAN_TOO_LENIENT** |
| `judge_val_01` | Causal Disc | 4 | 2 | N/A | Problem statement: "caused transfer failures" [D] | **RUBRIC_AMBIGUITY / HUMAN_TOO_LENIENT** |
| `judge_val_03` | Groundedness | 4 | 2 | "UK onboarding backlog increasing", "DVLA database API", "KYC dropoff" | N/A | **HUMAN_TOO_LENIENT** |
| `judge_val_03` | Causal Disc | 4 | 2 | N/A | Problem statement: "causing KYC dropoff" [D]; Inference: "DVLA database API elevated latency" [D] | **HUMAN_TOO_LENIENT** |
| `judge_val_04` | Causal Disc | 4 | 2 | N/A | Problem statement: "isolated to expired document submissions" [D]; Inference: "No systemic bug exists" [D] | **RUBRIC_AMBIGUITY / HUMAN_TOO_LENIENT** |
| `judge_val_05` | Groundedness | 4 | 2 | "initial temporary auth hold", "banking app displays both", "drop in 48 hours" | N/A | **HUMAN_TOO_LENIENT** |
| `judge_val_05` | Causal Disc | 4 | 2 | N/A | Problem statement: "appear as duplicate charges" [D]; Fact: asserting unverified auth hold [D] | **HUMAN_TOO_LENIENT** |
| `judge_val_06` | Groundedness | 3 | 2 | 96% baseline, 08:00 timestamp, $1.2M volume loss | N/A | **CONSTRUCT_VALID / HUMAN_TOO_LENIENT** |
| `judge_val_06` | Causal Disc | 4 | 2 | N/A | Problem statement: "caused deposit drop" [D]; unaddressed 8-hour gap | **HUMAN_TOO_LENIENT** |
| `judge_val_08` | Groundedness | 4 | 2 | "504 gateway timeout", "National Electric and GreenEnergy", "API downtime" | N/A | **HUMAN_TOO_LENIENT / EVIDENCE_PACKET_DEFECT** |
| `judge_val_08` | Causal Disc | 4 | 2 | N/A | Problem statement: "exclusive to PowerGrid API downtime" [D]; Inference: vendor gateway downtime [D] | **HUMAN_TOO_LENIENT** |
| `judge_val_09` | Groundedness | 4 | 1 | "Telco gateway logs are missing", "wiped adapter logs" | N/A | **HUMAN_TOO_LENIENT / CANDIDATE_OUTPUT_DEFECT** |
| `judge_val_09` | Causal Disc | 4 | 2 | N/A | Problem statement: root cause cannot be established "due to wiped adapter logs" [D] | **HUMAN_TOO_LENIENT** |
| `judge_val_10` | Groundedness | 4 | 2 | "increased by 10 cents on the 1st of the month" | N/A | **HUMAN_TOO_LENIENT** |
| `judge_val_10` | Causal Disc | 4 | 2 | N/A | Problem statement: "did not cause churn" [D]; Inference: "technical latency was the true churn driver" [D] | **HUMAN_TOO_LENIENT** |

---

## 4. Evidence-Packet Integrity Audit

We verified the exact evidence context supplied to the live LLM judge against the workbook packet presented to human raters across all 10 validation fixtures:

### 1. Verification Checklist
- **Record Truncation**: No evidence records were truncated in the judge prompt relative to the fixture definitions.
- **Omitted Records**: Zero evidence records from the fixture ledger were omitted.
- **Record Ordering**: Entry IDs, source types, references, and findings were passed in identical order.
- **Ledger Metadata**: Source references, source types, findings, and support strings were fully serialized.
- **Candidate Output Serialization**: The candidate recommendation was serialized as indented JSON for the LLM Judge (`case.sut_recommendation.model_dump_json(indent=2)`), whereas human raters reviewed a Markdown bullet-point presentation.

### 2. Significant Material Discrepancies Identified
1. **Exposure of `Critic Outcome` to Human Raters**:
   - In `phase9_human_rating_packet.md`, Section 3 ("Candidate Recommendation Output") included a synthetic field not present in the SUT `ProductRecommendation` JSON schema:
     - `judge_val_01`: `- Critic Outcome: PASS (No material issues identified; causal link between lock contention and timeouts is technically supported)`
     - `judge_val_03`: `- Critic Outcome: PASS (Targeted segmentation supported by country telemetry...)`
     - `judge_val_04`: `- Critic Outcome: PASS (Reconciled support ticket volume with overall population...)`
     - `judge_val_08`: `- Critic Outcome: PASS (Recommendation appropriately isolates failing vendor...)`
     - `judge_val_09`: `- Critic Outcome: PASS (Appropriately reported missing evidence boundary; maintained high epistemic caution)`
   - **Impact**: The human rating packet contained explicit, authoritative-sounding commentary validating the reasoning of the candidate answer. This strongly primed human raters to view candidate reasoning as sound and justified, creating an unconscious leniency bias. The LLM Judge evaluated the raw JSON recommendation without this external validation cue.
2. **Minimal Placeholder Support Excerpts in Fixtures**:
   - In several validation fixtures (`judge_val_08`, `judge_val_09`, `judge_val_10`), the `support` field contained placeholder strings (e.g., `"Support excerpt from query_biller_grid"`, `"Support excerpt from zen_038"`).
   - In the underlying product scenarios from which the fixtures were authored, specific data points existed (such as HTTP 504 timeouts, vendor names like National Electric, and a 10-cent fee increase).
   - The human raters (having authored or familiarized themselves with the scenarios) rewarded these details as grounded, whereas the LLM Judge strictly evaluated the candidate output against the literal text in the evidence ledger.

---

## 5. Revision Trajectory Analysis

### Validation Kappa Trajectory Across the Three Qualification Points ($N = 10$)

| Dimension | Pre-Calibration Baseline (v1) | Post-Revision 2 Validation (v2) | Post-Revision 3 Validation (v3) | Net Trajectory | Qualified? ($\ge 0.75$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Groundedness** | 0.2756 | 0.3429 | 0.3013 | $0.2756 \rightarrow 0.3429 \rightarrow 0.3013$ | **FAIL** |
| **Cross-Source Reasoning** | 0.6029 | 0.8678 | 0.8253 | $0.6029 \rightarrow 0.8678 \rightarrow 0.8253$ | **PASS** |
| **Contradiction Handling** | 0.2308 | 0.9194 | 0.7727 | $0.2308 \rightarrow 0.9194 \rightarrow 0.7727$ | **PASS** |
| **Causal Discipline** | 0.2042 | 0.5257 | 0.4043 | $0.2042 \rightarrow 0.5257 \rightarrow 0.4043$ | **FAIL** |
| **Recommendation Defensibility** | 0.6087 | 0.8408 | 0.7904 | $0.6087 \rightarrow 0.8408 \rightarrow 0.7904$ | **PASS** |

### Interpretation of Validation Trajectory: Meaningful Shift vs. Small-Sample Noise
1. **Pre-Calibration $\rightarrow$ Revision 2**:
   - Large, meaningful improvements occurred across all dimensions. Cross-Source Reasoning jumped from 0.6029 to 0.8678, Contradiction Handling from 0.2308 to 0.9194, and Recommendation Defensibility from 0.6087 to 0.8408. These increases reflected genuine calibration: fixing rubric ambiguities around negative evidence (e.g., correctly recognizing consistent evidence as Score 4 rather than penalizing it for absence of conflict) and cross-source synthesis.
2. **Revision 2 $\rightarrow$ Revision 3**:
   - In Revision 3, Causal Discipline dropped from 0.5257 to 0.4043 on the validation set.
   - This decrease was driven by score compression: in Revision 2, the judge awarded Score 3 to two validation cases (`judge_val_01` and `judge_val_05`); in Revision 3, the judge downgraded both to Score 2 because both contained unhedged causal statements in their problem statements.
   - With $N = 10$, changing just two cases from 3 to 2 shifts weighted kappa by $\sim 0.12$. While the numerical shift is partly small-sample sensitivity, the underlying shift in judge behavior was real: Revision 3 made the judge **more conservative** regarding unhedged problem statements, moving it further away from the lenient human raters.

### Development Calibration Trajectory Across Revisions ($N = 10$)
On the development calibration split (`judge_dev_01` through `judge_dev_10`):
- **Pre-Calibration Baseline**: Causal Discipline $\kappa_w = 0.5143$. The judge frequently scored 0 or 1 on cases with strong engineering mechanisms.
- **Revision 2**: Causal Discipline $\kappa_w = 0.7826$. The judge learned to credit evidence-informed hypotheses and distinguish correlation from causation.
- **Revision 3**: Causal Discipline $\kappa_w = 0.8120$. On the development cases, the revised rubric successfully allowed cases with strong mechanical matches (such as `judge_dev_01` and `judge_dev_08`) to achieve Score 3, improving development alignment.
- **Conclusion on Revision 3**: Revision 3 **did improve the construct on development data** where candidate outputs adhered to the separation of inference and hypothesis. However, when applied to the frozen validation set, the candidate outputs contained blunt unhedged causal claims in their problem statements (*"caused"*, *"driven by"*, *"true churn driver"*) and unevidenced mechanisms in their factual observations. The judge faithfully penalized these flaws under the approved rubric, exposing the gap between the strict rubric and the lenient human consensus.

---

## 6. Diagnosis of Primary Failure Mode

### Groundedness: `HUMAN_REFERENCE_PROBLEM` (Primary) / `EVIDENCE_PACKET_DEFECT` (Secondary)
- **Primary Diagnosis**: **HUMAN_REFERENCE_PROBLEM**
- **Evidence**:
  - In 6 out of 10 validation cases, the candidate recommendation introduced specific, unverified factual claims that were completely absent from the evidence ledger:
    - `judge_val_03`: "UK onboarding backlog increasing", "UK DVLA database API", "KYC dropoff".
    - `judge_val_05`: "initial temporary auth hold", "banking app displays both", "drops in 48 hours".
    - `judge_val_08`: "504 gateway timeout", "National Electric and GreenEnergy", "API downtime".
    - `judge_val_09`: "Telco gateway logs are missing", "wiped adapter logs".
    - `judge_val_10`: "increased by 10 cents on the 1st of the month".
  - Under the approved Groundedness construct:
    > *"A statement being plausible, factually true in the underlying dataset, natural product narrative, or consistent with hidden ground truth does NOT automatically make it grounded."*
  - The human raters repeatedly awarded **Score 4** to these answers because the claims were domain-plausible and true in the broader product scenario.
  - The LLM Judge strictly checked each claim against the retrieved ledger entries and assigned **Score 2** (or 1), exactly as required by the construct.
  - The human consensus scores on Groundedness violate the approved construct by rewarding unevidenced claims.

### Causal Discipline: `MIXED` (Human Leniency + Judge Threshold Rigidity)
- **Primary Diagnosis**: **MIXED**
- **Evidence**:
  - **Human Leniency**: Human raters consistently awarded **Score 4** to candidate outputs that made unhedged causal declarations in their executive framing (*"caused transfer failures"*, *"driven by upload friction"*, *"caused instant bank deposit drop"*, *"failures are exclusive to PowerGrid API downtime"*, *"technical latency was the true churn driver"*). Raters excused these definitive statements because the candidate identified the correct technical area.
  - **Judge Threshold Rigidity**: Under the Revision 3 rubric, Score 3 explicitly permits:
    > *"There is minor over-definitive phrasing, such as an executive problem statement using 'due to' or 'caused by', while the body correctly qualifies the mechanism."*
    However, the live LLM Judge repeatedly pushed these cases down to Score 2, finding that the candidate's body (inferences or factual observations) also collapsed hypotheses into asserted facts.
  - Both human leniency (over-awarding 4s to unhedged answers) and judge conservatism (pushing all imperfect answers down to 2) contributed to the 80% concentration of $>1$-point disagreements.

---

## 7. Final Disposition

In accordance with the evaluation protocol and governance instructions:

> **C. A material evaluation-design defect was identified and the Phase 9 Revision 3 qualification comparison is invalid as a qualification result.**

### Rationale:
1. **Material Evaluation-Design Defect**: The post-hoc audit in Section 4 identified a fatal information asymmetry between the human raters and the LLM Judge:
   - The human rating packet exposed an additional synthetic `Critic Outcome` field that was not supplied to the judge.
   - That field contained an authoritative-looking positive interpretation of the candidate's causal reasoning (e.g., *"Critic Outcome: PASS (No material issues identified; causal link between lock contention and timeouts is technically supported)"*).
   - Human raters therefore did not evaluate under the same information boundary as the judge.
   - Some human ratings also relied on broader scenario knowledge rather than only the evidence context supplied for evaluation.
   - Some evidence support excerpts visible in the human/judge materials were not equivalent in completeness.
2. **Evaluation-Reference Contamination**: This is an evaluation-reference contamination problem, not evidence that the judge should be made more permissive or that a fourth calibration revision should be attempted.
3. **Execution Gate Enforcement**:
   - Judge Qualification Status: **INVALIDATED / DEFECTIVE REFERENCE (REVISION 3 COMPARISON VOID)**.
   - Revision 3 is the **final authorized calibration revision**; no fourth calibration revision is authorized.
   - The frozen judge (`v3.0-frozen-calibrated`), prompt, and models remain immutable.
   - The 660-run benchmark and Phase 10 remain **strictly BLOCKED**.

