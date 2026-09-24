import type { EvidenceSupportingRecord, InvestigationDetailResponse } from '@/types/domain';

type EvidenceSource = 'zendesk' | 'posthog' | 'jira';
type Confidence = 'high' | 'medium' | 'low';

interface PreviewEvidence {
  source: EvidenceSource;
  sourceReference: string;
  finding: string;
  support: string;
  retrievedAt: string;
  confidence?: Confidence;
  supportingRecords?: EvidenceSupportingRecord[];
}

interface PreviewBrief {
  investigationId: string;
  question: string;
  durationSeconds: number;
  scope: NonNullable<InvestigationDetailResponse['scope']>;
  problem: string;
  whyItMatters: string;
  affectedUsers: string;
  recommendation: string;
  recommendationType: string;
  confidence: Confidence;
  successMetrics: string[];
  risks: string[];
  evidence: PreviewEvidence[];
  inferences: Array<{ statement: string; evidenceIndexes: number[] }>;
  hypotheses: Array<{ statement: string; evidenceIndexes: number[] }>;
  tensions?: string[];
  limitations: string[];
}

function createPreviewBrief(brief: PreviewBrief): InvestigationDetailResponse {
  const evidenceIds = brief.evidence.map((_, index) => `EV-${String(index + 1).padStart(3, '0')}`);
  const evidenceLedger = Object.fromEntries(
    brief.evidence.map((item, index) => [
      evidenceIds[index],
      {
        ledger_entry_id: evidenceIds[index],
        source_type: item.source,
        source_reference: item.sourceReference,
        finding: item.finding,
        support_excerpt: item.support,
        confidence: item.confidence ?? brief.confidence,
        retrieved_at: item.retrievedAt,
        supporting_records: item.supportingRecords ?? [],
      },
    ])
  );

  return {
    investigation_id: brief.investigationId,
    user_query: brief.question,
    status: 'completed',
    duration_seconds: brief.durationSeconds,
    scope: brief.scope,
    recommendation: {
      problem_statement: brief.problem,
      why_it_matters: brief.whyItMatters,
      affected_users: brief.affectedUsers,
      recommendation: brief.recommendation,
      recommendation_type: brief.recommendationType,
      confidence: brief.confidence,
      success_metrics: brief.successMetrics,
      risks: brief.risks,
      conflicting_evidence: brief.tensions ?? [],
      disclosed_limitations: brief.limitations,
      factual_observations: brief.evidence.map((item, index) => ({
        statement: item.finding,
        epistemic_type: 'fact' as const,
        evidence_ids: [evidenceIds[index]],
      })),
      inferences: brief.inferences.map(({ statement, evidenceIndexes }) => ({
        statement,
        epistemic_type: 'inference' as const,
        evidence_ids: evidenceIndexes.map((index) => evidenceIds[index]),
      })),
      hypotheses: brief.hypotheses.map(({ statement, evidenceIndexes }) => ({
        statement,
        epistemic_type: 'hypothesis' as const,
        evidence_ids: evidenceIndexes.map((index) => evidenceIds[index]),
      })),
      evidence_citations: brief.evidence.map((item, index) => ({
        ledger_entry_id: evidenceIds[index],
        source: item.source,
        source_reference: item.sourceReference,
        finding: item.finding,
        support: item.support,
        confidence: item.confidence ?? brief.confidence,
      })),
    },
    evidence_ledger: evidenceLedger,
    critic_review: {
      status: 'PASS',
      revisions_completed: 0,
      critique_summary: 'Quality review complete.',
      issues_addressed: [],
    },
    telemetry_summary: {
      investigation_id: brief.investigationId,
      llm_calls: 0,
      total_tokens: 0,
      provider_reported_cost: 0,
      internally_estimated_cost: 0,
    },
  };
}

function supportTicketRecords({
  firstId,
  title,
  excerpts,
  occurredAt,
}: {
  firstId: number;
  title: string;
  excerpts: string[];
  occurredAt: string;
}): EvidenceSupportingRecord[] {
  return Array.from({ length: 12 }, (_, index) => {
    const ticketId = firstId + index;
    return {
      record_id: `ticket-${ticketId}`,
      record_type: 'ticket',
      source_reference: `Customer conversation #${ticketId}`,
      title,
      excerpt: excerpts[index % excerpts.length],
      status: index < 9 ? 'Open' : 'Solved',
      occurred_at: occurredAt,
      attributes: {
        Priority: index < 5 ? 'High' : 'Normal',
        Channel: index % 2 === 0 ? 'Web' : 'Email',
      },
    };
  });
}

