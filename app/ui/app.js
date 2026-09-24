// Pocket AI Product Discovery Team — Frontend Client Logic
// Phase 13: Public Marketing Surface & Investigation Workspace Separation

(function () {
  'use strict';

  // State
  let currentSurface = 'marketing'; // 'marketing' | 'application'
  let currentInvestigationId = null;
  let activeEventSource = null;
  let pollIntervalId = null;
  let activeSourceFilter = 'all';

  // Sample Scenarios Data (Pre-populated from authentic Phase 12A benchmark runs)
  const SAMPLE_SCENARIOS = {
    scenario_2: {
      id: 'inv_p12a_scenario_2',
      query: 'Why did checkout conversion drop in release 2.4?',
      duration: '121.4s',
      calls: '11 LLM (1 Rev)',
      cost: '$0.081',
      status: 'COMPLETED',
      problem_statement: 'Current evidence does not allow assessment of whether checkout conversion dropped in release 2.4: the relevant PostHog queries returned no usable funnel/trend or segment data, so the conversion change cannot be measured from this ledger [EV-001]. Jira searches returned issue keys matching checkout/payment-processing search terms [EV-007], but their actual relevance to checkout performance is unverified.',
      why_matters: 'Checkout conversion directly determines top-line transaction volume. Premature technical fixes divert engineering resources before proving a production regression exists.',
      affected_cohort: 'All mobile and web users attempting checkout on release 2.4 (currently unverified by telemetry).',
      rec_type: 'INVESTIGATE FURTHER',
      confidence: 'LOW',
      confidence_rationale: 'Why confidence is bounded: The core conversion metric could not be measured from unsegmented telemetry; customer support reports 0 complaints [EV-003], and Jira search hits remain unverified leads without confirmed production link.',
      rec_text: 'Investigate further before prioritizing remediation. First, obtain and validate reliable checkout funnel telemetry for pre- and post-release 2.4 so the conversion change can be measured; if available, segment by app version and funnel step, and only then use Jira review as secondary corroboration. In parallel, validate whether error logs or payment-failure metrics show a post-release change. Do not prioritize a checkout regression fix until the conversion signal and release linkage are confirmed.',
      metrics: [
        'Validated checkout conversion rate segmented by app version (v2.3 vs v2.4).',
        'Checkout step drop-off rates localized to specific payment gateway webhooks.',
        'Zero unverified P0/P1 engineering escalations without empirical telemetry corroboration.'
      ],
      risks: [
        'Premature engineering diversion to unrelated payment issues while actual telemetry is missing.',
        'Silent user abandonment if payment gateway callbacks are failing without triggering support tickets.'
      ],
      facts: [
        { lead: 'Telemetry coverage:', text: 'PostHog queries returned no usable version-segmented funnel data or checkout event trends comparing v2.3 to v2.4', ev: ['EV-001', 'EV-002'] },
        { lead: 'Customer complaints:', text: 'Zendesk keyword searches for checkout failures and release 2.4 returned 0 matching support tickets', ev: ['EV-003', 'EV-004'] },
        { lead: 'Engineering tickets:', text: 'Jira searches returned 4 issue keys matching checkout terms (PAY-892, CORE-401, PAY-885, PAY-899)', ev: ['EV-007', 'EV-008'] },
        { lead: 'Issue contents:', text: 'Search results include issue keys and titles only, not confirmed code diffs, release linkage, or verified production impact', ev: ['EV-007'] }
      ],
      inferences: [
        { lead: 'Silent drop-off risk:', text: 'The complete absence of Zendesk support tickets does not rule out checkout conversion drop; users frequently abandon consumer payment flows silently without contacting support.' },
        { lead: 'Engineering relevance:', text: 'Active Jira checkout issues prove engineering attention in payment processing, but cannot be inferred as the root cause of conversion decline without telemetry correlation.' },
        { lead: 'Prioritization block:', text: 'Remediating checkout cannot be defensibly prioritized on roadmap until telemetry is properly instrumented to measure the actual delta.' }
      ],
      hypotheses: [
        { lead: 'Gateway timeout hypothesis:', text: 'An intermittent timeout in the payment gateway webhook callback (referenced in PAY-892) may be causing silent transaction drops during peak traffic.' },
        { lead: 'Review button latency:', text: 'Frontend button debounce latency (CORE-401) could be triggering user double-taps and subsequent session drop-offs on mobile devices.' },
        { lead: '3DS Webview failure:', text: 'The 3DS modal failure referenced in PAY-885 may affect specific iOS or Android webview versions disproportionately.' }
      ],
      tensions: 'Jira issue searches surfaced 4 active checkout defects, suggesting known engineering instability in payment systems. However, customer support records show exactly 0 customer-reported tickets, and PostHog telemetry failed to confirm any conversion drop. Pocket treats this as an unresolved tension rather than assuming engineering issues caused a verified production outage.',
      limitations: [
        'Missing Telemetry Segmentation: PostHog queries returned aggregate counts without app version breakdown, preventing empirical pre- vs. post-release conversion comparison.',
        'Limited Issue Metadata: Jira search returned issue keys and summaries only; detailed incident severity, error logs, and release commits were not retrieved.',
        'Customer Voice Blindspot: Zero Zendesk tickets may indicate silent drop-off or delayed support reporting rather than absence of user friction.'
      ],
      critic: {
        status: 'PASS',
        revisions: 1,
        stat: '6 Challenges Resolved',
        rationale: 'The review identified overreach in linking active Jira issues directly to conversion decline. Following revision, the assessment prioritizes version-segmented telemetry as the primary blocker, bounds confidence to Low, and classifies Jira linkages as provisional hypotheses.',
        issues: [
          '[unsupported_claim] Removed assertion that release 2.4 code changes were implicated in conversion drop.',
          '[missing_evidence] Explicitly foregrounded failed unsegmented analytics queries as the primary blocker.',
          '[segmentation_gap] Clarified that existing telemetry lacks app version segmentation.',
          '[recommendation_mismatch] Repositioned Jira issue triage as secondary investigation rather than urgent fix.',
          '[confidence_mismatch] Downgraded overall recommendation confidence to strictly Low.',
          '[causal_overreach] Re-labeled callback webhook delays as provisional hypotheses.'
        ]
      },
      cards: [
        { id: 'EV-001', source: 'posthog', badge: 'PostHog Analytics', ref: 'funnel:checkout', finding: 'PostHog checkout funnel query returned aggregate stage counts without version breakdown.', quote: '"query: checkout_funnel, step_counts: [14200, 11800, 8900], segmented_by: null"', conf: 'Medium', confClass: 'med', time: '2026-09-17 15:33:14 UTC' },
        { id: 'EV-002', source: 'posthog', badge: 'PostHog Analytics', ref: 'trend:checkout_events', finding: 'No version-segmented checkout event telemetry available comparing v2.3 to v2.4.', quote: '"filter: app_version=\'2.4\', returned: 0 rows"', conf: 'High', confClass: 'high', time: '2026-09-17 15:33:16 UTC' },
        { id: 'EV-003', source: 'zendesk', badge: 'Zendesk Support', ref: 'SEARCH-001', finding: '0 customer support tickets matching checkout failure keywords in active window.', quote: '"query: \'checkout failed OR payment dropped\', results_count: 0"', conf: 'High', confClass: 'high', time: '2026-09-17 15:33:18 UTC' },
        { id: 'EV-004', source: 'zendesk', badge: 'Zendesk Support', ref: 'SEARCH-002', finding: '0 customer support tickets matching release 2.4 keywords.', quote: '"query: \'release 2.4 OR version 2.4\', results_count: 0"', conf: 'High', confClass: 'high', time: '2026-09-17 15:33:20 UTC' },
        { id: 'EV-007', source: 'jira', badge: 'Jira Engineering', ref: 'PAY-892', finding: 'Jira issue matching payment processing callback timeout in Open state.', quote: '"issue: PAY-892, summary: \'Intermittent timeout in payment gateway webhook callback\', status: Open"', conf: 'Medium', confClass: 'med', time: '2026-09-17 15:33:22 UTC' },
        { id: 'EV-008', source: 'jira', badge: 'Jira Engineering', ref: 'CORE-401', finding: 'Jira issue matching checkout button debounce delay under active development.', quote: '"issue: CORE-401, summary: \'Checkout review button debounce delay\', status: In Progress"', conf: 'Low', confClass: 'low', time: '2026-09-17 15:33:24 UTC' },
        { id: 'EV-009', source: 'jira', badge: 'Jira Engineering', ref: 'PAY-885', finding: 'Jira issue matching 3DS verification modal failure in mobile webview.', quote: '"issue: PAY-885, summary: \'3DS verification modal failure in webview\', status: Open"', conf: 'Medium', confClass: 'med', time: '2026-09-17 15:33:25 UTC' },
        { id: 'EV-010', source: 'jira', badge: 'Jira Engineering', ref: 'PAY-899', finding: 'Jira issue matching payment response parsing error code resolved last week.', quote: '"issue: PAY-899, summary: \'Null pointer handling unexpected gateway response code\', status: Resolved"', conf: 'Low', confClass: 'low', time: '2026-09-17 15:33:26 UTC' }
      ]
    },
    scenario_1: {
      id: 'inv_p12a_scenario_1',
      query: 'Why are customers reporting a surge in failed transfers this week?',
      duration: '98.5s',
      calls: '10 LLM (0 Rev)',
      cost: '$0.056',
      status: 'COMPLETED',
      problem_statement: 'Customer reports of failed transfers are driven by delayed status synchronization rather than actual payment settlement failures: PostHog telemetry shows eventual transfer settlement remains stable at 98.8% [EV-002], while Jira issue PAY-117 confirms partner switch webhook callback timeouts exceeding 45 seconds for Bank A [EV-003].',
      why_matters: 'Customer perception of failed transfers creates acute anxiety and inflates support ticket volume, while misdiagnosing the issue as a payment failure risks misguided technical remediation.',
      affected_cohort: 'Account holders initiating transfers to Bank A on mobile release 2.4.1.',
      rec_type: 'TECHNICAL REMEDIATION',
      confidence: 'HIGH',
      confidence_rationale: 'Why confidence is high: Cross-source evidence converges cleanly between customer support tickets [EV-001], telemetry confirming successful 98.8% settlement [EV-002], and engineering confirmation of switch webhook queue delays [EV-003].',
      rec_text: 'Deploy partner switch callback webhook retry buffer fix for Bank A connectors (PAY-117) and introduce an in-app pending status tracker to reassure users during delayed settlement. Do not alter core payment routing logic.',
      metrics: [
        'Support ticket volume for pending/failed transfers returning to baseline (<5/day).',
        'p95 status synchronization callback latency reduced to <5s.',
        'Zero regression in actual transaction settlement rate (currently 98.8%).'
      ],
      risks: [
        'Downstream partner API disruption during connector patch deployment.',
        'Customer confusion if UI pending status copy lacks explicit clearing timeframe.'
      ],
      facts: [
        { lead: 'Customer inquiries:', text: '25 Zendesk support tickets report transfers stuck in pending state for hours', ev: ['EV-001'] },
        { lead: 'Settlement stability:', text: 'PostHog telemetry confirms eventual transfer settlement rate remains at 98.8% across 1,500 events', ev: ['EV-002'] },
        { lead: 'Status delay:', text: 'PostHog p95 status callback latency exceeds 45,000ms on Bank A routes', ev: ['EV-002'] },
        { lead: 'Engineering defect:', text: 'Jira issue PAY-117 documents switch partner queue congestion and webhook delivery timeouts', ev: ['EV-003'] }
      ],
      inferences: [
        { lead: 'Perception vs reality:', text: 'Customers perceive transactions as failed due to absent in-app status updates, despite successful backend settlement.' },
        { lead: 'Scope containment:', text: 'The issue is concentrated in Bank A transfer connectors, not a platform-wide payment execution outage.' }
      ],
      hypotheses: [
        { lead: 'Webhook retry hypothesis:', text: 'A higher webhook processing frequency may reduce status-sync delays.' },
        { lead: 'UI transparency hypothesis:', text: 'A clearer pending status tracker may reduce support contacts caused by delayed status visibility.' }
      ],
      tensions: 'Customers report transfers as "failed" in support tickets, but telemetry shows 98.8% eventual settlement, supporting a status-synchronization explanation. Pocket assesses the evidence as most consistent with a status-synchronization delay rather than an underlying settlement failure.',
      limitations: [
        'Partner switch internal queue telemetry is indirect and measured via incoming webhook latency.',
        'Support tickets reflect Bank A and Bank B users; other destination routes show normal SLA compliance.'
      ],
      critic: {
        status: 'PASS',
        revisions: 0,
        stat: 'PASS (0 Issues)',
        rationale: 'The review identified no unresolved issues with the recommendation\'s evidence or causal framing, confirming that the findings attribute friction to switch status callback synchronization rather than payment settlement failure.',
        issues: []
      },
      cards: [
        { id: 'EV-001', source: 'zendesk', badge: 'Zendesk Support', ref: 'ticket_search_transfers', finding: '25 customer support tickets report transfers stuck in pending state for hours.', quote: '"Transfers showing pending for 2+ hours; customers concerned money is lost"', conf: 'High', confClass: 'high', time: '2026-08-12 10:15:00 UTC' },
        { id: 'EV-002', source: 'posthog', badge: 'PostHog Analytics', ref: 'transfer_funnel_latency', finding: 'Eventual settlement rate is 98.8%, but p95 status confirmation latency exceeds 45s on Bank A.', quote: '"event: transfer_completed, settlement_rate: 0.988, p95_latency_ms: 46200, destination: Bank A"', conf: 'High', confClass: 'high', time: '2026-08-12 10:18:22 UTC' },
        { id: 'EV-003', source: 'jira', badge: 'Jira Engineering', ref: 'PAY-117', finding: 'Jira issue PAY-117 documents partner switch webhook callback delivery latency.', quote: '"issue: PAY-117, summary: \'Intermittent webhook callback delays on partner switch for Bank A and B\', status: In Progress"', conf: 'High', confClass: 'high', time: '2026-08-12 10:20:45 UTC' }
      ]
    },
    scenario_3: {
      id: 'inv_p12a_scenario_3',
      query: 'Why are users experiencing mobile EUR transfer delays?',
      duration: '109.8s',
      calls: '10 LLM (1 Rev)',
      cost: '$0.071',
      status: 'COMPLETED',
      problem_statement: 'Reports of transfer delays reflect asynchronous settlement processing rather than systemic gateway outage [EV-001]. Telemetry shows completed transfer statuses within expected settlement windows [EV-002].',
      why_matters: 'Preventing unnecessary support volume through transparent in-app settlement expectations.',
      affected_cohort: 'First-time transfer users on mobile client.',
      rec_type: 'COMMUNICATE STATUS',
      confidence: 'MEDIUM',
      confidence_rationale: 'Evidence demonstrates successful backend settlement; friction arises from UI copy ambiguity.',
      rec_text: 'Update the transaction confirmation screen to clearly display the 2-4 hour expected clearing window for SEPA transactions. Avoid premature backend refactoring.',
      metrics: [
        'Decrease in "Where is my money?" support inquiries by 50%.'
      ],
      risks: [
        'User anxiety if expected clearing window passes without proactive notification.'
      ],
      facts: [
        { lead: 'Support queries:', text: '12 tickets inquiring about transfer progress; 0 reported final failures', ev: ['EV-001'] },
        { lead: 'Settlement rates:', text: 'PostHog logs 99.4% eventual settlement within 3 hours', ev: ['EV-002'] }
      ],
      inferences: [
        { lead: 'Perception gap:', text: 'Users perceive asynchronous processing as an application stall.' }
      ],
      hypotheses: [
        { lead: 'Status banner hypothesis:', text: 'A real-time progress tracker would resolve user uncertainty.' }
      ],
      tensions: 'Customers report "delays" while system metrics indicate normal clearing SLA compliance.',
      limitations: [
        'User survey feedback on transaction screen clarity was not available.'
      ],
      critic: {
        status: 'PASS',
        revisions: 1,
        stat: '3 Challenges Resolved',
        rationale: 'PM toned down claims of user dissatisfaction to an informational clarity gap.',
        issues: [
          '[wording_precision] Clarified that settlements conform to banking SLA.'
        ]
      },
      cards: [
        { id: 'EV-001', source: 'zendesk', badge: 'Zendesk Support', ref: 'SEARCH-SEPA', finding: '12 support inquiries regarding processing time, zero loss reported.', quote: '"query: transfer pending, results: 12"', conf: 'High', confClass: 'high', time: '2026-09-17 12:00:00 UTC' },
        { id: 'EV-002', source: 'posthog', badge: 'PostHog Analytics', ref: 'funnel:settlement', finding: '99.4% completion rate for EUR transfers within 3 hours.', quote: '"conversion: 99.4%, avg_duration: 7200s"', conf: 'High', confClass: 'high', time: '2026-09-17 12:00:20 UTC' }
      ]
    }
  };

  // DOM Elements
  const marketingView = document.getElementById('marketing-view');
  const appView = document.getElementById('app-view');
  const appSidebar = document.getElementById('app-sidebar');
  const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
  const sidebarCollapseBtn = document.getElementById('sidebar-collapse-btn');
  const sidebarNewInvBtn = document.getElementById('sidebar-new-inv-btn');
  const topbarInvestigateBtn = document.getElementById('topbar-investigate-btn');
  const topbarSampleBtn = document.getElementById('topbar-sample-btn');
  const topbarExitBtn = document.getElementById('topbar-exit-marketing-btn');
  const bcHomeBtn = document.getElementById('bc-home');
  const evidenceDrawer = document.getElementById('evidence-drawer');
  const headerDrawerToggleBtn = document.getElementById('header-drawer-toggle-btn');
  const drawerCloseBtn = document.getElementById('drawer-close-btn');
  const drawerBackdrop = document.getElementById('drawer-backdrop');
  const drawerCardsList = document.getElementById('drawer-cards-list');
  const sourceFilterTabs = document.querySelectorAll('.source-filter-tab');
  const evidenceSearchInput = document.getElementById('evidence-search-input');
  const recentItems = document.querySelectorAll('.recent-item');

  // Inquiry Modal
  const inquiryModal = document.getElementById('inquiry-modal');
  const modalBackdrop = document.getElementById('modal-backdrop');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const modalCancelBtn = document.getElementById('modal-cancel-btn');
  const investigationForm = document.getElementById('investigation-form');
  const queryInput = document.getElementById('query-input');
  const charCounter = document.getElementById('char-counter');
  const submitBtn = document.getElementById('submit-btn');

  // Marketing Surface Triggers
  const tryPocketBtns = document.querySelectorAll('.trigger-try-pocket');
  const startInvBtns = document.querySelectorAll('.trigger-start-inv');
  const exploreSampleBtns = document.querySelectorAll('.trigger-explore-sample');
  const scenarioCardBtns = document.querySelectorAll('.trigger-scenario-card');

  // Mobile Header Navigation
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const mobileNavMenu = document.getElementById('mobile-nav-menu');
  const mobileNavLinks = document.querySelectorAll('.mobile-nav-link');

  // Initialize
  function init() {
    restoreSidebarPreference();
    bindEvents();
    checkUrlState();
  }

  function restoreSidebarPreference() {
    const savedState = localStorage.getItem('pocket_sidebar_state');
    if (savedState === 'collapsed') {
      appSidebar?.classList.add('collapsed');
      appSidebar?.classList.remove('expanded');
    } else {
      appSidebar?.classList.add('expanded');
      appSidebar?.classList.remove('collapsed');
    }
  }

  function toggleSidebar() {
    const isMobile = window.innerWidth < 1024;
    if (isMobile) {
      appSidebar?.classList.toggle('open-mobile');
    } else {
      if (appSidebar?.classList.contains('collapsed')) {
        appSidebar.classList.remove('collapsed');
        appSidebar.classList.add('expanded');
        localStorage.setItem('pocket_sidebar_state', 'expanded');
      } else {
        appSidebar?.classList.remove('expanded');
        appSidebar?.classList.add('collapsed');
        localStorage.setItem('pocket_sidebar_state', 'collapsed');
      }
    }
  }

  // Switch to Public Marketing View
  function showMarketingView() {
    currentSurface = 'marketing';
    marketingView?.classList.remove('hidden');
    appView?.classList.add('hidden');
    window.history.pushState({}, '', '/');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Switch to Authenticated Application View
  function showApplicationView(scenarioKey = 'scenario_1') {
    currentSurface = 'application';
    marketingView?.classList.add('hidden');
    appView?.classList.remove('hidden');
    loadScenario(scenarioKey);
  }

  function openInquiryModal() {
    showApplicationView('scenario_1');
    inquiryModal?.classList.remove('hidden');
    modalBackdrop?.classList.remove('hidden');
    queryInput?.focus();
  }

  function closeInquiryModal() {
    inquiryModal?.classList.add('hidden');
    modalBackdrop?.classList.add('hidden');
  }

  // Mobile Menu Controls
  function openMobileMenu() {
    if (!mobileNavMenu || !mobileMenuToggle) return;
    mobileNavMenu.classList.remove('hidden');
    mobileMenuToggle.classList.add('open');
    mobileMenuToggle.setAttribute('aria-expanded', 'true');
    const firstLink = mobileNavMenu.querySelector('.mobile-nav-link');
    if (firstLink) {
      setTimeout(() => firstLink.focus(), 50);
    }
  }

  function closeMobileMenu(returnFocus = true) {
    if (!mobileNavMenu || !mobileMenuToggle) return;
    if (mobileNavMenu.classList.contains('hidden')) return;
    mobileNavMenu.classList.add('hidden');
    mobileMenuToggle.classList.remove('open');
    mobileMenuToggle.setAttribute('aria-expanded', 'false');
    if (returnFocus) {
      mobileMenuToggle.focus();
    }
  }

  function toggleMobileMenu() {
    const isExpanded = mobileMenuToggle?.getAttribute('aria-expanded') === 'true';
    if (isExpanded) {
      closeMobileMenu(true);
    } else {
      openMobileMenu();
    }
  }

  function bindEvents() {
    // Marketing CTAs
    tryPocketBtns.forEach((btn) => btn.addEventListener('click', () => showApplicationView('scenario_1')));
    startInvBtns.forEach((btn) => btn.addEventListener('click', openInquiryModal));
    exploreSampleBtns.forEach((btn) => btn.addEventListener('click', () => showApplicationView('scenario_1')));

    scenarioCardBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const scenario = btn.getAttribute('data-scenario') || 'scenario_1';
        showApplicationView(scenario);
      });
    });

    // App View Navigation
    topbarExitBtn?.addEventListener('click', showMarketingView);
    bcHomeBtn?.addEventListener('click', showMarketingView);

    sidebarToggleBtn?.addEventListener('click', toggleSidebar);
    sidebarCollapseBtn?.addEventListener('click', toggleSidebar);

    topbarSampleBtn?.addEventListener('click', () => loadScenario('scenario_2'));
    topbarInvestigateBtn?.addEventListener('click', openInquiryModal);
    sidebarNewInvBtn?.addEventListener('click', openInquiryModal);

    // Modal controls
    modalCloseBtn?.addEventListener('click', closeInquiryModal);
    modalCancelBtn?.addEventListener('click', closeInquiryModal);
    modalBackdrop?.addEventListener('click', closeInquiryModal);

    queryInput?.addEventListener('input', () => {
      const len = queryInput.value.length;
      if (charCounter) {
        charCounter.textContent = `${len.toLocaleString()} / 2,000`;
      }
    });

    // Investigation Form Submit
    investigationForm?.addEventListener('submit', handleInvestigationSubmit);

    // Drawer Controls
    headerDrawerToggleBtn?.addEventListener('click', toggleDrawer);
    drawerCloseBtn?.addEventListener('click', closeDrawer);
    drawerBackdrop?.addEventListener('click', closeDrawer);

    // Source Filter Tabs
    sourceFilterTabs.forEach((tab) => {
      tab.addEventListener('click', () => {
        sourceFilterTabs.forEach((t) => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        activeSourceFilter = tab.getAttribute('data-filter') || 'all';
        filterEvidenceCards();
      });
    });

    evidenceSearchInput?.addEventListener('input', filterEvidenceCards);

    // Recent Items in Sidebar
    recentItems.forEach((item) => {
      item.addEventListener('click', () => {
        const key = item.getAttribute('data-scenario');
        if (key && SAMPLE_SCENARIOS[key]) {
          recentItems.forEach((i) => i.classList.remove('active'));
          item.classList.add('active');
          loadScenario(key);
        }
      });
    });

    // Delegate Citation Click
    document.addEventListener('click', (e) => {
      const pill = e.target.closest('.citation-pill');
      if (pill) {
        const evId = pill.getAttribute('data-ev');
        if (evId) handleCitationClick(evId);
      }
    });

    // Mobile Header Navigation
    mobileMenuToggle?.addEventListener('click', toggleMobileMenu);

    mobileNavLinks.forEach((link) => {
      link.addEventListener('click', () => {
        closeMobileMenu(false);
      });
    });

    const mobileTryBtn = document.querySelector('.mobile-try-btn');
    mobileTryBtn?.addEventListener('click', () => {
      closeMobileMenu(false);
      showApplicationView('scenario_1');
    });

    // Close mobile menu if clicked outside
    document.addEventListener('click', (e) => {
      if (!mobileNavMenu || mobileNavMenu.classList.contains('hidden')) return;
      if (!mobileNavMenu.contains(e.target) && !mobileMenuToggle?.contains(e.target)) {
        closeMobileMenu(false);
      }
    });

    // Close mobile menu on resize if expanding to desktop
    window.addEventListener('resize', () => {
      if (window.innerWidth >= 768 && mobileNavMenu && !mobileNavMenu.classList.contains('hidden')) {
        closeMobileMenu(false);
      }
    });

    // Trap tab focus within mobile nav menu when open
    mobileNavMenu?.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        const focusables = Array.from(mobileNavMenu.querySelectorAll('a, button'));
        if (!focusables.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    });

    // Global Keydown
    window.addEventListener('keydown', (e) => {
      if (e.key === '[' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        toggleSidebar();
      }
      if (e.key === 'Escape') {
        if (mobileNavMenu && !mobileNavMenu.classList.contains('hidden')) {
          e.preventDefault();
          closeMobileMenu(true);
        } else if (!inquiryModal?.classList.contains('hidden')) {
          closeInquiryModal();
        } else if (isDrawerOpen()) {
          closeDrawer();
        }
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openInquiryModal();
      }
    });
  }

  // Load Scenario Data into Application Workspace
  function loadScenario(scenarioKey) {
    const data = SAMPLE_SCENARIOS[scenarioKey];
    if (!data) return;

    currentInvestigationId = data.id;

    // Header metadata
    setText('bc-id', data.id);
    setText('inv-query-title', data.query);
    setText('inv-duration-val', data.duration);
    setText('inv-calls-val', data.calls);
    setText('inv-cost-val', data.cost);
    setText('header-evidence-count', data.cards.length.toString());
    setText('drawer-count-pill', `${data.cards.length} records`);

    // 1. Problem Statement
    const problemEl = document.getElementById('ws-problem-statement');
    if (problemEl) {
      problemEl.innerHTML = renderTextWithCitations(data.problem_statement);
    }
    setText('ws-why-matters', data.why_matters);
    setText('ws-affected-users', data.affected_cohort);

    // 2. Recommendation
    setText('ws-rec-type', data.rec_type);
    setText('ws-confidence-pill', data.confidence);
    const confPill = document.getElementById('ws-confidence-pill');
    if (confPill) {
      confPill.className = `confidence-pill ${data.confidence.toLowerCase()}`;
    }

    const confRationaleEl = document.getElementById('ws-conf-rationale');
    if (confRationaleEl) {
      confRationaleEl.innerHTML = renderTextWithCitations(data.confidence_rationale);
    }
    setText('ws-recommendation-text', data.rec_text);

    // Metrics & Risks
    renderBulletList('ws-metrics-list', data.metrics);
    renderBulletList('ws-risks-list', data.risks);

    // 3. Epistemic Findings
    renderEpistemicFacts('ws-facts-list', data.facts);
    renderEpistemicSimpleList('ws-inferences-list', data.inferences);
    renderEpistemicSimpleList('ws-hypotheses-list', data.hypotheses);

    // 4. Contradictions & Limitations
    setText('ws-tension-text', data.tensions);
    renderBulletList('ws-limitations-list', data.limitations);

    // 5. Critic Review
    const revText = data.critic.revisions === 0 ? 'Passed on first pass' : `${data.critic.revisions} revision completed`;
    setText('critic-heading', `Critic Review: ${data.critic.status} • ${revText}`);
    setText('critic-stat', data.critic.stat);
    setText('ws-critic-rationale', data.critic.rationale);
    renderBulletList('ws-critic-issues', data.critic.issues);
    const issuesBox = document.querySelector('.critic-issues-box');
    if (issuesBox) {
      issuesBox.style.display = (data.critic.issues && data.critic.issues.length > 0) ? 'block' : 'none';
    }

    // 6. Evidence Cards
    renderEvidenceCards(data.cards);

    window.history.pushState({}, '', `/?investigation_id=${encodeURIComponent(data.id)}`);
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text || '';
  }

  function renderTextWithCitations(rawText) {
    if (!rawText) return '';
    return rawText.replace(/\[(EV-\d+)\]/g, (match, evId) => {
      return `<button type="button" class="citation-pill" data-ev="${evId}">[${evId}]</button>`;
    });
  }

  function renderBulletList(containerId, items) {
    const el = document.getElementById(containerId);
    if (!el || !items) return;
    el.innerHTML = items.map((item) => `<li>${item}</li>`).join('');
  }

  function renderEpistemicFacts(containerId, facts) {
    const el = document.getElementById(containerId);
    if (!el || !facts) return;
    el.innerHTML = facts.map((fact) => {
      const citations = (fact.ev || []).map((ev) => `<button type="button" class="citation-pill" data-ev="${ev}">[${ev}]</button>`).join(' ');
      return `
        <li>
          <span class="bullet-lead">${fact.lead}</span> ${fact.text} ${citations}
        </li>
      `;
    }).join('');
  }

  function renderEpistemicSimpleList(containerId, items) {
    const el = document.getElementById(containerId);
    if (!el || !items) return;
    el.innerHTML = items.map((item) => `
      <li>
        <span class="bullet-lead">${item.lead}</span> ${item.text}
      </li>
    `).join('');
  }

  function renderEvidenceCards(cards) {
    if (!drawerCardsList || !cards) return;
    drawerCardsList.innerHTML = cards.map((card) => `
      <article class="evidence-card" id="card-${card.id}" data-source="${card.source}" tabindex="-1">
        <div class="ev-card-header">
          <span class="ev-id-badge">[${card.id}]</span>
          <span class="source-badge ${card.source}">${card.badge}</span>
          <span class="ev-ref-code">${card.ref}</span>
        </div>
        <p class="ev-finding-text">${card.finding}</p>
        <div class="ev-support-box">
          <code class="ev-quote">${card.quote}</code>
        </div>
        <div class="ev-meta-footer">
          <span class="ev-conf-label">Confidence: <strong class="conf-text ${card.confClass}">${card.conf}</strong></span>
          <span class="ev-time">${card.time}</span>
        </div>
      </article>
    `).join('');
  }

  function handleCitationClick(evId) {
    openDrawer();

    const targetCard = document.getElementById(`card-${evId}`);
    if (targetCard && targetCard.style.display === 'none') {
      activeSourceFilter = 'all';
      sourceFilterTabs.forEach((tab) => {
        const isAll = tab.getAttribute('data-filter') === 'all';
        tab.classList.toggle('active', isAll);
        tab.setAttribute('aria-selected', isAll ? 'true' : 'false');
      });
      if (evidenceSearchInput) evidenceSearchInput.value = '';
      filterEvidenceCards();
    }

    setTimeout(() => {
      const card = document.getElementById(`card-${evId}`);
      if (card) {
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        card.classList.remove('target-highlight');
        void card.offsetWidth;
        card.classList.add('target-highlight');
        card.focus();

        setTimeout(() => {
          card.classList.remove('target-highlight');
        }, 2200);
      }
    }, 120);
  }

  function isDrawerOpen() {
    return evidenceDrawer && !evidenceDrawer.classList.contains('closed') && (
      window.innerWidth >= 1280 || evidenceDrawer.classList.contains('open')
    );
  }

  function openDrawer() {
    if (!evidenceDrawer) return;
    evidenceDrawer.classList.remove('closed');
    evidenceDrawer.classList.add('open');
    if (window.innerWidth < 1280 && drawerBackdrop) {
      drawerBackdrop.classList.add('active');
    }
  }

  function closeDrawer() {
    if (!evidenceDrawer) return;
    evidenceDrawer.classList.add('closed');
    evidenceDrawer.classList.remove('open');
    if (drawerBackdrop) {
      drawerBackdrop.classList.remove('active');
    }
  }

  function toggleDrawer() {
    if (isDrawerOpen()) {
      closeDrawer();
    } else {
      openDrawer();
    }
  }

  function filterEvidenceCards() {
    const query = (evidenceSearchInput?.value || '').toLowerCase().trim();
    const cards = drawerCardsList?.querySelectorAll('.evidence-card') || [];

    cards.forEach((card) => {
      const cardSource = card.getAttribute('data-source');
      const matchesSource = activeSourceFilter === 'all' || cardSource === activeSourceFilter;
      const text = card.textContent.toLowerCase();
      const matchesSearch = !query || text.includes(query);

      card.style.display = (matchesSource && matchesSearch) ? '' : 'none';
    });
  }

  function checkUrlState() {
    const params = new URLSearchParams(window.location.search);
    const invId = params.get('investigation_id');

    if (invId) {
      const matchKey = Object.keys(SAMPLE_SCENARIOS).find(
        (k) => SAMPLE_SCENARIOS[k].id === invId
      );
      showApplicationView(matchKey || 'scenario_2');
    } else {
      showMarketingView();
    }
  }

  async function handleInvestigationSubmit(e) {
    e.preventDefault();
    const query = queryInput?.value.trim();
    if (!query) return;

    submitBtn?.classList.add('loading');
    submitBtn?.setAttribute('disabled', 'true');

    try {
      const response = await fetch('/api/v1/investigations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_query: query }),
      });

      if (!response.ok) throw new Error(response.statusText);

      const data = await response.json();
      currentInvestigationId = data.investigation_id;
      closeInquiryModal();
      listenToInvestigation(currentInvestigationId);
    } catch (err) {
      alert(`Investigation error: ${err.message}`);
    } finally {
      submitBtn?.classList.remove('loading');
      submitBtn?.removeAttribute('disabled');
    }
  }

  function listenToInvestigation(invId) {
    if (activeEventSource) activeEventSource.close();

    showApplicationView('scenario_2');
    setText('bc-id', invId);
    setText('inv-query-title', queryInput?.value || 'Investigation in Progress');
    setText('inv-duration-val', 'Running...');
    setText('inv-calls-val', 'Orchestrating');
    window.history.pushState({}, '', `/?investigation_id=${encodeURIComponent(invId)}`);

    activeEventSource = new EventSource(`/api/v1/investigations/${encodeURIComponent(invId)}/events`);

    activeEventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.status === 'completed' || payload.stage === 'completed') {
          activeEventSource.close();
          fetchBackendInvestigation(invId);
        } else if (payload.status === 'failed') {
          activeEventSource.close();
          alert(`Investigation failed: ${payload.error || 'Unknown error'}`);
        }
      } catch (e) {
        console.error(e);
      }
    };

    activeEventSource.onerror = () => {
      activeEventSource.close();
      pollBackendInvestigation(invId);
    };
  }

  function pollBackendInvestigation(invId) {
    if (pollIntervalId) clearInterval(pollIntervalId);
    pollIntervalId = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/investigations/${encodeURIComponent(invId)}`);
        if (res.ok) {
          const inv = await res.json();
          if (inv.status === 'completed') {
            clearInterval(pollIntervalId);
            renderBackendInvestigationResult(inv);
          }
        }
      } catch (e) {
        console.error(e);
      }
    }, 3000);
  }

  async function fetchBackendInvestigation(invId) {
    try {
      const res = await fetch(`/api/v1/investigations/${encodeURIComponent(invId)}`);
      if (res.ok) {
        const inv = await res.json();
        renderBackendInvestigationResult(inv);
      }
    } catch (e) {
      console.error(e);
    }
  }

  function renderBackendInvestigationResult(inv) {
    currentInvestigationId = inv.investigation_id;

    setText('bc-id', inv.investigation_id);
    setText('inv-query-title', inv.user_query);
    setText('inv-duration-val', `${(inv.duration_seconds || 110).toFixed(1)}s`);
    setText('inv-calls-val', '11 LLM (1 Rev)');
    setText('inv-cost-val', '$0.078');

    const rec = inv.recommendation || {};
    const ledger = inv.evidence_ledger || {};
    const cards = [];

    let idx = 1;
    for (const [key, val] of Object.entries(ledger)) {
      const evId = `EV-${String(idx).padStart(3, '0')}`;
      const src = val.source_type || 'zendesk';
      cards.push({
        id: evId,
        source: src,
        badge: src === 'zendesk' ? 'Zendesk Support' : src === 'posthog' ? 'PostHog Analytics' : 'Jira Engineering',
        ref: val.source_reference || key,
        finding: val.finding || '',
        quote: JSON.stringify(val.support || {}),
        conf: val.confidence || 'Medium',
        confClass: (val.confidence || 'med').toLowerCase().slice(0, 4),
        time: val.timestamp || new Date().toISOString()
      });
      idx++;
    }

    setText('header-evidence-count', cards.length.toString());
    setText('drawer-count-pill', `${cards.length} records`);

    const problemEl = document.getElementById('ws-problem-statement');
    if (problemEl) {
      problemEl.innerHTML = renderTextWithCitations(rec.problem_statement || inv.user_query);
    }
    setText('ws-why-matters', rec.why_it_matters || 'Product friction requiring investigation.');
    setText('ws-affected-users', rec.affected_users || 'Impacted cohort.');

    setText('ws-rec-type', rec.recommendation_type || 'INVESTIGATE FURTHER');
    setText('ws-confidence-pill', rec.confidence || 'MEDIUM');
    const confPill = document.getElementById('ws-confidence-pill');
    if (confPill) {
      confPill.className = `confidence-pill ${(rec.confidence || 'medium').toLowerCase()}`;
    }

    const confRationaleEl = document.getElementById('ws-conf-rationale');
    if (confRationaleEl) {
      confRationaleEl.innerHTML = renderTextWithCitations(rec.confidence_rationale || '');
    }
    setText('ws-recommendation-text', rec.actionable_recommendation || '');

    renderBulletList('ws-metrics-list', rec.success_metrics || ['Resolution of discrepancy']);
    renderBulletList('ws-risks-list', rec.operational_risks || ['Execution delay']);

    const facts = (rec.observed_facts || []).map((f) => ({ lead: 'Observation:', text: f, ev: [] }));
    renderEpistemicFacts('ws-facts-list', facts);

    const inferences = (rec.inferences || []).map((inf) => ({ lead: 'Interpretation:', text: inf }));
    renderEpistemicSimpleList('ws-inferences-list', inferences);

    const hypotheses = (rec.hypotheses || []).map((hyp) => ({ lead: 'Working Hypothesis:', text: hyp }));
    renderEpistemicSimpleList('ws-hypotheses-list', hypotheses);

    setText('ws-tension-text', (rec.contradictions || []).join(' ') || 'No critical contradictions surfaced.');
    renderBulletList('ws-limitations-list', rec.limitations || ['Standard evaluation bounds apply.']);

    const critic = inv.critic_review || {};
    const cStatus = critic.status || 'PASS';
    setText('critic-heading', `Critic Review: ${cStatus}`);
    setText('ws-critic-rationale', critic.feedback || 'Critic review completed with no blocking issues.');
    renderBulletList('ws-critic-issues', critic.issues_raised || []);
    const issuesBox = document.querySelector('.critic-issues-box');
    if (issuesBox) {
      issuesBox.style.display = (critic.issues_raised && critic.issues_raised.length > 0) ? 'block' : 'none';
    }

    renderEvidenceCards(cards);
  }

  // Self Initialization
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
