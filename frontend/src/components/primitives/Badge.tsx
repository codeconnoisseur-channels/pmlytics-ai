import React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'neutral' | 'pass' | 'warn' | 'danger' | 'brand';
}

export function Badge({ className, variant = 'neutral', ...props }: BadgeProps) {
  const base = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border';

  const variants = {
    neutral: 'bg-surface-subtle text-txt-secondary border-border',
    pass: 'bg-status-pass-bg text-status-pass-text border-status-pass-border',
    warn: 'bg-status-warn-bg text-status-warn-text border-status-warn-border',
    danger: 'bg-status-danger-bg text-status-danger-text border-status-danger-border',
    brand: 'bg-brand-subtle text-brand-primary border-brand-border',
  };

  return <span className={cn(base, variants[variant], className)} {...props} />;
}
