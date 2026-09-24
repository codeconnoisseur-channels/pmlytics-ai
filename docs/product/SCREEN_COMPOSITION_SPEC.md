# Pocket AI Product Discovery Team
## Screen Composition & Layout Specification

**Document Version:** 1.0  
**Status:** Approved for Design (Step 2 Complete)  
**Related Documents:**
- [Visual UX Specification](VISUAL_UX_SPEC.md)
- [Investigation Workspace Specification](INVESTIGATION_WORKSPACE_SPEC.md)
- [Component Design Specification](COMPONENT_DESIGN_SPEC.md)
- [Responsive Design Specification](RESPONSIVE_DESIGN_SPEC.md)

---

# 1. Primary Screen Compositions

This document specifies the exact structural layout, spatial proportions, and component relationships for all 13 core screens and operational states in Pocket.

---

## Screen 1: Landing Page (`/`)

```text
+---------------------------------------------------------------------------------------------------------+
| [NAVBAR]  (P) Pocket AI Product Discovery Team           [How It Works]  [Evidence]  [Sign In]  [Try Demo] |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
| [HERO SECTION] (Max-Width: 960px, Centered)                                                             |
|                                                                                                         |
|         Turn fragmented customer, analytics, and engineering signals                                    |
|         into a structured, defensible product investigation.                                            |
|                                                                                                         |
|         Pocket coordinates specialist AI agents that gather evidence across Zendesk, PostHog,           |
|         and Jira, challenge hypotheses with an adversarial critic, and present a verified brief.        |
|                                                                                                         |
|                   [ Start Live Investigation ]      [ View Sample Decision Brief ]                      |
|                                                                                                         |
+---------------------------------------------------------------------------------------------------------+
| [INTERACTIVE CANONICAL PREVIEW TEASER]                                                                  |
| +-----------------------------------------------------------------------------------------------------+ |
| | Query: "Why did checkout conversion drop in release 2.4?"                  [Completed in 107s] [PASS] | |
| | Problem Statement: Checkout drop in v2.4 is unverified by telemetry; support reports 0 issues.       | |
| | Recommendation: [INVESTIGATE FURTHER] Correct funnel telemetry before prioritizing Jira fix.         | |
| | Cited Evidence: [EV-001 PostHog] Funnel unsegmented  |  [EV-003 Zendesk] 0 tickets  | [EV-007 Jira] | |
| +-----------------------------------------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
| [MULTI-SOURCE WORKFLOW VISUALIZATION]                                                                   |
|   [1. Customer Voice]            [2. Product Telemetry]           [3. Engineering Issues]               |
|   Zendesk support complaints     PostHog funnel conversions       Jira bug tracking & PR links          |
|                 \                         |                         /                                   |
|                  ----->  [4. PM Inductive Synthesis]  <------------                                     |
|                                           |                                                             |
|                          [5. Adversarial Critic Challenge]                                              |
|                                           |                                                             |
|                          [6. Defensible Product Assessment]                                             |
+---------------------------------------------------------------------------------------------------------+
| [FOOTER]  Pocket AI Product Discovery Team • Open Source Architecture • Clean-Context Invariant         |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 2: Interactive Demo Sandbox (`/demo`)

```text
+---------------------------------------------------------------------------------------------------------+
| [TOP BANNER] Sandbox Demo Mode: You are exploring live scenarios. [Sign Up to Save to Workspace]      |
+---------------------------------------------------------------------------------------------------------+
| [LAUNCHPAD COMPOSER]                                                                                    |
|   Select a canonical scenario or type your own question:                                                |
|                                                                                                         |
|   [ Surge in Failed Transfers ]   [ Checkout Conversion Drop v2.4 ]   [ Mobile EUR Settlement Delays ]   |
|                                                                                                         |
|   +---------------------------------------------------------------------------------------------------+ |
|   | Why did checkout conversion drop in release 2.4?                                                  | |
|   +---------------------------------------------------------------------------------------------------+ |
|   [ Run Sandbox Investigation ]                                                  13 / 2,000 characters  |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 3 & 4: Sign In (`/auth/signin`) & Sign Up (`/auth/signup`)

