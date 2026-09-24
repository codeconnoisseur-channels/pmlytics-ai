# Frontend Design System Specification: Pocket AI Product Discovery System

**Document Version:** 1.0.0  
**Phase:** 14 (Next.js Frontend Foundation)  
**Status:** Draft / Needs Review  
**Date:** 2026-09-17  
**Author:** AI Product Discovery Engineering Team  

---

## 1. Design Direction & Core Philosophy

The Pocket AI Product Discovery frontend adheres to a strict design aesthetic validated in Phase 13:

* **Light-First & Neutral-First:** Engineered for clarity, deep analytical focus, daylight reading, and rigorous product review. The default canvas is `#f8fafc` with crisp `#ffffff` cards and surfaces.
* **Editorial & Restrained:** Resembles an authoritative intelligence briefing or premium financial publication (e.g., *The Economist*, *Stratechery*).
* **Anti-"Card-Wall" Discipline:** The workspace avoids generic dashboard card grids. Findings flow naturally with structured left-gutter epistemic borders, high-contrast headings, and continuous narrative typography.
* **Anti-AI-Slop:** 
  * Strictly no neon purples, magenta gradients, or rainbow accents.
  * Strictly no decorative chat bubbles, conversational back-and-forth threads, or agent avatars.
  * Strictly no synthetic progress spinners, fake percentage tickers, or simulated typewriter text.
  * Canonical evidence IDs (`[EV-xxx]`) are first-class, verifiable audit links.

### 1.1 Public Marketing Surface

The public root route uses a landing-specific expression of the same restrained product
system, approved in ADR-0021:

- Warm neutral canvas `#f4f5f2`, near-black ink `#171915`, and panel white `#fbfcf9`.
- Chartreuse `#c8f46b` is a bounded marketing accent for primary outcomes and calls to
  action. It is not a replacement for source provenance or epistemic-status colours.
- The real decision brief is the primary visual. Stock AI imagery, fabricated customer
  proof, vanity metrics, and non-functional product surfaces are prohibited.
- Bento compositions may vary card proportions, but section hierarchy, reading order, and
  mobile stacking must remain explicit.
- Static marketing sections remain React Server Components. Client state is limited to
  interactions that require it, such as accessible mobile navigation.
- The approved visual language extends to authentication, the investigation launchpad,
  the workspace, and the evidence drawer under ADR-0022. It does not alter application
  behavior or report information architecture.

---

## 2. Design Tokens Reference

These tokens are extracted directly from the frozen reference stylesheet (`app/ui/styles.css`) and constitute the production TailwindCSS theme extension.

### 2.1 Color Palette

#### Base & Surfaces
| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| `bg-canvas` | `#f4f5f2` | Global warm neutral application background |
| `bg-surface` | `#fbfcf9` | Content containers, sheets, and modal panels |
| `bg-subtle` | `#eef0eb` | Table headers, secondary toolbars, and hover rails |
| `bg-hover` | `#e3e6de` | Interactive item hover background |

#### Borders
| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| `border-light` | `#eceee9` | Subtle dividers within white cards |
| `border-default` | `#dfe2db` | Standard container borders and divider rules |
| `border-strong` | `#c9cdc4` | Emphasized containers and active input borders |
| `border-focus` | `#171915` | Accessible focus ring color (`outline: 2px solid`) |

#### Typography Colors
| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| `text-primary` | `#171915` | Headers, primary copy, and problem statements |
| `text-secondary` | `#62675f` | Subtext, cohort details, and secondary explanations |
| `text-muted` | `#73786f` | Timestamps, metadata keys, and footnote indicators |
| `text-disabled` | `#a0a59c` | Disabled triggers and inactive pagination |

#### Brand Primary
| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| `brand-primary` | `#171915` | Primary action buttons and active navigation markers |
| `brand-primary-hover`| `#000000` | Hover state for primary buttons |
| `brand-primary-subtle`| `#eff8df` | Selected row background and active metadata tint |
| `brand-border` | `#c8f46b` | Branded selection and accent border tint |

The live investigation progress bar remains `#2563eb`. This is an operational state
signal, not the general brand colour.

#### Source Provenance Indicators
Each external evidence source has a dedicated, non-overlapping semantic color pairing verified against the frozen prototype (`app/ui/styles.css`):
| Source | Text | Background | Border | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Zendesk** (Customer Support) | `#047857` (emerald-700) | `#ecfdf5` (emerald-50) | `#a7f3d0` (emerald-200) | Support tickets, customer quotes, CSAT notes |
| **PostHog** (Product Analytics) | `#6d28d9` (violet-700) | `#f5f3ff` (violet-50) | `#ddd6fe` (violet-200) | Funnel metrics, conversion telemetry, user drop-offs |
| **Jira** (Engineering Systems) | `#1d4ed8` (blue-700) | `#eff6ff` (blue-50) | `#bfdbfe` (blue-200) | Bugs, releases, backlog issues, pull requests |

