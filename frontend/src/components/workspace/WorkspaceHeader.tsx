'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, FileSpreadsheet } from 'lucide-react';
import { Button } from '@/components/primitives/Button';
import { cn } from '@/lib/utils';

export interface WorkspaceHeaderProps {
  investigationId: string;
  userQuery: string;
  status: string;
  durationSeconds?: number;
  evidenceCount: number;
  supportingRecordCount?: number;
  onToggleLedger: () => void;
  isLedgerOpen?: boolean;
  scope?: { start_time?: string | null; end_time?: string | null };
}

const SCOPE_DATE_FORMATTER = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
});

function formatScopeDate(value: string): string | null {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : SCOPE_DATE_FORMATTER.format(date);
}

export function WorkspaceHeader({
  investigationId: _investigationId,
  userQuery,
  status,
  durationSeconds,
  evidenceCount,
  onToggleLedger,
  isLedgerOpen,
  scope,
}: WorkspaceHeaderProps) {
  const isCompleted = status.toLowerCase() === 'completed';
  const isFailed = status.toLowerCase() === 'failed';
  const isCancelled = status.toLowerCase() === 'cancelled';
  const isPartial = status.toLowerCase() === 'partial';
  const scopeStart = scope?.start_time ? formatScopeDate(scope.start_time) : null;
  const scopeEnd = scope?.end_time ? formatScopeDate(scope.end_time) : null;
  const scopeLabel = scopeStart && scopeEnd ? `${scopeStart} to ${scopeEnd}` : null;

  return (
    <div className="border-b border-border bg-surface/90 px-4 py-5 backdrop-blur-xl sm:px-6">
      <div className="max-w-[1240px] mx-auto flex flex-col gap-3">
        {/* Top Navigation & Actions Row */}
        <div className="flex items-center justify-between gap-3 flex-wrap">
          {/* Back navigation */}
          <Link
            href="/investigations"
            className="inline-flex min-h-9 touch-manipulation items-center gap-1.5 rounded-full px-2 text-xs font-medium text-txt-secondary transition-colors hover:bg-surface-subtle hover:text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
          >
            <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Back to investigations</span>
          </Link>

          {/* Action Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant={isLedgerOpen ? 'primary' : 'secondary'}
              size="sm"
              onClick={onToggleLedger}
              className="text-xs gap-1.5 h-8 font-medium"
              aria-label={`View evidence from ${evidenceCount} sources`}
            >
              <FileSpreadsheet className="w-3.5 h-3.5" aria-hidden="true" />
              <span>View evidence</span>
              <span
                className={cn(
                  'px-1.5 py-0.5 rounded-full text-[10px] font-bold',
                  isLedgerOpen
                    ? 'bg-white/20 text-white'
                    : 'bg-brand-subtle text-brand-primary'
                )}
              >
                {evidenceCount}
              </span>
            </Button>
          </div>
        </div>

        {/* Main Title & Status Strip */}
        <div className="space-y-2">
          <h1 className="max-w-4xl text-xl font-black leading-snug tracking-[-0.035em] text-txt-primary sm:text-2xl">
            {userQuery}
          </h1>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs text-txt-muted">
            {/* Status Pill */}
            <span
              className={cn(
                'inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-bold text-[11px] tracking-wide uppercase',
                isCompleted &&
                  'bg-status-pass-bg text-status-pass-text border border-status-pass-border',
                isFailed &&
                  'bg-status-revise-bg text-status-revise-text border border-status-revise-border',
                isPartial &&
                  'bg-status-revise-bg text-status-revise-text border border-status-revise-border',
                isCancelled && 'bg-surface-subtle text-txt-muted border border-border',
                !isCompleted &&
                  !isFailed &&
                  !isPartial &&
                  !isCancelled &&
                  'bg-brand-subtle text-brand-primary border border-brand-border'
              )}
            >
              <span
                className={cn(
                  'w-1.5 h-1.5 rounded-full',
                  isCompleted && 'bg-status-pass-text',
                  isFailed && 'bg-status-revise-text',
                  isPartial && 'bg-status-revise-text',
                  isCancelled && 'bg-txt-muted',
                  !isCompleted && !isFailed && !isPartial && !isCancelled && 'bg-brand-primary animate-pulse motion-reduce:animate-none'
                )}
              />
              <span>{isPartial ? 'DECISION WITH FOLLOW-UP' : status.toUpperCase()}</span>
            </span>

            {durationSeconds !== undefined && durationSeconds > 0 && (
              <>
                <span className="text-txt-muted" aria-hidden="true">
                  •
                </span>
                <span className="font-mono text-txt-secondary">{durationSeconds.toFixed(1)}s</span>
              </>
            )}
            {scopeLabel && (
              <>
                <span className="text-txt-muted" aria-hidden="true">•</span>
                <span>Period: {scopeLabel}</span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
