# Pocket AI Product Discovery Team
## Data & API Specification

**Version:** 1.0  
**Status:** Draft  
**Related documents:**
- Pocket AI Product Discovery Team — PRD v1.0
- Pocket AI Product Discovery Team — Product Specification v1.0
- Pocket AI Product Discovery Team — System Architecture v1.0
- Pocket AI Product Discovery Team — Agent Specification v1.0

---

# 1. Purpose

This document defines the data environment and API contracts used by Pocket AI Product Discovery Team.

It answers five questions:

1. What fictional product data exists?
2. How is that data represented?
3. How do the AI agents access it?
4. How are the three systems related?
5. How is the environment seeded reproducibly?

The objective is to create a small but coherent fictional product environment that behaves like a real company's product stack.

The agents should interact with the data through APIs and application tools rather than accessing seed files or databases directly.

---

# 2. Data Architecture

Pocket uses three primary evidence systems:

```text
                         POCKET
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        MOCK ZENDESK    POSTHOG       MOCK JIRA
        Customer       Behaviour     Engineering
        evidence       evidence      evidence
```

These systems deliberately represent different perspectives.

### Zendesk

What customers **say**.

### PostHog

What users **do**.

### Jira

What engineering **knows or is working on**.

The systems are related but are not mirror images of one another.

---

# 3. Source-of-Truth Boundaries

Each source has a primary responsibility.

| Information | Primary source |
|---|---|
| Customer complaint | Zendesk |
| Customer conversation | Zendesk |
| Ticket status/priority | Zendesk |
| User behaviour | PostHog |
| Funnel performance | PostHog |
| Event-level product activity | PostHog |
| Engineering bug | Jira |
| Engineering status | Jira |
| Technical investigation | Jira |
| Engineering discussion | Jira |

An agent should not manufacture one source's information from another source.

For example:

> Zendesk contains a complaint.

does not imply:

> PostHog confirms the complaint.

The second claim requires analytics evidence.

---

# 4. Fictional Product

## Company

**Pocket**

## Category

Consumer fintech.

## Market

Nigeria.

## Product

A consumer financial application for sending, receiving and managing money.

## Primary capabilities

- wallet funding
- bank transfers
- receiving money
- bill payments
- transaction history
- basic account management

---

# 5. Product Journey

The core transfer journey is:

```text
User opens transfer
        ↓
Selects recipient
        ↓
Enters amount
        ↓
Reviews transfer
        ↓
Submits transfer
        ↓
Transfer processing
        ↓
Transfer completed
```

The main analytics journey is represented through events.

---

# 6. Product Analytics Event Taxonomy

PostHog events should use a controlled event vocabulary.

## Account

```text
signup_completed
login_completed
```

## Wallet

```text
wallet_funding_started
wallet_funding_submitted
wallet_funding_completed
wallet_funding_failed
```

## Transfers

```text
transfer_started
transfer_recipient_selected
transfer_reviewed
transfer_submitted
transfer_processing
transfer_completed
transfer_failed
transfer_cancelled
```

## Bill payments

```text
bill_payment_started
bill_payment_submitted
bill_payment_completed
bill_payment_failed
```

## KYC

```text
kyc_started
kyc_document_submitted
kyc_completed
kyc_failed
```

The event vocabulary should remain deliberately small.

---

# 7. Standard Analytics Properties

Relevant events should contain consistent properties.

Example:

```json
{
  "distinct_id": "usr_01428",
  "event": "transfer_submitted",
  "timestamp": "2026-08-14T15:23:01Z",
  "properties": {
    "transaction_id": "txn_003827",
    "amount_ngn": 75000,
    "bank": "Bank A",
    "app_version": "2.4.1",
    "user_type": "student"
  }
}
```

Not every event requires every property.

The seed generator should only attach properties that are meaningful for that event.

---

# 8. Controlled Dimensions

The synthetic environment should use a finite set of realistic dimensions.

## User type

```text
student
freelancer
young_professional
small_business
```

## Bank

Use fictional names rather than real Nigerian banks:

```text
Bank A
Bank B
Bank C
Bank D
Bank E
```

## App version

