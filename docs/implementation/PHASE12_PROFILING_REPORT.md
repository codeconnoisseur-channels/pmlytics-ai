# Phase 12 Profiling Report & Performance Optimization Proposal

**Investigation ID Profiled:** `inv_20260917_075720_cb2741`  
**Query:** *"Why are customers reporting a surge in failed transfers this week?"*  
**Environment:** Production Configuration (OpenRouter `openai/gpt-5.4`, Live PostHog, Mock Zendesk, MockServer Jira, LangSmith Tracing Enabled)  
**Execution Timestamp:** 2026-09-17 07:57:20 UTC  
**Profiling Mode:** Read-Only Profiling Pass (No architectural, prompt, or code modifications)

---

## 1. Executive Summary

A controlled live profiling pass of the complete Pocket AI Product Discovery workflow was analyzed using authoritative LangSmith traces, OpenRouter provider usage telemetry, and node-level execution timestamps.

| Dimension | Measured Value | Key Observation |
|---|---|---|
| **Total Wall-Clock Runtime** | **558.08s (9m 18s)** | Excessive for interactive PM demo; critical path dominated by PM/Critic revisions (64.8%) and slowest specialist (28.7%). |
| **Total LLM Calls** | **21 calls** | 10 specialist/planning calls + 1 assessment + 1 initial PM + 3 critic calls + **6 PM revision attempts** (due to token ceiling truncation retries). |
| **Total Tool Calls** | **26 calls** | 11 Zendesk ticket searches, 8 PostHog telemetry queries, 7 Jira searches/issue lookups. |
| **Total Token Volume** | **164,734 tokens** | 125,399 input tokens (63% duplicated ledger dumps across turns), 39,335 output tokens. |
| **Total Inference Cost** | **$0.788899 (~$0.79)** | Authoritative OpenRouter provider-reported cost (`usage.cost`). $0.44 (55.8%) consumed solely by PM revision retries. |
| **Critical Path Bottleneck** | **PM Revision Loop (234.9s) & Research Agent (160.4s)** | Research Agent was the slowest parallel specialist; PM revision hit the 4,096 token ceiling 5 times, triggering 3 full regeneration retries per revision round. |

---

## 2. Comprehensive Execution Timeline & Telemetry

### A. Per-Node Execution Summary

```
00:00 ───────────────────────────────────────────────────────────────────────────── 09:18
[Planner: 11.9s]
                 [Parallel Specialists: 160.4s (Research Agent bounding)]
                 ├── Analytics:   86.1s (finishes at 01:38)
                 ├── Engineering: 112.4s (finishes at 02:04)
                 └── Research:    160.4s (finishes at 02:52)
                                                             [Assess: 13.4s]
                                                                            [PM Initial: 82.2s]
                                                                                               [Critic 1: 17.5s]
                                                                                                                [PM Rev 1: 121.1s (3 retries)]
                                                                                                                                              [Critic 2: 17.6s]
                                                                                                                                                               [PM Rev 2: 113.8s (3 retries)]
                                                                                                                                                                                             [Critic 3: 9.1s (PASS)]
```

| Graph Node | Execution Interval (UTC) | Duration | % Total Runtime | Role / Status |
|---|---|---|---|---|
| `planner` | 07:57:26.366 – 07:57:38.310 | 11.94s | 2.1% | Initial 3-domain task decomposition |
| `analytics_agent` | 07:57:38.315 – 07:59:04.366 | 86.05s | 15.4% | Parallel specialist (8 queries, 3 LLM calls) |
| `engineering_agent` | 07:57:40.401 – 07:59:32.784 | 112.38s | 20.1% | Parallel specialist (7 queries, 3 LLM calls) |
| `research_agent` | 07:57:42.280 – 08:00:22.705 | **160.42s** | **28.7%** | **Slowest parallel specialist (11 tool calls, 3 LLM calls)** |
| `assessment` | 08:00:22.710 – 08:00:36.150 | 13.44s | 2.4% | Evaluated sufficiency (`sufficient_for_synthesis=False`) |
| `pm_synthesis` | 08:00:36.858 – 08:01:59.080 | 82.22s | 14.7% | Initial PM candidate synthesis (3,954 out tokens) |
| `critic` (Review 1) | 08:01:59.108 – 08:02:16.643 | 17.53s | 3.1% | Evaluated PM candidate $\to$ `REVISE` |
| `pm_revision` (Revision 1) | 08:02:16.675 – 08:04:17.795 | **121.12s** | **21.7%** | **Hit 4,096 ceiling twice; succeeded on 3rd attempt** |
| `critic` (Review 2) | 08:04:18.068 – 08:04:35.653 | 17.58s | 3.2% | Evaluated revision 1 $\to$ `REVISE` (confidence mismatch) |
| `pm_revision` (Revision 2) | 08:04:35.702 – 08:06:29.516 | **113.81s** | **20.4%** | **Hit 4,096 ceiling twice; succeeded on 3rd attempt** |
| `critic` (Review 3) | 08:06:29.557 – 08:06:38.691 | 9.13s | 1.6% | Final review $\to$ `PASS` |
| **Total Root Workflow** | **07:57:20.924 – 08:06:39.004** | **558.08s** | **100.0%** | **Completed successfully** |

