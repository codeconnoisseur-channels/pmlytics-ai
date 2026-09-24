import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useInvestigationResult } from '@/hooks/useInvestigations';
import { apiClient, ApiError } from '@/lib/api-client';
import { SAMPLE_INVESTIGATION_ID, VERIFIED_SCENARIO_1 } from '@/lib/sample-scenarios';

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

describe('Sample Data Fallback Boundary', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('1. sample ID + backend 200 returns backend data (not sample override)', async () => {
    const backendData: any = {
      investigation_id: SAMPLE_INVESTIGATION_ID,
      user_query: 'Backend live query',
      status: 'completed',
      duration_seconds: 42,
      recommendation: {
        problem_statement: 'Live backend result',
      },
    };

    vi.spyOn(apiClient, 'getInvestigationResult').mockResolvedValue(backendData);

    const { result } = renderHook(
      () => useInvestigationResult(SAMPLE_INVESTIGATION_ID, true, false),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(backendData);
    expect(result.current.data?.user_query).toBe('Backend live query');
  });

  it('2. sample ID + backend 404 uses curated VERIFIED_SCENARIO_1', async () => {
    vi.spyOn(apiClient, 'getInvestigationResult').mockRejectedValue(
      new ApiError('Investigation not found', 404, { detail: 'Not found in process memory' })
    );

    const { result } = renderHook(
      () => useInvestigationResult(SAMPLE_INVESTIGATION_ID, true, false),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(VERIFIED_SCENARIO_1);
    expect(result.current.data?.investigation_id).toBe(SAMPLE_INVESTIGATION_ID);
    expect(result.current.data?.recommendation.problem_statement).toContain('Customers');
    expect(result.current.data?.recommendation.problem_statement).not.toContain('PAY-117');
  });

  it('3. sample ID + backend 500 does NOT use curated sample (throws error)', async () => {
    const serverError = new ApiError('Internal Server Error', 500, {
      detail: 'Model invocation failure',
    });
    vi.spyOn(apiClient, 'getInvestigationResult').mockRejectedValue(serverError);

    const { result } = renderHook(
      () => useInvestigationResult(SAMPLE_INVESTIGATION_ID, true, false),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toBe(serverError);
  });

  it('4. sample ID + network/timeout failure does NOT use curated sample', async () => {
    const networkError = new TypeError('Failed to fetch (network disconnected)');
    vi.spyOn(apiClient, 'getInvestigationResult').mockRejectedValue(networkError);

    const { result } = renderHook(
      () => useInvestigationResult(SAMPLE_INVESTIGATION_ID, true, false),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toBe(networkError);
  });

  it('5. arbitrary ID + backend 404 does NOT use curated sample (throws 404 error)', async () => {
    const notFoundError = new ApiError('Investigation not found', 404, {
      detail: 'inv_other_999 not found',
    });
    vi.spyOn(apiClient, 'getInvestigationResult').mockRejectedValue(notFoundError);

    const { result } = renderHook(
      () => useInvestigationResult('inv_other_999', true, false),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
    expect(result.current.error).toBe(notFoundError);
  });
});
