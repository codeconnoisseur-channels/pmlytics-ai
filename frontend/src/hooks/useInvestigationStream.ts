'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';

export interface UseInvestigationStreamOptions {
  enabled?: boolean;
  onCompleted?: () => void;
  onError?: (err: Error) => void;
  pollIntervalMs?: number;
  maxConsecutiveErrors?: number;
}

export interface StreamState {
  status: 'idle' | 'connecting' | 'streaming' | 'polling' | 'completed' | 'partial' | 'failed' | 'cancelled' | 'recovery_required';
  stage: string;
  activeAgent: string | null;
  elapsedSeconds: number;
  revisionCount: number;
  error: string | null;
  isFallbackPolling: boolean;
  isReconnecting: boolean;
  progressStep: number;
  milestone: string | null;
}

const INITIAL_STREAM_STATE: StreamState = {
  status: 'idle',
  stage: 'pending',
  activeAgent: null,
  elapsedSeconds: 0,
  revisionCount: 0,
  error: null,
  isFallbackPolling: false,
  isReconnecting: false,
  progressStep: 0,
  milestone: null,
};

const TERMINAL_LIFECYCLE = new Set(['completed', 'partial', 'failed', 'cancelled', 'recovery_required']);
const SSE_EVENT_NAMES = ['snapshot', 'progress', 'complete', 'partial', 'failed', 'cancelled', 'recovery_required'] as const;

const STAGE_PROGRESS_STEPS: Record<string, number> = {
  pending: 0,
  planning: 1,
  gathering_evidence: 2,
  synthesizing: 3,
  reviewing: 4,
  revising: 4,
  completing: 5,
  completed: 6,
  partial: 6,
};

function progressStepForStage(stage: string): number {
  return STAGE_PROGRESS_STEPS[stage.toLowerCase()] ?? 0;
}

type RawProgressPayload = {
  event?: string;
  status?: string;
  stage?: string;
  current_stage?: string;
  message?: string;
  active_agent?: string | null;
  milestone?: string;
  elapsed_seconds?: number;
  revision_count?: number;
  error?: string | null;
};

function parseProgressPayload(raw: RawProgressPayload) {
  const lifecycleStatus = raw.status ?? '';
  const stage =
    raw.stage ??
    (TERMINAL_LIFECYCLE.has(lifecycleStatus) ? lifecycleStatus : lifecycleStatus || 'pending');

  const isTerminalCompleted =
    lifecycleStatus === 'completed' || raw.event === 'complete' || stage === 'completed';
  const isTerminalPartial = lifecycleStatus === 'partial' || raw.event === 'partial' || stage === 'partial';
  const isTerminalFailed = lifecycleStatus === 'failed' || raw.event === 'failed' || stage === 'failed';
  const isTerminalCancelled =
    lifecycleStatus === 'cancelled' || raw.event === 'cancelled' || stage === 'cancelled';
  const isRecoveryRequired =
    lifecycleStatus === 'recovery_required' || raw.event === 'recovery_required';

  return {
    streamStatus: isTerminalCompleted
      ? ('completed' as const)
      : isTerminalPartial
        ? ('partial' as const)
      : isTerminalFailed
        ? ('failed' as const)
        : isTerminalCancelled
          ? ('cancelled' as const)
          : isRecoveryRequired
            ? ('recovery_required' as const)
          : ('streaming' as const),
    stage,
    activeAgent: raw.active_agent ?? null,
    elapsedSeconds: raw.elapsed_seconds,
    revisionCount: raw.revision_count,
    error: raw.error ?? null,
    milestone: raw.milestone ?? raw.message ?? raw.current_stage ?? null,
    isTerminal: isTerminalCompleted || isTerminalPartial || isTerminalFailed || isTerminalCancelled || isRecoveryRequired,
    terminalKind: isTerminalCompleted
      ? ('completed' as const)
      : isTerminalPartial
        ? ('partial' as const)
      : isTerminalFailed
        ? ('failed' as const)
        : isTerminalCancelled
          ? ('cancelled' as const)
          : isRecoveryRequired
            ? ('recovery_required' as const)
          : null,
  };
}

