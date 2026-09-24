import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { InvestigationWorkspaceView } from '@/app/investigations/[id]/page';
import { apiClient } from '@/lib/api-client';

vi.mock('next/navigation', () => ({
  usePathname: () => '/investigations/inv_p12a_scenario_4',
  useRouter: () => ({ push: vi.fn() }),
}));

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('Reference scenario routes', () => {
  it('render synchronously as completed briefs without querying the live investigation APIs', () => {
    const statusSpy = vi.spyOn(apiClient, 'getInvestigationStatus');
    const resultSpy = vi.spyOn(apiClient, 'getInvestigationResult');

    render(<InvestigationWorkspaceView investigationId="inv_p12a_scenario_4" />, {
      wrapper: createWrapper(),
    });

    expect(screen.getByRole('heading', { name: /utility bill payment timeouts/i })).toBeInTheDocument();
    expect(screen.queryByText('Investigation in progress')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /stop investigation/i })).not.toBeInTheDocument();
    expect(statusSpy).not.toHaveBeenCalled();
    expect(resultSpy).not.toHaveBeenCalled();
  });
});
