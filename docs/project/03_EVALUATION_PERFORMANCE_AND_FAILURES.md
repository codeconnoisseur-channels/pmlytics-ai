# PMLytics AI: Evaluation, Performance, and Failures

This document records how PMLytics AI was evaluated, what the measurements did and did not establish, and which failures materially changed the system.

## Part I: Evaluation

## Why evaluation was necessary

The hardest failure mode in this product is not invalid JSON. It is a polished recommendation that sounds reasonable but is not supported by the retrieved evidence. The evaluation system therefore had to measure both mechanical correctness and product reasoning.

The evaluation questions were:

- Did every citation resolve to real retrieved evidence?
- Did the system use the right sources and cover the relevant scenario evidence?
- Did it reconcile disagreement across sources?
- Did it separate observations from interpretation and hypotheses?
- Did it avoid unsupported causal claims?
- Was the recommendation proportionate and defensible?
- What quality, latency, and cost did the architecture produce?
- Did multi-agent complexity earn its place relative to simpler baselines?

## Evaluation design

### Layer 1: deterministic evaluators

Programmatic checks measure properties that should not depend on another model's opinion:

- citation IDs exist in the Evidence Ledger;
- citation source and source reference match the cited ledger entry;
- required recommendation fields are present;
- facts, inferences, and hypotheses remain structurally distinct;
- expected scenario evidence is covered without duplicate credit;
- encoded contradictions are identified correctly;
- tool, model-call, follow-up, and revision bounds are respected;
- hidden ground truth remains outside runtime prompts.

These checks are necessary but not sufficient. A report can cite valid records and still make a poor product judgement.

### Layer 2: frozen LLM evaluator

The semantic evaluator scores five dimensions independently on a 0 to 4 scale:

1. groundedness;
2. cross-source reasoning;
3. contradiction handling;
4. causal discipline;
5. recommendation defensibility.

It also performs claim-level classification, including fully supported, partially supported, unsupported, contradicted, legitimate inference, evidence-informed hypothesis, and unsupported causal assertion.

The final judge prompt is frozen at SHA-256 `8981496ad497e5f68d809e322c0a2d98fd8b12f5104fb611f784534ec3ef1b63`. Freezing prevents post-hoc rubric changes from making later results incomparable.

### Behavioural stress testing

The evaluator was tested on 15 deliberately constructed cases, including:

- fabricated metrics and historical baselines;
- valid synthesis across multiple records;
- cautious and unsupported causal claims;
- explicit contradiction and no-contradiction cases;
- irrelevant citations;
- unsupported high-commitment recommendations;
- single-source overreach;
- source outage and insufficient evidence;
- adversarial instructions inside evidence;
- strong engineering matches.

The initial stress result was 14/15. After correcting an evidence-context serialization defect and refining one over-specified fixture, the frozen evaluator passed 15/15.

## The human-calibration attempt and why it was retired

Human calibration was attempted because an LLM judge should not be treated as self-validating. The initial qualification work included two human rating submissions and compared them with the judge.

The process exposed two validity problems:

1. the first human packet included a synthetic Critic outcome that the judge did not see, so the comparison was informationally asymmetric;
2. raters sometimes rewarded claims they knew were plausible from the broader scenario even when those facts were absent from the supplied Evidence Ledger.

A later artifact labelled as a clean, equivalent-input re-rating appeared to produce qualifying agreement. A provenance audit then established that those ratings had been generated programmatically in the agent environment, with access to prior judge results, rather than entered independently by human raters. That comparison was therefore void and cannot qualify the judge.

Current position:

- the provenance audit is preserved as historical research evidence, while the invalid raw rating artifacts are excluded from the public repository to avoid presenting them as human ground truth;
- the frozen semantic evaluator is useful but explicitly limited;
- deterministic evidence checks remain the primary hard gate;
- no claim is made that the LLM judge is human-qualified or objective ground truth.

This is an important product lesson: a file labelled as a human rating is not evidence of independent human review. Rater provenance, information symmetry, and the rating construct all have to be verified.

## Baseline architectures

The repository keeps three evaluatable architectures:

- a single agent using the same underlying domain tools;
- specialists plus PM synthesis, without a Critic;
- specialists plus PM synthesis and Critic.

