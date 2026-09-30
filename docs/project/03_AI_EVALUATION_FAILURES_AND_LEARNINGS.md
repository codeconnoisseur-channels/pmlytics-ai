# PMLytics AI: AI Evaluation, Failures, and Learnings

This document records what PMLytics AI has actually been evaluated on, what the evidence established, what failed, and what changed as a result.

The central lesson is that evaluation has two targets:

1. whether the system retrieved the right evidence;
2. whether it reasoned responsibly over that evidence.

The project initially concentrated more heavily on the second question. A later live investigation showed why both are necessary: the final recommendation was cautious and grounded in its evidence packet, but the packet was incomplete because the agents had queried available data incorrectly.

## Evaluation status

| Area | Current evidence | Interpretation |
| --- | --- | --- |
| Deterministic safeguards | Citation, schema, permission, budget, state, and provenance checks exist | Objective invariants can be enforced without an LLM judge |
| Behavioural stress suite | 15 development cases | Covers declared semantic failure patterns, not every future behaviour |
| Historical stress result | 14/15 initially, then 15/15 after a context defect and one fixture issue were corrected | The evaluator detects the behaviours represented by that suite |
| Independent judge pilot | 5 development cases reviewed blindly by an independent product manager and GPT-5.4 | 5/5 verdict and severity agreement on that sample |
| Critical pilot cases | 2 | Both the human and judge identified both critical failures |
| Pilot false passes | 0 | No failed case was passed in the five-case sample |
| Retrieval-quality gate | Partial | Tool contracts exist, but semantic query correctness needs stronger end-to-end coverage |
| Production validation | Not performed | Results come from synthetic and mocked company data |

## Part I: Evaluation

## Why evaluation was necessary

PMLytics AI produces recommendations that may influence prioritisation. A plausible answer is therefore not enough.

The evaluation system needs to determine whether:

- the investigation found the relevant evidence;
- empty results were genuine rather than caused by a poor query;
- facts can be traced to retrieved records;
- several sources were reconciled rather than listed independently;
- contradictions affected confidence or action;
- correlation was kept separate from causation;
- missing evidence was disclosed;
- the recommendation was proportionate to the available evidence;
- the workflow stayed within its permissions and execution limits;
- quality gains justified additional model cost and latency.

## Current evaluation model

The current operating methodology is defined in the [Evaluation Strategy](../evaluation/EVALUATION_STRATEGY.md) and [ADR-0027](../decisions/ADR-0027-product-owned-evaluation-cases-and-audited-judge-calibration.md).

It has five layers.

### 1. Retrieval evaluation

Retrieval evaluation checks whether the system selected the right source, used valid query semantics, respected the selected period, retrieved expected records, established a baseline, and challenged the premise of the question where necessary.

This layer is not yet complete. The wallet-funding investigation documented later in this report exposed a gap between tool-schema validity and semantic query validity.

### 2. Deterministic evaluation

Code-based checks cover conditions that have objective answers:

- citation IDs exist;
- citation source and reference match the ledger entry;
- role-specific tool permissions hold;
- structured outputs validate;
- evidence provenance survives synthesis;
- observations, interpretations, and hypotheses remain distinct;
- hidden expected answers stay outside runtime prompts;
- tool, model-call, follow-up, repair, and revision limits are respected;
- terminal workflow state is explicit.

These are hard gates. A favourable LLM judgment cannot compensate for a broken citation or a permission violation.

### 3. Semantic evaluation

The current semantic rubric asks one clear question at a time. It evaluates:

- material-claim support;
- citation relevance;
- cross-source reasoning;
- contradiction handling;
- causal discipline;
- recommendation proportionality;
- missing-source disclosure;
- resistance to instructions embedded in evidence.

Each criterion receives `PASS`, `FAIL`, `UNCLEAR`, or `NOT_APPLICABLE`. Failed criteria receive minor, major, or critical severity.

This replaced reliance on a single blended quality score. A report can be well grounded but still recommend an excessive action, or handle causality well while missing a material contradiction.

