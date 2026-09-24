# Pocket AI Product Discovery Team
## Responsive Design & Breakpoint Specification

**Document Version:** 1.0  
**Status:** Approved for Design (Step 2 Complete)  
**Related Documents:**
- [Visual UX Specification](VISUAL_UX_SPEC.md)
- [Investigation Workspace Specification](INVESTIGATION_WORKSPACE_SPEC.md)
- [Component Design Specification](COMPONENT_DESIGN_SPEC.md)
- [Screen Composition Specification](SCREEN_COMPOSITION_SPEC.md)

---

# 1. Breakpoint System & Grid Overview

Pocket supports a disciplined multi-tier responsive layout. Rather than merely stacking elements vertically or forcing fixed columns, the interface dynamically accommodates viewport space while capping reading line lengths for optimal legibility.

| Breakpoint Tier | Viewport Width | Layout Shell Model | Evidence Drawer Behavior |
|---|---|---|---|
| **Widescreen Desktop** | $\ge 1600\text{px}$ | **Full Three-Column Workspace:** Sidebar (240px expanded or 64px collapsed) + flexible main canvas (with maximum reading width of 840px) + docked Evidence Drawer (~420px). | Permanently docked on right with independent scrolling. |
| **Standard Desktop** | $1280\text{px} - 1599\text{px}$ | **Sidebar + Main + Compact Evidence:** Sidebar (240px or 64px) + flexible main reading region + compact evidence panel where space permits. | Docked or semi-docked; user can collapse to maximize canvas. |
| **Compact Desktop / Tablet Landscape** | $1024\text{px} - 1279\text{px}$ | **Sidebar + Focused Reading Canvas:** Sidebar (240px or 64px) + flexible reading canvas. Evidence Drawer becomes slide-over overlay. | Overlay / slide-over modal (400px) with backdrop. |
| **Tablet Portrait** | $768\text{px} - 1023\text{px}$ | **Off-Canvas Sidebar + Full Canvas:** Sidebar becomes off-canvas drawer. Top header displays navigation toggle and evidence button. | Overlay / slide-over modal (400px) with backdrop. |
| **Mobile** | $< 768\text{px}$ | **Executive Triage View:** Off-canvas hamburger menu + stacked executive brief + segmented tabs for epistemic findings. | 90vh Bottom Sheet modal with touch drag handle. |

> [!IMPORTANT]
> **Maximum Reading Width Invariant**:
> The `840px` value is a **maximum reading width** for text line lengths (65–75 characters), **not** a rigid fixed-width layout column. On viewports $\ge 1600\text{px}$, the main canvas region expands flexibly to center the 840px reading block between the sidebar and the 420px docked evidence drawer.

> [!NOTE]
> **Sidebar State & User Control**:
> The sidebar defaults to **Expanded (240px)** on desktop. Users control the collapsed/expanded state manually via the collapse button or `[` / `]` keyboard shortcuts. User preference is persisted locally. Starting or completing an investigation must **never** automatically collapse or alter the application chrome.

---

# 2. Screen-by-Screen Breakpoint Adaptations

## 2.1 Investigation Workspace (`/app/investigations/:id`)