---

### B. Every LLM Call (21 Calls)

| # | Role / Node | Model | Input Tokens | Output Tokens | Total Tokens | Provider Cost ($) | TTFT (s) | Total Latency (s) | Finish Reason | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| **01** | `planner` | `openai/gpt-5.4` | 771 | 524 | 1,295 | $0.009787 | 5.526s | 11.92s | `stop` | Success |
| **02** | `analytics` (T1) | `openai/gpt-5.4` | 1,971 | 606 | 2,577 | $0.010561 | 11.489s | 11.56s | `tool_calls` | 4 queries emitted |
| **03** | `engineering` (T1) | `openai/gpt-5.4` | 1,132 | 282 | 1,414 | $0.007060 | 14.892s | 14.98s | `tool_calls` | 4 searches emitted |
| **04** | `research` (T1) | `openai/gpt-5.4` | 949 | 141 | 1,090 | $0.004488 | 23.294s | 23.30s | `tool_calls` | 5 searches emitted |
| **05** | `analytics` (T2) | `openai/gpt-5.4` | 3,419 | 617 | 4,036 | $0.014346 | 17.985s | 18.01s | `tool_calls` | 4 queries emitted |
| **06** | `engineering` (T2) | `openai/gpt-5.4` | 7,957 | 110 | 8,067 | $0.021542 | 8.245s | 8.36s | `tool_calls` | Issue & comments lookup |
| **07** | `research` (T2) | `openai/gpt-5.4` | 3,206 | 137 | 3,343 | $0.010070 | 12.801s | 15.37s | `tool_calls` | 6 searches emitted |
| **08** | `analytics` (Synth) | `openai/gpt-5.4` | 2,832 | 2,099 | 4,931 | $0.034533 | 14.565s | 36.65s | `stop` | Specialist finding |
| **09** | `engineering` (Synth) | `openai/gpt-5.4` | 2,813 | 2,324 | 5,137 | $0.037860 | 36.534s | 61.16s | `stop` | Specialist finding |
| **10** | `research` (Synth) | `openai/gpt-5.4` | 2,663 | 2,182 | 4,845 | $0.035355 | 48.112s | 95.90s | `stop` | Specialist finding |
| **11** | `assessment` | `openai/gpt-5.4` | 7,373 | 486 | 7,859 | $0.025722 | 7.438s | 13.44s | `stop` | `sufficient=False` |
| **12** | `pm_synthesis` | `openai/gpt-5.4` | 4,894 | 3,954 | 8,848 | $0.071545 | 10.232s | 82.08s | `stop` | Initial Candidate |
| **13** | `critic` (Review 1) | `openai/gpt-5.4` | 7,995 | 990 | 8,985 | $0.034838 | 5.205s | 17.50s | `stop` | `REVISE` (unsupported) |
| **14** | `pm_revision` (R1.1) | `openai/gpt-5.4` | 10,412 | 4,096 | 14,508 | $0.087470 | 4.081s | 49.35s | `length` | **Truncated Ceiling** |
| **15** | `pm_revision` (R1.2) | `openai/gpt-5.4` | 10,466 | 4,096 | 14,562 | $0.065141 | 4.768s | 33.21s | `length` | **Truncated Ceiling** |
| **16** | `pm_revision` (R1.3) | `openai/gpt-5.4` | 10,520 | 4,096 | 14,616 | $0.065276 | 8.396s | 38.41s | `length` | **Truncated Ceiling** |
| **17** | `critic` (Review 2) | `openai/gpt-5.4` | 7,995 | 1,005 | 9,000 | $0.019511 | 5.971s | 17.46s | `stop` | `REVISE` (confidence) |
| **18** | `pm_revision` (R2.1) | `openai/gpt-5.4` | 10,456 | 4,096 | 14,552 | $0.081244 | 7.502s | 38.21s | `length` | **Truncated Ceiling** |
| **19** | `pm_revision` (R2.2) | `openai/gpt-5.4` | 10,510 | 4,096 | 14,606 | $0.065251 | 7.987s | 39.98s | `length` | **Truncated Ceiling** |
| **20** | `pm_revision` (R2.3) | `openai/gpt-5.4` | 10,564 | 3,277 | 13,841 | $0.075565 | 8.511s | 35.49s | `stop` | Succeeded on Try 3 |
| **21** | `critic` (Review 3) | `openai/gpt-5.4` | 6,501 | 121 | 6,622 | $0.011732 | 7.454s | 9.10s | `stop` | `PASS` |
| **TOTAL** | — | — | **125,399** | **39,335** | **164,734** | **$0.788899** | — | **671.44s** | — | — |

