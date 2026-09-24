import type { components } from './api.generated';

export type Schemas = components['schemas'];

export type InvestigationCreateRequest = Schemas['InvestigationCreateRequest'];
export type InvestigationSummaryResponse = Schemas['InvestigationSummaryResponse'];
export type InvestigationStatusResponse = Schemas['InvestigationStatusResponse'];
export type InvestigationDetailResponse = Schemas['InvestigationDetailResponse'];
export type ProductRecommendation = Schemas['ProductRecommendationSchema'];
export type StructuredFinding = Schemas['StructuredFindingSchema'];
export type EvidenceCitation = Schemas['StructuredEvidenceCitationSchema'];
export type EvidenceLedgerItem = Schemas['EvidenceLedgerItemSchema'];
export type EvidenceSupportingRecord = Schemas['EvidenceSupportingRecordSchema'];
export type CriticReview = Schemas['CriticReviewSchema'];
export type TelemetrySummary = Schemas['TelemetrySummarySchema'];
export type HealthResponse = Schemas['HealthResponse'];

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface InvestigationProgressEvent {
  event?: string;
  investigation_id: string;
  stage: string;
  status: string;
  active_agent?: string | null;
  milestone?: string;
  elapsed_seconds: number;
  revision_count?: number;
  error?: string | null;
}
