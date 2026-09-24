import React from 'react';
import { cn } from '@/lib/utils';

export type EvidenceSourceType = 'zendesk' | 'posthog' | 'jira';

export interface SourceBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  source: EvidenceSourceType;
  reference?: string;
}

function cleanReference(ref?: string): string | undefined {
  if (!ref) return undefined;
  let cleaned = ref
    .replace(/^issue_key:/i, '')
    .replace(/^ticket_id:/i, 'Ticket #')
    .replace(/^jql:.*?(PAY-\d+|CORE-\d+).*/i, '$1')
    .replace(/^jql:.*?project\s*=\s*(\w+).*/i, 'Search ($1)')
    .replace(/^jql:.*/i, 'Search')
    .replace(/\/rest\/api\/\d+\/(?:search\/jql|issue\/([A-Z]+-\d+))/i, '$1')
    .replace(/\/rest\/api\/[^\s]+/i, 'API Record');
  return cleaned;
}

export function SourceBadge({ source, reference, className, ...props }: SourceBadgeProps) {
  const configs = {
    zendesk: {
      label: 'Zendesk',
      styles: 'bg-src-zendesk-bg text-src-zendesk-text border-src-zendesk-border',
    },
    posthog: {
      label: 'PostHog',
      styles: 'bg-src-posthog-bg text-src-posthog-text border-src-posthog-border',
    },
    jira: {
      label: 'Jira',
      styles: 'bg-src-jira-bg text-src-jira-text border-src-jira-border',
    },
  };

  const config = configs[source];
  const displayRef = cleanReference(reference);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border',
        config.styles,
        className
      )}
      {...props}
    >
      <span className="font-semibold font-sans">{config.label}</span>
      {displayRef && <span className="opacity-80">· {displayRef}</span>}
    </span>
  );
}