```text
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
|                                         [ (P) Pocket AI ]                                               |
|                                                                                                         |
|                               +---------------------------------------+                                 |
|                               | Sign In to Your Workspace             |                                 |
|                               |                                       |                                 |
|                               | Work Email:                           |                                 |
|                               | [ user@company.com                  ] |                                 |
|                               |                                       |                                 |
|                               | Password:                             |                                 |
|                               | [ ********************              ] |                                 |
|                               |                                       |                                 |
|                               | [ Sign In ]                           |                                 |
|                               |                                       |                                 |
|                               | Don't have an account? [Create One]   |                                 |
|                               +---------------------------------------+                                 |
|                                                                                                         |
+---------------------------------------------------------------------------------------------------------+
```

---

## Screen 5: Launchpad (`/app`) — Authenticated Home

```text
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR]    | [LAUNCHPAD HEADER]                                                                       |
|              | Welcome back, Product Team                                                               |
| (P) Pocket   |                                                                                          |
|              | [FOCUSED QUERY COMPOSER]                                                                 |
| [+ New Inv]  | What product question do you need to investigate?                                        |
|              | +--------------------------------------------------------------------------------------+ |
| Launchpad    | | e.g. Why are customers reporting extended delays in EUR transfers this week?         | |
| History      | |                                                                                      | |
| Saved        | +--------------------------------------------------------------------------------------+ |
|              | [ Investigate ]                                                    0 / 2,000 characters |
|              |                                                                                          |
| Recent:      | Suggested Inquiries:                                                                     |
| • Surge in   | [ Transfer failure spike ]   [ Checkout drop v2.4 ]   [ Onboarding KYC drop-off ]         |
| • Checkout   |                                                                                          |
|              | [RECENT INVESTIGATIONS FEED]                                                             |
|              | Title                                     Status       Time       Confidence   Actions   |
| [Settings]   | Surge in failed transfers this week       Completed    107.4s     Low          [View]    |
| [User / Out] | Checkout conversion drop in release 2.4   Completed    121.4s     Low          [View]    |
|              | Mobile EUR transfer delays                Completed    98.5s      Low          [View]    |
|              |                                                                                          |
| [● Health]   | Integrations Ready: [● Zendesk] [● PostHog] [● Jira]                                     |
+--------------+------------------------------------------------------------------------------------------+
```

---

## Screen 6: Running Investigation Workspace (`/app/investigations/:id`)

```text
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR]    | Title: Why did checkout conversion drop in release 2.4?                                  |
| (Collapsed   | Status: [● GATHERING EVIDENCE (Specialists)]       Elapsed: 00:38       [Cancel Inv]    |
|  64px rail)  +------------------------------------------------------------------------------------------+
|              | [LIVE ORCHESTRATION PIPELINE MONITOR]                                                    |
|              | [1. Planning ✓] ----> [2. Specialists (Active)] ----> [3. Synthesis] ----> [4. Critic]   |
|              +------------------------------------------------------------------------------------------+
|              | [HONEST STATUS CONSOLE (No Fake Typing)]                                                 |
|              |                                                                                          |
|              | Stage: Gathering evidence across product systems                                         |
|              | Current Agent: `research_agent`, `analytics_agent`, `engineering_agent`                  |
|              | Detail: Querying Mock Zendesk, PostHog Analytics, and MockServer Jira concurrently.     |
|              |                                                                                          |
|              | Notice: Multi-source parallel execution typically takes ~100–120 seconds.                |
|              | All findings will be validated under strict epistemic separation upon arrival.           |
|              |                                                                                          |
|              | [Evidence Arriving: 13 records retrieved]                                                |
+--------------+------------------------------------------------------------------------------------------+
```

---

## Screen 7 & 8: Completed Investigation Workspace & Evidence Drawer