This preserves the ability to test whether additional coordination and review justify their cost. The planned large benchmark was not completed, so the project does not claim statistically proven multi-agent superiority.

## Large benchmark disposition

The planned benchmark was stopped rather than disguised as complete:

- 13 legitimate exploratory executions completed;
- 57 executions failed with HTTP 402 infrastructure errors;
- 134 executions were not attempted;
- no aggregate benchmark statistics were calculated.

The failure came from unbounded maximum-token reservation and retry amplification, not from the quality of a candidate architecture. The checkpoint is preserved, but those failures are not counted as model-quality results.

## What evaluation proved

The project demonstrated that:

- citation identity and provenance can be checked deterministically;
- the evaluator can detect the declared stress behaviours in its 15-case suite;
- a bounded multi-agent workflow can produce grounded, defensible reports on selected synthetic scenarios;
- model, prompt, and context changes can be compared against preserved quality dimensions;
- causal discipline and contradiction handling need separate measurement rather than one blended score.

## What evaluation did not prove

It did not prove:

- statistical superiority of multi-agent over single-agent architecture;
- production accuracy on real customer data;
- stable cost or latency under production provider load;
- broad domain generalisation outside the designed fintech scenarios;
- enterprise security, reliability, or tenant isolation;
- that the frozen judge is an objective gold standard.

## Part II: Performance and cost

## Measurement discipline

Performance numbers in this repository come from different phases and must not be blended. The two most useful datasets are:

1. a full-model profiling run used to diagnose cost and latency;
2. a later three-scenario Standard-profile validation used to measure the optimisation.

The current graph has since changed through ADR-0025 and ADR-0026. The historical numbers remain evidence of the optimisation, but are not current guarantees.

## Progression from baseline to optimisation

### Historical profiling baseline

| Metric | Value | Context |
| --- | ---: | --- |
| End-to-end runtime | 558.08s | One profiled Deep/full-model investigation |
| Model calls | 21 | Included six PM revision attempts |
| Tool calls | 26 | Multi-turn specialist retrieval |
| Input tokens | 125,399 | More than 60% attributed to duplicated context |
| Output tokens | 39,335 | Included repeated full recommendation generation |
| Total tokens | 164,734 | One investigation |
| Provider-reported cost | $0.788899 | OpenRouter usage cost |
| PM/Critic governance share | 73.2% of cost | $0.577571 |
| PM revision retries | Five truncated calls | 4,096-token ceiling |

### Diagnosis

The initial intuition could have been that three specialists were the dominant cost. Profiling showed otherwise:

- the slowest parallel specialist determined the fan-out wall time, but the PM revision loop dominated the sequential critical path;
- PM revisions alone consumed 55.8% of inference cost;
- the full Evidence Ledger, about 10,400 tokens in that run, was resent across PM synthesis and each retry;
- repeated ledger and specialist history accounted for more than 75,000 of 125,399 input tokens;
- five revision attempts reached the output ceiling and had to be regenerated.

### Changes

The optimisation introduced:

- compact prompt representations while retaining full typed ledger payloads;
- one retrieval batch and one synthesis turn per specialist on the normal Standard path;
- a targeted evidence working set for PM revision;
- calibrated role-specific token ceilings;
- GPT-4.1 mini for planning, assessment, and specialists in Standard mode;
- GPT-5.4 for initial PM synthesis;
- GPT-5.4 mini for PM revision and Critic;
- one revision in Standard mode;
- denser PM output instructions.

### Historical Phase 12A measured result

| Metric | Scenario 1 | Scenario 2 | Scenario 3 | Average or range |
| --- | ---: | ---: | ---: | ---: |
| Wall-clock latency | 98.46s | 121.41s | 107.43s | 109.10s average |
| Critical-path latency | 89.11s | 111.80s | 94.85s | 98.59s average |
| Model calls | 10 | 11 | 10 | 10.33 average |
| Tool calls | 13 | 13 | 13 | 13 |
| Input tokens | 17,692 | 25,111 | 21,042 | 21,281 average |
| Output tokens | 5,395 | 9,410 | 6,611 | 7,138 average |
| Provider cost | $0.0559 | $0.0807 | $0.0601 | $0.0656 average |
| Frozen judge score | 20/20 | 18/20 | 20/20 | 19.3/20 average |
| Citation validity | 8/8 | 8/8 | 9/9 | 100% |

