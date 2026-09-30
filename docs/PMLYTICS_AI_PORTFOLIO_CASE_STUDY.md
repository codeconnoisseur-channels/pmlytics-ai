# PMLytics AI Product Case Study

## Building a multi-agent system for evidence-backed product decisions

PMLytics AI is a multi-agent product investigation system that helps product managers investigate fragmented evidence across Zendesk, PostHog, and Jira before deciding what their team should do next.


[Watch the product demo](https://drive.google.com/file/d/1JdMQtMo5zCblaGgDW_vAIYqUwwh4aaSJ/view?usp=sharing)

| | |
| --- | --- |
| **Primary user** | Product managers and product leads |
| **Product job** | Turn evidence from customer support, product analytics, and engineering into a defensible next step |
| **Output** | A decision brief with a recommendation, confidence, findings, risks, success measures, and evidence citations |
| **My role** | AI Product Manager and product builder |
| **Data environment** | Synthetic fintech data across an API-compatible Zendesk mock, MockServer-based Jira, and a live PostHog integration |

### Explore the project

- [Architecture](project/02_ARCHITECTURE.md)
- [AI evaluation, failures, and learnings](project/03_AI_EVALUATION_FAILURES_AND_LEARNINGS.md)
- [AI Product Strategy](project/06_AI_PRODUCT_STRATEGY.md)
- [AI Operating and Safe Release Plan](project/07_AI_OPERATING_AND_SAFE_RELEASE_PLAN.md)
- [PMLytics AI Q&A](project/05_PMLYTICS_AI_Q_AND_A.md)

## Overview

Product managers are expected to make evidence-based decisions, but the evidence behind one decision often lives in several systems.

A change in a PostHog funnel may show where users are dropping off. Zendesk tickets may reveal what those users experienced. Jira may show a known defect, an incident, or work already underway. None of those systems independently answers the question a product manager actually has: **What should the team do next, and how strongly does the evidence support that decision?**

I built PMLytics AI to investigate that question. The system plans an investigation, gathers source-specific evidence, preserves where every finding came from, produces a recommendation, and checks whether that recommendation goes beyond what the evidence supports.

The result is a decision brief rather than a raw data dump. It leads with the recommended next move and provides the reasoning, confidence, risks, success measures, unresolved questions, and supporting records behind it.

## Problem

Consider a product manager investigating a rise in failed transfers. Their normal workflow might look like this:

1. Open PostHog and compare completion and failure behaviour for the relevant period.
2. Search Zendesk for complaints that may use different language from the analytics events.
3. Search Jira for incidents or defects that might explain the pattern.
4. Align dates, terminology, customer segments, and apparently conflicting signals.
5. Decide whether the evidence supports a fix, an experience change, more instrumentation, or further investigation.

The work is difficult because each system describes a different part of reality:

- Zendesk captures what customers report, but ticket volume does not establish prevalence.
- PostHog captures what users do, but correlation does not prove a cause.
- Jira captures engineering knowledge, but issue priority does not establish customer impact.

The PM is left to reconcile those differences manually. The process is slow, hard to repeat, and vulnerable to predictable reasoning errors. A plausible Jira issue can be mistaken for a confirmed root cause. A support theme can be treated as representative of the full customer population. Two events that happened at the same time can be presented as causal.

## Product Strategy

The product is positioned between evidence retrieval and product decision-making. It does not replace Zendesk, PostHog, Jira, governed analytics, or the PM responsible for the decision. It provides a controlled first-pass investigation that a PM can inspect and challenge.

The initial product wedge is evidence-heavy product questions where customer support, product analytics, and engineering tracking each contain part of the answer. Examples include a funnel decline, complaint surge, apparent transaction failure, low feature adoption, or disagreement between customer reports and measured behaviour.

The primary user is a product manager or product lead. The likely economic buyer is still a hypothesis and could be a Head of Product, Product Operations leader, business-unit product leader, or founder. I have not treated user interest, market demand, or willingness to pay as validated simply because the product has been implemented.

The value proposition has four parts:

1. reduce the manual effort required to investigate several systems;
2. improve decision discipline by separating evidence from interpretation;
3. make recommendations auditable through source-level records;
4. expose contradictory or missing evidence before a team commits to the wrong action.

The candidate north-star measure is the percentage of investigations that help a product team reach a defensible decision faster than its existing process. Supporting measures would include time to decision, recommendation adoption, evidence inspection, follow-up completion, later reversals, user trust, repeat usage, and cost per useful investigation. Report completion and citation clicks alone would not establish product value.

The landing page's Starter, Team, and Enterprise packages are product-design hypotheses, not validated commercial offers. A future pricing decision would need evidence about investigation frequency, value of time saved, acceptable latency, integration cost, model economics, buyer type, and whether use is individual or collaborative.

The technology itself is not the moat. Models, prompts, agents, and common SaaS integrations can be reproduced. A defensibility thesis would have to develop through organisation-specific source mappings, a trusted evaluation library built from real failures, decision-to-outcome feedback, workflow embedding, and demonstrated governance. None of those is claimed as an established moat today.

The complete strategic rationale, adoption hypothesis, outcome model, pricing trade-offs, risks, roadmap, and simplify-or-stop criteria are documented in the [AI Product Strategy](project/06_AI_PRODUCT_STRATEGY.md).

## Why AI Was Appropriate

A conventional dashboard is useful when the metric and question are already known. Search is useful when the user knows what record or phrase to look for. Neither is designed to plan an open-ended investigation across narrative, behavioural, and engineering evidence.

PMLytics AI uses models where language understanding and judgement are valuable:

- translating a product question into source-specific investigation tasks;
- selecting focused searches and analyses within fixed permissions;
- identifying patterns in support conversations and engineering issues;
- interpreting product behaviour without treating association as causation;
- reconciling incomplete or contradictory evidence;
- recommending a proportionate next step and expressing uncertainty;
- challenging a recommendation that is stronger than its evidence.

I did not use AI for conditions that must always hold. Application code controls authentication, ownership, schemas, tool permissions, citation identity, call budgets, loop limits, persistence, and final workflow status.

This hybrid boundary became one of the most important design principles in the project: models contribute judgement, while deterministic code controls access and enforces workflow invariants.

## Product Experience

A product manager signs in, enters a question, and can select the period they want to investigate. The system creates the investigation before model work begins, so the run has a durable identity and owner from the start.

The user then sees progress as the workflow moves through planning, evidence collection, analysis, recommendation, and review. Progress events are streamed from the backend. If the stream disconnects, the interface reconnects and can fall back to polling the persisted investigation rather than restarting it.

The completed brief contains:

- a recommendation and confidence level;
- an executive finding and affected customers;
- observed facts, interpretations, and hypotheses;
- measures that would show whether the decision worked;
- risks and questions that still need validation;
- citations linked to source summaries;
- a deeper evidence view containing the relevant tickets, analytics results, issues, and comments.

When the evidence cannot support a strong decision, the product can return a partial result or recommend further investigation. It is better to name the missing evidence than manufacture certainty.

## What Makes the System Agentic

PMLytics AI is not a set of prompts run in a fixed sequence. It has bounded autonomy inside an application-controlled workflow.

### Goal-directed planning

The Planner converts an open-ended product question and date range into a typed investigation plan. It identifies which evidence sources are relevant and gives each specialist a defined objective.

### Conditional tool use

Specialists decide which permitted searches or analyses are needed for their assigned task. They do not receive general internet or HTTP access. Their choices are constrained to domain tools owned by the application.

### Working state

The workflow maintains explicit state for the investigation plan, evidence, specialist findings, failures, call budgets, recommendation, Critic feedback, and revision count. This is working memory for the current investigation, not an informal conversation transcript.

### Feedback and adaptation

After the first evidence pass, an assessment step can identify a specific, answerable gap and authorize one targeted follow-up. The Critic can also return a `REVISE` decision that sends focused feedback to the PM agent.

### Stop conditions

Every iterative path is bounded. Tool calls have limits, only one targeted follow-up round is allowed, structured-output repair is conditional and finite, and recommendation revision is limited. The system can stop with a partial answer instead of pursuing certainty indefinitely.

### Persistence and recovery

Investigation records, events, final state, and LangGraph checkpoints are stored in PostgreSQL through Supabase. Completed work remains available after navigation or restart. When a process may have stopped during an unresolved paid model call, the workflow requires explicit recovery rather than silently risking duplicate spend.

The system does not use long-term agent memory. Previous investigations are durable user records, but their conclusions are not automatically injected into a new investigation. This avoids allowing an old interpretation to contaminate new evidence.

## Why I Used Multiple Agents

I considered a single general agent with access to all three sources. It would have been simpler to implement, but it would also have combined retrieval, interpretation, and recommendation inside one broad permission boundary.

I instead separated six logical responsibilities:

| Role | Responsibility | Tool access |
| --- | --- | --- |
| Planner | Scopes the question and creates source-specific tasks | No evidence-source tools |
| Research | Investigates what customers are reporting | Zendesk only |
| Analytics | Investigates what users are doing | PostHog only |
| Engineering | Investigates relevant defects, incidents, and delivery context | Jira only |
| PM Synthesis | Reconciles evidence and recommends the next move | No external tools |
| Critic | Tests the recommendation for unsupported claims and overconfidence | No external tools |

The three specialists can run in parallel after planning because their retrieval work is independent. Their results join before assessment and synthesis.

The most important benefit is not the number of agents. It is the separation of responsibilities. The PM agent cannot quietly perform another search until it finds support for the answer it wants to give. The Critic reviews the recorded evidence and candidate recommendation rather than gathering a different evidence set.

This also makes failures easier to diagnose. I can distinguish between information that was never retrieved, a source that failed, a specialist that misinterpreted a record, and a PM recommendation that went beyond otherwise valid evidence.

The trade-off is real. Multiple agents increase model calls, coordination, latency, and cost. The project retains simpler baseline architectures because multi-agent complexity should remain testable rather than be treated as automatically superior. A planned large comparison was not completed successfully, so I do not claim that this topology outperforms a single agent in every situation.

## Architecture

```text
User
  |
Next.js application
  |
Supabase authentication
  |
FastAPI lifecycle and authorization layer
  |
LangGraph investigation workflow
  |-- Planner
  |-- Research specialist ------ Zendesk adapter
  |-- Analytics specialist ----- PostHog adapter
  |-- Engineering specialist --- Jira adapter
  |-- Evidence assessment and optional follow-up
  |-- PM synthesis
  |-- Critic and bounded revision
  |
Decision brief and Evidence Ledger
  |
Supabase PostgreSQL and LangGraph checkpoints
```

The main technology choices were:

- **LangGraph** for stateful orchestration, parallel branches, conditional routing, bounded revision, and checkpoints.
- **FastAPI** for authenticated lifecycle APIs, typed contracts, source adapters, streaming, and explicit failure states.
- **Next.js** for the product interface and investigation experience.
- **OpenRouter** for central model access and role-based routing.
- **Supabase Auth and PostgreSQL** for identity, owner-scoped investigations, events, final state, and workflow checkpoints.
- **LangSmith** for investigation traces, node runs, tool calls, tokens, latency, and errors.
- **PostHog** as a live analytics integration containing deterministic synthetic events.
- **API-compatible Zendesk and Jira mocks** for reproducible customer-support and engineering evidence.

## Evidence Grounding and Safety

The hardest failure in this product is not malformed JSON. It is a polished recommendation that sounds reasonable but is not supported by the organisation's evidence.

I introduced an append-only Evidence Ledger as the grounding boundary. Every successful tool result becomes an evidence entry with an identifier, source, source reference, retrieval time, factual summary, confidence, limitations, and typed source payload. Failed tool calls are recorded separately as errors and never converted into evidence.

Specialist findings can cite only ledger entries created by their permitted source. The final recommendation retains those references, and the application validates them again before presenting the report. The main brief can stay concise while the evidence view exposes the records behind a claim.

Other safeguards include:

- role-specific tool allowlists enforced in code rather than prompts;
- typed tool inputs, outputs, agent findings, recommendations, and reviews;
- explicit separation of observations, interpretations, and hypotheses;
- deterministic date scoping for support and analytics queries;
- read-only source access;
- bounded model calls, tool calls, follow-up, repair, and revision;
- owner-scoped API operations and private investigation records;
- explicit `completed`, `partial`, `failed`, and `recovery_required` outcomes.

The agents cannot create Jira issues, modify tickets, change analytics configuration, or execute a production remediation. I deliberately kept consequential actions under human control. If I later added an action layer, I would begin with proposed actions, require explicit approval, and use separate write credentials, policy checks, idempotency, and audit logs.

## Failure Handling

The project taught me that “retry” is not one behaviour.

A transient provider failure may justify a bounded retry. A response cut off because the task is too large requires a smaller context or output contract. Missing evidence requires another authorised investigation step or an honest limitation. A provider credit rejection will not be fixed by waiting and sending the same expensive request again.

The workflow therefore treats failures according to their meaning:

- A failed source can produce a partial report when the remaining evidence still supports a useful conclusion.
- No usable evidence produces a failed investigation rather than a guessed answer.
- Invalid structured output receives only its permitted repair attempt.
- A dropped progress stream reconnects or falls back to the persisted state without restarting the investigation.
- An ambiguous in-flight paid request requires explicit recovery when an automatic replay could spend twice.

The rule I took from this was simple: a retry helps only when something relevant about the next attempt is different.

## Evaluation

I initially focused evaluation on the quality of the final recommendation. That was necessary, but it was not enough. The project eventually exposed two different ways the product could fail:

1. it could retrieve the right evidence and reason badly about it;
2. it could reason carefully over an evidence set that was incomplete because retrieval went wrong.

That distinction now shapes the evaluation system.

### What is checked in code

Deterministic checks enforce conditions that should not depend on another model's opinion. Citations must resolve to real Evidence Ledger entries, sources and references must match, tool permissions and call budgets must hold, structured outputs must validate, and hidden expected answers must remain outside runtime prompts.

### What requires judgement

The semantic evaluator examines one clear question at a time:

- Is every important factual claim supported?
- Does each citation support the claim attached to it?
- Are relevant sources connected rather than listed separately?
- Are contradictions reflected in confidence and action?
- Does causal language match the available evidence?
- Is the recommendation proportionate?
- Are missing sources disclosed?
- Are instructions embedded inside retrieved data ignored?

Each question receives a pass, fail, unclear, or not-applicable verdict. Failures are classified as minor, major, or critical. This replaced dependence on one blended score that could hide an unsafe weakness inside a reasonable average.

### What the stress suite taught me

Fifteen development cases cover fabricated metrics, irrelevant citations, contradictory sources, causal overreach, missing evidence, disproportionate recommendations, and malicious instructions hidden inside retrieved content.

The first run detected 14 of the 15 expected behaviours. The missing case led me to a defect in the evaluator itself: its packet builder had omitted the substantive support behind each evidence record. After repairing the packet and correcting one over-specified fixture, the evaluator detected all 15 declared behaviours.

That did not prove that the judge was universally correct. It proved that evaluation infrastructure needs the same scrutiny as the product it evaluates.

## The Human and LLM Evaluation Dilemma

I initially treated human scoring as the natural reference point for an LLM judge. The work made that assumption less comfortable.

Human reviewers could understand nuance, but the project author could also fill gaps using knowledge of what the system intended to do. The judge was stricter about unsupported claims, but its decision still depended on its rubric and the evidence packet it received.

The first comparison also gave the human and judge different information. A later artifact presented as clean human ratings was generated programmatically in the agent environment and had access to prior judge results. I withdrew that evidence rather than use circular agreement to claim that the judge was validated.

I changed the division of labour:

- the judge reviews declared cases consistently;
- humans independently audit a sample and difficult disagreements;
- both receive the same blind, content-hashed packet;
- expected answers and previous decisions are hidden;
- disagreements are adjudicated rather than averaged;
- deterministic checks remain hard gates.

This process changed the rubric itself. Author review found two severity labels that were too harsh, one contradiction case with the wrong expected verdict, and one security question written ambiguously. Those disagreements produced a clearer second version of the rubric.

A later independent pilot compared GPT-5.4 with a product manager across five development cases. They agreed on all five verdicts and severities, identified both critical failures, and produced no false passes or false failures in that sample. I did not call this a held-out benchmark because the cases had already influenced development. Five matching cases are evidence that the protocol worked on that sample, not proof of permanent judge reliability.

## The Retrieval Gap That Changed the Evaluation Again

A later paid wallet-funding investigation revealed the next weakness.

The final report cautiously said there was not enough evidence to confirm elevated failures. Its citations were valid relative to the retrieved packet. But the packet was incomplete:

- PostHog contained 483 wallet-funding starts, 283 submissions, and 283 completions.
- The Analytics Agent filtered `user_type` using `debit_card`, which was a payment method rather than a valid customer type, so it removed the relevant events.
- Zendesk contained 12 relevant tickets, but the Research Agent repeatedly searched for the word “failure” instead of starting with the broad wallet-funding journey.
- Jira correctly showed no matching incident.

The intended insight was that customers were abandoning before submission, with support evidence pointing to unexpected cost, not that transactions were failing after submission.

The Critic could make the recommendation more cautious, but it could not recover evidence the specialists had failed to retrieve. This exposed a boundary in the earlier evaluation design: it tested whether conclusions were grounded in the packet more strongly than whether the packet represented the evidence available in the sources.

The evaluation standard is now broader:

> Did the system retrieve the right evidence, interpret it at the strength that evidence supports, challenge the question's premise, and recommend a next step a product manager could defend?

The held-out set remains empty, and retrieval quality is the next major evaluation gate. I would rather preserve that limitation than turn a small development pilot into a claim the evidence cannot support.

The lesson was larger than evaluator selection. Evaluation is itself a product system. Its inputs, permissions, information symmetry, rubric, and provenance require the same scrutiny as the system it measures.

## Operating and Safe Release Approach

I separated the ability to demonstrate the product from the evidence required to call it production ready. A successful model response or polished reference report is not a release standard.

The operating model uses stage-specific release gates across:

- identity, ownership, and secrets;
- source connectivity and retrieval correctness;
- evidence integrity and provenance;
- recommendation quality and uncertainty;
- workflow termination and recovery;
- evaluation evidence;
- performance and provider economics;
- product experience and user trust;
- production data governance.

The current controlled portfolio demonstration is **approved with documented limitations**. It can use the recorded demo, precomputed reference investigations, and controlled local access. Another paid live investigation should wait until the offline retrieval regression gate passes.

A private design-partner or production release is **blocked**. The major gaps are incomplete end-to-end retrieval validation, no production-shaped source validation, no qualified held-out set, no enterprise tenant and governance model, no sustained-concurrency validation, and no demonstrated business outcomes with target users.

The held-out set remains intentionally empty. The existing 15 stress cases are development cases, and the five independently reviewed cases form a calibration pilot. Actual held-out cases will be created only after the system is stable and an independent reviewer is available. Until then, I would rather disclose the gap than manufacture a release claim.

The plan also distinguishes failures that need different responses. A transient provider error may justify a bounded retry. A semantically wrong query needs retrieval correction. Missing evidence requires targeted investigation or disclosure. A credit failure should stop. An ambiguous paid call requires explicit checkpoint recovery. Treating all of these as “retry” would make the system more expensive and less predictable.

The full ownership model, change policy, release gates, incident process, cost controls, and readiness assessment are documented in the [AI Operating and Safe Release Plan](project/07_AI_OPERATING_AND_SAFE_RELEASE_PLAN.md).

## Performance and Cost

One early profiled investigation took 558.08 seconds, made 21 model calls and 26 tool calls, used 164,734 tokens, and cost $0.788899 through the model provider.

I initially expected the three specialists to be the main source of cost and delay. The trace showed something different:

- PM and Critic work represented 73.2 percent of provider cost.
- PM revision attempts represented 55.8 percent of provider cost.
- More than 60 percent of input tokens came from duplicated context.
- The full evidence history was repeatedly sent into synthesis and revision.
- Five revision attempts reached the output limit and regenerated substantially the same work.

The system was preserving evidence and presenting evidence to a model as though they were the same problem. They are not. A complete record must remain available for audit, but every reasoning step does not need every field from every record.

I changed the system in four ways:

1. The complete typed Evidence Ledger remained durable, while model prompts received compact representations suited to their task.
2. PM revision received a focused evidence set related to the Critic's challenged claims, contradictions, and limitations.
3. Normal specialist work was consolidated into one tool-selection turn and one synthesis turn.
4. Models and output limits were allocated by role instead of using the strongest model and largest context everywhere.

In the matched historical scenario, runtime fell from 558.08 seconds to 98.46 seconds, an 82 percent reduction. Provider cost fell from $0.788899 to $0.0559, a 93 percent reduction.

A three-scenario validation of that optimisation averaged:

| Metric | Result | Context |
| --- | ---: | --- |
| End-to-end latency | 109.10 seconds | Three historical Standard-profile scenarios |
| Provider cost | $0.0656 | Average per investigation |
| Semantic quality | 20/20, 18/20, 20/20 | Versioned five-dimension evaluator |
| Citation validity | 25/25 | No hallucinated citation identifiers |
| Truncated outputs | 0 | Across the three validation runs |

These are controlled historical project results, not a production service-level promise. Later safety changes restored a final Critic check after revision and allowed one conditional specialist repair, so the current workflow can perform more work than the measured optimisation path. I would run a new controlled benchmark before publishing current latency or cost expectations.

The performance work changed how I think about AI economics. The biggest improvement did not come from adding another agent or rewriting every prompt. It came from examining the trace, identifying repeated work, changing what each role received, and reserving expensive reasoning for the step where it added the most value.

## Product and Architecture Trade-offs

| Decision | Benefit | Trade-off |
| --- | --- | --- |
| Specialist agents | Clear source and tool boundaries | More calls and coordination than one agent |
| Separate PM and Critic | Independent challenge of unsupported recommendations | Additional latency and another fallible model judgement |
| Evidence Ledger | Traceable claims and deeper auditability | More state and context-management work |
| Bounded follow-up and revision | Allows adaptation without uncontrolled loops | May return a partial result before every uncertainty is resolved |
| Read-only agents | Keeps consequential actions under human control | Limits operational autonomy |
| Mock Zendesk and Jira | Safe and reproducible evidence scenarios | Does not prove behaviour on production schemas or permissions |
| Live PostHog with synthetic events | Exercises a real analytics integration | Does not represent real customer behaviour |
| Supabase identity and persistence | Durable private investigations and checkpoints | Adds authorization, migration, and recovery complexity |
| Server-Sent Events with polling fallback | Responsive progress without making the browser authoritative | Requires two delivery paths and careful state reconciliation |

## Current Limitations

The system has not been validated on real customer support data, production Jira projects, or real customer-event data. Pocket is a fictional fintech context, and all scenario evidence is synthetic.

The product also has no production traffic or enterprise-scale validation. It uses direct user ownership rather than organisations, workspaces, SSO, delegated administration, or enterprise role-based access. Provider cost and latency remain variable, and the current post-hardening workflow needs a new controlled performance baseline.

End-to-end retrieval quality is not yet a complete release gate. A recent wallet-funding investigation showed that the final recommendation could be cautious and correctly cited relative to its packet while still missing evidence that existed in PostHog and Zendesk. The four demo scenarios need deterministic retrieval-regression coverage before another paid run is treated as validation.

PMLytics AI is a read-only decision-support system. It does not execute its recommendations, use long-term agent memory, or provide public links to private investigations. Those are deliberate boundaries, not capabilities hidden behind the interface.

## What I Would Build Next

My next priorities would be:

1. **Complete the retrieval-quality gate.** Turn the wallet-funding failure and the other demo scenarios into end-to-end cases that verify query semantics, expected evidence coverage, broad-search recovery, and premise challenge before paying for another live validation run.
2. **Validate the product problem and outcomes.** Test whether PMs reach decisions faster, whether briefs change or clarify action, and whether users return after the novelty of the first investigation.
3. **Production-shaped source validation.** Test authorised support, analytics, and engineering schemas to understand source mapping, permissions, and data-quality problems that synthetic scenarios cannot reveal.
4. **Adaptive workflow routing.** Send straightforward questions through a cheaper path and reserve the full multi-agent workflow for questions with multiple sources, contradictions, or higher decision risk.
5. **Qualify a held-out reference set later.** When the system is stable and an independent reviewer is available, create new unseen cases, adjudicate them, seal the version, and run one bounded release evaluation.
6. **Durable background execution.** Move active work from API-process tasks to a worker and queue architecture before supporting substantial concurrent usage.
7. **Enterprise ownership when justified.** Add organisations, workspaces, tenant roles, retention controls, and audit administration before handling production company data.

## My Role

I worked as the AI Product Manager and product builder. I defined the user problem and product scope, designed the investigation and decision-brief experience, specified the agent responsibilities and safety boundaries, and established the evaluation strategy.

I also worked directly with the implementation across the Next.js interface, FastAPI services, LangGraph workflow, source tools and adapters, Supabase persistence, model routing, observability, evaluation tooling, and documentation. My role was not limited to writing requirements. I stayed close enough to the implementation to understand why the system failed, read the traces, and make informed product and technical decisions.

The project required decisions across product usefulness, user trust, model behaviour, latency, cost, security, and system reliability. My responsibility was to keep those decisions connected rather than optimise one of them in isolation.

## Key Learnings

### A multi-agent system is an operating structure, not a collection of prompts

The prompts matter, but the system underneath them determines whether the product is reliable. State, tool permissions, evidence contracts, retries, stop conditions, persistence, and ownership decide what an agent is allowed to do and what happens when it is wrong.

### More context can produce worse results

Preserving complete evidence is important. Sending all of it to every model on every attempt is not. Repeated context increased cost, delayed the answer, and made the relevant evidence harder to identify. Durable state and task-specific model context should be designed separately.

### A retry requires a theory of the failure

Retries improved reliability only when the failure was plausibly temporary or the next attempt changed. Repeating an oversized request, a missing-evidence problem, or a provider credit failure multiplied cost without improving the outcome.

### Evaluation systems need their own controls

The evaluator's missing support field changed what it could judge. The human-comparison process showed that information symmetry and provenance matter as much as the scoring rubric. A confident evaluation result is still weak if the evaluator did not receive the right evidence.

### Uncertainty is part of the product

A decision-support product should not force a strong answer from weak evidence. Partial results, explicit limitations, lower confidence, and “investigate further” can protect the team from spending time on a plausible but unsupported explanation.

## What This Means for Your Team

This project reflects how I approach AI product work. I start with the decision a user needs to make, identify where model judgement is useful, and keep permissions, evidence, reliability, and ownership under deterministic control.

I can work with engineers on orchestration, traces, tool failures, state, evaluation, latency, and cost without losing sight of whether the final experience helps the user make a better decision. I can also challenge AI complexity when a deterministic component, narrower workflow, or explicit limitation would produce a more trustworthy product.

For a team building AI products, that means having an AI Product Manager who can frame the problem, design the product and its evaluation, understand the system beneath the interface, and make evidence-based trade-offs across usefulness, quality, speed, cost, safety, and user trust.
