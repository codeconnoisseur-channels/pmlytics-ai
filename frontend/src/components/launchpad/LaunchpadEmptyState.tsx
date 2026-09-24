import React from 'react';
import { EmptyState } from '@/components/primitives/EmptyState';
import { Button } from '@/components/primitives/Button';
import { Sparkles } from 'lucide-react';

export interface LaunchpadEmptyStateProps {
  onStartInquiry?: () => void;
}

export function LaunchpadEmptyState({ onStartInquiry }: LaunchpadEmptyStateProps) {
  return (
    <EmptyState
      title="No recent investigations"
      description="Start a new investigation above to turn a product question into a decision brief."
      action={
        onStartInquiry && (
          <Button
            size="sm"
            variant="secondary"
            onClick={onStartInquiry}
            className="gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Start an investigation</span>
          </Button>
        )
      }
    />
  );
}
