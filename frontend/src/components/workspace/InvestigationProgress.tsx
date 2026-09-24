'use client';

import React from 'react';
import { Loader2, AlertCircle, CheckCircle2, RefreshCw, Square } from 'lucide-react';
import { Button } from '@/components/primitives/Button';

export interface InvestigationProgressProps {
  stage: string;
  status: string;
  activeAgent?: string | null;
  elapsedSeconds: number;
  progressStep?: number;
  isReconnecting?: boolean;
  isPolling?: boolean;
  error?: string | null;
  onCancel?: () => void;
  isCancelling?: boolean;
}

const STATUS_COPY: Record<string, string> = {
  planning: 'Clarifying the question',
  gathering_evidence: 'Gathering the evidence',
  synthesizing: 'Bringing the findings together',
  reviewing: 'Checking the recommendation',
  revising: 'Refining the recommendation',
  completing: 'Preparing your decision brief',
  completed: 'Your decision brief is ready',
  partial: 'Your decision brief is ready with follow-up items',
  pending: 'Preparing the investigation',
};

const ACTIVITY_COPY: Record<string, string> = {
  planner: 'Clarifying what to investigate',
  research: 'Reviewing customer feedback',
  research_agent: 'Reviewing customer feedback',
  analytics: 'Examining product usage',
  analytics_agent: 'Examining product usage',
  engineering: 'Checking delivery context',
  engineering_agent: 'Checking delivery context',
  pm: 'Bringing the findings together',
  critic: 'Checking the recommendation',
  specialists: 'Gathering the evidence',
  orchestrator: 'Coordinating the investigation',
};

const LIFECYCLE_STEP: Record<string, number> = {
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

export function InvestigationProgress({
  stage,
  status,
  activeAgent,
  elapsedSeconds,
  progressStep = 0,
  isReconnecting,
  isPolling,
  error,
  onCancel,
  isCancelling = false,
}: InvestigationProgressProps) {
  const normalizedStage = stage.toLowerCase();
  const headline = STATUS_COPY[normalizedStage] ?? 'Analysing your question';
  const activity = activeAgent
    ? ACTIVITY_COPY[activeAgent] ?? 'Analysing the available evidence'
    : headline;
  const formattedElapsed = elapsedSeconds < 60
    ? `${Math.floor(elapsedSeconds)}s`
    : `${Math.floor(elapsedSeconds / 60)}m ${Math.floor(elapsedSeconds % 60)}s`;
  const boundedProgressStep = Math.min(
    6,
    Math.max(0, progressStep, LIFECYCLE_STEP[normalizedStage] ?? 0)
  );
  const progressWidth = `${(boundedProgressStep / 6) * 100}%`;
  const isReady = normalizedStage === 'completed' || normalizedStage === 'partial';

  return (
    <div className="space-y-4 rounded-2xl border border-border bg-surface/90 p-5 shadow-[0_14px_40px_rgba(25,31,17,0.06)]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 flex-wrap">
          {isReady ? (
            <CheckCircle2 className="h-4 w-4 text-status-pass-text" aria-hidden="true" />
          ) : (
            <Loader2 className="h-4 w-4 animate-spin text-[#2563eb] motion-reduce:animate-none" aria-hidden="true" />
          )}
          <div>
            <p className="text-sm font-bold text-txt-primary">
              {isReady ? 'Analysis complete' : 'Analysing your question'}
            </p>
            <p className="text-xs text-txt-secondary mt-0.5" aria-live="polite">{activity}</p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          {isReconnecting && (
            <span className="flex items-center gap-1 text-amber-600 font-medium">
              <RefreshCw className="w-3 h-3 animate-spin" aria-hidden="true" />
              Reconnecting securely… your investigation is still running.
            </span>
          )}
          {isPolling && !isReconnecting && (
            <span className="text-txt-muted">Keeping this view up to date…</span>
          )}
          <span className="font-mono text-txt-secondary">
            {formattedElapsed} elapsed
          </span>

          {onCancel && status !== 'completed' && status !== 'failed' && status !== 'cancelled' && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onCancel}
              disabled={isCancelling}
              className="text-xs h-7 gap-1 text-status-danger-text border-status-danger-border hover:bg-status-danger-bg/50 px-2.5"
              aria-label="Stop investigation"
            >
              <Square className="w-3 h-3 fill-current" aria-hidden="true" />
              <span>{isCancelling ? 'Stopping…' : 'Stop'}</span>
            </Button>
          )}
        </div>
      </div>

      <div
        className="h-1.5 overflow-hidden rounded-full bg-surface-subtle"
        role="progressbar"
        aria-label="Investigation lifecycle progress"
        aria-valuemin={0}
        aria-valuemax={6}
        aria-valuenow={boundedProgressStep}
        aria-valuetext={`${headline}. Step ${boundedProgressStep} of 6.`}
      >
        <div
          className="h-full rounded-full bg-[#2563eb] transition-[width] duration-500 motion-reduce:transition-none"
          style={{ width: progressWidth }}
        />
      </div>
      {!isReady ? <p className="text-xs text-txt-muted">{headline}</p> : null}

      {error && (
        <div className="flex items-center gap-2 p-2.5 rounded bg-status-revise-bg text-status-revise-text border border-status-revise-border text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