### 4. Human audit and adjudication

The LLM judge reviews declared cases consistently. Humans independently audit a sample and investigate disagreements.

Both receive the same content-hashed candidate-and-evidence packet. Expected labels and previous judgments are hidden. A disagreement does not automatically mean that either reviewer is correct. It may indicate a weak rubric, an ambiguous packet, human contamination, or judge error.

### 5. Operational evaluation

LangSmith and provider telemetry support analysis of:

- end-to-end and critical-path latency;
- time to first token and generation time;
- model and tool calls;
- tokens and provider cost;
- revision and repair behaviour;
- tool and provider failures;
- recovery and terminal state.

## Evolution of the evaluation approach

### Earlier approach

The first semantic evaluator scored five dimensions from 0 to 4:

1. groundedness;
2. cross-source reasoning;
3. contradiction handling;
4. causal discipline;
5. recommendation defensibility.

The project initially attempted to compare those scores directly with human ratings.

### What happened

The comparison exposed several problems:

- the first human packet included a synthetic Critic outcome that the judge did not receive;
- reviewers sometimes rewarded claims that were plausible from the broader scenario but absent from the supplied Evidence Ledger;
- fine-grained scores introduced ambiguity about the difference between adjacent values;
- a later artifact presented as independent human rating data was generated programmatically in the agent environment and had access to prior judge results;
- cases, expectations, and runner logic were too closely coupled for easy product ownership.

The apparently strong agreement from the invalid artifact was withdrawn. It is not used as evidence that the judge was human-qualified.

### What changed

- Product-owned cases and runner infrastructure were separated.
- The 15 existing stress fixtures became a development catalog rather than human ground truth.
- Semantic evaluation moved to one explicit criterion at a time.
- Severity received written anchors.
- Human reviewers became auditors of sampled judge decisions rather than scorers of every output.
- Review packets became blind, identical, and content-hashed.
- Reviewer provenance and independence attestations became mandatory.
- Disagreements gained a formal adjudication record.
- Paid evaluation gained preflight estimates, cost ceilings, case limits, and content-addressed caching.

### Current position

Deterministic checks remain the primary hard gate. The LLM judge provides repeatable semantic review. Humans inspect a sample and maintain the product standard. No source is treated as infallible.

## Behavioural stress suite

The versioned development suite contains 15 constructed cases covering:

- a directly supported multi-source recommendation;
- a fabricated metric;
- an invented historical baseline;
- valid three-source synthesis;
- unsupported causal assertion;
- cautious causal inference;
- a contradiction resolved through an invented mechanism;
- consistent evidence where no contradiction should be invented;
- an irrelevant citation;
- a disproportionate recommendation;
- a supported recommendation;
- single-source extrapolation;
- missing-source disclosure;
- an instruction embedded inside evidence;
- a strong engineering match expressed with qualified causal language.

### Result

The first run detected 14 of the 15 declared behaviours. Investigation found that the evaluator's context builder had omitted the substantive support field from each evidence entry. One fixture also asked for a more specific answer than its evidence justified.

After repairing the serialized context and correcting that fixture, the evaluator passed all 15 development stress cases.

This establishes that the evaluator detects the behaviours represented by those cases. It does not establish universal evaluator reliability.

## What author review changed

The project author completed a structured review before the independent pilot. That review was treated as a rubric audit, not independent human ground truth.

It found:

- two failures whose expected severity was too harsh;
- one contradiction case that had incorrectly been expected to pass;
- one embedded-instruction criterion written from the evaluator's perspective rather than the candidate recommendation's perspective.

The disagreements were adjudicated individually. The result was `atomic_semantic_v2`, with clearer severity boundaries and candidate-focused security wording.

This changed the evaluation system itself. The useful question was not simply, “Did the human or model win?” It was, “What does this disagreement reveal about the definition of acceptable product behaviour?”

## Independent five-case judge pilot

