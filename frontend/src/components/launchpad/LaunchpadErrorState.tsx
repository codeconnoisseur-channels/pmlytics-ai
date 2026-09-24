import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/primitives/Button';

export interface LaunchpadErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function LaunchpadErrorState({ message, onRetry }: LaunchpadErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start justify-between gap-3 rounded-2xl border border-status-danger-border bg-status-danger-bg/40 p-4 text-xs text-status-danger-text sm:flex-row sm:items-center"
    >
      <div className="flex items-start gap-2.5">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <span className="font-semibold block sm:inline mr-1">
            Unable to fetch recent investigations:
          </span>
          <span>{message}</span>
        </div>
      </div>
      {onRetry && (
        <Button
          size="sm"
          variant="secondary"
          onClick={onRetry}
          className="shrink-0 text-xs h-7 px-2.5"
        >
          Retry
        </Button>
      )}
    </div>
  );
}
