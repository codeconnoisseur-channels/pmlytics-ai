import React from 'react';
import { cn } from '@/lib/utils';
import { HelpCircle } from 'lucide-react';

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center rounded-lg border border-dashed border-border bg-surface',
        className
      )}
      {...props}
    >
      <div className="w-10 h-10 rounded-full bg-surface-subtle flex items-center justify-center text-txt-muted mb-3">
        <HelpCircle className="w-5 h-5" />
      </div>
      <h3 className="text-base font-semibold text-txt-primary mb-1">{title}</h3>
      <p className="text-sm text-txt-secondary max-w-sm mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}