function metricRecord(
  id: string,
  reference: string,
  title: string,
  excerpt: string,
  attributes: Record<string, string>
): EvidenceSupportingRecord {
  return {
    record_id: id,
    record_type: 'metric',
    source_reference: reference,
    title,
    excerpt,
    attributes,
  };
}

function issueRecord(
  key: string,
  title: string,
  excerpt: string,
  status: string,
  priority: string,
  occurredAt: string
): EvidenceSupportingRecord {
  return {
    record_id: `issue-${key}`,
    record_type: 'issue',
    source_reference: `Engineering issue ${key}`,
    title,
    excerpt,
    status,
    occurred_at: occurredAt,
    attributes: { Priority: priority },
  };
}

export const REFERENCE_SCENARIO_1 = createPreviewBrief({
  investigationId: 'inv_p12a_scenario_1',
  question: 'Why are customers reporting a surge in failed transfers this week?',
  durationSeconds: 98.5,
  scope: {
    start_time: '2026-08-10T08:00:00Z',
    end_time: '2026-08-15T20:00:00Z',
    timezone: 'UTC',
  },
  problem:
    'Customers are interpreting long pending periods as failed transfers, although the observed settlement failure rate remains low [EV-001] [EV-002].',
  whyItMatters:
    'The gap between money movement and the status customers see creates anxiety, repeat attempts, and avoidable support demand.',
  affectedUsers:
    'Customers sending transfers to Bank A and Bank B during the selected period; other destination banks show normal confirmation times.',
  recommendation:
    'Prioritise transfer-status synchronisation for Bank A and Bank B. Until delivery is restored, clearly show when a transfer is still processing, explain what happens next, and provide a safe status-check path.',
  recommendationType: 'prioritise',
  confidence: 'high',
  successMetrics: [
    'Bank A and Bank B transfer confirmation time|Baseline: p95 of about 3h 38m and 3h 48m|Target: p95 under 30 seconds|Review: Daily until stable, then weekly',
    'Customer contacts about pending or missing transfers|Baseline: 12 reviewed contacts in the selected period|Target: 50% fewer|Review: Four weeks after release',
  ],
  risks: [
    'Do not describe a transfer as complete until settlement is confirmed.',
    'Prevent repeat-transfer prompts while the original payment is still processing.',
  ],
  tensions: [
    'Customers describe these transfers as failed, while the observed data contains 718 completions and only 10 failures; the larger problem is delayed status confirmation.',
  ],
  limitations: [
    'Measure confirmation time after the fix and verify that Bank A and Bank B return to the same range as other destinations.',
  ],
  evidence: [
    {
      source: 'zendesk',
      sourceReference: 'transfer-status contacts',
      finding: 'Twelve reviewed customer contacts describe transfers remaining pending or appearing missing.',
      support: 'Customers report that funds left their balance while the recipient and in-app status remained unconfirmed.',
      retrievedAt: '2026-08-15T20:00:00Z',
      supportingRecords: supportTicketRecords({
        firstId: 1,
        title: 'Transfer status is still pending',
        occurredAt: '2026-08-15T12:00:00Z',
        excerpts: [
          'My transfer has been processing for more than two hours and the recipient has not received it.',
          'The money left my account, but the status has not changed and I need to know whether it will arrive.',
          'I sent money to a supplier and the transfer is still marked as pending after several hours.',
          'Other transfers worked today, but this one is still waiting for confirmation.',
        ],
      }),
    },
    {
      source: 'posthog',
      sourceReference: 'transfer outcome and confirmation time',
      finding: 'The selected period contains 718 completed transfer events and 10 failed events; confirmation delays are concentrated in Bank A and Bank B.',
      support: 'Observed failure share: about 1.4% of completed and failed outcomes. Confirmation-time p95: Bank A about 3h 38m; Bank B about 3h 48m; other destinations about 5 seconds.',
      retrievedAt: '2026-08-15T20:00:00Z',
      supportingRecords: [
        metricRecord('metric-bank-a', 'Bank A', 'Bank A confirmation time', 'Status confirmation is substantially delayed.', { 'Completion records': '142', 'P95 confirmation': 'About 3h 38m' }),
        metricRecord('metric-bank-b', 'Bank B', 'Bank B confirmation time', 'Status confirmation is substantially delayed.', { 'Completion records': '142', 'P95 confirmation': 'About 3h 48m' }),
        metricRecord('metric-other-banks', 'Other destinations', 'Other destination banks', 'Confirmation remains within the normal range.', { 'P95 confirmation': 'About 5 seconds' }),
        metricRecord('metric-transfer-outcomes', 'Transfer outcomes', 'Overall transfer outcomes', 'The observed failure share remains low.', { Completed: '718', Failed: '10', 'Failure share': 'About 1.4%' }),
      ],
    },
    {
      source: 'jira',
      sourceReference: 'PAY-117',
      finding: 'PAY-117 is in progress and tracks delayed transfer-status delivery for Bank A and Bank B.',
      support: 'Priority: High. The delivery team has reproduced the delayed status updates and is working on reconciliation.',
      retrievedAt: '2026-08-15T20:00:00Z',
      supportingRecords: [
        issueRecord('PAY-117', 'Delayed transfer status updates for Bank A and Bank B', 'The delivery team reproduced the delay and is working on status reconciliation.', 'In Progress', 'High', '2026-08-15T20:00:00Z'),
      ],
    },
  ],
  inferences: [
    {
      statement: 'The customer problem is status uncertainty rather than a broad increase in failed settlement.',
      evidenceIndexes: [0, 1, 2],
    },
    {
      statement: 'Fixing synchronisation and improving the pending experience should reduce false failure perception and repeat attempts.',
      evidenceIndexes: [0, 1],
    },
  ],
  hypotheses: [
    {
      statement: 'A clearer pending state may reduce support demand while the synchronisation fix is completed.',
      evidenceIndexes: [0, 2],
    },
  ],
});