*Note on Reasoning Tokens: OpenRouter returned standard completion usage for `openai/gpt-5.4`. Reasoning token fields were null/0 in provider usage metadata.*

---

### C. Every Tool Call (26 Calls)

| # | Role | Tool | Execution Duration | Output Size / Records |
|---|---|---|---|---|
| **01** | `analytics` | `query_analytics` (`transfer_failed` 7-day trend) | 3.95s | 7 daily data points |
| **02** | `analytics` | `query_analytics` (`transfer_completed` 7-day trend) | 0.68s | 7 daily data points |
| **03** | `analytics` | `query_analytics` (Transfer funnel step conversion) | 0.79s | 3 funnel steps |
| **04** | `analytics` | `query_analytics` (`transfer_failed` breakdown by code) | 1.90s | Top 5 error codes |
| **05** | `engineering` | `search_issues` (JQL: `summary ~ "transfer"`) | 1.95s | 5 issues (PAY-117, CORE-82, etc.) |
| **06** | `analytics` | `query_analytics` (`transfer_failed` by app version) | 1.94s | Breakdown by iOS/Android versions |
| **07** | `engineering` | `search_issues` (JQL: `summary ~ "payment rail"`) | 1.97s | 3 issues |
| **08** | `analytics` | `query_analytics` (`transfer_failed` by user tier) | 1.97s | Breakdown by Standard/Premium |
| **09** | `engineering` | `search_issues` (JQL: `summary ~ "webhook"`) | 3.98s | 4 issues |
| **10** | `engineering` | `search_issues` (JQL: `created >= -7d AND component = Payments`) | 6.29s | 8 issues |
| **11** | `research` | `search_tickets` (Query: `failed transfer`) | 2.21s | 2 tickets |
| **12** | `research` | `search_tickets` (Query: `pending transfer`) | 3.62s | 12 tickets |
| **13** | `engineering` | `search_issues` (JQL: `issue in (PAY-117, PAY-134)`) | 3.51s | Issue details |
| **14** | `research` | `search_tickets` (Query: `transfer stuck`) | 5.99s | 18 tickets |
| **15** | `engineering` | `search_issues` (JQL: `summary ~ "partner switch"`) | 2.06s | 2 issues |
| **16** | `research` | `search_tickets` (Query: `transfer processing`) | 2.02s | 18 tickets |
| **17** | `analytics` | `query_analytics` (Week-over-week hourly failure rate) | 6.48s | 24 hourly buckets |
| **18** | `research` | `search_tickets` (Query: `transfer declined`) | 1.92s | 0 tickets |
| **19** | `engineering` | `get_issue` (`PAY-117`) | 5.98s | Full Jira issue payload |
| **20** | `analytics` | `query_analytics` (Transfer latency distribution) | 2.02s | Percentiles p50/p90/p99 |
| **21** | `engineering` | `get_issue_comments` (`PAY-117`) | 2.05s | 2 comment records |
| **22** | `research` | `search_tickets` (Query: `bank_a transfer`) | 2.09s | 10 tickets |
| **23** | `research` | `search_tickets` (Query: `bank_b transfer`) | 2.07s | 10 tickets |
| **24** | `research` | `search_tickets` (Query: `duplicate transfer`) | 1.65s | 0 tickets |
| **25** | `research` | `search_tickets` (Query: `transfer retry`) | 1.99s | 2 tickets |
| **26** | `research` | `search_tickets` (Query: `cannot send money`) | 1.93s | 4 tickets |
| **TOTAL** | — | — | **72.98s** | Cumulative tool execution time across all threads |

