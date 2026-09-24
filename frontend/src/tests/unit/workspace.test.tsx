import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WorkspaceHeader } from '@/components/workspace/WorkspaceHeader';
import { RecommendationPanel } from '@/components/workspace/RecommendationPanel';
import { ExecutiveFinding } from '@/components/workspace/ExecutiveFinding';
import { EpistemicDeck } from '@/components/workspace/EpistemicDeck';
import { TensionsBanner } from '@/components/workspace/TensionsBanner';
import { LimitationsBanner } from '@/components/workspace/LimitationsBanner';
import { CriticReviewSection } from '@/components/workspace/CriticReviewSection';
import { EvidenceLedgerDrawer } from '@/components/workspace/EvidenceLedgerDrawer';
import { VERIFIED_SCENARIO_1 } from '@/lib/sample-scenarios';
import { InvestigationWorkspaceView } from '@/app/investigations/[id]/page';
import { apiClient, ApiError } from '@/lib/api-client';

vi.mock('next/navigation', () => ({
  usePathname: () => '/investigations/inv_test_123',
  useRouter: () => ({ push: vi.fn() }),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('Investigation Workspace Components', () => {
  describe('WorkspaceHeader', () => {
    it('renders query title, metadata strip, and triggers ledger toggle', () => {
      const onToggleLedger = vi.fn();
      render(
        <WorkspaceHeader
          investigationId="inv_test_123"
          userQuery="Why did checkout drop?"
          status="completed"
          durationSeconds={109.5}
          evidenceCount={8}
          onToggleLedger={onToggleLedger}
          isLedgerOpen={false}
        />
      );

      expect(screen.getByRole('heading', { name: /why did checkout drop\?/i })).toBeInTheDocument();
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByText('109.5s')).toBeInTheDocument();
      // Telemetry (LLM calls/cost) should NOT appear in the workspace header
      expect(screen.queryByText(/LLM/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Provider Cost/i)).not.toBeInTheDocument();

      const ledgerBtn = screen.getByRole('button', { name: /view evidence from/i });
      expect(ledgerBtn).toBeInTheDocument();
      fireEvent.click(ledgerBtn);
      expect(onToggleLedger).toHaveBeenCalledTimes(1);
    });

    it('formats the investigation period deterministically in UTC', () => {
      render(
        <WorkspaceHeader
          investigationId="inv_test_123"
          userQuery="Why did checkout drop?"
          status="completed"
          evidenceCount={3}
          scope={{
            start_time: '2026-08-05T00:00:00Z',
            end_time: '2026-08-19T00:00:00Z',
          }}
          onToggleLedger={vi.fn()}
        />
      );

      expect(screen.getByText('Period: 5 Aug 2026 to 19 Aug 2026')).toBeInTheDocument();
    });

    it('does not expose a private-link control', () => {
      render(
        <WorkspaceHeader
          investigationId="inv_test_123"
          userQuery="Why did checkout drop?"
          status="completed"
          evidenceCount={3}
          onToggleLedger={vi.fn()}
        />
      );

      expect(screen.queryByRole('button', { name: /copy private link/i })).not.toBeInTheDocument();
    });
  });

  describe('RecommendationPanel', () => {
    it('renders elevated recommendation, confidence, and target metrics', () => {
      const onSelectCitation = vi.fn();
      render(
        <RecommendationPanel
          recommendation={VERIFIED_SCENARIO_1.recommendation}
          onSelectCitation={onSelectCitation}
        />
      );

      expect(screen.getByRole('heading', { name: 'Recommendation' })).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
      expect(
        screen.getByText(/Prioritise transfer-status synchronisation for Bank A and Bank B/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/How success will be measured/i)).toBeInTheDocument();
      expect(screen.getByText(/Decision watch-outs/i)).toBeInTheDocument();
    });
  });

  describe('ExecutiveFinding', () => {
    it('renders problem statement, why it matters, and affected users', () => {
      render(
        <ExecutiveFinding
          problemStatement={VERIFIED_SCENARIO_1.recommendation.problem_statement}
          whyItMatters={VERIFIED_SCENARIO_1.recommendation.why_it_matters}
          affectedUsers={VERIFIED_SCENARIO_1.recommendation.affected_users}
        />
      );

      expect(screen.getByText(/Executive Finding/i)).toBeInTheDocument();
      expect(screen.getByText(/The gap between money movement and the status customers see/i)).toBeInTheDocument();
      expect(screen.getByText(/Customers sending transfers to Bank A and Bank B/i)).toBeInTheDocument();
      expect(screen.getByText('[EV-001]')).toBeInTheDocument();
      expect(screen.getByText('[EV-002]')).toBeInTheDocument();
    });
  });

  describe('EpistemicDeck', () => {
    it('renders Facts, Inferences, and Hypotheses categories with interactive citations', () => {
      const onSelectCitation = vi.fn();
      render(
        <EpistemicDeck
          facts={VERIFIED_SCENARIO_1.recommendation.factual_observations}
          inferences={VERIFIED_SCENARIO_1.recommendation.inferences}
          hypotheses={VERIFIED_SCENARIO_1.recommendation.hypotheses}
          onSelectCitation={onSelectCitation}
        />
      );

      expect(screen.getByText('What we know')).toBeInTheDocument();
      expect(screen.getByText('What it suggests')).toBeInTheDocument();
      expect(screen.getByText('Possible explanations to test')).toBeInTheDocument();

      // Click on a citation pill
      const citationPills = screen.getAllByRole('button', { name: /view evidence record/i });
      expect(citationPills.length).toBeGreaterThanOrEqual(3);
      fireEvent.click(citationPills[0]);
      expect(onSelectCitation).toHaveBeenCalled();
    });
  });

  describe('TensionsBanner & LimitationsBanner', () => {
    it('renders tensions callout banner with discrepancy description', () => {
      render(
        <TensionsBanner
          tensions={VERIFIED_SCENARIO_1.recommendation.conflicting_evidence}
        />
      );
      expect(
        screen.getByRole('heading', { name: /where the evidence differs/i })
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          /Customers describe these transfers as failed, while the observed data contains 718 completions and only 10 failures/i
        )
      ).toBeInTheDocument();
    });

    it('renders limitations banner with data gaps', () => {
      render(
        <LimitationsBanner
          limitations={VERIFIED_SCENARIO_1.recommendation.disclosed_limitations}
        />
      );
      expect(
        screen.getByRole('heading', { name: /what still needs validation/i })
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Measure confirmation time after the fix and verify that Bank A and Bank B/i)
      ).toBeInTheDocument();
    });
  });

  describe('CriticReviewSection', () => {
    it('renders the customer-facing quality-check status without internal critique', () => {
      render(<CriticReviewSection criticReview={VERIFIED_SCENARIO_1.critic_review} />);

      expect(screen.getByText('QUALITY CHECKED')).toBeInTheDocument();
      expect(screen.getByText(/checked for evidence and an appropriately confident decision/i)).toBeInTheDocument();
      expect(screen.queryByText(/adversarial critic/i)).not.toBeInTheDocument();
    });
  });

  describe('EvidenceLedgerDrawer', () => {
    it('renders evidence cards, source filter tabs, and handles close via Esc', () => {
      const onClose = vi.fn();
      render(
        <EvidenceLedgerDrawer
          isOpen={true}
          onClose={onClose}
          evidenceLedger={VERIFIED_SCENARIO_1.evidence_ledger}
        />
      );

      expect(screen.getByRole('dialog', { name: /evidence ledger drawer/i })).toBeInTheDocument();
      expect(screen.getByText('All sources')).toBeInTheDocument();
      expect(screen.getByText('Customer support')).toBeInTheDocument();
      expect(screen.getByText('Product analytics')).toBeInTheDocument();
      expect(screen.getByText('Engineering')).toBeInTheDocument();
      expect(screen.getByText('Evidence from 3 sources')).toBeInTheDocument();

      // Card contents
      expect(screen.getByText('[EV-001]')).toBeInTheDocument();
      expect(screen.getByText('[EV-002]')).toBeInTheDocument();
      expect(screen.getByText('[EV-003]')).toBeInTheDocument();
      expect(screen.queryByText(/PAY-117/i)).not.toBeInTheDocument();

      // Filter by Zendesk
      fireEvent.click(screen.getByText('Customer support'));
      expect(screen.getByText('[EV-001]')).toBeInTheDocument();
      expect(screen.queryByText('[EV-002]')).not.toBeInTheDocument();

      // Close via Escape key
      fireEvent.keyDown(window, { key: 'Escape' });
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('expands source summaries and searches the underlying audit records', () => {
      render(
        <EvidenceLedgerDrawer
          isOpen={true}
          onClose={vi.fn()}
          evidenceLedger={VERIFIED_SCENARIO_1.evidence_ledger}
        />
      );

      fireEvent.click(screen.getAllByRole('button', { name: /view records/i })[0]);
      expect(screen.getByText('Customer conversation #1')).toBeInTheDocument();
      expect(screen.getByText('Customer conversation #12')).toBeInTheDocument();

      fireEvent.change(screen.getByPlaceholderText(/search tickets/i), {
        target: { value: 'Customer conversation #6' },
      });

      expect(screen.getByText('Customer conversation #6')).toBeInTheDocument();
      expect(screen.queryByText('Customer conversation #1')).not.toBeInTheDocument();
      expect(screen.queryByText('[EV-002]')).not.toBeInTheDocument();
    });

    it('filters cards by search query input', () => {
      render(
        <EvidenceLedgerDrawer
          isOpen={true}
          onClose={vi.fn()}
          evidenceLedger={VERIFIED_SCENARIO_1.evidence_ledger}
        />
      );

      const searchInput = screen.getByPlaceholderText(/search tickets/i);
      fireEvent.change(searchInput, { target: { value: 'PAY-117' } });

      expect(screen.getByText('[EV-003]')).toBeInTheDocument();
      expect(screen.queryByText('[EV-001]')).not.toBeInTheDocument();
    });

    it('counts repeated records once and presents each source once', () => {
      const jiraEvidence = VERIFIED_SCENARIO_1.evidence_ledger['EV-003'];
      render(
        <EvidenceLedgerDrawer
          isOpen={true}
          onClose={vi.fn()}
          evidenceLedger={{
            'jira-search-1': { ...jiraEvidence, ledger_entry_id: 'jira-search-1' },
            'jira-search-2': { ...jiraEvidence, ledger_entry_id: 'jira-search-2' },
            'jira-search-3': { ...jiraEvidence, ledger_entry_id: 'jira-search-3' },
          }}
        />
      );

      expect(screen.getByText('Evidence from 1 source')).toBeInTheDocument();
      expect(screen.getByText('1 unique engineering issue')).toBeInTheDocument();
      expect(screen.getAllByText('Engineering')).toHaveLength(1);
    });
  });

  describe('InvestigationWorkspacePage Assembly & States', () => {
    beforeEach(() => {
      vi.restoreAllMocks();
    });

    it('renders curated Scenario 1 sample when backend returns 404 for inv_p12a_scenario_1', async () => {
      vi.spyOn(apiClient, 'getInvestigationResult').mockRejectedValue(
        new ApiError('Not found', 404)
      );

      render(<InvestigationWorkspaceView investigationId="inv_p12a_scenario_1" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(
          screen.getByRole('heading', {
            name: /why are customers reporting a surge in failed transfers this week\?/i,
          })
        ).toBeInTheDocument();
      });

      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Recommendation' })).toBeInTheDocument();
      expect(screen.getByText(/Executive Finding/i)).toBeInTheDocument();
      expect(screen.getByText('What we know')).toBeInTheDocument();
    });

    it('renders honest Not Found state when arbitrary ID returns 404', async () => {
      vi.spyOn(apiClient, 'getInvestigationStatus').mockRejectedValue(
        new ApiError('Investigation not found', 404)
      );

      render(<InvestigationWorkspaceView investigationId="inv_unknown_999" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /investigation not found/i })).toBeInTheDocument();
      });

      expect(
        screen.getByRole('link', { name: /back to investigations/i })
      ).toBeInTheDocument();
    });

    it('renders ErrorState when backend returns 500 error', async () => {
      vi.spyOn(apiClient, 'getInvestigationStatus').mockRejectedValue(
        new ApiError('Internal Server Error', 500)
      );

      render(<InvestigationWorkspaceView investigationId="inv_err_500" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /investigation failed/i })).toBeInTheDocument();
      });
      expect(screen.getByRole('button', { name: /retry investigation/i })).toBeInTheDocument();
      expect(
        screen.getByRole('link', { name: /back to investigations/i })
      ).toBeInTheDocument();
    });
  });
});
