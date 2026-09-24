'use client';

import React, { use, useState, useMemo, useCallback, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { WorkspaceSkeleton } from '@/components/primitives/LoadingSkeleton';
import { ErrorState } from '@/components/primitives/ErrorState';
import { Button } from '@/components/primitives/Button';
import { WorkspaceHeader } from '@/components/workspace/WorkspaceHeader';
import { InvestigationProgress } from '@/components/workspace/InvestigationProgress';
import { RecommendationPanel } from '@/components/workspace/RecommendationPanel';
import { ExecutiveFinding } from '@/components/workspace/ExecutiveFinding';
import { EpistemicDeck } from '@/components/workspace/EpistemicDeck';
import { TensionsBanner } from '@/components/workspace/TensionsBanner';
import { LimitationsBanner } from '@/components/workspace/LimitationsBanner';
import { EvidenceLedgerDrawer } from '@/components/workspace/EvidenceLedgerDrawer';
import {
  useInvestigationResult,
  useCancelInvestigation,
  useRecoverInvestigation,
  useRetryInvestigation,
  useInvestigationStatus,
} from '@/hooks/useInvestigations';
import { useInvestigationStream } from '@/hooks/useInvestigationStream';
import { ApiError } from '@/lib/api-client';
import { getSampleScenario, isSampleScenarioId } from '@/lib/sample-scenarios';
import { cn } from '@/lib/utils';
import { ArrowLeft, SearchX, AlertTriangle, XCircle } from 'lucide-react';

export interface InvestigationWorkspaceViewProps {
  investigationId: string;
}

function isNotFoundError(error: unknown): boolean {
  if (error instanceof ApiError) return error.status === 404;
  return (
    typeof error === 'object' &&
    error !== null &&
    'status' in error &&
    (error as { status?: unknown }).status === 404
  );
}

export function InvestigationWorkspaceView({ investigationId }: InvestigationWorkspaceViewProps) {
  const router = useRouter();
  // Local UI state for Evidence Ledger drawer and active citation deep link
  const [isLedgerOpen, setIsLedgerOpen] = useState(false);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [reportRevealReady, setReportRevealReady] = useState(true);
  const observedActiveRunRef = useRef(false);
  const previewResult = getSampleScenario(investigationId);
  const isReferenceScenario = previewResult !== null;

  // The status endpoint is the source of truth for a running investigation.
  // It continues polling after this route remounts, unlike local SSE state.
  const {
    data: investigationStatus,
    error: investigationStatusError,
  } = useInvestigationStatus(investigationId, !isReferenceScenario);
  const lifecycleStatus = investigationStatus?.status;
  const hasReport = lifecycleStatus === 'completed' || lifecycleStatus === 'partial';

  // Fetch the immutable report only after the authoritative lifecycle has
  // reached a report-bearing terminal state. This prevents an active-run 409/null response becoming the
  // cached workspace result.
  const {
    data: fetchedResult,
    isLoading: isResultLoading,
    error: resultError,
    refetch,
  } = useInvestigationResult(
    investigationId,
    !isReferenceScenario && hasReport
  );
  const result = previewResult ?? fetchedResult;

  useEffect(() => {
    observedActiveRunRef.current = false;
    setReportRevealReady(true);
  }, [investigationId]);

  useEffect(() => {
    if (isReferenceScenario || !lifecycleStatus) return;
    const isTerminal = ['completed', 'partial', 'failed', 'cancelled', 'recovery_required'].includes(lifecycleStatus);
    if (!isTerminal) {
      observedActiveRunRef.current = true;
      setReportRevealReady(false);
      return;
    }
    if (!observedActiveRunRef.current || (lifecycleStatus !== 'completed' && lifecycleStatus !== 'partial')) {
      setReportRevealReady(true);
      return;
    }
    const revealTimer = window.setTimeout(() => setReportRevealReady(true), 900);
    return () => window.clearTimeout(revealTimer);
  }, [isReferenceScenario, lifecycleStatus]);

  // Cancellation mutation
  const cancelMutation = useCancelInvestigation();
  const recoverMutation = useRecoverInvestigation();
  const retryMutation = useRetryInvestigation();

  // Real-time lifecycle streaming hook with automatic reconnection & fallback polling
  const isTerminalResult =
    lifecycleStatus === 'completed' ||
    lifecycleStatus === 'partial' ||
    lifecycleStatus === 'failed' ||
    lifecycleStatus === 'cancelled' ||
    lifecycleStatus === 'recovery_required' ||
    result?.status === 'completed' ||
    result?.status === 'partial' ||
    result?.status === 'failed' ||
    result?.status === 'cancelled';

  const handleStreamCompleted = useCallback(() => {
    void refetch();
  }, [refetch]);

  const stream = useInvestigationStream(investigationId, {
    enabled: Boolean(investigationId) && !isReferenceScenario && !isTerminalResult,
    onCompleted: handleStreamCompleted,
  });

  // SSE is the live path. Status remains the recovery path for navigation and
  // missed events, but must not replace the locally interpolated timer.
  const progressStatus = lifecycleStatus ?? stream.status;
  const progressStage = lifecycleStatus ?? stream.stage;
  const progressActiveAgent = investigationStatus?.active_agent ?? stream.activeAgent;
  const progressElapsedSeconds = stream.elapsedSeconds || investigationStatus?.elapsed_seconds || 0;

  // Build canonical EV-NNN ID map from raw internal ledger IDs (stable, index-based)
  const canonicalIdMap = useMemo<Record<string, string>>(() => {
    if (!result?.evidence_ledger) return {};
    const entries = Object.keys(result.evidence_ledger);
    const map: Record<string, string> = {};
    entries.forEach((rawId, idx) => {
      map[rawId] = `EV-${String(idx + 1).padStart(3, '0')}`;
    });
    return map;
  }, [result?.evidence_ledger]);

  const evidenceMetrics = useMemo(() => {
    const ledger = result?.evidence_ledger ?? {};
    const sources = new Set(Object.values(ledger).map((item) => item.source_type));
    const records = new Set<string>();
    Object.values(ledger).forEach((item) => {
      (item.supporting_records ?? []).forEach((record) => {
        records.add(`${item.source_type}:${record.record_id}`);
      });
    });
    return { sourceCount: sources.size, recordCount: records.size };
  }, [result?.evidence_ledger]);

  // Handle interactive citation pill click: open ledger and scroll/highlight card
  const handleSelectCitation = (evId: string) => {
    setSelectedEvidenceId(evId);
    setIsLedgerOpen(true);
  };

  const handleCancel = () => {
    if (investigationId) {
      cancelMutation.mutate(investigationId);
    }
  };

  const handleRetry = async () => {
    try {
      const next = await retryMutation.mutateAsync(investigationId);
      router.push(`/investigations/${encodeURIComponent(next.investigation_id)}`);
    } catch {
      // The failed state remains visible with an inline retry error.
    }
  };

  const is404 = isNotFoundError(investigationStatusError) || isNotFoundError(resultError);

  const isCancelled =
    lifecycleStatus === 'cancelled' ||
    stream.status === 'cancelled' ||
    result?.status === 'cancelled' ||
    cancelMutation.isSuccess;

  const isFailed =
    lifecycleStatus === 'failed' ||
    stream.status === 'failed' ||
    result?.status === 'failed' ||
    (investigationStatusError instanceof ApiError && investigationStatusError.status >= 500) ||
    (resultError instanceof ApiError && resultError.status === 500);

  const isRecoveryRequired =
    lifecycleStatus === 'recovery_required' || stream.status === 'recovery_required';

  const failureMessage =
    stream.error ??
    (investigationStatusError instanceof ApiError
      ? investigationStatusError.message
      : investigationStatusError instanceof Error
        ? investigationStatusError.message
        : null) ??
    (resultError instanceof ApiError
      ? (typeof resultError.details === 'object' &&
        resultError.details !== null &&
        'error' in resultError.details &&
        typeof (resultError.details as { error?: unknown }).error === 'string'
          ? (resultError.details as { error: string }).error
          : resultError.message)
      : resultError instanceof Error
        ? resultError.message
        : 'This investigation failed during execution.');

  // If result is not yet available, show either 404, Cancelled, or Active Progress
  if (!result || !reportRevealReady) {
    return (
      <AppShell>
        <div className="min-h-[60vh]">
          <Link
            href="/investigations"
            className="inline-flex min-h-10 items-center gap-2 rounded-full px-2 text-sm font-semibold text-txt-secondary hover:bg-surface-subtle hover:text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to investigations
          </Link>
          <div className="flex min-h-[52vh] flex-col justify-center">
          {/* 1. Honest 404 Not Found State */}
          {is404 && (
            <div className="py-16 text-center max-w-[540px] mx-auto space-y-4">
              <div
                className="w-12 h-12 rounded-full bg-surface-subtle text-txt-muted flex items-center justify-center mx-auto"
                aria-hidden="true"
              >
                <SearchX className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-txt-primary">Investigation not found</h2>
              <p className="text-sm text-txt-secondary leading-relaxed">
                We couldn&apos;t find this investigation. It may no longer be available in this session.
              </p>
            </div>
          )}

          {/* 2. Explicit Failed State */}
          {isRecoveryRequired && !is404 && !isCancelled && (
            <div className="py-16 text-center max-w-[540px] mx-auto space-y-4">
              <div className="w-12 h-12 rounded-full bg-status-revise-bg text-status-revise-text flex items-center justify-center mx-auto" aria-hidden="true">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-txt-primary">Investigation paused safely</h2>
              <p className="text-sm text-txt-secondary leading-relaxed">
                Completed work has been preserved. The interruption happened during an active step, so PMLytics AI will not repeat a potentially paid request without your confirmation.
              </p>
              <Button
                variant="primary"
                onClick={() => recoverMutation.mutate(investigationId)}
                disabled={recoverMutation.isPending}
              >
                {recoverMutation.isPending ? 'Resuming…' : 'Resume this step'}
              </Button>
            </div>
          )}

          {/* 3. Explicit Failed State */}
          {isFailed && !isRecoveryRequired && !is404 && !isCancelled && (
            <div className="py-16 text-center max-w-[540px] mx-auto space-y-4">
              <div
                className="w-12 h-12 rounded-full bg-status-revise-bg text-status-revise-text flex items-center justify-center mx-auto"
                aria-hidden="true"
              >
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-txt-primary">Investigation failed</h2>
              <p className="text-sm text-txt-secondary leading-relaxed">{failureMessage}</p>
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                <Button
                  variant="primary"
                  onClick={() => void handleRetry()}
                  disabled={retryMutation.isPending}
                >
                  {retryMutation.isPending ? 'Retrying…' : 'Retry investigation'}
                </Button>
                <Link href="/investigations">
                  <Button variant="secondary">Ask a different question</Button>
                </Link>
              </div>
              {retryMutation.isError ? (
                <p className="text-sm text-status-danger-text" role="alert">
                  The retry could not be started. Please try again.
                </p>
              ) : null}
            </div>
          )}

          {/* 4. Explicit Cancelled State */}
          {isCancelled && !is404 && !isFailed && (
            <div className="py-16 text-center max-w-[540px] mx-auto space-y-4">
              <div
                className="w-12 h-12 rounded-full bg-surface-subtle text-txt-muted flex items-center justify-center mx-auto"
                aria-hidden="true"
              >
                <XCircle className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-txt-primary">Investigation stopped</h2>
              <p className="text-sm text-txt-secondary leading-relaxed">
                This investigation was cancelled. No further analysis was performed.
              </p>
            </div>
          )}

          {/* 5. In-Progress Live Stream View (Default during execution) */}
          {!is404 && !isCancelled && !isFailed && !isRecoveryRequired && (
            <div className="py-8 max-w-[840px] w-full mx-auto space-y-6">
              <InvestigationProgress
                stage={progressStage}
                status={progressStatus}
                activeAgent={progressActiveAgent}
                elapsedSeconds={progressElapsedSeconds}
                progressStep={stream.progressStep}
                isReconnecting={stream.isReconnecting}
                isPolling={stream.status === 'polling'}
                error={stream.error}
                onCancel={handleCancel}
                isCancelling={cancelMutation.isPending}
              />
              <WorkspaceSkeleton />
            </div>
          )}
          </div>
        </div>
      </AppShell>
    );
  }

  // Completed or synthesized investigation with full workspace layout and no padding conflicts.
  return (
    <AppShell hidePadding>
      {/* Sticky inquiry header, full bleed and directly below the global topbar. */}
      <WorkspaceHeader
        investigationId={result.investigation_id}
        userQuery={result.user_query}
        status={result.status}
        durationSeconds={result.duration_seconds}
        evidenceCount={evidenceMetrics.sourceCount}
        supportingRecordCount={evidenceMetrics.recordCount}
        scope={result.scope}
        onToggleLedger={() => setIsLedgerOpen((prev) => !prev)}
        isLedgerOpen={isLedgerOpen}
      />

      {/* Editorial Reading Canvas */}
      <div
        className={cn(
          'mx-auto max-w-[960px] space-y-8 px-4 pb-20 pt-8 transition-[max-width,padding] sm:px-6',
          isLedgerOpen && 'widescreen:mr-[420px]'
        )}
      >
        {/* 1. Primary Recommendation + Confidence */}
        <RecommendationPanel
          recommendation={result.recommendation}
          onSelectCitation={handleSelectCitation}
        />

        {/* 2. Executive Finding & Problem Statement */}
        <ExecutiveFinding
          problemStatement={result.recommendation.problem_statement}
          whyItMatters={result.recommendation.why_it_matters}
          affectedUsers={result.recommendation.affected_users}
          onSelectCitation={handleSelectCitation}
        />

        {/* 3. Evidence-Backed Findings (Epistemic Flow: Facts, Inferences, Hypotheses) */}
        <EpistemicDeck
          facts={result.recommendation.factual_observations || []}
          inferences={result.recommendation.inferences || []}
          hypotheses={result.recommendation.hypotheses || []}
          evidenceLedger={result.evidence_ledger || {}}
          canonicalIdMap={canonicalIdMap}
          onSelectCitation={handleSelectCitation}
        />

        {/* 4. Cross-Source Evidentiary Tension Callout Banner */}
        <TensionsBanner
          tensions={result.recommendation.conflicting_evidence}
          onSelectCitation={handleSelectCitation}
        />

        {/* 5. Disclosed Limitations & Evidence Gaps Banner */}
        <LimitationsBanner
          limitations={result.recommendation.disclosed_limitations}
          onSelectCitation={handleSelectCitation}
        />

      </div>

      {/* Authoritative Evidence Ledger Drawer */}
      <EvidenceLedgerDrawer
        isOpen={isLedgerOpen}
        onClose={() => setIsLedgerOpen(false)}
        evidenceLedger={result.evidence_ledger || {}}
        selectedEvidenceId={selectedEvidenceId}
        onClearSelectedEvidence={() => setSelectedEvidenceId(null)}
        canonicalIdMap={canonicalIdMap}
      />
    </AppShell>
  );
}

export default function InvestigationWorkspacePage({
  params,
}: {
  params: Promise<{ id: string }> | { id: string };
}) {
  const resolvedParams = 'then' in params ? use(params) : params;
  return <InvestigationWorkspaceView investigationId={resolvedParams.id} />;
}