> [!IMPORTANT]
> **Strict Semantic Invariant: Source Provenance vs. Epistemic Status**  
> Source provenance colors (Zendesk Emerald, PostHog Violet, Jira Blue) represent **data origin** (which external system emitted the record).  
> Epistemic classifications (Facts Emerald, Inferences Blue, Hypotheses Amber) represent **truth and analytical certainty**.  
> **Source colors must never be reused as substitutes for epistemic classifications.** A PostHog record is not an "inference", and a Zendesk ticket is not automatically an "unverified claim". The two semantic axes remain strictly independent in both the UI and the data model.

#### Epistemic Classifications
Epistemic statements are differentiated primarily by section structure and left-gutter indicator borders:
| Classification | Border (Gutter) | Background Tint | Badge Text | Badge Background |
| :--- | :--- | :--- | :--- | :--- |
| **Facts** | `#10b981` (emerald-500) | `#f0fdf4` | `#065f46` | `#d1fae5` |
| **Inferences** | `#3b82f6` (blue-500) | `#eff6ff` | `#1e40af` | `#dbeafe` |
| **Hypotheses** | `#f59e0b` (amber-500) | `#fffbeb` | `#92400e` | `#fef3c7` |

#### Status & Review Colors
| Status | Text | Background | Border | Context |
| :--- | :--- | :--- | :--- | :--- |
| **PASS** | `#166534` | `#dcfce7` | `#bbf7d0` | Critic PASS badge, healthy dependency |
| **REVISE / WARN** | `#9a3412` | `#ffedd5` | `#fed7aa` | Critic REVISE badge, tension alert |
| **DANGER / FAIL** | `#991b1b` | `#fee2e2` | `#fecaca` | Pipeline failure, high-risk flag |

---

### 2.2 Typography Scale

The type system uses **Inter** for all editorial prose, UI labels, and data tables, paired with **JetBrains Mono** for evidence references (`[EV-001]`), timestamps, and code identifiers.

| Scale Token | Font Size | Line Height | Weight | Tracking | Typical Component Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `text-display` | `2.25rem` (36px) | `1.2` | 700 (Bold) | `-0.025em` | Marketing Hero Headline |
| `text-h1` | `1.75rem` (28px) | `1.25`| 700 (Bold) | `-0.02em` | Section Titles, Investigation Question |
| `text-h2` | `1.35rem` (21.6px)| `1.35`| 600 (Semibold)| `-0.015em` | Primary Recommendation, Workspace Subheadings |
| `text-h3` | `1.125rem` (18px) | `1.4` | 600 (Semibold)| `-0.01em` | Epistemic Category Titles (`Facts`, `Inferences`) |
| `text-body-lg` | `1.05rem` (16.8px)| `1.6` | 400 (Regular) | `normal` | Executive Problem Statement, Recommendation Body |
| `text-body` | `0.9375rem` (15px)| `1.6` | 400 (Regular) | `normal` | Standard Workspace Reading Copy |
| `text-body-sm` | `0.875rem` (14px) | `1.5` | 400 (Regular) | `normal` | Evidence Excerpts, Drawer Metadata |
| `text-caption` | `0.75rem` (12px) | `1.4` | 500 (Medium) | `+0.01em` | Badges, Timestamps, Source Tags |
| `text-mono` | `0.8125rem` (13px)| `1.4` | 600 (Semibold)| `normal` | Citation Pills (`[EV-001]`), Trace IDs |

---

### 2.3 Layout Dimensions & Viewport Breakpoints

| Dimension Token | Value | Applied Rule |
| :--- | :--- | :--- |
| `--sidebar-width-expanded` | `240px` | Fixed desktop sidebar width when open |
| `--sidebar-width-collapsed`| `64px` | Fixed desktop sidebar width when collapsed to icon rail |
| `--topbar-height` | `56px` | Sticky workspace application header |
| `--reading-canvas-max-width`| `840px` | Constrained reading width (max 65–75 characters/line) |
| `--drawer-width-desktop` | `420px` | Docked right-hand column ($\ge 1600\text{px}$) |
| `--drawer-width-overlay` | `440px` | Slide-over drawer on standard desktop ($1280\text{px}–1599\text{px}$) |

