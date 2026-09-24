import React from 'react';
import { LoadingSkeleton } from '@/components/primitives/LoadingSkeleton';
import { InvestigationListItem } from './InvestigationListItem';
import { LaunchpadEmptyState } from './LaunchpadEmptyState';
import { LaunchpadErrorState } from './LaunchpadErrorState';
import type { InvestigationStatusResponse } from '@/types/domain';

export interface InvestigationListProps {
  investigations?: InvestigationStatusResponse[];
  isLoading: boolean;
  error?: Error | null;
  onRetry?: () => void;
  onStartInquiry?: () => void;
}

export function InvestigationList({
  investigations,
  isLoading,
  error,
  onRetry,
  onStartInquiry,
}: InvestigationListProps) {
  return (
    <section
      role="region"
      aria-labelledby="recent-investigations-heading"
      className="space-y-3"
    >
      <div className="flex items-end justify-between gap-4 pb-1 pt-4">
        <h2
          id="recent-investigations-heading"
          className="text-xl font-black tracking-[-0.03em] text-txt-primary"
        >
          Recent investigations
        </h2>
      </div>

      {isLoading && (
        <div className="space-y-2.5" role="status" aria-label="Loading recent investigations">
          <LoadingSkeleton className="h-16 w-full rounded-lg" />
          <LoadingSkeleton className="h-16 w-full rounded-lg" />
        </div>
      )}

      {error && !isLoading && (
        <LaunchpadErrorState message={error.message} onRetry={onRetry} />
      )}

      {!isLoading && !error && (!investigations || investigations.length === 0) && (
        <LaunchpadEmptyState onStartInquiry={onStartInquiry} />
      )}

      {!isLoading && !error && investigations && investigations.length > 0 && (
        <div className="space-y-3">
          {investigations.map((inv) => (
            <InvestigationListItem key={inv.investigation_id} investigation={inv} />
          ))}
        </div>
      )}
    </section>
  );
}
