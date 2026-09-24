'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export interface CitationPillProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  evidenceId: string;
  onSelectCitation?: (id: string) => void;
}

export function CitationPill({
  evidenceId,
  onSelectCitation,
  className,
  ...props
}: CitationPillProps) {
  const formattedId = evidenceId.startsWith('[') ? evidenceId : `[${evidenceId}]`;

  return (
    <button
      type="button"
      role="button"
      onClick={() => onSelectCitation?.(evidenceId.replace(/[[\]]/g, ''))}
      className={cn(
        'inline-flex items-center justify-center font-mono font-semibold text-xs px-1.5 py-0.5 rounded',
        'bg-brand-subtle text-brand-primary border border-brand-border',
        'hover:bg-blue-100 hover:border-blue-300 hover:text-blue-800 transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary',
        className
      )}
      aria-label={`View evidence record ${formattedId}`}
      {...props}
    >
      {formattedId}
    </button>
  );
}