export function useInvestigationStream(
  investigationId: string | undefined | null,
  options: UseInvestigationStreamOptions = {}
) {
  const {
    enabled = true,
    onCompleted,
    onError,
    pollIntervalMs = 3000,
    maxConsecutiveErrors = 3,
  } = options;

  const [state, setState] = useState<StreamState>(INITIAL_STREAM_STATE);

  const streamAbortRef = useRef<AbortController | null>(null);
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const consecutiveErrorsRef = useRef<number>(0);
  const isMountedRef = useRef<boolean>(true);
  const startTimeRef = useRef<number>(Date.now());
  const terminalRef = useRef<boolean>(false);
  const onCompletedRef = useRef(onCompleted);
  const onErrorRef = useRef(onError);

  onCompletedRef.current = onCompleted;
  onErrorRef.current = onError;

  const cleanup = useCallback(() => {
    if (streamAbortRef.current) {
      streamAbortRef.current.abort();
      streamAbortRef.current = null;
    }
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const markTerminal = useCallback(
    (kind: 'completed' | 'partial' | 'failed' | 'cancelled' | 'recovery_required', errorMessage?: string | null) => {
      terminalRef.current = true;
      cleanup();
      if (kind === 'completed' || kind === 'partial') {
        onCompletedRef.current?.();
      } else if (kind === 'failed') {
        onErrorRef.current?.(new Error(errorMessage || 'Investigation failed during execution.'));
      }
    },
    [cleanup]
  );

  const applyProgressPayload = useCallback(
    (raw: RawProgressPayload) => {
      const parsed = parseProgressPayload(raw);

      if (typeof parsed.elapsedSeconds === 'number' && parsed.elapsedSeconds > 0) {
        // Reconciliation must never move an active timer backwards after a stale
        // snapshot or reconnect.
        startTimeRef.current = Math.min(
          startTimeRef.current,
          Date.now() - parsed.elapsedSeconds * 1000
        );
      }

      setState((prev) => ({
        ...prev,
        status: parsed.streamStatus,
        stage: parsed.stage || prev.stage,
        activeAgent: parsed.activeAgent ?? prev.activeAgent,
        elapsedSeconds:
          typeof parsed.elapsedSeconds === 'number'
            ? Math.max(prev.elapsedSeconds, parsed.elapsedSeconds)
            : prev.elapsedSeconds,
        revisionCount: parsed.revisionCount ?? prev.revisionCount,
        error: parsed.error ?? prev.error,
        milestone: parsed.milestone ?? prev.milestone,
        isFallbackPolling: false,
        isReconnecting: false,
        progressStep: Math.max(prev.progressStep, progressStepForStage(parsed.stage)),
      }));

      if (parsed.isTerminal && parsed.terminalKind) {
        markTerminal(parsed.terminalKind, parsed.error);
      }
    },
    [markTerminal]
  );

  const pollStatus = useCallback(async () => {
    if (!investigationId || !isMountedRef.current || terminalRef.current) return;

    try {
      const data = await apiClient.getInvestigationStatus(investigationId);
      if (!isMountedRef.current || terminalRef.current) return;

      const isTerminal = TERMINAL_LIFECYCLE.has(data.status);

      setState((prev) => ({
        ...prev,
        status:
          data.status === 'completed'
            ? 'completed'
            : data.status === 'partial'
              ? 'partial'
            : data.status === 'failed'
              ? 'failed'
            : data.status === 'cancelled'
                ? 'cancelled'
                : data.status === 'recovery_required'
                  ? 'recovery_required'
                : 'polling',
        stage: data.current_stage || data.status,
        activeAgent: data.active_agent,
        elapsedSeconds: data.elapsed_seconds,
        revisionCount: data.revision_count,
        error: data.error ?? null,
        isFallbackPolling: true,
        isReconnecting: false,
        progressStep: Math.max(
          prev.progressStep,
          progressStepForStage(data.current_stage || data.status)
        ),
      }));

      if (data.status === 'completed' || data.status === 'partial') {
        markTerminal(data.status);
      } else if (data.status === 'failed') {
        markTerminal('failed', data.error);
      } else if (data.status === 'cancelled') {
        markTerminal('cancelled');
      } else if (data.status === 'recovery_required') {
        markTerminal('recovery_required', data.error);
      } else if (!terminalRef.current) {
        pollTimerRef.current = setTimeout(pollStatus, pollIntervalMs);
      }
    } catch {
      if (!isMountedRef.current || terminalRef.current) return;
      pollTimerRef.current = setTimeout(pollStatus, pollIntervalMs);
    }
  }, [investigationId, pollIntervalMs, markTerminal]);

  const connectSSE = useCallback(() => {
    if (!investigationId || !enabled || !isMountedRef.current || terminalRef.current) return;

    cleanup();

    setState((prev) => ({
      ...prev,
      status: 'connecting',
      isReconnecting: consecutiveErrorsRef.current > 0,
      isFallbackPolling: false,
    }));

    const controller = new AbortController();
    streamAbortRef.current = controller;

    const handleStreamError = () => {
      if (!isMountedRef.current || terminalRef.current) return;
      consecutiveErrorsRef.current += 1;
      cleanup();

      if (consecutiveErrorsRef.current >= maxConsecutiveErrors) {
        setState((prev) => ({
          ...prev,
          status: 'polling',
          isFallbackPolling: true,
          isReconnecting: false,
        }));
        pollStatus();
        return;
      }

      const backoffMs = Math.min(1000 * Math.pow(2, consecutiveErrorsRef.current - 1), 4000);
      setState((prev) => ({ ...prev, status: 'connecting', isReconnecting: true }));
      reconnectTimerRef.current = setTimeout(() => {
        if (!terminalRef.current) {
          connectSSE();
        }
      }, backoffMs);
    };

    void apiClient.streamInvestigationEvents(investigationId, {
      signal: controller.signal,
      onOpen: () => {
        if (!isMountedRef.current || terminalRef.current) return;
        consecutiveErrorsRef.current = 0;
        setState((prev) => ({
          ...prev,
          status: 'streaming',
          isFallbackPolling: false,
          isReconnecting: false,
        }));
      },
      onEvent: (eventName, data) => {
        if (!isMountedRef.current || terminalRef.current) return;
        if (!SSE_EVENT_NAMES.includes(eventName as (typeof SSE_EVENT_NAMES)[number])) return;
        applyProgressPayload(data as RawProgressPayload);
      },
    }).then(() => {
      if (!controller.signal.aborted && !terminalRef.current) handleStreamError();
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      handleStreamError();
      if (error instanceof Error) onErrorRef.current?.(error);
    });
  }, [
    investigationId,
    enabled,
    cleanup,
    maxConsecutiveErrors,
    pollStatus,
    applyProgressPayload,
  ]);

  const connectSSERef = useRef(connectSSE);
  connectSSERef.current = connectSSE;

  useEffect(() => {
    isMountedRef.current = true;
    consecutiveErrorsRef.current = 0;
    terminalRef.current = false;
    startTimeRef.current = Date.now();
    setState(INITIAL_STREAM_STATE);

    if (enabled && investigationId) {
      connectSSERef.current();
    } else {
      cleanup();
      setState(INITIAL_STREAM_STATE);
    }

    return () => {
      isMountedRef.current = false;
      cleanup();
    };
  }, [investigationId, enabled, cleanup]);

  useEffect(() => {
    const isActive =
      state.status === 'streaming' || state.status === 'connecting' || state.status === 'polling';

    if (!isActive) return;

    const interval = setInterval(() => {
      if (!isMountedRef.current) return;
      const computed = (Date.now() - startTimeRef.current) / 1000;
      const nextElapsed = Math.max(0, Math.round(computed * 10) / 10);
      setState((prev) => {
        if (prev.elapsedSeconds === nextElapsed) return prev;
        return {
          ...prev,
          elapsedSeconds: Math.max(prev.elapsedSeconds, nextElapsed),
        };
      });
    }, 200);

    return () => clearInterval(interval);
  }, [state.status]);

  return {
    ...state,
    reconnect: connectSSE,
  };
}