After the rubric audit, an independent product manager reviewed five development cases using only the neutral review instructions, blind evidence packets, and blank review form. The reviewer confirmed that they did not see the project author's answers, expected labels, adjudication history, or LLM judge results before submitting.

GPT-5.4 evaluated the same content-hashed packets using `atomic_semantic_v2` and `atomic_judge_v1`.

| Metric | Result | Context |
| --- | ---: | --- |
| Cases | 5 | Selected development cases |
| Exact verdict agreement | 5/5 | Human and GPT-5.4 |
| Exact severity agreement | 5/5 | Human and GPT-5.4 |
| Critical reference failures | 2 | Fabricated core evidence and embedded-instruction misuse |
| Critical failures agreed | 2/2 | Both reviewers identified both |
| False passes | 0 | Within the five-case sample |
| Critical false passes | 0 | Within the five-case sample |
| False failures | 0 | Within the five-case sample |
| Unresolved disagreements | 0 | After the final corrected packet |
| Provider calls | 6 | Five original calls and one approved corrected rerun |
| Approved cost ceiling | $0.18 | Estimate-based ceiling |
| Actual provider cost | Not captured | The runner did not record exact provider-reported cost |

The result is deliberately narrow. These cases came from the development catalog and were not genuinely unseen. The pilot validates the review protocol on this sample. It is not a held-out benchmark or a claim of permanent judge reliability.

## The defective packet that improved the evaluator

One pilot case was designed to test whether a recommendation disclosed a missing source and adjusted its confidence. The candidate described a source failure, but the generated review packet omitted the structured source-failure record.

The judge returned `NOT_APPLICABLE` because the evidence it received did not establish that a source had failed.

Inspection showed that the packet, not the judge verdict, was defective. The packet was corrected and only that case was purchased again. The other four results were reused from the content-addressed cache.

The lesson was important: evaluation infrastructure is also a system with inputs, contracts, and failure modes. A judge cannot evaluate evidence it was never given.

## A live investigation exposed a larger blind spot

On 29 September 2026, a paid investigation asked:

> Why are debit card wallet funding transactions failing at elevated rates?

The selected period was 5 August to 18 August 2026. The report concluded that analytics, support, and engineering systems contained no matching records and recommended checking backend logs and payment-processor monitoring.

The recommendation was cautious relative to its evidence packet. The evidence packet itself was wrong.

### What the sources actually contained

A direct read-only source check found:

- 483 `wallet_funding_started` events;
- 283 `wallet_funding_submitted` events;
- 283 `wallet_funding_completed` events;
- no recorded `wallet_funding_failed` events;
- 12 relevant Zendesk tickets within the selected period;
- no related Jira incident, which was the intended engineering result.

The scenario was designed to show abandonment before submission, particularly around unexpected cost, rather than a transaction-processing failure.

### Why the agents missed it

The Analytics Agent applied `user_type = debit_card`. The synthetic event schema uses `user_type` for customer segments, not payment method. The query was structurally valid but semantically invalid, so it removed every wallet-funding event.

The Research Agent ran four searches centred on the word “failure.” It never ran the broad `tag:wallet_funding` search required by its own discovery policy. That broad search returned all 12 relevant tickets when checked directly.

The Planner also accepted “elevated failures” as the investigation premise instead of first testing whether failures were actually elevated.

### Why the existing quality gates passed it

- The tools returned successful responses.
- The Evidence Ledger faithfully recorded the empty responses.
- The PM Agent did not invent a cause.
- The Critic challenged overstatement and passed the revised cautious answer.
- The citations resolved to records that existed.

The system checked whether the recommendation was supported by the retrieved packet. It did not adequately check whether the packet represented the source data that was available.

### Consequence

The report was marked partial after 158.9 seconds. It used 12 model calls, 13 tool calls, one PM revision, and two Critic reviews. LangSmith captured at least $0.0747 of model cost, but the final Critic cost was absent because its usage span failed to record the provider metadata.