Relative to the single matched profiling baseline, Scenario 1 moved from 558.08 seconds to 98.46 seconds and from $0.788899 to $0.0559. That is evidence that context and routing changes mattered. It is not a controlled claim that every current question will achieve the same improvement.

## Time to first token and provider throughput

TTFT and total generation latency are measured separately. This distinction exposed a 310.35-second outlier:

- the PM synthesis TTFT was only 2.82 seconds;
- the same call took 170.62 seconds to generate 2,823 output tokens, about 16.8 tokens per second;
- a subsequent GPT-5.4 PM revision took 47.33 seconds;
- together, the two sequential PM calls contributed 217.9 seconds.

The bottleneck was upstream generation throughput, not connection setup, tools, orchestration, or tracing. This is why a product cannot promise latency based only on TTFT.

Routing PM revision to GPT-5.4 mini reduced the measured revision call from a historical 35.0 to 47.3 seconds to 15.55 seconds in the controlled validation, saving roughly 20 to 32 seconds when revision occurred.

## Current performance interpretation

After Phase 12A:

- ADR-0025 restored a second Critic check after revision, adding a safety call when revision occurs;
- ADR-0026 allows one extra specialist call only when structured synthesis is invalid;
- the checked-in settings default to the Deep profile unless deployment configuration selects Standard.

Therefore:

- 10 calls before revision and 11 with revision are historical Phase 12A properties, not the current maximum;
- Standard now uses up to 12 calls when a PM revision must be re-reviewed, plus a bounded conditional specialist repair if a specialist output is invalid;
- Deep mode has different routing and permits up to two PM revisions;
- no new controlled current benchmark has measured the full combination.

## Part III: Failures and iterations

## 1. Context and Evidence Ledger bloat

**What we expected**  
Passing the full evidence history to later roles would maximise grounding.

**What happened**  
The same large ledger and tool history were retransmitted across synthesis and revision turns. More than 60% of input tokens were duplicated in the profiling run.

**How we noticed**  
LangSmith and OpenRouter telemetry showed 125,399 input tokens, with more than 75,000 estimated as repeated context.

**Root cause**  
Evidence retention and prompt representation had been treated as the same concern.

**What changed**  
The ledger remains complete and immutable, but prompts use compact factual envelopes. PM revision receives a targeted working set linked to challenged claims, contradictions, and limitations.

**Measured result**  
The Phase 12A scenarios averaged 21,281 input tokens, versus 125,399 in the profiling run, while citation validity remained 100% in that set.

**Remaining limitation**  
Complex real datasets could still produce large contexts. Compaction quality must be revalidated when source schemas change.

**Lesson**  
Do not delete evidence to save tokens. Separate durable evidence from the representation each reasoning step actually needs.

## 2. PM revision truncation and retry amplification

**What we expected**  
A 4,096-token ceiling would be sufficient for a revised recommendation.

**What happened**  
Five PM revision attempts stopped at the ceiling. Each retry regenerated a large structured recommendation and resent the evidence context.

**How we noticed**  
Finish reasons, output-token counts, and retry spans showed repeated `length` termination. PM revisions consumed $0.439947, 55.8% of the profiled run's cost.

**Root cause**  
Verbose schema output, full-context retransmission, and retrying the entire generation after truncation.

**What changed**  
The PM context was compacted, revision evidence was targeted, output density was tightened, token ceilings were calibrated, and revision moved to a faster model in Standard mode.

**Measured result**  
The three Phase 12A validations had zero truncation events. The observed revision call completed in 15.55 seconds.

**Remaining limitation**  
Structured generation can still fail. ADR-0026 adds one bounded specialist repair, but does not create unlimited retries.

**Lesson**  
Retries are not free resilience. A retry that repeats the same oversized prompt can multiply cost without changing the failure condition.

## 3. Provider tail latency

**What we expected**  
With compact prompts and parallel specialists, most investigations would stay near the target window.

**What happened**  
One run reached 310.35 seconds even though tools, specialist calls, and TTFT looked normal.

**How we noticed**  
Per-span profiling isolated a 170.62-second GPT-5.4 PM synthesis call.

**Root cause**  
Upstream generation throughput dropped to about 16.8 tokens per second. This was provider variability, not a local orchestration delay.