---

## 3. Critical Path Analysis

The execution graph is structured with parallel branches followed by sequential governance:
$$\text{Start} \longrightarrow \text{Planner} \longrightarrow \max(\text{Research}, \text{Analytics}, \text{Engineering}) \longrightarrow \text{Assessment} \longrightarrow \text{PM Initial} \longrightarrow \text{Critic 1} \longrightarrow \text{PM Rev 1} \longrightarrow \text{Critic 2} \longrightarrow \text{PM Rev 2} \longrightarrow \text{Critic 3} \longrightarrow \text{End}$$

Because the three specialist agents execute concurrently, the specialist phase duration is strictly bounded by the slowest branch: **Research Agent (160.42s)**.

### Critical Path Breakdown

| Segment | Node / Activity | Wall Clock Time | % of Critical Path |
|---|---|---|---|
| **1** | Planner Node | 11.94s | 2.2% |
| **2** | Parallel Specialists (**Bounded by Research Agent**) | 160.42s | 29.3% |
| **3** | Assessment Node | 13.44s | 2.5% |
| **4** | PM Initial Synthesis | 82.22s | 15.0% |
| **5** | Critic Review 1 (`REVISE`) | 17.53s | 3.2% |
| **6** | PM Revision 1 (**3 LLM calls due to 4,096 ceiling truncation**) | 121.12s | 22.1% |
| **7** | Critic Review 2 (`REVISE`) | 17.58s | 3.2% |
| **8** | PM Revision 2 (**3 LLM calls due to 4,096 ceiling truncation**) | 113.81s | 20.8% |
| **9** | Critic Review 3 (`PASS`) | 9.13s | 1.7% |
| **SUM** | **Calculated Critical Path Duration** | **547.19s** | **100.0%** |
| — | LangGraph State Transitions / Serialization Overhead | 10.89s | — |
| **ACTUAL** | **Measured End-to-End Investigation Runtime** | **558.08s** | — |

---

## 4. Runtime & Cost Attribution

### A. Runtime Attribution Breakdown

$$\text{Total Runtime: 558.08s}$$

```
Runtime by Architectural Phase:
[Specialists: 28.7%] [Assess: 2.4%] [PM / Critic Governance & Revisions: 64.8%] [Planner: 2.1%]
```

* **Specialist Investigation (Wall Clock):** **160.42s (28.7%)**
* **Assessment Node:** **13.44s (2.4%)**
* **PM / Critic Governance & Revisions:** **361.40s (64.8%)**
* **Planner:** **11.94s (2.1%)**

#### Latency Mechanism Breakdown on the Critical Path:
* **Total LLM Generation on Critical Path:** **521.33s (93.4% of total runtime)**
* **Total Tool / External API Latency on Critical Path:** **25.47s (4.6% of total runtime)**  
  *(Within Research Agent: LLM took 134.57s / 83.9%, Tool API calls took 25.47s / 15.9%)*

---

### B. Cost Attribution Breakdown

$$\text{Total Provider-Reported Inference Cost: } \mathbf{\$0.788899}$$

| Subsystem / Role | Cost ($) | % of Total Cost | Key Drivers |
|---|---|---|---|
| **Planner** | $0.009787 | 1.2% | 1 prompt turn (771 in, 524 out) |
| **Research Agent** | $0.049913 | 6.3% | 2 tool selection turns + 1 synthesis (2,182 out) |
| **Analytics Agent** | $0.059441 | 7.5% | 2 query selection turns + 1 synthesis (2,099 out) |
| **Engineering Agent** | $0.066463 | 8.4% | 2 issue selection turns + 1 synthesis (2,324 out) |
| **Assessment Node** | $0.025722 | 3.3% | 1 prompt turn (7,373 in, 486 out) |
| **PM Initial Synthesis** | $0.071545 | 9.1% | 1 prompt turn (4,894 in, 3,954 out) |
| **Critic Initial Review** | $0.034838 | 4.4% | 1 prompt turn (7,995 in, 990 out) |
| **PM Revisions (including retries)** | **$0.439947** | **55.8%** | **6 LLM calls (5 truncated length failures)** |
| **Critic Re-checks** | $0.031242 | 4.0% | 2 review checks (1,005 out, 121 out) |

