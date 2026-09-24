# Pocket AI Product Discovery Team
## Visual UX & Design System Specification

**Document Version:** 1.0  
**Status:** Approved for Design (Step 2 Complete)  
**Related Documents:**
- [UX Product Specification](UX_PRODUCT_SPEC.md)
- [Investigation Workspace Specification](INVESTIGATION_WORKSPACE_SPEC.md)
- [Component Design Specification](COMPONENT_DESIGN_SPEC.md)
- [Screen Composition Specification](SCREEN_COMPOSITION_SPEC.md)
- [ADR-0015: Visual UX Implementation Strategy](../decisions/ADR-0015-visual-ux-implementation-strategy.md)

---

# 1. Visual Design Philosophy: Credible, Calm & Analytical

Pocket is an **AI product investigation workspace** designed for product managers and technical leaders who need to make defensible prioritization and remediation decisions.

### 1.1 Core Aesthetic Attributes
1. **Editorial Authority:** The workspace feels like reading an elite intelligence brief (Stripe Press, Linear Docs, The Economist) rather than chatting with a bot.
2. **Analytical Density Without Clutter:** Generous whitespace, precise typography, and disciplined visual containers allow complex multi-source evidence to be absorbed quickly without cognitive overload.
3. **Anti-AI-Slop Discipline:** No floating bot avatars, no glowing neon gradients, no simulated typewriter text, and no decorative animations. Every pixel serves an analytical purpose.

---

# 2. The Formal Visual Hierarchy (Time-to-Insight)

The UI explicitly guides the reader's eye across four distinct temporal reading tiers:

```text
==================================================================================================
TIME-TO-INSIGHT HIERARCHY
==================================================================================================
15 SECONDS  | [AWARENESS]
            | High-contrast Query Title (20px bold) + Live Status Pill + Elapsed Duration Timer.
            | The user instantly knows what question is running, its state, and how long it took.
--------------------------------------------------------------------------------------------------
30 SECONDS  | [EXECUTIVE TAKEAWAY]
            | Synthesized Problem Statement (Editorial text) + Primary Recommendation Block.
            | High-contrast Action Type Badge ("INVESTIGATE FURTHER") + Confidence Rating ("Low").
            | The user understands Pocket's core conclusion and immediate action without scrolling.
--------------------------------------------------------------------------------------------------
60 SECONDS  | [ANALYTICAL EVALUATION]
            | Epistemic Findings Panel: Verified Facts (Emerald) vs Inferences (Blue) vs Hypotheses (Amber).
            | Full-width Callout Banners: Contradictions between systems & Disclosed Limitations.
            | The user understands the primary evidence, tensions, and why confidence is bounded.
--------------------------------------------------------------------------------------------------
3 MINUTES   | [EVIDENTIARY AUDIT]
            | Interactive Citation Badges ("[EV-001]") deep-linking into the docked Evidence Drawer.
            | Verbatim support quotes, source references (TICKET-1042, PAY-892), and Critic Review log.
            | The user audits the exact underlying records and verifies adversarial vetting.
==================================================================================================
```

---

# 3. Typography & Type Scale

The typographic system is built on **Inter** for clean UI readability, **JetBrains Mono** for attributable data identifiers, and optional **Newsreader / Editorial Serif** for executive problem statement callouts.

### 3.1 Typographic Hierarchy Table

| Token Name | Font Family | Size (px / rem) | Weight | Line Height | Letter Spacing | Usage Context |
|---|---|---|---|---|---|---|
| `type-display` | `Inter` | 24px / 1.5rem | 700 (Bold) | 32px (1.33) | -0.02em | Investigation Query Heading |
| `type-h1` | `Inter` | 18px / 1.125rem | 600 (Semibold) | 26px (1.44) | -0.015em | Major Canvas Sections (Recommendation, Findings) |
| `type-h2` | `Inter` | 15px / 0.9375rem | 600 (Semibold) | 22px (1.46) | -0.01em | Sub-headers, Drawer Header, Modal Titles |
| `type-body-lead` | `Inter` | 15px / 0.9375rem | 400 (Regular) | 24px (1.60) | -0.005em | Executive Problem Statement, Primary Recommendation |
| `type-body` | `Inter` | 14px / 0.875rem | 400 (Regular) | 22px (1.57) | 0 | Findings body text, limitations, descriptions |
| `type-body-medium`| `Inter` | 14px / 0.875rem | 500 (Medium) | 22px (1.57) | 0 | Bullet bold lead-ins, table cell labels |
| `type-caption` | `Inter` | 12px / 0.75rem | 500 (Medium) | 16px (1.33) | +0.01em | Status pills, metadata tags, elapsed timer |
| `type-code` | `JetBrains Mono`| 11px / 0.6875rem| 500 (Medium) | 16px (1.45) | 0 | Evidence Ledger IDs (`[EV-001]`), JQL, queries |
| `type-quote` | `Inter` / Mono | 12px / 0.75rem | 400 (Regular) | 18px (1.50) | 0 | Verbatim support excerpt in evidence cards |