```text
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR]    | Title: Why did checkout conversion drop in release 2.4?                                  |
|              | Status: [✓ COMPLETED]    Duration: 121.4s    LLM Calls: 11    [Share]  [PDF]  [★ Save]     |
| (Collapsed   +------------------------------------------------------------------+-----------------------+
|  64px rail)  | MAIN EDITORIAL READING CANVAS (Max Width: 840px)                 | EVIDENCE DRAWER       |
|              |                                                                  | (Width: 420px Docked) |
|              | 1. EXECUTIVE PROBLEM STATEMENT (Editorial Typography)            |                       |
|              | The claimed checkout conversion drop in release 2.4 is not       | Source Filters:       |
|              | empirically verified by retrieved analytics or support signals.  | [All: 13] [Zendesk: 5]|
|              | Telemetry returned unsegmented event counts [EV-001], support    | [PostHog: 4] [Jira: 4]|
|              | reports 0 tickets [EV-003], and Jira issues remain unconfirmed   |                       |
|              | leads [EV-007].                                                  | Search: [Filter...  ] |
|              | Affected Users: All users attempting checkout on v2.4 (unverif.) |                       |
|              |                                                                  | Evidence Card:        |
|              | 2. ACTIONABLE RECOMMENDATION (Structured Action Panel)           | +-------------------+ |
|              | Action Type: [ INVESTIGATE FURTHER ]    Confidence: [ LOW ]       | | [EV-001] PostHog  | |
|              | Confidence Rationale: Core conversion metric could not be        | | Ref: funnel:check | |
|              | measured from unsegmented telemetry; Jira hits are unconfirmed.  | | "Query returned   | |
|              | Recommendation: Obtain and validate segmented checkout funnel    | |  aggregate count  | |
|              | telemetry for pre- and post-release 2.4 before prioritizing any  | |  without version" | |
|              | technical remediation.                                           | | Conf: Medium      | |
|              | Success Metrics: Conversion rate segmented by app version; 0 P0s.| +-------------------+ |
|              |                                                                  |                       |
|              | 3. EPISTEMIC FINDINGS PANEL (Structured Analytical Rows)         | Evidence Card:        |
|              | [FACTS - Emerald Accent]                                         | +-------------------+ |
|              | • PostHog queries returned no usable version segmentation [EV-001| | [EV-003] Zendesk  | |
|              | • Zendesk searches returned 0 customer tickets for checkout [EV-0| | Ref: SEARCH-001    | |
|              | • Jira returned 4 issue keys matching checkout terms [EV-007].   | | "0 tickets found" | |
|              | [INFERENCES - Blue Accent]                                       | | Conf: High        | |
|              | • Absence of support complaints does not rule out silent drops.  | +-------------------+ |
|              | [HYPOTHESES - Amber Accent]                                      |                       |
|              | • A regression in the payment processing callback may exist.     | [Clicking citation    |
|              |                                                                  |  highlights card here]|
|              | 4. CONTRADICTIONS & TENSIONS (Callout Banner)                    |                       |
|              | Tension: Jira shows checkout issues while Zendesk shows 0 tickets|                       |
|              |                                                                  |                       |
|              | 5. DISCLOSED LIMITATIONS (Warning Banner)                        |                       |
|              | Missing version-segmented telemetry prevents causal validation.  |                       |
|              |                                                                  |                       |
|              | 6. ADVERSARIAL CRITIC REVIEW (Collapsible Accordion)             |                       |
|              | [v] PASS (1 revision completed) • 6 issues successfully addressed|                       |
+--------------+------------------------------------------------------------------+-----------------------+
```

---

## Screen 9: Investigation History (`/app/history`)

```text
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR]    | [PAGE HEADER]                                                                            |
|              | Investigation History                                                                    |
|              | Search & Filter:                                                                         |
|              | [ Search investigations...               ]   [ Domain: All v ]   [ Status: Completed v ] |
|              +------------------------------------------------------------------------------------------+
|              | [HYBRID ANALYTICAL TABLE / LIST]                                                         |
|              | Query Title                            Status      Duration   Confidence   Date   Action |
|              | ---------------------------------------------------------------------------------------  |
|              | Why did checkout conversion drop v2.4? Completed   121.4s     Low          Today  [Open] |
|              | Surge in failed transfers this week    Completed   98.5s      Low          Today  [Open] |
|              | Mobile EUR transfer settlement delays  Completed   107.4s     Low          Yest.  [Open] |
|              |                                                                                          |
|              | Showing 3 of 3 investigations in current process session                                 |
+--------------+------------------------------------------------------------------------------------------+
```

---

## Screen 10: Saved Investigations (`/app/saved`)