```text
2.3.0
2.3.1
2.4.0
2.4.1
```

## Transaction size

The seed generator should produce numerical amounts, with useful ranges such as:

```text
< ₦10,000
₦10,000–₦49,999
₦50,000–₦199,999
≥ ₦200,000
```

These ranges exist primarily to support segmentation.

---

# 9. Synthetic User Population

The environment should contain a consistent fictional user population.

Initial target:

**2,000 users**

Each user should have:

```text
user_id
user_type
signup_date
bank
app_version
```

Not all users need to perform all actions.

The generator should create realistic behavioural differences.

---

# 10. Synthetic Transaction Population

The initial environment should contain approximately:

**5,000 transfer attempts**

Each transaction should have a stable identifier:

```text
transaction_id
```

and relevant properties:

```text
user_id
amount_ngn
bank
app_version
timestamp
status
```

These identifiers are primarily useful for maintaining internal data consistency.

---

# 11. PostHog Event Volume

Approximately:

**10,000–20,000 events**

should initially be generated.

The exact volume may change as the dataset is tuned.

The goal is not to simulate millions of users.

The goal is to produce enough behavioural data for:

- funnels
- segmentation
- comparisons
- time trends
- anomaly investigation

---

# 12. Zendesk Data Model

The mock Zendesk environment should represent support tickets using a subset of the real Zendesk ticket model.

Zendesk's real Tickets API supports ticket creation through `POST /api/v2/tickets`, and the ticket resource contains core ticket properties such as requester, subject and comments.

## Ticket

Required conceptual fields:

```text
id
subject
description
status
priority
created_at
updated_at
requester
tags
comments
```

Optional fields:

```text
type
assignee
group
channel
custom_fields
```

Only fields needed by the investigation workflow should be implemented.

---

# 13. Zendesk Ticket Statuses

Use:

```text
new
open
pending
solved
closed
```

The mock should preserve meaningful lifecycle relationships.

For example:

- a newly reported problem may be `new`
- an actively investigated issue may be `open`
- a customer response may result in `pending`
- resolved cases may be `solved`

---

# 14. Zendesk Priority

Use:

```text
low
normal
high
urgent
```

Priority should not automatically indicate product importance.

This is intentional.

The PM Agent should not infer:

> urgent ticket = highest-priority product problem.

---

# 15. Zendesk Channels

Use a small realistic set:

```text
email
web
chat
```

The purpose is to add natural variation rather than reproduce every Zendesk capability.

---

# 16. Zendesk Comments

Comments represent the conversation surrounding a ticket.

The real Zendesk API exposes ticket comments through:

```text
GET /api/v2/tickets/{ticket_id}/comments
```

and comments may contain public or private content.

For the mock environment, implement the fields required by the agent:

```text
id
author_id
body
created_at
public
```

Comments should sometimes contain information unavailable from the original ticket description.

This makes comment retrieval meaningful.

---

# 17. Zendesk Search Contract

The primary research operation is:

```text
GET /api/v2/search
```

The real Zendesk Search API supports filtering/searching tickets and has pagination constraints, including up to 100 results per page and up to 1,000 results for a query.

The mock only needs to support the subset required by our agents.

Conceptual request:

```text
GET /api/v2/search?query=transfer+pending
```

Response:

```json
{
  "results": [
    {
      "id": 1047,
      "subject": "My transfer is still pending",
      "status": "open",
      "priority": "high"
    }
  ],
  "count": 1,
  "next_page": null
}
```

---

# 18. Zendesk Read API Surface

The Research Agent receives these tools:

```text
search_tickets
get_ticket
get_ticket_comments
```

Underlying API operations:

```text
GET /api/v2/search
GET /api/v2/tickets/{ticket_id}
GET /api/v2/tickets/{ticket_id}/comments
```

A list operation may also exist for development/testing:

```text
GET /api/v2/tickets
```

but it is not required as a primary research tool.

---

# 19. Zendesk Seed API Surface

The seed system may use:

```text
POST /api/v2/tickets
```

and, where convenient, the mock may support:

```text
POST /api/v2/tickets/create_many
```

The real Zendesk API supports bulk ticket creation through `create_many`, accepting up to 100 ticket objects per request.