---

# 4. Spacing Scale & Spatial Grid

Pocket utilizes a 4px base spatial scale. Consistent mathematical rhythm prevents layout fragmentation.

### 4.1 Spacing Scale Tokens
- `space-1`: 4px — Badge internal padding, icon gaps.
- `space-2`: 8px — Button horizontal padding (compact), input inline spacing.
- `space-3`: 12px — Card internal padding, list item vertical gaps.
- `space-4`: 16px — Standard component padding, panel gutters.
- `space-5`: 20px — Section separation in compact viewports.
- `space-6`: 24px — Major section vertical margins, grid gutters.
- `space-8`: 32px — Canvas vertical rhythm between major reading blocks.
- `space-12`: 48px — Page top/bottom outer margins.
- `space-16`: 64px — Hero section vertical breathing room.

### 4.2 Content Widths & Analytical Grid
- **Widescreen Desktop ($\ge 1600\text{px}$):** Full three-column analytical workspace:
  - Sidebar: `240px` expanded (or `64px` collapsed, user-controlled).
  - Main Reading Region: Flexible container with a **maximum reading width of `840px`** (guarantees optimal line length of 65–75 characters for reading comprehension).
  - Docked Evidence Drawer: `~420px` width on the right with independent scrolling.
- **Standard Desktop ($1280\text{px} - 1599\text{px}$):** Sidebar (240px or 64px) + flexible main region (max 840px reading width) + compact evidence panel where space permits.
- **Compact Desktop / Tablet ($< 1280\text{px}$):** Evidence Drawer becomes a slide-over overlay (400px).
- **Tablet Portrait ($< 1024\text{px}$):** Sidebar collapses off-canvas behind a hamburger menu.
- **Mobile ($< 768\text{px}$):** Dedicated mobile investigation triage layout.

> [!IMPORTANT]
> **Reading Width vs. Fixed Column**:
> The `840px` value is a **maximum reading width** for typography and analytical comprehension, **not** a rigid fixed column. The container expands flexibly across the workspace while constraining line lengths to 65–75 characters.

> [!NOTE]
> **Sidebar Control**:
> The sidebar defaults to **Expanded (240px)** on desktop. The user maintains full manual control over collapse/expand via button or `[` / `]` shortcuts. Starting or completing an investigation must **never** automatically alter the application chrome.

---

# 5. Color Palette & Semantic Assignment

Pocket operates as a **Light-First / Neutral-First** application with an optional system-aware **Dark Analytical Mode**.