The run spent additional time making a defensible recommendation from a defective retrieval set. Revision could improve the wording but could not recover evidence the specialists failed to retrieve.

### Evaluation change required

This failure establishes retrieval quality as a separate release gate. Future coverage must test:

- valid property and value combinations;
- required baseline funnels before failure-event analysis;
- broad discovery before repeated narrow support searches;
- expected evidence coverage by scenario and period;
- premise challenge;
- false no-evidence outcomes;
- whether the Critic should block synthesis when retrieval behaviour is internally inconsistent.

The governing lesson is:

> Grounding is necessary, but grounding against the wrong evidence is still a product failure.

## Architecture baselines

The repository retains three evaluatable architectures:

1. single agent using the same domain tools;
2. specialists plus PM synthesis;
3. specialists plus PM synthesis and Critic.

This keeps the multi-agent decision falsifiable. The project does not assume that more agents are automatically better.

## Large benchmark disposition

A planned large architecture benchmark did not complete:

- 13 legitimate exploratory executions completed;
- 57 executions failed with HTTP 402 provider-credit errors;
- 134 executions were not attempted;
- no aggregate architecture comparison was calculated.

The immediate cause was excessive maximum-token reservation combined with retries that treated a credit-capacity rejection as if it were transient.

The checkpoint was preserved and the benchmark was closed rather than represented as a successful comparison. Statistical multi-agent superiority therefore remains unproven.

## What evaluation has established

The project has demonstrated that:

- citation identity and provenance can be checked deterministically;
- known semantic failure patterns can be represented as versioned cases;
- the evaluator detects all 15 behaviours in its current development stress suite;
- human disagreement can expose errors in expected labels and rubric wording;
- blind, identical, content-hashed packets make judge comparison more credible;
- GPT-5.4 and an independent product manager agreed on all verdicts and severities in a five-case development pilot;
- evaluation calls can be bounded, estimated, approved, and cached;
- performance traces can identify context, retry, routing, and provider bottlenecks.

## What evaluation has not established

It has not proved:

- universal judge reliability;
- a qualified held-out result;
- statistical superiority of the multi-agent architecture;
- consistent live retrieval quality across the four demo scenarios;
- production accuracy on real customer data;
- performance under sustained production traffic;
- stable provider cost or latency;
- broad domain generalisation outside the designed fintech cases.

## Part II: Performance and cost

## Measurement discipline

Performance figures come from different phases. They must not be blended into one “current” number.

The most useful comparison is between:

1. one historical Deep/full-model profiling run used to diagnose the system;
2. one matched Standard-profile validation scenario after optimisation.

The current graph has changed since those measurements. They demonstrate the effect of the optimisation, not a production service-level promise.

## Historical profiling baseline

| Metric | Value | Context |
| --- | ---: | --- |
| End-to-end runtime | 558.08 seconds | One Deep/full-model profiled investigation |
| Model calls | 21 | Included six PM revision attempts |
| Tool calls | 26 | Multi-turn specialist retrieval |
| Input tokens | 125,399 | More than 60% attributed to duplicated context |
| Output tokens | 39,335 | Included repeated recommendation generation |
| Total tokens | 164,734 | One investigation |
| Provider-reported cost | $0.788899 | OpenRouter usage cost |
| PM and Critic cost share | 73.2% | $0.577571 |
| Truncated PM revisions | 5 | Each reached the 4,096-token ceiling |

## What the trace showed

The initial assumption was that three specialists were causing most of the cost. The trace showed otherwise.

- The slowest specialist affected the parallel branch duration, but the PM revision loop dominated the sequential critical path.
- PM revisions alone used 55.8% of the investigation's inference cost.
- The full Evidence Ledger, about 10,400 tokens in that run, was resent to PM synthesis and each retry.
- Repeated ledger and specialist history accounted for more than 75,000 of the 125,399 input tokens.
- Five revision attempts reached the output ceiling and repeated almost the same failure.

The system was paying models to reread the same evidence and regenerate a large structured answer.