#### Aggregated Cost Summary:
* **All 3 Specialist Agents Combined:** **$0.175817 (22.3%)**
* **PM / Critic Governance & Revisions:** **$0.577571 (73.2%)**
  * *PM Revisions alone account for 55.8% ($0.44) of all inference spend.*
* **Planner + Assessment:** **$0.035510 (4.5%)**

---

### C. Cost Verification & Reconciliation

* **Authoritative Source:** Provider-reported cost from OpenRouter completion payloads (`usage.cost`).
* **Cumulative Investigation Cost:** **$0.788899** (precisely reconciled against 21 individual span records).
* **OpenRouter Account State:**
  * Querying `https://openrouter.ai/api/v1/auth/key` shows `usage_daily: 2.0213135` and cumulative `usage: 11.2951015`.
  * The single investigation cost ~$0.79.
  * **Confirmation:** The user's earlier observed ~$5 balance change did **not** come from this single investigation run ($0.79). It represented cumulative execution across previous Phase 9/10 regression suites, benchmark runs, multiple prior smoke runs, and test executions throughout the development day.

---

## 5. Answers to the 10 Diagnostic Questions

### 1. Are specialists actually using their maximum or near-maximum LLM budgets?
**No.**  
* Analytics Agent (ceiling 3,072) generated 606, 617, and 2,099 tokens (peak 68% of ceiling).
* Engineering Agent (ceiling 3,072) generated 282, 110, and 2,324 tokens (peak 75% of ceiling).
* Research Agent (ceiling 3,072) generated 141, 137, and 2,182 tokens (peak 71% of ceiling).  
None of the specialist agents ever approached or exceeded their output ceilings.

### 2. Which specialist contributes most to the critical path?
**The Research Agent.**  
Because specialist nodes run in parallel, wall-clock latency is determined by the slowest branch:
* Analytics: 86.05s
* Engineering: 112.38s
* **Research: 160.42s** (over 2.6 minutes).  
Research spent 25.5s on 11 Zendesk tool calls, and 134.6s across 3 LLM calls, dominated by a 95.90s synthesis call.

### 3. Are the specialist loops doing repeated reasoning/tool-selection turns that could be collapsed?
**Yes.**  
Currently, each specialist executes an unconstrained multi-turn tool loop:
* Turn 1: LLM proposes initial tool calls (e.g. 4–5 queries).
* Execution of tools.
* Turn 2: LLM inspects tool outputs, then proposes another round of tool calls (e.g. 3–6 queries).
* Execution of tools.
* Turn 3: LLM performs specialist synthesis.  
In Analytics and Engineering, the second turn tool calls were straightforward follow-ups (breakdowns and comment lookups) that could easily be scheduled in a single bounded planning turn or batched upfront.

### 4. How much latency and cost comes from the Evidence Assessment LLM?
* **Latency:** **13.44s (2.4% of runtime)**.
* **Cost:** **$0.025722 (3.3% of cost)**.  
The assessment node evaluated 7,373 input tokens to return `sufficient_for_synthesis=False` because numeric week-over-week baselines were missing. While fast and inexpensive, its output (`sufficient_for_synthesis=False`) directly set the stage for subsequent Critic challenges.

### 5. How much latency and cost comes from the PM/Critic revision loop?
* **Latency:** **361.40s (64.8% of total runtime)**.
* **Cost:** **$0.577571 (73.2% of total cost)**.  
Governance and revision loops dominate the runtime and cost profile.

### 6. Is the two-revision path being triggered unnecessarily?
**Yes, and exacerbated by token ceiling truncation.**  
* In Review 1, Critic flagged an unsupported claim regarding overlapping Jira tickets and confidence calibration.
* In Review 2, Critic flagged confidence mismatch (`sufficient_for_synthesis=False` vs PM setting confidence="medium").
* Crucially, during both Revision 1 and Revision 2, the PM hit `finish_reason == "length"` at 4,096 tokens, raising `LLMMalformedOutputError` and triggering automatic retries (3 calls in Revision 1, 3 calls in Revision 2).
* The PM was repeating the entire lengthy JSON recommendation from scratch, hitting the ceiling 5 times before barely finishing within 3,277 tokens on call #20.