#### Viewport Breakpoint Logic
```text
 1600px+        Three-column workspace (Expanded/Collapsed Sidebar + 840px Canvas + Docked Evidence Drawer)
 1280px–1599px  Two-column workspace (Sidebar + 840px Canvas + Slide-over Evidence Drawer on click)
 1024px–1279px  Compact workspace (Collapsed Sidebar + Full Canvas + Slide-over Drawer)
 768px–1023px   Tablet layout (Off-canvas navigation + Full Canvas + Slide-over Drawer)
 < 768px        Mobile layout (Hamburger Header + 100% Canvas + Full-width 100vw Evidence Sheet)
```

---

## 3. Component Primitive Specifications

### 3.1 Buttons (`Button.tsx`)
* **Variants:**
  * `primary`: Solid `#2563eb`, white text, subtle hover dark `#1d4ed8`, active transform scale(0.99).
  * `secondary`: Background `#ffffff`, border `1px solid #e2e8f0`, text `#0f172a`, hover `#f8fafc`.
  * `ghost`: Transparent background, hover `#f1f5f9`, text `#475569`.
  * `subtle`: Background `#eff6ff`, border `1px solid #bfdbfe`, text `#1d4ed8`.
* **Sizes:**
  * `sm`: Height 32px, text 13px, padding 0 10px.
  * `md`: Height 38px, text 14px, padding 0 14px.
  * `lg`: Height 44px, text 15px, padding 0 18px.
* **Accessibility:** Minimum touch target 44px on mobile viewports. Visible 2px outline on `:focus-visible`.

### 3.2 Badges & Source Badges (`Badge.tsx`, `SourceBadge.tsx`)
* **Source Badge:**
  * Renders source logo/icon (Zendesk, PostHog, Jira) + source title + identifier.
  * Format: `[Icon] Zendesk · TICKET-1042` or `[Icon] PostHog · query_payment_funnel`.
  * Height 22px, border-radius 4px, font-family `JetBrains Mono` for ID, font-size 11px.
* **Confidence Badge:**
  * `HIGH`: Emerald text (`#065f46`), background `#d1fae5`, border `#a7f3d0`.
  * `MEDIUM`: Amber text (`#92400e`), background `#fef3c7`, border `#fde68a`.
  * `LOW`: Slate text (`#475569`), background `#f1f5f9`, border `#e2e8f0`.

### 3.3 Citation Pill (`CitationPill.tsx`)
* **Appearance:**
  * Inline badge styled as `[EV-001]`.
  * Font: `JetBrains Mono`, weight 600, size 12px.
  * Background: `#eff6ff`, border: `1px solid #bfdbfe`, text: `#1d4ed8`.
  * Hover state: Background `#dbeafe`, border `#93c5fd`, text `#1e40af`.
* **Interaction:**
  * Click triggers focus transfer and smooth-scroll to the target record in the Evidence Ledger.
  * Renders `role="button"` and `tabIndex={0}` with keyboard Enter/Space event handlers.

### 3.4 Recommendation Panel (`RecommendationPanel.tsx`)
* **Placement:** Elevated to the top of the reading canvas, directly below the investigation title and header metadata.
* **Styling:**
  * Background `#ffffff`, border `1px solid #bfdbfe` with an emphasized top border accent `3px solid #2563eb`.
  * Padding: 24px (desktop), 18px (mobile).
  * Border radius: 10px.
  * Shadow: Subtle elevated shadow (`0 4px 6px -1px rgba(0, 0, 0, 0.05)`).
* **Header Elements:**
  * "PRIMARY RECOMMENDATION" label in uppercase 11px tracking +0.05em text muted.
  * Recommendation action type badge (e.g., `Immediate Bugfix`, `Product Clarification`).
  * Confidence badge (`HIGH CONFIDENCE`).
* **Content:**
  * Heading: Concise imperative action statement (e.g., *"Instrument immediate payment-status webhooks and display a transitional 'Processing Settlement' state in-app"*).
  * Supporting analytical synthesis text with embedded `CitationPill` components.
  * Expected outcome / success metrics bullet points.

### 3.5 Epistemic Findings Flow (`EpistemicFlow.tsx`)
* **Philosophy:** Replaces three stacked cards with a unified, continuous editorial flow.
* **Structure:**
  * Section title: "Verified Evidence & Findings".
  * Subsections for **Factual Observations**, **Inferences**, and **Hypotheses**.
* **Visual Treatment:**
  * Left gutter border `3px solid`:
    * Facts: `#10b981` (Emerald)
    * Inferences: `#3b82f6` (Blue)
    * Hypotheses: `#f59e0b` (Amber)
  * Background: Transparent / neutral `#ffffff`.
  * Item structure:
    * Statement in crisp `text-body` (slate-900).
    * Inline or trailing `CitationPill` group linking to ledger items.
    * Concise annotation explaining the epistemic boundary.