## What changed

- The full typed ledger remained durable, while prompts received compact factual representations.
- Specialists used one retrieval batch and one synthesis turn on the normal Standard path.
- PM revision received a targeted evidence working set instead of the full history.
- Role-specific output limits replaced one broad token allowance.
- GPT-4.1 mini handled planning, assessment, and specialists in Standard mode.
- GPT-5.4 remained responsible for the initial product recommendation.
- GPT-5.4 mini handled Critic and PM revision work.
- Standard mode limited recommendation revision to one cycle.
- Output instructions were made denser.

## Historical Phase 12A validation

| Metric | Scenario 1 | Scenario 2 | Scenario 3 | Average or range |
| --- | ---: | ---: | ---: | ---: |
| Wall-clock latency | 98.46s | 121.41s | 107.43s | 109.10s average |
| Critical-path latency | 89.11s | 111.80s | 94.85s | 98.59s average |
| Model calls | 10 | 11 | 10 | 10.33 average |
| Tool calls | 13 | 13 | 13 | 13 |
| Input tokens | 17,692 | 25,111 | 21,042 | 21,281 average |
| Output tokens | 5,395 | 9,410 | 6,611 | 7,138 average |
| Provider cost | $0.0559 | $0.0807 | $0.0601 | $0.0656 average |
| Historical five-dimension judge score | 20/20 | 18/20 | 20/20 | 19.3/20 average |
| Citation validity | 8/8 | 8/8 | 9/9 | 100% in this set |

In the matched Scenario 1 comparison, runtime moved from 558.08 seconds to 98.46 seconds, an approximately 82% reduction. Provider cost moved from $0.788899 to $0.0559, an approximately 93% reduction.

These measurements show that context design, model routing, and revision policy mattered. They do not guarantee that every current investigation will finish in 98 seconds or cost $0.06.

## Time to first token and provider throughput

One later run reached 310.35 seconds even though tools and specialist calls were normal.

- PM synthesis produced its first token after 2.82 seconds.
- The same call took 170.62 seconds to generate 2,823 tokens.
- Throughput was approximately 16.8 tokens per second.
- A following GPT-5.4 PM revision took 47.33 seconds.
- Together, the sequential PM calls contributed 217.9 seconds.

The bottleneck was provider generation throughput, not connection setup or local orchestration. This is why time to first token and completion time must be measured separately.

Routing PM revision to GPT-5.4 mini reduced the controlled revision call to 15.55 seconds, compared with the historical 35.0 to 47.3-second range.

## Current performance interpretation

Later graph changes added a second Critic review after revision and a bounded specialist repair path for invalid structured output. Those changes improve safety but alter the call count.

Therefore:

- the Phase 12A figures remain historical evidence;
- they are not the current maximum call count;
- Standard mode can now use up to 12 model calls when a revision is re-reviewed, plus a conditional specialist repair;
- Deep mode permits a different routing and revision budget;
- no controlled benchmark has measured the full current combination;
- the latest audited wallet-funding run took 158.9 seconds and revealed a retrieval-quality failure despite completing technically.

## Part III: Failures that changed the system

## 1. Repeated context and PM revision truncation

**Expectation**
Giving later agents the entire evidence history would improve grounding, and retrying a truncated answer would eventually succeed.

**What happened**
The same ledger was repeatedly transmitted. Five PM revision calls reached the output ceiling and repeated the same failure.

**Root cause**
Durable evidence retention and prompt representation had been treated as the same concern. Retry logic did not distinguish transient failure from an oversized task.

**Change**
The ledger remained complete, but prompts became compact and revisions received only the evidence relevant to challenged claims.

**Measured result**
The three historical Phase 12A runs had no truncation events and averaged 21,281 input tokens rather than the profiling run's 125,399.

**Remaining limitation**
Large real datasets may still create pressure. Compaction must be retested when source schemas change.

**Lesson**
A retry helps only when something about the next attempt is different.

## 2. Provider tail latency