The seed endpoints are **not exposed as AI-agent tools**.

---

# 20. Zendesk Ticket Content Strategy

The seed generator should create several ticket categories.

### Normal support

Examples:

- password reset
- account settings
- transaction history question
- how-to questions

### Transfer problems

Examples:

- transfer pending
- transfer failed
- recipient not receiving funds
- transaction status confusion

### KYC

Examples:

- document upload problems
- verification pending
- verification confusion

### Wallet funding

Examples:

- funding failure
- funding delay
- fee-related questions

### Bill payments

Examples:

- payment failed
- bill status uncertainty
- payment not reflected

The exact ticket wording should vary.

---

# 21. Zendesk Noise Requirements

Approximately **25–35%** of tickets should be unrelated to the current investigation scenarios.

This prevents keyword search from becoming equivalent to correct reasoning.

The environment should also contain:

- duplicate-like complaints
- vaguely worded complaints
- isolated edge cases
- tickets with insufficient information
- tickets whose status is already solved
- customer interpretations that are technically inaccurate

---

# 22. Jira Data Model

The mock Jira environment should represent engineering issues using a subset of Jira Cloud REST API v3.

Jira's current REST API provides JQL-based issue search, issue retrieval and issue comments. The current enhanced JQL search uses `POST /rest/api/3/search/jql`.

## Issue

Required conceptual fields:

```text
id
key
summary
description
issue_type
status
priority
created_at
updated_at
labels
comments
issuelinks
```

Optional:

```text
assignee
reporter
components
fix_version
environment
```

---

# 23. Jira Issue Types

Use:

```text
Bug
Task
Story
Incident
```

The distribution should include all four.

---

# 24. Jira Statuses

Use:

```text
To Do
In Progress
Blocked
Done
```

Issues should have believable lifecycle states.

---

# 25. Jira Priorities

Use:

```text
Low
Medium
High
Critical
```

Again, priority is engineering context, not direct evidence of user impact.

---

# 26. Jira Comments

The Engineering Agent can retrieve issue comments through:

```text
GET /rest/api/3/issue/{issueIdOrKey}/comment
```

The real Jira API provides issue comment retrieval and creation through this resource.

The mock should support:

```text
id
author
body
created_at
```

Comments should occasionally contain the most important technical context.

---

# 27. Jira Issue Links

Issues may contain relationships such as:

```text
blocks
is blocked by
relates to
duplicates
```

Jira provides an Issue Link resource for creating and retrieving links between issues.

The Engineering Agent should be able to inspect linked issues when useful.

---

# 28. Jira Read API Surface

Agent-facing operations:

```text
search_issues
get_issue
get_issue_comments
get_linked_issues
```

Underlying conceptual API surface:

```text
POST /rest/api/3/search/jql
GET  /rest/api/3/issue/{issueIdOrKey}
GET  /rest/api/3/issue/{issueIdOrKey}/comment
GET  /rest/api/3/issue/{issueIdOrKey}?fields=issuelinks
```

The current Jira documentation indicates that the GET form of JQL issue search is being removed/deprecated, so the mock should model the newer POST-based JQL search rather than building around the legacy GET search endpoint.

---

# 29. Jira Seed API Surface

The seed process may use:

```text
POST /rest/api/3/issue
POST /rest/api/3/issue/{issueIdOrKey}/comment
POST /rest/api/3/issueLink
```

These are setup operations only.

Agents are not given these write capabilities.

---

# 30. Engineering Ticket Categories

The seed dataset should contain:

### Transfer

```text
delayed callback
payment status synchronization
provider timeout
transaction reconciliation
```

### KYC

```text
document upload failure
verification timeout
incorrect verification state
```

### Wallet

```text
funding callback
wallet balance refresh
```

### Bills

```text
bill payment confirmation
provider response timeout
```

### Unrelated

```text
profile settings
UI improvements
onboarding copy
accessibility
```

---

# 31. PostHog Data Contract

PostHog is the real external analytics system.

The application should send fictional events into a dedicated Pocket project.

PostHog positions Product Analytics around event ingestion and querying, and currently offers a free Product Analytics tier with up to 1 million events per month.