```text
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR]    | [PAGE HEADER]                                                                            |
|              | Starred & Saved Investigations                                                           |
|              | Curated high-impact decision briefs bookmarked for roadmap reference.                    |
|              +------------------------------------------------------------------------------------------+
|              | [SAVED LIST VIEW]                                                                        |
|              | ★ Why did checkout conversion drop in release 2.4?                       [Remove Star]   |
|              |   Recommendation: Investigate Further • Confidence: Low • Completed 121.4s               |
|              |   Saved Notes: "Pending analytics instrumentation fix in sprint 44."                     |
|              |                                                                                          |
|              | ★ Surge in failed transfers this week                                     [Remove Star]   |
|              |   Recommendation: Investigate Further • Confidence: Low • Completed 98.5s                |
+--------------+------------------------------------------------------------------------------------------+
```

---

## Screen 11: Workspace Settings (`/app/settings`)

```text
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR]    | [PAGE HEADER]                                                                            |
|              | Workspace & Integration Settings                                                         |
|              +------------------------------------------------------------------------------------------+
|              | [INTEGRATION READINESS CARDS]                                                            |
|              | +--------------------------------------------------------------------------------------+ |
|              | | Zendesk Support Mock       [● Connected]   URL: http://localhost:8080                | |
|              | | PostHog Product Telemetry  [● Connected]   Project ID: 610450                        | |
|              | | Jira Issue Tracker Mock    [● Connected]   URL: http://localhost:1080                | |
|              | | OpenRouter Gateway         [● Connected]   Model: openai/gpt-5.4                     | |
|              | +--------------------------------------------------------------------------------------+ |
|              |                                                                                          |
|              | [INVESTIGATION PROFILE SELECTION]                                                        |
|              | (•) Standard Profile (Recommended: ~100s, 10–11 calls, cost <$0.10)                      |
|              | ( ) Deep Profile (Exhaustive multi-turn investigation)                                   |
+--------------+------------------------------------------------------------------------------------------+
```

---

## Screen 12: User Account (`/app/account`)

```text
+---------------------------------------------------------------------------------------------------------+
| [SIDEBAR]    | [PAGE HEADER]                                                                            |
|              | Account Profile & Preferences                                                            |
|              +------------------------------------------------------------------------------------------+
|              | Name: Product Manager                                                                    |
|              | Email: pm@pocket.internal                                                                |
|              | Role: Workspace Owner                                                                    |
|              |                                                                                          |
|              | Display Preferences:                                                                     |
|              | Theme: [ (•) Light Neutral (Default)   ( ) Dark Analytical   ( ) System Default ]         |
|              | Motion: [ (•) Standard Transitions     ( ) Reduced Motion ]                              |
+--------------+------------------------------------------------------------------------------------------+
```

---

## Screen 13: Shared Investigation Brief (`/share/:token`)

```text
+---------------------------------------------------------------------------------------------------------+
| [PUBLIC HEADER] (P) Pocket AI • Executive Decision Brief                        [Download PDF] [Sign Up] |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
| Investigation Query: "Why did checkout conversion drop in release 2.4?"                                 |
| Date: September 17, 2026 • Status: Completed (Adversarial Critic Passed) • Duration: 121.4s             |
|                                                                                                         |
| EXECUTIVE PROBLEM STATEMENT:                                                                            |
| The claimed checkout conversion drop in release 2.4 is not empirically verified by retrieved telemetry.  |
| PostHog returned unsegmented data [EV-001], Zendesk reports 0 tickets [EV-003], and Jira keys remain    |
| unconfirmed leads [EV-007].                                                                             |
|                                                                                                         |
| PRIMARY RECOMMENDATION:                                                                                 |
| [ ACTION: INVESTIGATE FURTHER ]    CONFIDENCE: [ LOW ]                                                  |
| Validate segmented checkout funnel metrics before prioritizing technical fixes.                         |
|                                                                                                         |
| OBSERVED FACTS:                                                                                         |
| • PostHog queries lacked version segmentation [EV-001].                                                 |
| • Zendesk returned 0 matching customer tickets [EV-003].                                                |
| • Jira returned 4 checkout-related search keys [EV-007].                                                |
|                                                                                                         |
| EVIDENCE APPENDIX:                                                                                      |
| [EV-001] PostHog funnel:checkout — "Query returned aggregate event counts without version"               |
| [EV-003] Zendesk SEARCH-001 — "0 customer tickets matching checkout drop"                               |
| [EV-007] Jira PAY-892 — "Open issue matching checkout callback timeout"                                 |
|                                                                                                         |
| Generated by Pocket AI Product Discovery Team • Clean Context Invariant Enforced                        |
+---------------------------------------------------------------------------------------------------------+
```