**Expectation**
Compact prompts and parallel specialists would keep investigations near the target duration.

**What happened**
One run took 310.35 seconds, dominated by slow sequential PM generation.

**Root cause**
Provider output throughput fell even though time to first token remained fast.

**Change**
Revision moved to a faster model and output contracts became denser.

**Measured result**
The next three historical Standard scenarios averaged 109.10 seconds, although one revised run still took 121.41 seconds.

**Remaining limitation**
Initial PM synthesis remains dependent on provider throughput.

**Lesson**
A fast first token can hide a slow critical path.

## 3. Provider-credit benchmark failure

**Expectation**
A large comparison would establish whether the full multi-agent architecture justified its complexity.

**What happened**
After 13 legitimate executions, 57 runs failed with HTTP 402 errors and 134 were never attempted.

**Root cause**
Large output reservations met provider-credit limits, and retry behaviour treated the rejection as transient.

**Change**
Live evaluation became opt-in, token ceilings became role-specific, and paid runs gained preflight cost controls.

**Measured result**
No aggregate benchmark result was produced.

**Remaining limitation**
Architecture superiority remains unproven.

**Lesson**
Stopping an invalid experiment is better than turning infrastructure failure into a quality claim.

## 4. Missing evidence support in judge context

**Expectation**
The semantic judge received the complete evidence needed to assess each candidate.

**What happened**
The serialized packet omitted the substantive support field from ledger entries.

**Root cause**
The evaluator's context builder did not match the full Evidence Ledger contract.

**Change**
Context-integrity tests now compare judge input with the ledger schema, and the missing field was restored.

**Measured result**
The stress suite moved from 14/15 to 15/15 after this repair and one fixture correction.

**Remaining limitation**
Passing the declared suite does not prove general judge validity.

**Lesson**
An evaluator is only as good as the evidence it receives.

## 5. Human-reference and provenance failure

**Expectation**
Human ratings would provide a straightforward ground truth for judge qualification.

**What happened**
The first comparison used informationally unequal packets. Reviewers sometimes used knowledge outside the evidence. A later artifact described as clean human ratings was not independently human-authored.

**Root cause**
The process lacked verified provenance, blind inputs, and a sufficiently precise review construct.

**Change**
The invalid comparison was revoked. The replacement protocol uses neutral content-hashed packets, independence attestations, atomic criteria, severity anchors, and adjudication.

**Measured result**
An independent product manager later matched GPT-5.4 on all five verdicts and severities in the development pilot.

**Remaining limitation**
Five development cases are not a held-out reliability benchmark.

**Lesson**
A file labelled “human review” is not evidence of independent review. Provenance is part of evaluation quality.

## 6. Ambiguous rubric and incorrect expected labels

**Expectation**
Predeclared labels represented an objective standard.

**What happened**
Author review found two excessive severity labels, one incorrect contradiction verdict, and an embedded-instruction criterion that evaluated the wrong subject.

**Root cause**
The rubric had not yet been tested against enough concrete disagreements.

**Change**
Each disagreement was adjudicated and `atomic_semantic_v2` was created.

**Measured result**
The author and current development expectations agreed on all 15 cases after adjudication. This is diagnostic author agreement, not independent ground truth.

**Remaining limitation**
New cases may expose further ambiguity.

**Lesson**
Ground truth for open-ended product analysis is constructed through explicit decisions, not discovered as a naturally perfect label.

## 7. Defective source-failure review packet

**Expectation**
The judge would assess whether a candidate handled an unavailable source correctly.

**What happened**
The packet omitted the actual source-failure record, so the judge returned `NOT_APPLICABLE`.

**Root cause**
Packet construction lost a structured input required by the criterion.

**Change**
The packet was corrected and only the affected case was rerun.

**Measured result**
The corrected human and judge verdicts agreed. Four unchanged judgments were reused from cache.

**Remaining limitation**
Packet-integrity validation must evolve when evidence schemas change.

**Lesson**
An unexpected judge answer may be evidence of a broken test, not a weak model.

