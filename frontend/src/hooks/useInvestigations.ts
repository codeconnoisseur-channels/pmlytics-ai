'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { getSampleScenario, isSampleScenarioId } from '@/lib/sample-scenarios';
import type {
  InvestigationCreateRequest,
  InvestigationSummaryResponse,
  InvestigationStatusResponse,
  InvestigationDetailResponse,
  HealthResponse,
} from '@/types/domain';

export const queryKeys = {
  recentInvestigations: ['investigations', 'recent'] as const,
  investigationStatus: (id: string) => ['investigations', id, 'status'] as const,
  investigationResult: (id: string) => ['investigations', id, 'result'] as const,
  health: ['system', 'health'] as const,
};

/**
 * Query recent investigations authoritatively from backend memory.
 * Dynamically polls while any investigation is actively running.
 */
export function useRecentInvestigations(enabled: boolean = true) {
  return useQuery<InvestigationStatusResponse[], Error>({
    queryKey: queryKeys.recentInvestigations,
    queryFn: () => apiClient.listRecentInvestigations(),
    enabled,
    staleTime: 2 * 1000,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return false;
      const hasActive = data.some(
        (inv) => inv.status !== 'completed' && inv.status !== 'partial' && inv.status !== 'failed' && inv.status !== 'cancelled' && inv.status !== 'recovery_required'
      );
      return hasActive ? 1500 : false;
    },
  });
}

/**
 * Query status for an individual investigation.
 */
export function useInvestigationStatus(id: string | undefined | null, enabled: boolean = true) {
  return useQuery<InvestigationStatusResponse, Error>({
    queryKey: queryKeys.investigationStatus(id || ''),
    queryFn: () => apiClient.getInvestigationStatus(id!),
    enabled: Boolean(id) && enabled,
    staleTime: 2 * 1000,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data) return 1500;
      return data.status === 'completed' || data.status === 'partial' || data.status === 'failed' || data.status === 'cancelled' || data.status === 'recovery_required'
        ? false
        : 1500;
    },
  });
}

/**
 * Query full synthesized result for an investigation.
 */
export function useInvestigationResult(
  id: string | undefined | null,
  enabled: boolean = true,
  retryOption?: boolean | ((failureCount: number, error: any) => boolean)
) {
  return useQuery<InvestigationDetailResponse | null, Error>({
    queryKey: queryKeys.investigationResult(id || ''),
    queryFn: async () => {
      try {
        return await apiClient.getInvestigationResult(id!);
      } catch (err: any) {
        // Gracefully handle in-progress state (HTTP 409 Conflict):
        // The investigation is still running, so result is not ready yet.
        // Returning null prevents React Query from treating this as a fatal failure.
        if (err?.status === 409) {
          return null;
        }
        // Fallback boundary: local, curated preview briefs only when backend returns 404.
        if (isSampleScenarioId(id) && err?.status === 404) {
          const sample = getSampleScenario(id!);
          if (sample) return sample;
        }
        throw err;
      }
    },
    enabled: Boolean(id) && enabled,
    // A 409 is represented as `null` while an investigation is active. That
    // placeholder must not be cached forever, otherwise returning to this
    // workspace keeps showing an old "not ready" result after completion.
    staleTime: (query) => (query.state.data ? Infinity : 0),
    retry:
      retryOption !== undefined
        ? retryOption
        : (failureCount, error: any) => {
            if (error?.status === 409 || error?.status === 404) return false;
            return false;
          },
  });
}

/**
 * Query system dependencies readiness.
 */
export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: queryKeys.health,
    queryFn: () => apiClient.getHealth(),
    staleTime: 60 * 1000,
  });
}

/**
 * Mutation to create a new product investigation.
 */
export function useCreateInvestigation() {
  const queryClient = useQueryClient();

  return useMutation<InvestigationSummaryResponse, Error, InvestigationCreateRequest>({
    mutationFn: (data) => apiClient.createInvestigation(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.recentInvestigations });
    },
  });
}

/**
 * Mutation to explicitly cancel an active investigation.
 */
export function useCancelInvestigation() {
  const queryClient = useQueryClient();

  return useMutation<InvestigationStatusResponse, Error, string>({
    mutationFn: (id: string) => apiClient.cancelInvestigation(id),
    onSuccess: (data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.recentInvestigations });
      queryClient.invalidateQueries({ queryKey: queryKeys.investigationStatus(id) });
    },
  });
}

export function useRecoverInvestigation() {
  const queryClient = useQueryClient();
  return useMutation<InvestigationStatusResponse, Error, string>({
    mutationFn: (id: string) => apiClient.recoverInvestigation(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.recentInvestigations });
      queryClient.invalidateQueries({ queryKey: queryKeys.investigationStatus(id) });
    },
  });
}

export function useRetryInvestigation() {
  const queryClient = useQueryClient();
  return useMutation<InvestigationSummaryResponse, Error, string>({
    mutationFn: (id: string) => apiClient.retryInvestigation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.recentInvestigations });
    },
  });
}

export function useRenameInvestigation() {
  const queryClient = useQueryClient();
  return useMutation<
    InvestigationStatusResponse,
    Error,
    { id: string; displayName: string }
  >({
    mutationFn: ({ id, displayName }) => apiClient.renameInvestigation(id, displayName),
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.recentInvestigations });
      queryClient.invalidateQueries({ queryKey: queryKeys.investigationStatus(id) });
    },
  });
}

export function useDeleteInvestigation() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (id: string) => apiClient.deleteInvestigation(id),
    onSuccess: (_data, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.investigationStatus(id) });
      queryClient.removeQueries({ queryKey: queryKeys.investigationResult(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.recentInvestigations });
    },
  });
}