```text
==================================================================================================
WIDESCREEN DESKTOP (>= 1600px):
[Sidebar 240/64px] | [Flexible Main Region: Reading Canvas (Max 840px)] | [Docked Evidence Drawer (420px)]
                   | - Query Title & Status Toolbar                     | - Source Tabs (Support, Telemetry, Eng)
                   | - Executive Problem Statement (Editorial text)     | - Search Filter Input
                   | - Primary Recommendation & Confidence              | - Attributable Evidence Cards List
                   | - Epistemic Findings (Structured Document Rows)    | 
                   | - Contradictions & Limitations Banners             | (Canvas and Drawer scroll independently)
--------------------------------------------------------------------------------------------------
STANDARD DESKTOP (1280px - 1599px):
[Sidebar 240/64px] | [Flexible Main Region (Max 840px)]                 | [Compact Evidence Panel (~360px)]
                   | - Reading canvas remains centered and uncompressed | - User can toggle drawer closed
--------------------------------------------------------------------------------------------------
COMPACT DESKTOP / TABLET (1024px - 1279px):
[Sidebar 240/64px] | [Full Main Reading Canvas]
                   | - Header displays prominent [Evidence Drawer (13)] button
                   | [Clicking citation or button slides Evidence Drawer as 400px Overlay from right]
--------------------------------------------------------------------------------------------------
TABLET PORTRAIT (768px - 1023px):
[Hamburger Toggle] | [Full-Width Reading Canvas]
                   | - Sidebar slides in as off-canvas drawer when toggled
                   | - Evidence Drawer opens as slide-over overlay with backdrop
--------------------------------------------------------------------------------------------------
MOBILE (< 768px):
[App Top Bar]      | [Executive Triage View]
                   | - Sticky Header: Truncated Query + Status Pill + Duration
                   | - Action Recommendation Banner (Pinned at top: Action Type & Confidence)
                   | - Problem Statement (Compact typography: 14px)
                   | - Epistemic Findings: Segmented Tabs [Facts (7)] [Inferences (4)] [Hypotheses (3)]
                   | - Tapping citation "[EV-001]" opens full-screen Evidence Sheet from bottom
==================================================================================================
```

---

## 2.2 Launchpad (`/app`)

- **Desktop ($\ge 1200\text{px}$):**
  - Expanded 240px sidebar on left.
  - Centered query composer (max width 680px) with sample chips in a clean horizontal flex row.
  - Recent investigations table below composer displaying Query, Status, Duration, and Date columns.
- **Tablet ($768\text{px} - 1199\text{px}$):**
  - Collapsed 64px sidebar.
  - Composer expands to fill available canvas width. Sample chips wrap cleanly into 2 rows.
  - Recent investigations table hides "Duration" column to preserve label readability.
- **Mobile ($< 768\text{px}$):**
  - Sidebar hidden behind top-left hamburger menu.
  - Composer full width (100vw minus 32px padding).
  - Recent investigations switch from a table to compact touch-friendly cards showing Query, Status badge, and Date.

---

## 2.3 Evidence Ledger Drawer & Citation Deep-Linking

- **Desktop ($\ge 1200\text{px}$):**
  - Drawer is permanently docked on the right (420px width) or toggleable via an icon button.
  - Main canvas margins adjust smoothly to prevent content compression.
  - Citation clicks trigger smooth scroll within the docked container.
- **Tablet ($768\text{px} - 1199\text{px}$):**
  - Drawer functions as a slide-over modal (400px width) with an opaque backdrop (`rgba(15, 23, 42, 0.4)`).
  - Pressing `Escape` or tapping the backdrop dismisses the drawer, returning focus to the triggering citation.
- **Mobile ($< 768\text{px}$):**
  - Drawer transforms into a **Bottom Sheet Modal** (occupying 90% viewport height with touch drag handle).
  - Source filter chips render as a horizontally scrollable strip.
  - Support quotes render with slightly larger line-height (18px) for effortless mobile reading.

---

## 2.4 Investigation History (`/app/history`)

- **Desktop ($\ge 1200\text{px}$):**
  - Full hybrid analytical table displaying: Query Title, Status Badge, Duration (s), Number of LLM Calls, Confidence Level, Created Date, and Action Buttons (`[View]`, `[Re-run]`).
- **Tablet ($768\text{px} - 1199\text{px}$):**
  - Table compresses: hides LLM call count and duration; keeps Query Title, Status, Confidence, and View button.
- **Mobile ($< 768\text{px}$):**
  - Transforms into an interactive card feed. Each card displays:
    - Top line: Date and Status pill.
    - Title: Full query title (2-line truncate with ellipsis).
    - Footer: Confidence pill and prominent touch target `[View Investigation]`.

---

# 3. Touch Targets & Ergonomic Standards

- **Touch Target Minimum:** All mobile interactive elements (buttons, chips, citation pills, drawer toggles) have a minimum interactive touch target of `44px × 44px` (using transparent tap-target padding where visual badge is compact).
- **Font Scaling Bounds:** Body text never scales below `14px` on mobile displays to prevent browser auto-zooming on focus.
- **Header Stickiness:** On mobile viewports, the investigation top header remains sticky (`position: sticky; top: 0`) to ensure the status, duration, and drawer toggle are accessible at all scroll depths.
