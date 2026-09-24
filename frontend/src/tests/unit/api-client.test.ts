import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient, ApiError } from '@/lib/api-client';

describe('ApiClient', () => {
  let client: ApiClient;

  beforeEach(() => {
    client = new ApiClient('/api/v1');
    vi.restoreAllMocks();
  });

  it('can be instantiated with custom or default base URL', () => {
    expect(client).toBeDefined();
    expect(client.getEventsUrl('inv-123')).toBe('/api/v1/investigations/inv-123/events');
  });

  it('correctly formats investigation status URL', async () => {
    const mockData = {
      investigation_id: 'inv-123',
      user_query: 'test query',
      status: 'completed',
      current_stage: 'completed',
      active_agent: null,
      revision_count: 0,
      elapsed_seconds: 12.5,
      created_at: '2026-09-17T00:00:00Z',
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    });

    const res = await client.getInvestigationStatus('inv-123');
    expect(res.investigation_id).toBe('inv-123');
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/v1/investigations/inv-123',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
  });

  it('throws ApiError with status and details when server returns 404 or 500', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Investigation not found' }),
    });

    await expect(client.getInvestigationStatus('invalid-id')).rejects.toThrow(ApiError);
  });
});