**What changed**  
PM revision was routed to GPT-5.4 mini and outputs were made denser. The frontier model remained on initial PM synthesis because that step carries the most product judgement.

**Measured result**  
The next three-scenario validation averaged 109.10 seconds, but still included one 121.41-second revised run.

**Remaining limitation**  
Initial PM synthesis still depends on provider throughput. Production service levels would require timeout policy, capacity planning, and possibly adaptive routing.

**Lesson**  
Measure TTFT and completion latency separately. A fast first token can hide a slow critical path.

## 4. Benchmark cost failure

**What we expected**  
A large comparison across architectures and scenarios would provide stronger evidence.

**What happened**  
The run encountered 57 HTTP 402 failures after only 13 legitimate executions; 134 executions remained unattempted.

**How we noticed**  
The preserved checkpoint showed repeated provider rejections and retry delays.

**Root cause**  
The benchmark did not bound maximum output tokens, so the provider reserved for a very large possible output. Backoff retried a credit-capacity problem that was not transient.

**What changed**  
Role token ceilings, explicit live-test opt-in, and bounded evaluation practice were introduced. The large benchmark was closed rather than resumed.

**Measured result**  
No benchmark result was calculated. That absence is the honest outcome.

**Remaining limitation**  
Multi-agent superiority remains unproven statistically.

**Lesson**  
Evaluation scope must be proportional to the product decision. A large benchmark can become an infrastructure project that delays the product.

## 5. Evaluator context omission

**What we expected**  
The semantic judge was evaluating each candidate against the full Evidence Ledger.

**What happened**  
The context builder omitted each entry's support field, so the judge sometimes saw a thinner evidence record than the candidate had used.

**How we noticed**  
The first stress suite missed one expected behaviour. A context-integrity audit compared serialized judge input with the actual ledger contract.

**Root cause**  
The evaluator had its own lossy evidence projection.

**What changed**  
Judge context now includes ledger ID, source type, source reference, finding, support, confidence, and limitations. A regression test protects the contract.

**Measured result**  
The stress suite moved from 14/15 to 15/15 after the context patch and one fixture correction.

**Remaining limitation**  
Passing a declared stress suite does not prove universal judge validity.

**Lesson**  
An evaluator is another product system. Its inputs, information symmetry, and failure modes require the same scrutiny as the system under test.

## 6. Human-reference and provenance failure

**What we expected**  
Human ratings would provide an unquestioned calibration reference.

**What happened**  
The first packet exposed a synthetic Critic judgement, and raters sometimes used broader scenario knowledge rather than the supplied ledger. A later purportedly clean rating set was not independently human-authored at all.

**How we noticed**  
The judge appeared systematically harsher on groundedness and causal discipline. Case-level review showed that several “judge errors” were actually unsupported candidate claims that humans had forgiven. A subsequent provenance audit traced the clean files to an AI-authored generation script and found strong circular agreement with the judge they were meant to validate.

**Root cause**  
Information asymmetry, an ambiguous rating construct, and unverified rater provenance.

**What changed**  
The clean requalification was revoked, the provenance failure was documented, and the final framework stopped treating the available human-labelled artifacts as quantitative ground truth.

**Measured result**  
There is no valid human-qualified agreement result. The frozen judge passed its 15-case behavioural stress suite, but that is a test of declared evaluator behaviours, not independent human validation.

**Remaining limitation**  
The frozen judge retains model bias and should not be the sole production acceptance mechanism.

**Lesson**  
Human review is valuable, but its provenance and protocol must be auditable. Synthetic or AI-generated ratings cannot be used to validate an LLM judge.

## 7. Post-revision quality-gate bypass

**What we expected**  
Skipping a second Critic call after PM revision would reduce Standard-profile latency without weakening correctness.

**What happened**  
Finalisation inspected the earlier `REVISE` review even though the recommendation had changed. A revised report could not truthfully become completed, and the new claims were not semantically reviewed.

**How we noticed**  
Terminal-state behaviour and finaliser invariants contradicted the optimisation assumption.

**Root cause**  
The workflow treated deterministic schema validation as if it could replace semantic review of a changed candidate.

**What changed**  
ADR-0025 routes every PM revision back to the Critic. A final `REVISE` at the revision limit produces an honest partial result.

