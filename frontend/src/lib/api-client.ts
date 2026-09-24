import type {
  InvestigationCreateRequest,
  InvestigationSummaryResponse,
  InvestigationStatusResponse,
  InvestigationDetailResponse,
  HealthResponse,
} from '@/types/domain';
import { createClient as createSupabaseClient } from '@/lib/supabase/client';

export class ApiError extends Error {
  public status: number;
  public details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private async authorizationHeader(): Promise<Record<string, string>> {
    const supabase = createSupabaseClient();
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token
      ? { Authorization: `Bearer ${data.session.access_token}` }
      : {};
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(await this.authorizationHeader()),
      ...options.headers,
    };

    const res = await fetch(url, { ...options, headers });

    if (!res.ok) {
      let details: unknown = null;
      try {
        details = await res.json();
      } catch {
        // Response wasn't json
      }
      throw new ApiError(
        `API request failed with status ${res.status}: ${res.statusText}`,
        res.status,
        details
      );
    }

    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  }

  /**
   * Launch a new product investigation.
   */
  public async createInvestigation(
    data: InvestigationCreateRequest
  ): Promise<InvestigationSummaryResponse> {
    return this.request<InvestigationSummaryResponse>('/investigations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * Retrieve current lifecycle progress for an investigation.
   */
  public async getInvestigationStatus(id: string): Promise<InvestigationStatusResponse> {
    return this.request<InvestigationStatusResponse>(`/investigations/${encodeURIComponent(id)}`);
  }

  /**
   * Cancel an in-progress investigation.
   */
  public async cancelInvestigation(id: string): Promise<InvestigationStatusResponse> {
    return this.request<InvestigationStatusResponse>(`/investigations/${encodeURIComponent(id)}/cancel`, {
      method: 'POST',
    });
  }

  public async recoverInvestigation(id: string): Promise<InvestigationStatusResponse> {
    return this.request<InvestigationStatusResponse>(
      `/investigations/${encodeURIComponent(id)}/recover`,
      { method: 'POST' }
    );
  }

  public async retryInvestigation(id: string): Promise<InvestigationSummaryResponse> {
    return this.request<InvestigationSummaryResponse>(
      `/investigations/${encodeURIComponent(id)}/retry`,
      { method: 'POST' }
    );
  }

  public async renameInvestigation(
    id: string,
    displayName: string
  ): Promise<InvestigationStatusResponse> {
    return this.request<InvestigationStatusResponse>(
      `/investigations/${encodeURIComponent(id)}`,
      { method: 'PATCH', body: JSON.stringify({ display_name: displayName }) }
    );
  }

  public async deleteInvestigation(id: string): Promise<void> {
    return this.request<void>(`/investigations/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
  }

  /**
   * Retrieve full synthesized result and evidence ledger.
   * May throw ApiError with status 409 if still executing.
   */
  public async getInvestigationResult(id: string): Promise<InvestigationDetailResponse> {
    return this.request<InvestigationDetailResponse>(`/investigations/${encodeURIComponent(id)}/result`);
  }

  /**
   * List recent investigations in process memory.
   */
  public async listRecentInvestigations(): Promise<InvestigationStatusResponse[]> {
    return this.request<InvestigationStatusResponse[]>('/investigations');
  }

  /**
   * Retrieve system and dependency health.
   */
  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  /**
   * Returns the URL for the SSE live event stream.
   */
  public getEventsUrl(id: string): string {
    return `${this.baseUrl}/investigations/${encodeURIComponent(id)}/events`;
  }

  /** Stream authenticated SSE over fetch because native EventSource cannot send bearer headers. */
  public async streamInvestigationEvents(
    id: string,
    options: {
      signal: AbortSignal;
      onOpen: () => void;
      onEvent: (eventName: string, data: unknown) => void;
    }
  ): Promise<void> {
    const response = await fetch(this.getEventsUrl(id), {
      headers: {
        Accept: 'text/event-stream',
        ...(await this.authorizationHeader()),
      },
      cache: 'no-store',
      signal: options.signal,
    });
    if (!response.ok || !response.body) {
      throw new ApiError('Unable to connect to investigation updates.', response.status);
    }

    options.onOpen();
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
      let boundary = buffer.indexOf('\n\n');
      while (boundary >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        let eventName = 'message';
        const dataLines: string[] = [];
        for (const line of block.split('\n')) {
          if (line.startsWith('event:')) eventName = line.slice(6).trim();
          if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
        }
        if (dataLines.length > 0) {
          const rawData = dataLines.join('\n');
          try {
            options.onEvent(eventName, JSON.parse(rawData));
          } catch {
            // Heartbeats and malformed payloads are ignored safely.
          }
        }
        boundary = buffer.indexOf('\n\n');
      }
    }
  }
}

export const apiClient = new ApiClient();