### 3.6 Tensions & Limitations Banners (`TensionsBanner.tsx`, `LimitationsBanner.tsx`)
* **Contradictions / Tensions Banner:**
  * Background `#fff7ed` (amber-50), border `1px solid #fed7aa` (amber-200), left border `4px solid #f97316` (orange-500).
  * Header with alert triangle icon: "Identified Contradictions & Trade-offs".
  * Explicitly highlights contradictory signals (e.g., customer complaints claiming total failure vs. PostHog telemetry showing 99.2% eventual backend settlement).
* **Limitations Banner:**
  * Background `#f8fafc` (slate-50), border `1px solid #e2e8f0` (slate-200).
  * Header with info icon: "Investigation Limitations & Data Gaps".
  * Discloses missing data, telemetry latency, or unverified edge cases.

### 3.7 Critic Review Accordion (`CriticAccordion.tsx`)
* **Default State:** Collapsed summary banner showing verdict (`PASS`), revisions completed (`1 revision`), and adversarial status.
* **Expanded State:** Reveals full critique trail, challenges raised by the Critic Agent, and how the PM Agent revised the recommendation to address unsupported claims or causal overreach.
* **Styling:** Headless Radix UI Accordion with subtle border and zero distracting animations.

### 3.8 Evidence Ledger Sheet (`EvidenceLedgerSheet.tsx`)
* **Container:**
  * Desktop $\ge 1600\text{px}$: Docked column within grid layout.
  * Standard desktop & mobile: Radix Dialog/Sheet with slide-over animation (`translateX(0)`).
* **Record Row (`EvidenceRow.tsx`):**
  * Top bar: Canonical ID (`EV-001`) + `SourceBadge` + Confidence tag.
  * Finding: Bold summary sentence.
  * Support: Quoted excerpt or raw metric value enclosed in subtle mono block (`bg-slate-50`, `border-l-2 border-slate-300`).
  * Retrieved timestamp: Date and time formatted in UTC.
  * An explicit `Review N ...` control expands the bounded underlying audit records. Customer support shows conversations, engineering shows work items, and product analytics shows aggregate metric details rather than user-level events.
  * Supporting records remain subordinate to the source summary and use compact stacked rows so the drawer does not become a replacement operational dashboard.
* **Search and privacy:**
  * Search spans source summaries and the visible fields of supporting records, automatically revealing a matching child record.
  * Customer/user identifiers, transaction identifiers, internal failure codes, raw query syntax, transport details, and prompt content are excluded from the rendered audit layer.
* **Active Highlight Animation:**
  * When deep-linked from a citation, target row triggers CSS class `.is-active-target`:
    `animation: target-flash 1.2s ease-out;`
    `@keyframes target-flash { 0% { background: #dcfce7; border-color: #10b981; } 100% { background: #ffffff; border-color: #e2e8f0; } }`

---

## 4. Mobile Responsiveness Standards

On mobile viewports ($< 768\text{px}$, audited at $390\text{px} \times 844\text{px}$):
1. **Header Chrome:** Breadcrumbs collapse to compact format (`Pocket / ... / inv_p12a_1`); action buttons collapse into icon triggers with accessible tooltips.
2. **Reading Order:**
   1. Header & Title.
   2. Recommendation Panel (immediate viewport visibility).
   3. Executive Finding & Affected Cohort.
   4. Epistemic Findings Flow.
   5. Tensions & Limitations.
   6. Critic Review Accordion.
3. **Evidence Sheet:** Fixed bottom bar or floating pill displays `"Evidence Ledger (18 records)"`. Tapping opens a full-screen sheet (`width: 100vw; height: 100vh`) with a prominent close header and large touch dismissal.
4. **Typography Adjustments:**
   * Hero headline downscales from `2.25rem` to `1.65rem`.
   * Body copy stays at `15px` for strict readability.
   * Tables switch to stacked attribute cards.

---

## 5. Anti-AI-Slop Review Checklist

Every new component must pass this verification checklist before merging:
- [x] Does it use `#f8fafc` / `#ffffff` light-first backgrounds without dark-mode glow hacks?
- [x] Are font families strictly `Inter` and `JetBrains Mono`?
- [x] Is the recommendation positioned above epistemic details?
- [x] Are Facts, Inferences, and Hypotheses rendered as an integrated flow rather than 3 bulky cards?
- [x] Do all citations render as `[EV-xxx]` pills and deep-link to the ledger?
- [x] Are there zero conversational chat bubbles, agent avatars, or fake streaming tickers?
- [x] Does every interactive trigger provide keyboard navigation and visible focus rings?