**Measured result**  
The state and review now refer to the same candidate. No post-change latency benchmark has been run.

**Remaining limitation**  
The safer path adds a model call when revision occurs.

**Lesson**  
Optimisation cannot invalidate the meaning of a quality gate. The object reviewed must be the object released.

## 8. Analytics rows hidden by `value=None`

**What we expected**  
The analytics summary would expose the important result of every successful query.

**What happened**  
Event counts and breakdowns often return rows with no scalar value. The ledger summary treated the absent scalar as an absent result, hiding useful measurements from synthesis.

**How we noticed**  
Reports claimed telemetry was unavailable even when PostHog had returned tabular data.

**Root cause**  
The summary logic assumed all analytics were scalar.

**What changed**  
Ledger summaries now render bounded tabular rows when the scalar is absent. Failure-event queries are also separated from primary conversion funnels so a missing failure event does not erase valid started/submitted/completed activity.

**Measured result**  
Current source inspection shows the canonical synthetic scenarios contain usable behavioural patterns. A new provider-backed evaluation has not been run after this correction.

**Remaining limitation**  
Prompted query selection can still miss a useful segment; the deterministic tool boundary cannot guarantee perfect analytical strategy.

**Lesson**  
Missing one output shape is not the same as missing data. Data contracts need to represent tables, scalars, and empty results distinctly.

## 9. Evidence handoff and customer-facing projection failures

**What we expected**  
Sanitising internal details would make reports safer and more understandable.

**What happened**  
The projection discarded entire useful sentences when they contained an internal term or ledger citation, replacing distinct findings with repeated filler. Separately, specialist summaries sometimes passed counts and IDs without the ticket or issue content already retrieved.

**How we noticed**  
Paid reports repeated “Verified evidence was reviewed,” generic success measures, and internal validation errors despite strong underlying source data.

**Root cause**  
Over-broad sentence rejection plus lossy handoff between retrieval and synthesis. One malformed structured specialist output could also exhaust the strict two-call Standard budget.

**What changed**  
ADR-0026 introduced terminology translation, citation preservation, internal-failure filtering, deduplication, bounded report lists, representative search-result content, and one conditional specialist repair call.

**Measured result**  
The stored utility-bill evidence could be reprojected into specific facts, measures, and risks without another model call. Focused deterministic and UI checks passed during the correction, but no new paid quality benchmark was run.

**Remaining limitation**  
A historical run that never retrieved the needed evidence cannot be repaired by presentation logic without inventing data.

**Lesson**  
Customer-safe language should translate evidence, not erase it. A good internal result and a good product report are separate quality gates.

## 10. Process-local lifecycle and stream trust

**What we expected**  
An in-process task map and live SSE stream were sufficient for a portfolio workflow.

**What happened**  
Navigation could reconstruct a workspace from incomplete client state, backend restarts lost active execution, and stream reconnection could make progress appear to restart or jump.

**How we noticed**  
History and workspace state disagreed about which run was active, and a new investigation could appear to resume old progress.

**Root cause**  
The process and client were carrying authority that belonged in durable server state.

**What changed**  
Supabase owner-scoped records, persisted events, server-authoritative snapshots, monotonic progress reconciliation, PostgreSQL checkpoints, leases, heartbeats, and explicit recovery states were introduced.

**Measured result**  
Completed reports survive restart; safe node-boundary work resumes; ambiguous paid work pauses for user recovery; the frontend falls back to polling after stream failures.

**Remaining limitation**  
Execution is still hosted in the API process rather than a distributed durable job system.

**Lesson**  
Streaming is a delivery channel, not a source of truth. Progress and ownership must be reconstructable from durable server state.

## Source documents

- [Phase 9 final evaluation report](../../evaluations/runs/phase9_final_report.md)
- [Phase 9 validation integrity amendment](../../evaluations/runs/phase9_validation_integrity_amendment.md)
- [Phase 12 profiling report](../implementation/PHASE12_PROFILING_REPORT.md)
- [Phase 12A completion report](../implementation/PHASE12A_COMPLETION_REPORT.md)
- [ADR-0025](../decisions/ADR-0025-post-revision-quality-gate.md)
- [ADR-0026](../decisions/ADR-0026-report-projection-and-bounded-specialist-repair.md)