The seed dataset is therefore comfortably within the service's stated free-tier event volume.

---

# 32. PostHog Ingestion

The seed generator should use PostHog's event ingestion mechanism or supported SDK/API.

The generator must preserve:

```text
distinct_id
event
timestamp
properties
```

The exact SDK/API client implementation belongs to the integration layer.

The seed process must be idempotent or provide a clean reset strategy.

---

# 33. Analytics Query Interface

The Analytics Agent should have one high-level application tool:

```text
query_analytics
```

The tool should translate the agent's structured request into an appropriate PostHog query.

The model should not be given unrestricted knowledge of authentication or project credentials.

---

# 34. Query Abstraction

The tool should support analytical intents such as:

```text
funnel
trend
breakdown
comparison
segment analysis
event count
conversion rate
```

The implementation may use PostHog's supported query mechanisms internally.

The important product contract is:

> The Analytics Agent can ask a well-defined analytical question and receive a structured result.

It should not need to understand the complete PostHog API.

---

# 35. Analytics Query Result

Conceptual schema:

```python
class AnalyticsResult(BaseModel):
    query_description: str
    metric: str
    value: str
    dimensions: list[str]
    rows: list[dict]
    time_range: str | None
    limitations: list[str]
```

The actual implementation may contain additional metadata.

---

# 36. Analytics Data Relationships

Analytics events must preserve relationships among:

```text
user_id
transaction_id
timestamp
event
```

For example:

```text
transaction_id = txn_003827

transfer_started
transfer_submitted
transfer_processing
transfer_completed
```

This allows the environment to represent a coherent journey.

---

# 37. Cross-System Entity Mapping

The central mapping concept is:

```text
Pocket user
   │
   ├── PostHog distinct_id
   │
   └── Zendesk requester
```

and:

```text
Pocket transaction
   │
   └── PostHog transaction_id
```

Jira does not need to reference every transaction.

Instead, Jira issues should reference:

- product area
- incident period
- affected component
- technical condition

This preserves realistic system differences.

---

# 38. Cross-System Time Relationship

The most important shared relationship is time.

Example:

```text
August 10–15
│
├── Zendesk:
│   transfer complaints increase
│
├── PostHog:
│   transfer-processing completion deteriorates
│
└── Jira:
    callback delay issue created
```

Other scenarios may deliberately break this alignment.

For example:

```text
Zendesk:
complaints increase

PostHog:
no corresponding metric movement

Jira:
no relevant incident
```

That creates ambiguity the agents must resolve.

---

# 39. Ground-Truth Problem Model

The seed generator should be driven by a **scenario specification**, not by independent random generation.

Each scenario should define:

```python
class ScenarioDefinition(BaseModel):
    scenario_id: str
    name: str
    product_area: str
    true_problem: str
    affected_users: list[str]
    expected_evidence: list[str]
    contradictory_evidence: list[str]
    misleading_signals: list[str]
```

This object controls the relationships between the three systems.

---

# 40. Scenario A: Transfer Status Delays

## Ground truth

A meaningful subset of transfers experiences delayed status updates.

## Zendesk

Customers report:

```text
"My transfer has been pending for hours."
"My transfer says processing."
"I was charged but the recipient has not received confirmation."
```

Some customers describe the problem as:

> "transfer failed"

even though the transaction eventually completes.

## PostHog

Create:

- increased processing duration
- reduced observed completion within the normal window
- stable actual failure rate

## Jira

Create:

```text
PAY-117
Delayed transfer callbacks

Status:
In Progress
```

with comments explaining the issue.

## Expected product insight

The strongest explanation is a transfer-status reliability problem rather than a broad increase in genuine transfer failures.

---

# 41. Scenario B: KYC Abandonment

## Ground truth

KYC completion is below desired levels, but technical failures explain only part of the problem.

## Zendesk

Customers mention:

- failed document uploads
- uncertainty about verification requirements
- repeated verification requests

## PostHog

KYC completion drops after document submission.

The drop is concentrated in particular cohorts.

## Jira

Some KYC bugs exist.

## Deliberate ambiguity

The engineering issues do not fully explain the behavioural drop.

