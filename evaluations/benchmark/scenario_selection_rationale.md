# Phase 9 Benchmark Scenario Selection Rationale

**Document Status**: Frozen & Verified Pre-Launch  
**Date**: `2026-09-16`  
**Total Benchmark Pool**: 45 scenarios  
**Selected Core Scenarios**: 24 scenarios  
**Locked Holdout Scenarios**: 10 scenarios  
**Total Planned Executions**: 204 runs (24 core × 3 architectures × 2 reps = 144; 10 holdouts × 3 architectures × 2 reps = 60)

---

## 1. Representativeness Criteria Verification

The 24 core scenarios were selected using predefined representativeness criteria to ensure balanced coverage across product domains, failure modes, data complexities, and reasoning challenges.

### A. Balanced Product Area Coverage (Exactly 6 Scenarios Each)
1. **Transfers (6 scenarios)**: `scn_001`, `scn_002`, `scn_003`, `scn_004`, `scn_005`, `scn_009`
2. **KYC / Identity Verification (6 scenarios)**: `scn_013`, `scn_014`, `scn_015`, `scn_016`, `scn_017`, `scn_018`
3. **Wallet Funding (6 scenarios)**: `scn_024`, `scn_025`, `scn_026`, `scn_027`, `scn_028`, `scn_030`
4. **Bill Payments (6 scenarios)**: `scn_035`, `scn_036`, `scn_037`, `scn_038`, `scn_039`, `scn_041`

---

### B. Failure Archetype Coverage
The core scenarios represent all major failure archetypes designed into the evaluation dataset:
- **Diagnostic (5 scenarios)**: `scn_001`, `scn_009`, `scn_013`, `scn_024`, `scn_035` (Multi-system troubleshooting requiring cross-corroboration).
- **Causality Traps (4 scenarios)**: `scn_002`, `scn_014`, `scn_025`, `scn_036` (Plausible temporal correlations that mask true underlying causes).
- **Segmentation Traps (4 scenarios)**: `scn_003`, `scn_015`, `scn_027`, `scn_038` (Aggregates conceal localized failure cohorts like bank, OS, card scheme, or meter type).
- **Contradictory Signals (3 scenarios)**: `scn_016`, `scn_026`, `scn_037` (Support complaints conflict with telemetry or accounting reconciliations).
- **Missing / Insufficient Evidence (3 scenarios)**: `scn_018`, `scn_030`, `scn_041` (Critical variables are uninstrumented; tests epistemic humility and confidence calibration).
- **Outages / System Degradation (2 scenarios)**: `scn_005`, `scn_017` (A primary tool/adapter returns 503 or empty data; tests partial degradation handling).
- **Magnitude Traps (2 scenarios)**: `scn_028`, `scn_039` (Extreme outliers or isolated large events distort priorities).
- **Direct Factual (1 scenario)**: `scn_004` (Single-source customer inquiry testing baseline retrieval fidelity).

---

### C. Contradiction Handling Cases (7 Scenarios)
Scenarios with explicit, verified contradictory signals across sources:
- `scn_001`: Customer perception of failure vs telemetry confirming eventual backend settlement.
- `scn_009`: Technical settlement confirmed vs customer panic in pending notification window.
- `scn_016`: Low support volume suggests low severity, but analytics proves severe commercial funnel leakage.
- `scn_025`: Deposit initiations are up 8%, but checkout completions dropped due to 3DS timeouts.
- `scn_026`: Top-line deposit numbers appear healthy due to channel substitution, while card channel is failing.
- `scn_035`: Wallet debit succeeded on core ledger, but biller execution failed on downstream aggregator.
- `scn_037`: Double-debit eventually reversed, but delayed accounting creates immediate panic.

---

### D. Causal-Overreach & Causal Boundary Cases (5 Scenarios)
Scenarios enforcing explicit causal boundaries where overclaiming is penalized:
- `scn_001`: Prohibits concluding core payment settlement failed platform-wide.
- `scn_002`: Prohibits concluding Switch X caused all platform payment failures.
- `scn_014`: Prohibits blaming an organized fraud syndicate for normal image compression artifacts.
- `scn_025`: Prohibits attributing funding drops to macro interest rate shifts when 3DS timeouts are present.
- `scn_036`: Prohibits blaming client cellular networks for biller API gateway 504 errors.

---

### E. Adversarial & Prompt Injection Cases
- **Holdout Allocation (4 scenarios)**: `scn_012` (Transfers), `scn_023` (KYC), `scn_033` (Funding), `scn_045` (Bill Payments).
- In accordance with the security evaluation strategy, adversarial prompt injection fixtures are preserved in the locked holdout partition so candidate architectures are tested on prompt injection immunity without prior exposure. (In addition, the frozen semantic evaluator was validated on adversarial rejection via `stress_14_adversarial_instruction`).

---

### F. Source Breadth & Boundary Discipline
- **Single-Source Investigations (8 scenarios)**: Tests boundary discipline (not fabricating unretrieved sources): `scn_004`, `scn_015`, `scn_018`, `scn_027`, `scn_028`, `scn_030`, `scn_038`, `scn_041`.
- **Two-Source Investigations (9 scenarios)**: `scn_003`, `scn_005`, `scn_016`, `scn_017`, `scn_025`, `scn_026`, `scn_036`, `scn_039`, `scn_041`.
- **Three-Source Tripartite Investigations (7 scenarios)**: `scn_001`, `scn_002`, `scn_009`, `scn_013`, `scn_024`, `scn_035`, `scn_037`.

---

## 2. Locked Holdout Partition (10 Scenarios)
The 10 holdout scenarios remain strictly isolated from development, qualification, and prompt calibration:
- `scn_011`, `scn_012` (Transfers holdouts)
- `scn_022`, `scn_023` (KYC holdouts)
- `scn_031`, `scn_033`, `scn_034` (Funding holdouts)
- `scn_042`, `scn_044`, `scn_045` (Bill Payments holdouts)

---

## 3. Immutability Declaration
The 24 core and 10 holdout scenarios are frozen for the reduced 204-run Phase 9 benchmark. No scenario will be added, removed, or modified during or after benchmark execution.