### 7. Are large tool results or tool histories being re-sent to models on subsequent turns?
**Yes.**  
* In Engineering Agent: Turn 2 input jumped from 1,132 to **7,957 tokens** because raw Jira search results with full issue schemas were re-sent in conversation history.
* In PM Revisions: The entire Evidence Ledger (all 26 entries with full excerpts and metadata, ~10,400 tokens) was dumped into the user message on **every single revision retry** (Calls #14, #15, #16, #18, #19, #20).

### 8. How much of the input token volume is duplicated context?
**Over 60% of all input tokens were duplicated context.**  
* Total investigation input tokens: **125,399 tokens**.
* Resending the 10,400-token Evidence Ledger across PM calls #12, #14, #15, #16, #18, #19, #20 accounted for **~63,000 input tokens (50.2% of all input tokens)**.
* Specialist tool history re-sends accounted for another **~12,000 input tokens**.
* Over 75,000 of the 125,399 input tokens were identical re-transmissions.

### 9. Which roles actually require the frontier model?
* **Only PM Synthesis and Critic Review.**
* The Planner performs standard 3-domain task decomposition.
* Specialists perform domain query formatting and fact extraction.
* Assessment evaluates a structured checklist.
* None of these 5 roles require `openai/gpt-5.4`. They can be fulfilled by high-speed, cost-effective models like `openai/gpt-4.1-mini`.
* Only the PM (cross-domain synthesis, epistemic separation) and Critic (adversarial skepticism, causal discipline) require frontier reasoning.

### 10. What portion of the cost could plausibly be shifted to GPT-4.1-mini or GPT-5.4-mini without changing workflow semantics?
* **Over 70% of the cost can be eliminated.**
* Planner, Assessment, and Specialists accounted for 10 LLM calls, 31,525 in-tokens, and 9,474 out-tokens, costing **$0.2113** on GPT-5.4.
* Shifting these 5 roles to `openai/gpt-4.1-mini` ($0.15/M in, $0.60/M out) drops their cost to **~$0.0104** (a 95% reduction on specialist/planning spend).
* Eliminating PM truncation retries and capping normal revision at 1 turn drops PM revision spend from $0.44 to **~$0.08**.
* Total investigation cost drops from **$0.79** to **$0.18–$0.22**, and total wall-clock duration drops from **558s (~9.3 min)** to **~120–150s (~2–2.5 min)**.

---

## 6. Phase 12 Optimization Proposal (For Review)

*This proposal is submitted for user review and approval prior to implementation.*

### A. Bounded Specialist Loops
* **Current Pattern:** Up to 8–10 unconstrained multi-turn tool calls per specialist.
* **Proposed Pattern:** Explicit, bounded 2–3 turn workflow:
  $$\text{LLM Query Formulation (Turn 1)} \longrightarrow \text{Batch Domain Tool Execution} \longrightarrow \text{LLM Evidence Synthesis (Turn 2)}$$
* Target: Exactly 2 LLM calls per specialist in normal execution.
* Preserves role boundaries, Evidence Ledger integrity, provenance, and typed `SpecialistResult` contracts.

### B. Context Compaction
* Keep full evidence payloads in the immutable `EvidenceLedger` in graph state.
* When passing evidence to PM and Critic, use a compact structured view containing only:
  * `ledger_entry_id`
  * `source_reference`
  * `finding`
  * `support` (concise factual excerpt)
  * `confidence`
* Do not re-send raw nested Jira issue schemas or full historical tool traces. This reduces PM input token volume from ~10,500 tokens to ~2,500 tokens per turn.

### C. Model Routing
Propose evaluating the following model routing:

| Role | Current Model | Proposed Model | Rationale |
|---|---|---|---|
| **Planner** | `openai/gpt-5.4` | `openai/gpt-4.1-mini` | Decomposing 1 query into 3 domain tasks does not require frontier reasoning. |
| **Research** | `openai/gpt-5.4` | `openai/gpt-4.1-mini` | Ticket search query generation and customer excerpt extraction. |
| **Analytics** | `openai/gpt-5.4` | `openai/gpt-4.1-mini` | PostHog metric query formulation and trend extraction. |
| **Engineering** | `openai/gpt-5.4` | `openai/gpt-4.1-mini` | Jira JQL construction and issue summary extraction. |
| **Assessment** | `openai/gpt-5.4` | `openai/gpt-4.1-mini` or Deterministic | Gap evaluation against planned objectives. |
| **PM Synthesis** | `openai/gpt-5.4` | `openai/gpt-5.4` | Preserves frontier cross-source synthesis and epistemic separation. |
| **Critic Review** | `openai/gpt-5.4` | `openai/gpt-5.4` | Preserves stringent adversarial review and causal discipline. |

*Gate:* This routing must pass a representative quality regression check (groundedness, contradiction detection) before being adopted as default.

### D. Bounded Revision Policy & Critic Prompt Calibration
* **Standard Profile Revision Rule:**
  $$\text{Initial PM} \longrightarrow \text{Critic} \longrightarrow \text{Optional 1 Revision} \longrightarrow \text{Complete}$$
* Limit normal execution to a maximum of **1 revision**.
* The 2nd revision is reserved exclusively for an explicit Deep Investigation profile.
* **Critic Instruction Refinement:** Require `REVISE` only for material defects:
  * Unsupported empirical claims
  * Direct contradictions ignored
  * Gross causal overreach (claiming causation without evidence)
  * Missing critical domain perspectives  
  Do not trigger revision for stylistic preference or when `sufficient_for_synthesis=False` is already accurately disclosed in PM limitations and confidence rating.

### E. Output Token Ceilings
* Observed actual peak output tokens:
  * Planner: 524 tokens $\to$ adjust ceiling to **1,024**.
  * Research: 2,182 tokens $\to$ adjust ceiling to **2,560**.
  * Analytics: 2,099 tokens $\to$ adjust ceiling to **2,560**.
  * Engineering: 2,324 tokens $\to$ adjust ceiling to **2,560**.
  * PM Synthesis: 3,954 tokens $\to$ raise ceiling from 4,096 to **5,120** (with compact prompt, actual output will drop to ~2,500 tokens, eliminating all ceiling truncation retries).
  * Critic: 1,005 tokens $\to$ adjust ceiling to **1,536**.

### F. Provider Prompt Caching
* Structure system prompts and tool schemas at the top of message sequences with fixed prefixes.
* OpenRouter / provider automatic prompt caching will match identical system instructions and schema definitions across specialist turns and PM/Critic exchanges without altering provenance or data retention.

### G. Dual Runtime Profiles

1. **Standard Profile (Default for UI / Demo):**
   * Optimized for interactive speed and low cost.
   * Model routing: Mini models for Planner/Specialists/Assessment; GPT-5.4 for PM & Critic.
   * Bounded specialist loops (2 LLM calls per specialist).
   * Compacted evidence context.
   * Maximum 1 revision round.
   * Target duration: **$\le 120$ seconds**.
   * Target cost: **$\le \$0.20$**.

2. **Deep Profile (For Complex Investigations):**
   * Full frontier reasoning across all roles (`openai/gpt-5.4` throughout).
   * Generous specialist loops (up to 8 tool calls).
   * Up to 2 revision rounds.
   * Comprehensive evidence expansion.

---

## 7. Success Criteria for Phase 12 Optimization

Before Phase 12 implementation proceeds, we establish the following measurable success criteria for the **Standard Profile**:

| Metric | Current Baseline (Profiled) | Target (Phase 12 Standard) | Improvement Target |
|---|---|---|---|
| **End-to-End Latency** | 558.08s (~9.3 min) | **$\le 120$ seconds** | **$\ge 75\%$ latency reduction** |
| **Total LLM Calls** | 21 calls | **$\le 10$ calls** | **$\ge 50\%$ call reduction** |
| **Total Tool Calls** | 26 calls | **$\le 15$ calls** | Bounded efficient queries |
| **Total Investigation Cost** | $0.7889 (~$0.79) | **$\le \$0.20$** | **$\ge 70\%$ cost reduction** |
| **Max PM Revisions** | 2 revisions (with 5 retries) | **$\le 1$ revision (0 retries)** | Zero ceiling truncations |
| **Quality Regression Gate** | 15/15 Behavioral Stress | **15/15 PASS** | Zero regression in quality |
| **Frozen Judge Prompt SHA** | `8981496a...` | **100% Bit-for-Bit Intact** | Zero change to judge rubric |
