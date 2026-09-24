import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  InvestigationComposer,
  InvestigationList,
  InvestigationListItem,
  LaunchpadEmptyState,
  LaunchpadErrorState,
} from '@/components/launchpad';
import InvestigationsPage from '@/app/investigations/page';
import * as useInvestigationsModule from '@/hooks/useInvestigations';
import { ApiError } from '@/lib/api-client';

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/investigations',
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('Investigation Launchpad Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('InvestigationComposer', () => {
    it('renders heading, explanatory copy, textarea, counter, and submit button', () => {
      render(
        <InvestigationComposer
          query=""
          onChangeQuery={vi.fn()}
          onSubmit={vi.fn()}
          isSubmitting={false}
        />
      );

      expect(screen.getByRole('heading', { name: /what would you like to investigate/i })).toBeInTheDocument();
      expect(
        screen.getByText(/ask a product question\. pmlytics ai will examine/i)
      ).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/why did checkout conversion drop/i)).toBeInTheDocument();
      expect(screen.getByText('0 / 2000')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start investigation/i })).toBeDisabled();
    });

    it('enforces validation: rejects empty or whitespace-only input', () => {
      const { rerender } = render(
        <InvestigationComposer
          query="   "
          onChangeQuery={vi.fn()}
          onSubmit={vi.fn()}
          isSubmitting={false}
        />
      );

      // Whitespace only is disabled
      expect(screen.getByRole('button', { name: /start investigation/i })).toBeDisabled();

      // Valid text activates button
      rerender(
        <InvestigationComposer
          query="Why did Android checkout drop?"
          onChangeQuery={vi.fn()}
          onSubmit={vi.fn()}
          isSubmitting={false}
        />
      );
      expect(screen.getByRole('button', { name: /start investigation/i })).not.toBeDisabled();
    });

    it('submits on button click and on Ctrl+Enter keyboard shortcut', () => {
      const onSubmit = vi.fn();
      render(
        <InvestigationComposer
          query="Why did Android checkout drop?"
          onChangeQuery={vi.fn()}
          onSubmit={onSubmit}
          isSubmitting={false}
        />
      );

      const textarea = screen.getByPlaceholderText(/why did checkout conversion drop/i);
      const submitBtn = screen.getByRole('button', { name: /start investigation/i });

      // Click submit
      fireEvent.click(submitBtn);
      expect(onSubmit).toHaveBeenCalledTimes(1);

      // Ctrl+Enter submit
      fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: true });
      expect(onSubmit).toHaveBeenCalledTimes(2);

      // Plain Enter does NOT submit (multiline preservation)
      fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: false });
      expect(onSubmit).toHaveBeenCalledTimes(2);
    });

    it('prevents duplicate submission when isSubmitting is true', () => {
      const onSubmit = vi.fn();
      render(
        <InvestigationComposer
          query="Why did Android checkout drop?"
          onChangeQuery={vi.fn()}
          onSubmit={onSubmit}
          isSubmitting={true}
        />
      );

      const textarea = screen.getByPlaceholderText(/why did checkout conversion drop/i);
      const submitBtn = screen.getByRole('button', { name: /starting/i });

      expect(textarea).toBeDisabled();
      expect(submitBtn).toBeDisabled();
      expect(screen.getByText(/starting…/i)).toBeInTheDocument();

      fireEvent.click(submitBtn);
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('renders error alert and calls onClearError when dismissed', () => {
      const onClearError = vi.fn();
      render(
        <InvestigationComposer
          query="Test query"
          onChangeQuery={vi.fn()}
          onSubmit={vi.fn()}
          isSubmitting={false}
          error="Network error occurred"
          onClearError={onClearError}
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Network error occurred')).toBeInTheDocument();

      const dismissBtn = screen.getByRole('button', { name: /dismiss error/i });
      fireEvent.click(dismissBtn);
      expect(onClearError).toHaveBeenCalledTimes(1);
    });
  });

  describe('InvestigationListItem & Status Rendering', () => {
    it('renders completed status with pass badge variant', () => {
      const item = {
        investigation_id: 'inv_test_completed',
        user_query: 'Why did conversion drop?',
        status: 'completed',
        current_stage: 'Investigation complete',
        active_agent: null,
        revision_count: 1,
        elapsed_seconds: 120.4,
        created_at: '2026-09-18T08:00:00Z',
        completed_at: '2026-09-18T08:02:00Z',
        error: null,
      };

      render(<InvestigationListItem investigation={item} />, { wrapper: createWrapper() });

      expect(screen.getByText('completed')).toBeInTheDocument();
      expect(screen.getByText('Why did conversion drop?')).toBeInTheDocument();
      expect(screen.getByText('120.4s')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /view investigation: why did conversion drop/i })).toHaveAttribute(
        'href',
        '/investigations/inv_test_completed'
      );
    });

    it('renders in-flight active status with stage indicator', () => {
      const item = {
        investigation_id: 'inv_test_active',
        user_query: 'Why did payments fail?',
        status: 'gathering_evidence',
        current_stage: 'Querying PostHog and Zendesk',
        active_agent: 'specialists',
        revision_count: 0,
        elapsed_seconds: 45.2,
        created_at: '2026-09-18T08:05:00Z',
        completed_at: null,
        error: null,
      };

      render(<InvestigationListItem investigation={item} />, { wrapper: createWrapper() });

      expect(screen.getByText('gathering_evidence')).toBeInTheDocument();
      expect(screen.getByText('Querying PostHog and Zendesk')).toBeInTheDocument();
      expect(screen.getByText('45.2s')).toBeInTheDocument();
    });
  });

  describe('InvestigationList States', () => {
    it('renders loading skeleton when isLoading=true', () => {
      render(
        <InvestigationList
          investigations={undefined}
          isLoading={true}
          error={null}
        />
      );

      expect(screen.getByRole('status', { name: /loading recent investigations/i })).toBeInTheDocument();
    });

    it('renders empty state when investigations list is empty', () => {
      const onStart = vi.fn();
      render(
        <InvestigationList
          investigations={[]}
          isLoading={false}
          error={null}
          onStartInquiry={onStart}
        />
      );

      expect(screen.getByRole('heading', { name: /no recent investigations/i })).toBeInTheDocument();
      const startBtn = screen.getByRole('button', { name: /start an investigation/i });
      fireEvent.click(startBtn);
      expect(onStart).toHaveBeenCalledTimes(1);
    });

    it('renders error state with retry button', () => {
      const onRetry = vi.fn();
      render(
        <InvestigationList
          investigations={undefined}
          isLoading={false}
          error={new Error('Connection refused')}
          onRetry={onRetry}
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/connection refused/i)).toBeInTheDocument();
      const retryBtn = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryBtn);
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Full InvestigationsPage Integration Flow', () => {
    it('submits a new query, triggers mutation, and navigates to investigation workspace', async () => {
      const mockMutateAsync = vi.fn().mockResolvedValue({
        investigation_id: 'inv_new_test_12345',
        status: 'pending',
        created_at: '2026-09-18T08:10:00Z',
        status_url: '/api/v1/investigations/inv_new_test_12345',
        events_url: '/api/v1/investigations/inv_new_test_12345/events',
        result_url: '/api/v1/investigations/inv_new_test_12345/result',
      });

      vi.spyOn(useInvestigationsModule, 'useRecentInvestigations').mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      vi.spyOn(useInvestigationsModule, 'useCreateInvestigation').mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
      } as any);

      render(<InvestigationsPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('heading', { name: /what would you like to investigate/i })).toBeInTheDocument();

      // Enter a product question directly.
      const textarea = screen.getByPlaceholderText(/why did checkout conversion drop/i);
      fireEvent.change(textarea, {
        target: { value: 'Why did user verification drop off at the identity upload step for new signups?' },
      });

      // Click submit
      const submitBtn = screen.getByRole('button', { name: /start investigation/i });
      expect(submitBtn).not.toBeDisabled();
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          user_query:
            'Why did user verification drop off at the identity upload step for new signups?',
        });
        expect(mockPush).toHaveBeenCalledWith('/investigations/inv_new_test_12345');
      });
    });

    it('handles API submission errors cleanly and displays actionable message', async () => {
      const mockMutateAsync = vi.fn().mockRejectedValue(
        new ApiError('Validation error', 400, {
          detail: 'user_query length (2001) exceeds the maximum allowed length of 2000 characters.',
        })
      );

      vi.spyOn(useInvestigationsModule, 'useRecentInvestigations').mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      } as any);

      vi.spyOn(useInvestigationsModule, 'useCreateInvestigation').mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
      } as any);

      render(<InvestigationsPage />, { wrapper: createWrapper() });

      const textarea = screen.getByPlaceholderText(/why did checkout conversion drop/i);
      fireEvent.change(textarea, { target: { value: 'Valid question text' } });

      const submitBtn = screen.getByRole('button', { name: /start investigation/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(
          screen.getByText(/exceeds the maximum allowed length of 2000 characters/i)
        ).toBeInTheDocument();
      });
    });
  });
});
