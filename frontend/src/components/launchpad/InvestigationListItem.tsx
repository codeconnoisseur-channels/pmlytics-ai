import React from 'react';
import Link from 'next/link';
import { Badge } from '@/components/primitives/Badge';
import { Clock, ArrowRight, Activity, Square } from 'lucide-react';
import { useCancelInvestigation } from '@/hooks/useInvestigations';
import type { InvestigationStatusResponse } from '@/types/domain';

export interface InvestigationListItemProps {
  investigation: InvestigationStatusResponse;
}

function getStatusBadgeVariant(status: string): 'pass' | 'danger' | 'warn' | 'brand' | 'neutral' {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'pass';
    case 'failed':
      return 'danger';
    case 'cancelled':
      return 'neutral';
    case 'reviewing':
    case 'revising':
      return 'warn';
    case 'planning':
    case 'gathering_evidence':
    case 'synthesizing':
    case 'pending':
    default:
      return 'brand';
  }
}

function formatInvestigationDate(dateString?: string | null): string {
  if (!dateString) return '';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-GB', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
    });
  } catch {
    return dateString;
  }
}

export function InvestigationListItem({ investigation }: InvestigationListItemProps) {
  const badgeVariant = getStatusBadgeVariant(investigation.status);
  const formattedDate = formatInvestigationDate(investigation.created_at);
  const isRunning =
    investigation.status !== 'completed' &&
    investigation.status !== 'failed' &&
    investigation.status !== 'cancelled';

  const cancelMutation = useCancelInvestigation();

  const handleStop = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    cancelMutation.mutate(investigation.investigation_id);
  };

  return (
    <Link
      href={`/investigations/${encodeURIComponent(investigation.investigation_id)}`}
      className="group flex flex-col justify-between gap-4 rounded-2xl border border-border bg-surface/90 p-4 shadow-[0_10px_30px_rgba(25,31,17,0.04)] transition-[border-color,box-shadow,transform] hover:-translate-y-0.5 hover:border-border-strong hover:shadow-[0_18px_45px_rgba(25,31,17,0.08)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary sm:flex-row sm:items-center sm:p-5"
      aria-label={`View investigation: ${investigation.user_query}`}
    >
      <div className="space-y-1.5 min-w-0 flex-1 pr-2">
        {/* Status + Date Header */}
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={badgeVariant} className="uppercase text-[10px] tracking-wider">
            {investigation.status}
          </Badge>
          {formattedDate && (
            <>
              <span className="text-txt-muted text-xs hidden sm:inline">&bull;</span>
              <span className="text-xs text-txt-muted hidden sm:inline">
                {formattedDate}
              </span>
            </>
          )}
          {isRunning && investigation.current_stage && (
            <span className="inline-flex items-center gap-1 text-xs text-brand-primary font-medium">
              <Activity className="w-3 h-3 animate-pulse" aria-hidden="true" />
              <span>{investigation.current_stage}</span>
            </span>
          )}
        </div>

        {/* User Query as Primary Subject */}
        <h3 className="line-clamp-2 text-sm font-semibold leading-6 text-txt-primary transition-colors">
          {investigation.user_query}
        </h3>
      </div>

      {/* Metadata & Navigation Affordance */}
      <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0 text-xs text-txt-muted">
        {isRunning && (
          <button
            type="button"
            onClick={handleStop}
            disabled={cancelMutation.isPending}
            className="inline-flex min-h-8 touch-manipulation items-center gap-1 rounded-full border border-status-danger-border px-3 py-1 text-[11px] font-medium text-status-danger-text transition-colors hover:bg-status-danger-bg/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-status-danger-text"
            title="Stop this running investigation"
          >
            <Square className="w-2.5 h-2.5 fill-current" aria-hidden="true" />
            <span>{cancelMutation.isPending ? 'Stopping…' : 'Stop'}</span>
          </button>
        )}

        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" aria-hidden="true" />
          <span>
            {typeof investigation.elapsed_seconds === 'number'
              ? `${investigation.elapsed_seconds.toFixed(1)}s`
              : '0.0s'}
          </span>
        </div>
        <ArrowRight className="w-4 h-4 text-txt-muted transition-[color,transform] group-hover:translate-x-0.5 group-hover:text-txt-primary" aria-hidden="true" />
      </div>
    </Link>
  );
}
