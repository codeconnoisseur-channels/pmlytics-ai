import React from 'react';
import { cn } from '@/lib/utils';
import { AlertTriangle } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  message: string;
  statusCode?: number;
  onRetry?: () => void;
}

export function ErrorState({
  title = 'Investigation Error',
  message,
  statusCode,
  onRetry,
  className,
  ...props
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center rounded-lg border border-status-danger-border bg-status-danger-bg/40',
        className
      )}
      {...props}
    >
      <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-status-danger-text mb-3">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <h3 className="text-base font-semibold text-txt-primary mb-1">
        {title} {statusCode && <span className="text-txt-muted text-sm font-mono">({statusCode})</span>}
      </h3>
      <p className="text-sm text-txt-secondary max-w-md mb-4">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Retry Action
        </Button>
      )}
    </div>
  );
}
