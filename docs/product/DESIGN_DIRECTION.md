# Pocket AI Product Discovery Team
## Design Direction & Design System Foundations

**Document Version:** 1.1  
**Status:** Approved Specification (Step 1 Approved)  
**Related Documents:**
- [UX Product Specification](UX_PRODUCT_SPEC.md)
- [Investigation Workspace Specification](INVESTIGATION_WORKSPACE_SPEC.md)
- [ADR-0014: Frontend Product Experience Architecture](../decisions/ADR-0014-frontend-product-experience.md)

---

# 1. Product Positioning & Visual Philosophy

Pocket is an **AI product investigation workspace that helps product teams turn fragmented customer, behavioral, and engineering evidence into a structured, evidence-backed product assessment.**

Its visual language must reflect this mission: evoking **analytical clarity, editorial discipline, intellectual rigor, and calm credibility**.

### 1.1 Core Aesthetic Attributes
- **Credible & Calm:** Generous whitespace, disciplined typography, and a structured grid that prevents visual panic during high-urgency investigations.
- **Editorial & Document-Centric:** Feels like reading an elite briefing document or financial report rather than chatting with a bot.
- **Evidence-Oriented:** Citations, data points, and confidence boundaries are treated as first-class visual elements.

### 1.2 Anti-Card-Wall & Anti-Chat Principles
- **NO Generic AI-Chat Styling:** No user/assistant speech bubbles, floating bot heads, or typewriter streaming text on completed recommendations.
- **NO "Card Wall" Dashboard Traps:** Avoid packing every paragraph and metric into stacked rounded boxes. Distinguish between continuous editorial reading flow (problem statement, recommendation), analytical panels (structured epistemic deck), full-width callout banners (contradictions, limitations), and bounded cards (used only for atomic items like evidence drawer cards).
- **NO Dark-Glowing Neon Aesthetic:** No purple/cyan glowing neon gradients, cyberpunk grids, or artificial "hacker" darkness.
- **NO Decorative AI Gimmicks:** No pulsating sparkles (`✨`), animated AI mascots, or floating particle effects.
- **NO Bubbly Oversized Radii:** No 24px+ cartoonish pill containers. Radius scale is capped at 4px–8px.

---

# 2. Reading Hierarchy & Visual Prominence

Layouts and typography must directly enforce the formal reading hierarchy:
- **15 seconds (Awareness):** Large, crisp query title (`h1`), live status pill, and ticking duration timer.
- **30 seconds (Executive Takeaway):** High-contrast Action Type badge (`INVESTIGATE FURTHER`, `REMEDIATE`), bold Primary Recommendation text, and explicit Confidence meter (`High`, `Medium`, `Low`).
- **60 seconds (Analytical Evaluation):** Structured Epistemic Findings panel with color-coded left borders, and warm callout banners for Contradictions and Limitations.
- **3 minutes (Evidentiary Audit):** Interactive citation badges (`[EV-001]`) triggering the docked Evidence Ledger drawer for deep record verification.

---

# 3. Theme Strategy: Light-First / Neutral-First Foundation

### 3.1 The Evaluation
| Consideration | Dark-First Glowing UI | Light-First Neutral Foundation | Decision Impact |
|---|---|---|---|
| **Reading Ergonomics** | Causes eye strain when reading 2,000+ words of dense analytical text during daylight office hours. | Maximizes reading comprehension, text contrast, and scannability for long-form briefs. | Strongly favors Light-First. |
| **Professional Perception** | Looks like a developer CLI tool, gaming interface, or crypto platform; undermines corporate credibility. | Looks like Linear Docs, Stripe Press, or The Economist; commands analytical credibility. | Strongly favors Light-First. |
| **Data & Table Density** | Difficult to render subtle borders, table grids, and multi-source color badges without visual vibration. | Renders clean 1px borders, subtle slate backgrounds, and crisp multi-source badge tints effortlessly. | Strongly favors Light-First. |
| **Print & PDF Alignment** | Requires complete inverted rendering stylesheets for white-paper PDF export. | Maps 1:1 with executive PDF briefs and printable documents. | Strongly favors Light-First. |

### 3.2 The Theme Decision: **Light-First / Neutral-First with Optional Dark Mode**
- **Primary / Default Mode:** **Light Neutral Mode** (Clean paper white `#ffffff`, warm slate canvas `#f8fafc`, crisp borders `#e2e8f0`, deep slate text `#0f172a`).
- **Secondary Mode:** **Dark Analytical Mode** (Deep slate `#090d16` rather than pitch black, with muted borders `#1e293b` and soft white text `#f1f5f9`), toggleable via system preference or user account settings for low-light evening investigations.

---

# 4. Design System Foundations & Tokens

```text
================================================================================
DESIGN TOKEN FOUNDATION
================================================================================
Base Font: Inter (UI/Body) | Monospace: JetBrains Mono (Ledger IDs & Data)
Base Spatial Unit: 4px (4, 8, 12, 16, 20, 24, 32, 40, 48, 64px)
Border Radius Scale: 4px (inputs/badges), 6px (buttons/cards), 8px (panels/drawers)
Border Style: 1px solid, low-contrast neutral (#e2e8f0)
================================================================================
```