## Expected product insight

The system should not conclude that fixing the known bugs will necessarily solve KYC abandonment.

---

# 42. Scenario C: Wallet Funding Abandonment

## Ground truth

Users frequently begin wallet funding but some abandon before completion.

## Zendesk

A smaller number of customers complain about fees or uncertainty.

## PostHog

A meaningful drop occurs between funding initiation and submission.

The issue is concentrated in certain transaction ranges.

## Jira

There is no major active technical incident.

## Expected product insight

The problem requires further investigation into user expectations, pricing and flow friction rather than an automatic engineering escalation.

---

# 43. Scenario D: Bill Payment Failure

## Ground truth

Some bill payments genuinely fail.

## Zendesk

Customers report failed bill payments.

## PostHog

Actual failure rate is elevated for one category of bill payment.

## Jira

An active provider integration issue exists.

## Expected product insight

The three evidence sources converge strongly enough to justify technical remediation.

---

# 44. Deliberate False Leads

At least two scenarios should contain misleading signals.

Examples:

### False lead 1

High Zendesk volume but low population impact.

### False lead 2

An engineering issue exists but is unrelated to the behavioural problem.

### False lead 3

An analytics drop exists but is explained by a change in user mix rather than a product regression.

### False lead 4

Customers describe a successful-but-delayed transaction as a failed transaction.

These should be explicitly encoded into the seed configuration.

---

# 45. Background Noise

The dataset should contain normal activity.

Target proportions:

```text
60–75% normal/background
15–25% clearly relevant problem evidence
5–15% ambiguous/contradictory/misleading evidence
```

These ratios can be tuned during evaluation.

The exact percentages are less important than preserving realistic noise.

---

# 46. Do Not Randomise Ground Truth Away

The seed generator should use deterministic random seeds.

Example:

```text
SEED=20260914
```

The environment should be reproducible.

Running the same seed configuration should produce the same scenario relationships.

Changing the seed may create different wording and user records while preserving the underlying scenario structure.

---

# 47. Synthetic Data Generation Strategy

The data generator should use three layers.

## Layer 1: Base data

Create:

- users
- transactions
- normal events
- normal tickets
- unrelated Jira issues

## Layer 2: Scenario injections

Add:

- problem events
- problem tickets
- relevant Jira issues
- scenario-specific relationships

## Layer 3: Noise injections

Add:

- ambiguous wording
- irrelevant records
- contradictory evidence
- misleading signals

This is preferable to generating each system independently.

---

# 48. Seed Execution Flow

```text
Scenario configuration
        ↓
Seed generator
        ↓
Generate shared entities
        ↓
Generate PostHog events
        ↓
Generate Zendesk tickets/comments
        ↓
Generate Jira issues/comments/links
        ↓
Validate cross-system relationships
        ↓
Produce seed report
```

---

# 49. Seed Validation

The seed process must validate:

### Referential integrity

Every referenced user/transaction must exist where required.

### Temporal integrity

Events and tickets should occur within coherent time ranges.

### Scenario integrity

Every scenario must contain the intended supporting and contradictory evidence.

### Noise integrity

Background data should remain sufficiently independent from the scenario.

### Queryability

The seeded data must actually be discoverable through the agent-facing APIs.

---

# 50. Seed Report

Every seed execution should produce a report such as:

```text
Pocket Seed Report

Users: 2,000
Transfers: 5,000
PostHog events: 14,827
Zendesk tickets: 200
Jira issues: 50

Scenarios:
TRANSFER_STATUS: OK
KYC_ABANDONMENT: OK
WALLET_FUNDING: OK
BILL_PAYMENT: OK

Cross-system validation: PASS
```

This gives us a quick sanity check before running agents.

---

# 51. Data Reset

The development environment must support a clean reset.

Mock systems should be resettable.

PostHog should have a documented strategy for:

- using a disposable project
- using a test namespace
- or otherwise isolating seed data

The application must not depend on manually deleting records one at a time.

---

# 52. API Error Contract

All adapters should normalise external errors into an internal structure.

Conceptual schema:

```python
class APIError(BaseModel):
    source: Literal["zendesk", "posthog", "jira"]
    status_code: int | None
    error_type: str
    message: str
    retryable: bool
```