```text
==================================================================================================
COLOR TOKENS & ROLES
==================================================================================================
CANVAS & SURFACES:
  Canvas Base:       #f8fafc (Slate 50)     | Dark: #090d16 (Deep Slate)
  Surface Base:      #ffffff (Pure White)   | Dark: #111827 (Gray 900)
  Surface Tinted:    #f1f5f9 (Slate 100)    | Dark: #1f2937 (Gray 800)
  Border Subtle:     #e2e8f0 (Slate 200)    | Dark: #1e293b (Slate 800)
  Border Strong:     #cbd5e1 (Slate 300)    | Dark: #334155 (Slate 700)

TEXT TOKENS:
  Text Primary:      #0f172a (Slate 900)    | Dark: #f8fafc (Slate 50)
  Text Secondary:    #475569 (Slate 600)    | Dark: #94a3b8 (Slate 400)
  Text Muted:        #94a3b8 (Slate 400)    | Dark: #64748b (Slate 500)

BRAND & ACCENTS:
  Brand Primary:     #2563eb (Sapphire 600) | Focus Ring: #3b82f6 (Blue 500)
  Brand Primary Tint:#dbeafe (Blue 100)     | Dark Focus: #60a5fa

SOURCE IDENTITIES (DATA PROVENANCE BADGES ONLY):
  Zendesk (Support): Text: #059669 (Emerald 600) | Tint: #ecfdf5 (Emerald 50) | Border: #a7f3d0
  PostHog (Analytics):Text: #7c3aed (Violet 600)  | Tint: #f5f3ff (Violet 50)  | Border: #ddd6fe
  Jira (Engineering): Text: #0284c7 (Sky 600)     | Tint: #f0f9ff (Sky 50)     | Border: #bae6fd

EPISTEMIC CLASSIFICATION (NOT DEPENDENT ON COLOR ALONE):
  Observed Facts:    Section label "Observed Facts" + subtle neutral/slate left rule + 100% citations [EV-xxx]
  Logical Inferences:Section label "Logical Inferences" + subtle sapphire left rule
  Working Hypotheses:Section label "Working Hypotheses" + subtle amber left rule
  Contradictions:    Full-width warm callout banner with warning icon
  Limitations:       Full-width alert banner with disclosure icon

  *Accessibility Rule:* Color is NEVER the sole signal distinguishing epistemic types.
  Section labels, typography, and structural placement are the primary differentiators.

CANONICAL EVIDENCE IDENTIFIER RULE:
  All evidence citations strictly maintain the canonical format: [EV-001], [EV-002], [EV-003].
  Do NOT use provider prefixes ([ZD-01], [PH-01]). Source identity is communicated
  via adjacent SourceBadges and metadata: e.g., "[EV-003] · Zendesk · TICKET-1042".
==================================================================================================
```

---

# 6. Borders, Geometry & Elevation

### 6.1 Radius Scale
- `radius-sm`: **4px** — Input fields, citation badges, tag pills.
- `radius-md`: **6px** — Buttons, individual evidence cards, callout alerts.
- `radius-lg`: **8px** — Main analytical panels, drawer containers, modal dialogs.
- *Strict Rule:* **No 24px+ rounded pills** for large layout blocks. Bubbly containers degrade analytical credibility.

### 6.2 Elevation & Shadows
Pocket avoids heavy blurry drop shadows, relying primarily on crisp 1px borders for visual definition:
- `elevation-flat`: No shadow; `1px solid #e2e8f0`. Used for canvas panels and inline callouts.
- `elevation-sm`: `0 1px 2px 0 rgb(0 0 0 / 0.04)`, `1px solid #cbd5e1`. Used for active buttons and hovered cards.
- `elevation-drawer`: `-4px 0 16px 0 rgb(0 0 0 / 0.08)`. Used for the docked slide-out Evidence Drawer.

---

# 7. Long-Form Text Readability & Editorial Behavior

Because real investigations generate extensive analytical output, strict document readability rules are enforced:
- **Maximum Line Length:** Strictly bounded to `65–75 characters` (`max-w-[840px]`). Text never spans the full width of ultrawide displays.
- **Paragraph Spacing:** `margin-bottom: 16px` between paragraphs; line height `1.57` to prevent visual crowding.
- **Bulleted Metric Density:** Factual observations and limitations use bold lead-ins (e.g., **Event trend:** 0.04% drop-off...) followed by concise findings and citation badges.
- **Expandable Section Thresholds:** Lists exceeding 6 items (e.g. extensive limitation disclosures) render the first 4 items with a clean `Show 3 more limitations...` toggle.

---

# 8. Motion Rules & Accessibility

Motion in Pocket communicates state and spatial orientation; it never acts as entertainment:

### 8.1 Permitted Motion
- **Evidence Drawer Slide:** `200ms cubic-bezier(0.16, 1, 0.3, 1)` slide from right edge.
- **Citation Attention Glow:** `1.5s` subtle amber/blue outline fade when clicking an inline citation badge.
- **Status Milestone Transition:** `150ms ease-out` color transition when stepper advances from `Planning` to `Specialists`.

### 8.2 Prohibited Motion (Anti-AI-Slop Invariants)
- **NO Fake AI Typewriter Streaming:** Text renders instantly when a stage finishes.
- **NO Pulsating "Thinking" Rings or Particle Animations:** Replaced with a clean, static or subtle spinning 14px indicator.
- **NO Decorative Shimmer Sweeps across cards.**

### 8.3 Reduced-Motion Enforcement
When `prefers-reduced-motion: reduce` is active:
- Drawer transitions become instant opacity toggles (`0ms`).
- Attention glows become static solid border rings.
- Spinners become static textual labels (`"In progress..."`).
