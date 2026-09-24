# Demo Dataset v2 Validation Report

## Purpose

Dataset v2 provides a coherent, reproducible synthetic company environment for
the four PMLytics AI demonstration investigations. It is designed to exercise
the same product workflow that will later use production Zendesk, Jira, and
PostHog connections.

## Source coverage

| Source | Validation result |
| --- | --- |
| Customer support | 51 customer-language tickets: 12 for each scenario and 3 ordinary support contacts. |
| Product analytics | 15,223 deterministic PostHog events, all tagged `dataset_version=2.0`. |
| Engineering delivery context | MockServer `7.6.0` running with 17 explicit Jira expectations. |

## Scenario alignment

The utility-bill scenario now uses a month-end settlement window across all
three sources. Its analytics population covers 28–31 August 2026, and the
active engineering record is **PAY-134: Electricity token purchases timing out
during month-end settlement**.

## Dataset isolation

Every runtime analytics query is constrained to `dataset_version=2.0`. This
means the v2 population can coexist with prior synthetic events without
combining them in an investigation result. Seed runs must not remove or alter
historical data without an explicitly approved data-retention action.

## Verified utility-bill signal

Using the production analytics tool and the 28–31 August window, the v2
dataset returned:

- 247 bill-payment starts and submissions
- 209 completions
- 38 failures

## Release gate

The source services and seed data are ready for a single controlled live
investigation. Before the four-scenario demo is signed off, inspect that one
result for source grounding, recommendation quality, and latency, then use the
same dataset for the remaining scenario checks.