Agents should receive controlled error information.

---

# 53. Pagination

The mock APIs should support pagination where the real API does.

For MVP, the implementation may keep pagination simple, but the interface should not assume:

> one API request always returns the entire dataset.

This is particularly relevant to Zendesk and Jira search.

---

# 54. API Authentication Boundaries

### Mock Zendesk

No external credentials required.

### Mock Jira

No external credentials required.

### PostHog

Credentials remain application configuration.

The seed process uses the PostHog credentials.

The runtime integration uses the same project configuration.

Secrets must never be embedded into seed records or passed to LLMs.

---

# 55. Agent Tool Boundaries

The final agent-facing tool surface is:

## Research Agent

```text
search_tickets
get_ticket
get_ticket_comments
```

## Analytics Agent

```text
query_analytics
```

## Engineering Agent

```text
search_issues
get_issue
get_issue_comments
get_linked_issues
```

## PM Agent

```text
No external data tools
```

## Critic Agent

```text
No external data tools in MVP
```

These boundaries must be enforced by the application.

---

# 56. Domain Tool vs Raw API

The agents should call:

```text
search_tickets(...)
```

rather than:

```text
GET /api/v2/search?query=...
```

Likewise:

```text
search_issues(...)
```

rather than exposing raw HTTP.

The domain-tool layer allows us to:

- validate input
- normalise responses
- handle authentication
- handle errors
- change the backend without changing the agent
- log tool usage consistently

---

# 57. Tool Input Schemas

Example:

```python
class SearchTicketsInput(BaseModel):
    query: str
    page: int = 1
    limit: int = 20
```

```python
class GetTicketInput(BaseModel):
    ticket_id: int
```

```python
class SearchIssuesInput(BaseModel):
    jql: str
    max_results: int = 20
```

```python
class GetIssueInput(BaseModel):
    issue_id_or_key: str
```

```python
class AnalyticsQueryInput(BaseModel):
    question: str
    time_range: str | None = None
    segment: dict[str, str] | None = None
```

The exact schemas may be adjusted during implementation after testing.

---

# 58. Tool Output Schemas

The tool layer should return structured application objects.

Example:

```python
class TicketSummary(BaseModel):
    id: int
    subject: str
    status: str
    priority: str
    created_at: str
    tags: list[str]
```

Rather than passing raw vendor-specific payloads directly into the model.

This keeps the agent contract stable.

---

# 59. API Versioning

The mock APIs should explicitly identify their supported contract version.

Example:

```text
Mock Zendesk API: v2-compatible subset
Mock Jira API: v3-compatible subset
PostHog: current supported API integration
```

The implementation should document any intentional deviations from the real API.

---

# 60. Real API Alignment

The project should maintain a distinction between:

### API-compatible

The mock follows the external service's relevant request/response conventions.

and:

### API-identical

The mock reproduces the entire external service.

The goal is **not** to implement Zendesk or Jira in full.

The goal is to implement the subset required by our product while retaining realistic boundaries.

---

# 61. Data Privacy

The entire data environment is fictional.

Do not seed:

- real customer names
- real customer email addresses
- real financial account numbers
- real card details
- real transaction identifiers
- real personal information

Use synthetic identifiers throughout.

---

# 62. Sensitive Data Rules

Synthetic transaction amounts are acceptable for simulation.

However:

```text
NO real card numbers
NO bank account numbers
NO authentication credentials
NO API keys
NO real customer information
```

The seed system should enforce this through generated schemas.

---

# 63. Dataset Size Targets

Initial target:

| Dataset | Target |
|---|---:|
| Users | ~2,000 |
| Transfer attempts | ~5,000 |
| PostHog events | ~10,000–20,000 |
| Zendesk tickets | ~200 |
| Jira issues | ~50 |
| Core scenarios | 4 |
| Ambiguous/false-lead scenarios | ≥ 2 |

These are starting values rather than hard technical limits.

The final dataset should be determined partly by evaluation performance.

---

# 64. Data Evolution

The first seed version should be considered:

```text
seed_v1
```

Changes to:

- event definitions
- scenario ground truth
- ticket relationships
- Jira relationships
- important metric distributions

should be versioned.

This allows evaluation results to remain attributable to a specific dataset.

---

# 65. Dataset Manifest

The seed repository should contain a machine-readable manifest.

Conceptually:

```yaml
dataset_version: "1.0"
seed: 20260914

population:
  users: 2000
  transfers: 5000

sources:
  zendesk:
    tickets: 200
  jira:
    issues: 50
  posthog:
    events_target: 15000

scenarios:
  - transfer_status
  - kyc_abandonment
  - wallet_funding
  - bill_payment
```

---

# 66. Data Quality Gates

Before agents can use a dataset, the seed process must pass:

```text
Schema validation
       ↓
Referential validation
       ↓
Scenario validation
       ↓
API retrieval validation
       ↓
Query validation
       ↓
Dataset approved
```

A seed process that generates data but fails to make it retrievable is not considered successful.

---

# 67. Evaluation Dataset Separation

The seed data and evaluation ground truth should not be identical files.

The runtime system should only know:

```text
Pocket data
```

The evaluation system separately knows:

```text
ground truth
expected evidence
expected traps
expected conclusion
```

This prevents the application from accidentally leaking the answer into the agent context.

---

# 68. Ground-Truth Example

Conceptual evaluation record:

```yaml
scenario_id: transfer_status_01

question: "Why are users abandoning transfers?"

expected_findings:
  - customer_reports_pending_transfers
  - completion_drop_after_submission
  - delayed_callback_engineering_issue

contradictions:
  - actual_failure_rate_stable

expected_conclusion:
  "Transfer status delays are a stronger explanation than a broad increase in genuine transfer failures."

known_trap:
  "Customers frequently use 'failed' to describe delayed transactions."
```

This belongs to evaluation, not to runtime data.

---

# 69. API Contract Tests

For each mock API, create contract tests.

### Zendesk

Verify:

```text
create ticket
search ticket
retrieve ticket
retrieve comments
pagination
not found
invalid search
```

### Jira

Verify:

```text
create issue
search JQL
retrieve issue
retrieve comments
retrieve links
not found
invalid JQL
```

### PostHog

Verify:

```text
event ingestion
query
segmentation
time filtering
result parsing
authentication error
```

---

# 70. Integration Tests

Tests should verify that:

```text
Research Agent
    ↓
Tool
    ↓
Mock Zendesk
```

and:

```text
Analytics Agent
    ↓
Tool
    ↓
PostHog
```

and:

```text
Engineering Agent
    ↓
Tool
    ↓
Mock Jira
```

all function independently.

---

# 71. Data & API Definition of Done

This specification is implemented when:

1. Pocket's core entities are defined.
2. The event taxonomy is defined and validated.
3. Synthetic users and transactions can be generated.
4. Mock Zendesk can store and retrieve tickets/comments.
5. Mock Jira can store and retrieve issues/comments/links.
6. PostHog contains the seeded analytics data.
7. Agent-facing tools expose only the required operations.
8. Tool responses are structured.
9. Cross-system relationships are validated.
10. Scenario relationships are reproducible.
11. Background noise and contradictory evidence are present.
12. The seed process can be reset and rerun.
13. Contract tests pass for the mock APIs.
14. Integration tests pass for all source adapters.
15. The runtime environment does not expose ground-truth scenario answers to agents.

---

# 72. Final Data Architecture

The intended relationship is:

```text
                         POCKET DATA
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
      CUSTOMER VOICE      USER BEHAVIOUR   ENGINEERING CONTEXT
           │                  │                  │
           ▼                  ▼                  ▼
       MOCK ZENDESK         POSTHOG           MOCK JIRA
           │                  │                  │
           └──────────────┬───┴───┬──────────────┘
                          │       │
                          ▼       ▼
                    Agent Tools
                          │
                          ▼
                  Specialist Agents
                          │
                          ▼
                    Evidence State
```

The key architectural rule is:

> **The three systems should contain evidence that can be connected, but they should never be so perfectly aligned that the answer can be obtained by simple keyword matching.**

The environment must force the AI product team to investigate, compare, challenge and reason.