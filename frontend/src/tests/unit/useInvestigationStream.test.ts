import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useInvestigationStream } from '@/hooks/useInvestigationStream';
import { apiClient } from '@/lib/api-client';

type StreamOptions = Parameters<typeof apiClient.streamInvestigationEvents>[1];

describe('useInvestigationStream Hook', () => {
  let streamOptions: StreamOptions | undefined;
  let settleStream: (() => void) | undefined;

  beforeEach(() => {
    streamOptions = undefined;
    vi.spyOn(apiClient, 'streamInvestigationEvents').mockImplementation(async (_id, options) => {
      streamOptions = options;
      await new Promise<void>((resolve) => {
        settleStream = resolve;
      });
    });
  });

  afterEach(() => {
    settleStream?.();
    vi.restoreAllMocks();
  });

  it('opens the authenticated stream and transitions to streaming', async () => {
    const { result } = renderHook(() => useInvestigationStream('inv-123'));
    expect(result.current.status).toBe('connecting');
    expect(result.current.isReconnecting).toBe(false);
    expect(result.current.progressStep).toBe(0);
    await waitFor(() => expect(streamOptions).toBeDefined());

    act(() => streamOptions?.onOpen());
    expect(result.current.status).toBe('streaming');
    expect(apiClient.streamInvestigationEvents).toHaveBeenCalledWith(
      'inv-123',
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  it('applies named progress and completion events', async () => {
    const onCompleted = vi.fn();
    const { result } = renderHook(() => useInvestigationStream('inv-123', { onCompleted }));
    await waitFor(() => expect(streamOptions).toBeDefined());

    act(() => {
      streamOptions?.onOpen();
      streamOptions?.onEvent('progress', {
        stage: 'gathering_evidence',
        status: 'gathering_evidence',
        active_agent: 'research',
        elapsed_seconds: 4.2,
      });
    });
    expect(result.current.stage).toBe('gathering_evidence');
    expect(result.current.activeAgent).toBe('research');
    expect(result.current.elapsedSeconds).toBe(4.2);
    expect(result.current.progressStep).toBe(2);

    act(() => {
      streamOptions?.onEvent('progress', {
        stage: 'synthesizing',
        status: 'synthesizing',
        active_agent: 'pm',
      });
      streamOptions?.onEvent('snapshot', {
        stage: 'planning',
        status: 'planning',
        active_agent: 'planner',
      });
    });
    expect(result.current.progressStep).toBe(3);

    act(() => {
      streamOptions?.onEvent('complete', {
        status: 'completed',
        elapsed_seconds: 14.5,
      });
    });
    expect(result.current.status).toBe('completed');
    expect(onCompleted).toHaveBeenCalledTimes(1);
    expect(streamOptions?.signal.aborted).toBe(true);
  });

  it('hydrates a snapshot without moving elapsed time backwards', async () => {
    const { result } = renderHook(() => useInvestigationStream('inv-123'));
    await waitFor(() => expect(streamOptions).toBeDefined());

    act(() => {
      streamOptions?.onEvent('snapshot', {
        status: 'reviewing',
        current_stage: 'Checking the recommendation',
        active_agent: 'critic',
        elapsed_seconds: 42.3,
        revision_count: 1,
      });
    });
    expect(result.current.stage).toBe('reviewing');
    expect(result.current.elapsedSeconds).toBe(42.3);

    act(() => {
      streamOptions?.onEvent('snapshot', {
        status: 'reviewing',
        elapsed_seconds: 12,
      });
    });
    expect(result.current.elapsedSeconds).toBe(42.3);
  });

  it('stops streaming when an interrupted step requires explicit recovery', async () => {
    const { result } = renderHook(() => useInvestigationStream('inv-123'));
    await waitFor(() => expect(streamOptions).toBeDefined());

    act(() => {
      streamOptions?.onEvent('recovery_required', {
        status: 'recovery_required',
        error: 'Completed work has been preserved.',
        elapsed_seconds: 65,
      });
    });

    expect(result.current.status).toBe('recovery_required');
    expect(result.current.error).toBe('Completed work has been preserved.');
    expect(result.current.elapsedSeconds).toBe(65);
    expect(streamOptions?.signal.aborted).toBe(true);
  });

  it('aborts the authenticated stream on unmount', async () => {
    const { unmount } = renderHook(() => useInvestigationStream('inv-123'));
    await waitFor(() => expect(streamOptions).toBeDefined());
    const signal = streamOptions?.signal;
    expect(signal?.aborted).toBe(false);
    unmount();
    expect(signal?.aborted).toBe(true);
  });

  it('only labels a connection as reconnecting after a stream failure', async () => {
    vi.mocked(apiClient.streamInvestigationEvents).mockRejectedValueOnce(
      new Error('connection lost')
    );

    const { result } = renderHook(() =>
      useInvestigationStream('inv-123', { maxConsecutiveErrors: 3 })
    );

    expect(result.current.isReconnecting).toBe(false);
    await waitFor(() => expect(result.current.isReconnecting).toBe(true));
    expect(result.current.status).toBe('connecting');
  });
});
