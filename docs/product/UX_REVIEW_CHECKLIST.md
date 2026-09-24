# Pocket AI Product Discovery Team
## UX Review & Anti-AI-Slop Acceptance Checklist

**Document Version:** 1.0  
**Status:** Approved for Design (Step 2 Complete)  
**Related Documents:**
- [Visual UX Specification](VISUAL_UX_SPEC.md)
- [Investigation Workspace Specification](INVESTIGATION_WORKSPACE_SPEC.md)
- [Component Design Specification](COMPONENT_DESIGN_SPEC.md)
- [ADR-0015: Visual UX Implementation Strategy](../decisions/ADR-0015-visual-ux-implementation-strategy.md)

---

# 1. Purpose & Enforcement Policy

This checklist is an authoritative quality gate for all frontend implementations of Pocket. Any pull request or UI build that fails any item in this checklist must be **rejected** for remediation before user review.

---

# 2. The 14 Anti-AI-Slop & Quality Acceptance Tests

### Test 1: Anti-Chatbot Architecture
- [ ] **PASS:** The screen renders as an analytical workspace / decision brief.
- [ ] **FAIL:** Uses user/assistant speech bubbles, conversational chat streams, floating bot heads, or typewriter streaming text on completed recommendations.

### Test 2: Anti-"Card-Wall" Discipline
- [ ] **PASS:** The reading experience uses continuous editorial typography for problem statements and recommendation text, structured tabular rows for findings, and full-width alert callouts for tensions.
- [ ] **FAIL:** The screen is assembled as a generic dashboard of identical stacked rounded rectangular cards.

### Test 3: Color & Gradient Discipline
- [ ] **PASS:** Uses a clean Light Neutral foundation (`#ffffff` surfaces, `#f8fafc` canvas, `#e2e8f0` borders) with semantic source identity badges.
- [ ] **FAIL:** Uses neon gradients, purple/cyan glowing backgrounds, dark cyberpunk themes, or rainbow accent bars.

### Test 4: Genuine Motion & Zero Fake AI Theatrics
- [ ] **PASS:** Motion is restricted to functional state transitions (drawer slide 200ms, attention glow 1.5s, milestone completion).
- [ ] **FAIL:** Displays pulsating "thinking" rings, floating sparkles (`✨`), decorative shimmer sweeps, fake progress bars, or simulated agent reasoning logs.

### Test 5: Visual Noise & Cognitive Load
- [ ] **PASS:** The workspace is calm, restrained, and editorial. Whitespace provides clear vertical breathing room between sections.
- [ ] **FAIL:** Cluttered with decorative badges, unnecessary divider lines, floating toolbars, or excessive saturated accent colors.

### Test 6: Typographic Structural Hierarchy
- [ ] **PASS:** Typography does the primary structural work: Display (24px bold), H1 (18px semibold), Lead text (15px), and Body (14px) clearly establish importance without relying on heavy box containers.
- [ ] **FAIL:** Flat typography where text hierarchy is ambiguous and relies on nested card borders for separation.

### Test 7: The 30-Second Executive Rule
- [ ] **PASS:** A reader can look at the screen for 30 seconds and immediately understand the core conclusion, the Action Type (`INVESTIGATE FURTHER` / `REMEDIATE`), and the Confidence rating (`Low` / `Medium` / `High`).
- [ ] **FAIL:** The user must read multiple paragraphs of dense text or scroll past execution logs just to find the primary recommendation.

### Test 8: Attributable Evidence Auditability
- [ ] **PASS:** Every factual assertion contains an inline citation badge (`[EV-001]`). Clicking a badge opens the Evidence Drawer, smoothly scrolls to the card, and highlights it with an attention glow.
- [ ] **FAIL:** Citations are missing, unlinked, or lead to raw unformatted JSON dumps.

### Test 9: Strict Epistemic Demarcation
- [ ] **PASS:** Clear visual separation between verified **Facts** (Emerald), inductive **Inferences** (Sapphire), and provisional **Hypotheses** (Amber).
- [ ] **FAIL:** Facts and hypotheses are mixed together in a single bulleted list or narrative paragraph without epistemic labeling.

### Test 10: Real-World Long-Form Robustness
- [ ] **PASS:** When populated with real, complex multi-thousand-word investigation outputs, the layout remains stable: line lengths remain bounded to 65–75 characters (`max-w-[840px]`), and lists over 6 items provide clean pagination/expansion.
- [ ] **FAIL:** Long outputs cause horizontal scrolling, layout blowout, or unreadable 100-character line lengths on widescreen monitors.

### Test 11: Technical Honesty (Zero Data Simulation)
- [ ] **PASS:** During execution (~100–120s), the UI displays only verified API states (`planning`, `specialists`, `pm`, `critic`). Features requiring future API support display honest descriptive text.
- [ ] **FAIL:** The UI fakes incremental evidence counts, invents tool execution progress bars, or fabricates live token generation counters.

### Test 12: Keyboard & Accessibility Verification
- [ ] **PASS:** The entire interface is navigable via `Tab` / `Shift+Tab`. Pressing `Enter` on a citation badge opens the drawer and shifts focus. `Escape` dismisses the drawer.
- [ ] **FAIL:** Interactive elements lack focus indicators, or focus is lost when drawers open/close.

### Test 13: Color Contrast Verification
- [ ] **PASS:** All body text meets WCAG 2.1 AA ($\ge 4.5:1$ against surface). Large headings and badge borders meet $\ge 3:1$.
- [ ] **FAIL:** Faint light-gray text (`#94a3b8`) used for body copy or low-contrast text on colored badge backgrounds.

### Test 14: Reduced-Motion Conformance
- [ ] **PASS:** When `prefers-reduced-motion: reduce` is enabled in OS settings, all slide transitions and glowing fades become instant state toggles.
- [ ] **FAIL:** Animations continue running despite reduced-motion preferences.