export const SAMPLE_INVESTIGATION_ID = REFERENCE_SCENARIO_1.investigation_id;

export const SAMPLE_SCENARIOS: Record<string, InvestigationDetailResponse> = {
  [SAMPLE_INVESTIGATION_ID]: REFERENCE_SCENARIO_1,
  inv_p12a_scenario_2: createPreviewBrief({
    investigationId: 'inv_p12a_scenario_2',
    question: 'Why did user verification drop off at the identity upload step for new signups?',
    durationSeconds: 104.2,
    scope: { start_time: '2026-08-01T00:00:00Z', end_time: '2026-08-20T23:59:59Z', timezone: 'UTC' },
    problem: 'Nearly half of customers who start verification leave before submitting an identity document [EV-001] [EV-002].',
    whyItMatters: 'Customers cannot activate, and support teams absorb questions that clearer document guidance could prevent.',
    affectedUsers: 'New signups, especially students and freelancers who are unsure which documents and image quality are accepted.',
    recommendation: 'Test clearer document guidance before upload, with examples of accepted documents and photo quality, plus a specific retry path when a submission cannot be read. Deliver the small Android camera fix separately.',
    recommendationType: 'experiment',
    confidence: 'high',
    successMetrics: [
      'Customers who submit a document after starting verification|Baseline: 52.8% (261 of 494)|Target: at least 70%|Review: Weekly for four weeks',
      'Customer contacts about document acceptance and upload help|Baseline: 12 reviewed contacts|Target: 30% fewer|Review: Four weeks after release',
    ],
    risks: [
      'Guidance must make the requirements easier to understand without weakening verification controls.',
      'Measure students and freelancers separately so an overall average does not hide continued friction.',
    ],
    tensions: [
      'An Android camera defect exists, but it affects about 1.8% of onboarding sessions and cannot explain the wider drop-off.',
    ],
    limitations: [
      'Validate the experiment by customer type, document type, device, and acquisition channel before a full rollout.',
    ],
    evidence: [
      {
        source: 'zendesk',
        sourceReference: 'identity-upload contacts',
        finding: 'Twelve reviewed contacts ask which identity documents are accepted or why an uploaded image was rejected.',
        support: 'The recurring questions concern student identification, document eligibility, and unreadable-photo messages.',
        retrievedAt: '2026-08-20T23:59:59Z',
        supportingRecords: supportTicketRecords({
          firstId: 13,
          title: 'I cannot finish identity verification',
          occurredAt: '2026-08-20T12:00:00Z',
          excerpts: [
            'My identity document upload keeps being rejected even after I retake the photo in good light.',
            'I reach the document step but cannot complete verification. The photo looks clear to me.',
            'I have tried my national ID several times and the app still asks me to upload it again.',
            'Verification is blocking me from using my account, and I do not understand what needs to change.',
          ],
        }),
      },
      {
        source: 'posthog',
        sourceReference: 'verification funnel',
        finding: '261 of 494 customers who started verification submitted a document; 247 of those submissions completed verification.',
        support: 'Start-to-submit rate: 52.8%. Submit-to-complete rate: 94.6%. The largest loss occurs before submission.',
        retrievedAt: '2026-08-20T23:59:59Z',
        supportingRecords: [
          metricRecord('metric-kyc-started', 'Verification started', 'Verification starts', 'Customers who entered the verification journey.', { Customers: '494' }),
          metricRecord('metric-kyc-submitted', 'Document submitted', 'Document submissions', 'Just over half of starters submitted a document.', { Customers: '261', 'Start-to-submit': '52.8%' }),
          metricRecord('metric-kyc-completed', 'Verification completed', 'Completed verification', 'Most submitted documents went on to complete.', { Customers: '247', 'Submit-to-complete': '94.6%' }),
        ],
      },
      {
        source: 'jira',
        sourceReference: 'CORE-82',
        finding: 'CORE-82 tracks camera distortion on a small set of Android 12 devices and affects about 1.8% of onboarding sessions.',
        support: 'Priority: Medium. A patch is in staging; the issue represents less than 2% of verification starts.',
        retrievedAt: '2026-08-20T23:59:59Z',
        supportingRecords: [
          issueRecord('CORE-82', 'Camera distortion on selected Android 12 devices', 'The issue affects about 1.8% of onboarding sessions and a patch is in staging.', 'In Progress', 'Medium', '2026-08-20T23:59:59Z'),
        ],
      },
    ],
    inferences: [
      {
        statement: 'Most abandonment happens before a document is submitted, making comprehension and preparation the primary product opportunity.',
        evidenceIndexes: [0, 1],
      },
      {
        statement: 'The device defect should be fixed, but treating it as the main cause would leave the larger problem unresolved.',
        evidenceIndexes: [1, 2],
      },
    ],
    hypotheses: [
      {
        statement: 'Showing accepted-document examples before upload will improve submission among students and freelancers.',
        evidenceIndexes: [0, 1],
      },
    ],
  }),
  inv_p12a_scenario_3: createPreviewBrief({
    investigationId: 'inv_p12a_scenario_3',
    question: 'Why are debit card wallet funding transactions failing at elevated rates?',
    durationSeconds: 96.8,
    scope: { start_time: '2026-08-05T00:00:00Z', end_time: '2026-08-18T23:59:59Z', timezone: 'UTC' },
    problem: 'The evidence does not show elevated transaction failures. Customers are abandoning higher-value funding attempts before submission when the fee becomes clear [EV-001] [EV-002].',
    whyItMatters: 'Misdiagnosing this as an outage would spend engineering time without addressing the pricing surprise that is stopping customers.',
    affectedUsers: 'Customers attempting to fund ₦50,000 or more by debit card; lower-value attempts continue at a much higher rate.',
    recommendation: 'Do not open an incident. Test earlier, clearer fee disclosure for funding of ₦50,000 or more, and explain the total charge before customers enter the final submission step.',
    recommendationType: 'experiment',
    confidence: 'high',
    successMetrics: [
      'High-value funding attempts submitted after starting|Baseline: 18.9% (41 of 217)|Target: at least 35%|Review: Two weeks after the experiment starts',
      'Customers who report being surprised by the funding fee|Baseline: 12 reviewed contacts|Target: 50% fewer|Review: Four weeks after release',
    ],
    risks: [
      'Earlier disclosure may reduce starts while improving informed completion; evaluate completed funding value, not submission rate alone.',
      'Keep fee wording precise and avoid implying that the charge can be waived when it cannot.',
    ],
    tensions: [
      'The question assumes elevated failures, but no wallet-funding failure events or related engineering incident were found in the selected period.',
    ],
    limitations: [
      'Run the disclosure change as an experiment and measure completed funding value, abandonment, and support demand before wider rollout.',
    ],
    evidence: [
      {
        source: 'zendesk',
        sourceReference: 'wallet-funding fee contacts',
        finding: 'Twelve reviewed contacts focus on unexpected debit-card funding fees rather than failed processing.',
        support: 'Customers describe reaching the fee disclosure and deciding not to continue with the funding attempt.',
        retrievedAt: '2026-08-18T23:59:59Z',
        supportingRecords: supportTicketRecords({
          firstId: 25,
          title: 'Card wallet funding was not completed',
          occurredAt: '2026-08-18T12:00:00Z',
          excerpts: [
            'I tried to add money with my debit card but stopped when the final amount was higher than I expected.',
            'The card top-up screen showed an extra charge just before I confirmed, so I did not continue.',
            'I started a card deposit but left before payment because I was not sure what I would be charged.',
            'Please make the total cost clearer before asking me to confirm a card top-up.',
          ],
        }),
      },
      {
        source: 'posthog',
        sourceReference: 'wallet-funding funnel by amount',
        finding: 'Only 41 of 217 attempts of ₦50,000 or more were submitted, compared with 228 of 236 lower-value attempts.',
        support: 'Submission rate: 18.9% at ₦50,000 or more versus 96.6% below ₦50,000. No wallet-funding failure events were recorded.',
        retrievedAt: '2026-08-18T23:59:59Z',
        supportingRecords: [
          metricRecord('metric-wallet-high-value', '₦50,000 or more', 'Higher-value funding attempts', 'Submission drops sharply at and above the fee threshold.', { Started: '217', Submitted: '41', 'Submission rate': '18.9%' }),
          metricRecord('metric-wallet-lower-value', 'Below ₦50,000', 'Lower-value funding attempts', 'Most lower-value attempts continue to submission.', { Started: '236', Submitted: '228', 'Submission rate': '96.6%' }),
          metricRecord('metric-wallet-failures', 'Recorded failures', 'Wallet-funding failures', 'No processing failures were recorded in the selected period.', { Failures: '0' }),
        ],
      },
      {
        source: 'jira',
        sourceReference: 'wallet-funding issue search',
        finding: 'No active wallet-funding incident or reliability defect was found for the selected period.',
        support: 'Engineering issue search returned no wallet-funding outage or processor-failure item.',
        retrievedAt: '2026-08-18T23:59:59Z',
        supportingRecords: [],
      },
    ],
    inferences: [
      {
        statement: 'The sharp amount threshold, fee-focused contacts, and absence of failures point to pricing surprise rather than broken payment processing.',
        evidenceIndexes: [0, 1, 2],
      },
    ],
    hypotheses: [
      {
        statement: 'Showing the fee and total charge earlier will improve informed completion for higher-value funding.',
        evidenceIndexes: [0, 1],
      },
    ],
  }),
  inv_p12a_scenario_4: createPreviewBrief({
    investigationId: 'inv_p12a_scenario_4',
    question: 'What is causing utility bill payment timeouts during peak month-end settlement?',
    durationSeconds: 101.4,
    scope: { start_time: '2026-08-28T08:00:00Z', end_time: '2026-08-31T23:00:00Z', timezone: 'UTC' },
    problem: 'A critical electricity-provider incident is causing most electricity purchases to fail during the month-end period, while other bill categories remain healthy [EV-001] [EV-002] [EV-003].',
    whyItMatters: 'Customers may be debited without receiving a prepaid token, creating urgent household impact, repeat attempts, and reconciliation work.',
    affectedUsers: 'Customers buying prepaid electricity during the selected month-end period; cable, airtime, and internet customers are not showing the same failure pattern.',
    recommendation: 'Treat this as an active electricity-payment incident: warn customers before purchase, pause new electricity attempts if safe fulfilment cannot be confirmed, prioritise affected-payment reconciliation, and escalate restoration with the provider. Keep unaffected bill categories available.',
    recommendationType: 'technical_remediation',
    confidence: 'high',
    successMetrics: [
      'Electricity payment failure rate|Baseline: 75.5% (37 of 49 outcomes)|Target: below 2%|Review: Hourly during the incident and daily for seven days',
      'Customers waiting for an electricity token after debit|Baseline: Establish from reconciliation records|Target: Zero unresolved cases older than 24 hours|Review: Twice daily until cleared',
    ],
    risks: [
      'Do not present an electricity purchase as successful until the token is confirmed.',
      'Do not disable cable, airtime, or internet payments when their completion remains healthy.',
    ],
    tensions: [
      'Aggregate bill performance can hide the severity of the electricity incident because other categories continue to complete normally.',
    ],
    limitations: [
      'Reconciliation records are needed to establish how many debited customers are still waiting for a token.',
    ],
    evidence: [
      {
        source: 'zendesk',
        sourceReference: 'electricity-token contacts',
        finding: 'Twelve reviewed contacts describe electricity payments timing out or a debit occurring before a token arrived.',
        support: 'The complaints are concentrated in prepaid electricity purchases during the month-end period.',
        retrievedAt: '2026-08-31T23:00:00Z',
        supportingRecords: supportTicketRecords({
          firstId: 37,
          title: 'Electricity token has not arrived',
          occurredAt: '2026-08-31T12:00:00Z',
          excerpts: [
            'I paid for electricity and my balance was reduced, but I have not received a token yet.',
            'My electricity purchase timed out at month end. Please confirm whether my payment will be reversed or completed.',
            'The app says the bill payment did not finish, but the money has already left my wallet.',
            'I need a clear update on my electricity token because I cannot top up my meter without it.',
          ],
        }),
      },
      {
        source: 'posthog',
        sourceReference: 'bill-payment outcomes by category',
      finding: 'Electricity recorded 37 failures and 12 completions, while cable, airtime, and internet remained near normal completion.',
      support: 'Electricity failure rate: 75.5%. Cable: 56 completed and 1 failed. Airtime: 69 completed. Internet: 63 completed.',
        retrievedAt: '2026-08-31T23:00:00Z',
        supportingRecords: [
          metricRecord('metric-bills-electricity', 'Electricity', 'Electricity payment outcomes', 'Failures are concentrated in electricity purchases.', { Completed: '12', Failed: '37', 'Failure rate': '75.5%' }),
          metricRecord('metric-bills-cable', 'Cable', 'Cable payment outcomes', 'Cable payments remain near normal completion.', { Completed: '56', Failed: '1' }),
          metricRecord('metric-bills-airtime', 'Airtime', 'Airtime payment outcomes', 'No matching failure spike was observed.', { Completed: '69' }),
          metricRecord('metric-bills-internet', 'Internet', 'Internet payment outcomes', 'No matching failure spike was observed.', { Completed: '63' }),
        ],
      },
      {
        source: 'jira',
        sourceReference: 'PAY-134',
        finding: 'PAY-134 is a Critical incident confirming disruption at the electricity fulfilment provider.',
        support: 'Status: In Progress. The provider has acknowledged the incident and the delivery team is awaiting restoration timing.',
        retrievedAt: '2026-08-31T23:00:00Z',
        supportingRecords: [
          issueRecord('PAY-134', 'Electricity token purchases timing out at month end', 'The provider has acknowledged the incident and restoration is being escalated.', 'In Progress', 'Critical', '2026-08-31T23:00:00Z'),
        ],
      },
    ],
    inferences: [
      {
        statement: 'The converging customer, outcome, and delivery evidence supports an electricity-specific provider incident rather than a platform-wide bill-payment problem.',
        evidenceIndexes: [0, 1, 2],
      },
    ],
    hypotheses: [
      {
        statement: 'A pre-purchase warning and temporary pause will reduce duplicate attempts and new reconciliation cases while restoration is underway.',
        evidenceIndexes: [0, 1, 2],
      },
    ],
  }),
};

export const SAMPLE_INVESTIGATION_IDS = Object.keys(SAMPLE_SCENARIOS);

export function isSampleScenarioId(id: string | undefined | null): boolean {
  return Boolean(id && SAMPLE_SCENARIOS[id]);
}

export function getSampleScenario(id: string): InvestigationDetailResponse | null {
  return SAMPLE_SCENARIOS[id] ?? null;
}

/** @deprecated Use REFERENCE_SCENARIO_1. Retained for internal test compatibility. */
export const VERIFIED_SCENARIO_1 = REFERENCE_SCENARIO_1;