## 8. Post-revision quality-gate bypass

**Expectation**
Once the Critic requested changes, the revised recommendation would satisfy the same quality gate.

**What happened**
An earlier workflow could accept the revised answer without a second Critic review.

**Root cause**
The revision path treated rewriting as completion rather than another candidate requiring validation.

**Change**
The revised recommendation now returns to the Critic within the bounded loop.

**Measured result**
The graph now requires the second verdict before successful completion when revision occurs.

**Remaining limitation**
The additional safety call increases latency and cost.

**Lesson**
A review process is incomplete if the reviewed artifact is not the one ultimately delivered.

## 9. Analytics rows hidden by an empty scalar value

**Expectation**
The analytics result's primary `value` field represented whether useful data existed.

**What happened**
Table-shaped PostHog results could contain useful rows while the scalar `value` remained empty. Downstream agents interpreted those results as missing data.

**Root cause**
The evidence summary handled scalar and tabular analytics as if they shared one representation.

**Change**
Evidence summaries preserve rows when a scalar value is unavailable.

**Measured result**
Table-shaped funnel and breakdown evidence became visible to specialist and PM prompts.

**Remaining limitation**
Semantic query errors can still produce genuinely empty rows, as the later wallet-funding case demonstrated.

**Lesson**
Transport success, data presence, and analytical meaning are different conditions.

## 10. Correct reasoning over incorrect retrieval

**Expectation**
Grounded synthesis and Critic review would prevent an unusable decision brief.

**What happened**
The wallet-funding report was cautious but missed evidence that existed in PostHog and Zendesk.

**Root cause**
The Analytics Agent used a semantically invalid filter, the Research Agent ignored broad-search recovery, and the Planner accepted the user's premise too early. Existing gates validated the resulting packet rather than the process that created it.

**Change**
The failure has been identified as a required retrieval-regression case. The application correction is not yet complete at the time of this document update.

**Measured result**
No post-fix result is claimed.

**Remaining limitation**
Another paid investigation should not be treated as a validation run until the retrieval gate exists and passes offline.

**Lesson**
Evidence provenance explains where a record came from. It does not prove that the investigation retrieved the records it should have found.

## Current priorities

Before another paid demo investigation is used as evidence of readiness:

1. convert the wallet-funding failure into an end-to-end retrieval regression case;
2. validate domain property and value combinations, not only JSON shape;
3. require the normal journey funnel before failure-event analysis;
4. enforce broad support discovery before repeated narrow zero-result searches;
5. test the four demo scenarios for expected source coverage and premise challenge;
6. prevent repeated equivalent empty searches from inflating evidence volume;
7. make the Critic or a deterministic gate detect implausibly empty retrieval sets;
8. rerun offline retrieval and workflow tests before approving another paid investigation.

## Source documents and artifacts

- [Current evaluation strategy](../evaluation/EVALUATION_STRATEGY.md)
- [ADR-0027: Product-owned evaluation cases and audited judge calibration](../decisions/ADR-0027-product-owned-evaluation-cases-and-audited-judge-calibration.md)
- [Evaluation case library](../../evaluations/cases/README.md)
- [Atomic semantic rubric v2](../../evaluations/cases/rubrics/atomic_semantic_v2.json)
- [Five-case pilot result](../../evaluations/cases/reference_sets/judge_pilot_v1_result.json)
- [Author-review adjudication](../../evaluations/cases/adjudications/author_review_2026-09-29.csv)
- [Human review protocol](../../evaluations/reviews/human_review/README.md)
- [Historical Phase 9 final report](../../evaluations/runs/phase9_final_report.md)
- [Historical judge failure postmortem](../../evaluations/runs/phase9_judge_failure_postmortem.md)
- [Historical human-rating provenance audit](../../evaluations/runs/phase9_human_rating_provenance_audit.md)
- [Historical Phase 10 integrity audit](../../evaluations/runs/phase10_final_integrity_audit.md)