### 4.1 Color Palette & Semantic Tokens

#### A. Neutrals & Canvas Tokens
- **Canvas Base:** `#f8fafc` (Slate 50)
- **Surface / Card Background:** `#ffffff` (Pure White)
- **Surface Elevated / Drawer:** `#ffffff` with subtle elevation shadow (`0 4px 6px -1px rgb(0 0 0 / 0.05)`)
- **Border Subtle:** `#e2e8f0` (Slate 200)
- **Border Strong:** `#cbd5e1` (Slate 300)
- **Text Primary:** `#0f172a` (Slate 900)
- **Text Secondary:** `#475569` (Slate 600)
- **Text Muted:** `#94a3b8` (Slate 400)

#### B. Primary Brand & Interactive Tokens
- **Brand Primary:** `#2563eb` (Royal Sapphire Blue)
- **Brand Primary Hover:** `#1d4ed8`
- **Brand Primary Light / Focus Ring:** `#dbeafe` (Blue 100) / `#3b82f6`

#### C. Source-Specific Evidence Tokens
To ensure instantaneous recognition of data provenance across the application, each external system is assigned an immutable color identity:
- **Customer Support (Zendesk):** Text/Border: `#059669` (Emerald 600) | Tint: `#ecfdf5` (Emerald 50)
- **Product Telemetry (PostHog):** Text/Border: `#7c3aed` (Violet 600) | Tint: `#f5f3ff` (Violet 50)
- **Engineering Issues (Jira):** Text/Border: `#0284c7` (Sky 600) | Tint: `#f0f9ff` (Sky 50)

#### D. Epistemic Separation Tokens
- **Observed Facts:** `#059669` (Emerald) — Signals verified, empirical ground truth.
- **Logical Inferences:** `#2563eb` (Sapphire) — Signals reasoned deduction.
- **Working Hypotheses:** `#d97706` (Amber) — Signals unproven, provisional claims.
- **Contradictions / Gaps:** `#dc2626` (Rose / Crimson) — Signals evidentiary tension or missing data.

---

### 4.2 Typography Hierarchy

| Level / Token | Font Family | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|---|
| **Display / Title** | `Inter` | 24px (1.5rem) | 700 (Bold) | 32px | -0.02em | Investigation query heading |
| **Heading 1 (H1)** | `Inter` | 18px (1.125rem) | 600 (Semibold) | 26px | -0.01em | Major section headers (Recommendation, Facts) |
| **Heading 2 (H2)** | `Inter` | 15px (0.9375rem) | 600 (Semibold) | 22px | 0 | Sub-section titles, panel headers |
| **Body Primary** | `Inter` | 14px (0.875rem) | 400 (Regular) | 22px | 0 | Executive problem statement, findings text |
| **Body Medium** | `Inter` | 14px (0.875rem) | 500 (Medium) | 22px | 0 | Bold lead-ins, bullet summaries |
| **Caption / Meta** | `Inter` | 12px (0.75rem) | 500 (Medium) | 16px | +0.01em | Timestamps, agent labels, status subtext |
| **Code / Data** | `JetBrains Mono` | 12px (0.75rem) | 500 (Medium) | 18px | 0 | Evidence Ledger IDs (`[EV-001]`), JQL, queries |

---

### 4.3 Component System Specifications

#### A. Buttons
- **Primary:** High-contrast solid brand color (`#0f172a` deep slate or `#2563eb` blue), white text, 6px radius.
- **Secondary:** White background with 1px border (`#cbd5e1`), slate text (`#334155`), 6px radius.
- **Ghost:** Transparent background, hover tint (`#f1f5f9`), 6px radius.

#### B. Evidence Citation Badges (Inline)
- Interactive citation pills embedded directly inside text (e.g. `[EV-003]`).
- Monospace font (`JetBrains Mono`, 11px), 4px radius, 1px solid border matching source color.
- Hover effect: Underlines reference and shows immediate tooltip preview of support quote.
- Click effect: Scrolls and highlights card in the Evidence Drawer.

#### C. Evidence Cards (Drawer Items)
- White card surface, 1px solid border (`#e2e8f0`), 6px radius, 12px internal padding.
- Displays Ledger ID (`EV-003`), Source Badge, Reference Tag (`TICKET-1042`), Finding text, and quote excerpt in a light gray tinted code box (`#f8fafc`).
- Focus state: 2px solid `#2563eb` ring with smooth fade.

#### D. Status Pills & Progress Stepper
- Clean pill container with 4px dot and text.
- Running: Blue pulsing ring (`#2563eb`).
- Completed: Solid green dot (`#10b981`).
- Revising: Solid amber dot (`#f59e0b`).
- Failed: Solid red dot (`#ef4444`).
