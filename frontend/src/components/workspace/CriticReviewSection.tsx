'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { CriticReview } from '@/types/domain';

export interface CriticReviewSectionProps {
  criticReview: CriticReview;
}

export function CriticReviewSection({ criticReview }: CriticReviewSectionProps) {
  const { status } = criticReview;

  const isPass = status === 'PASS';

  return (
    <section className="editorial-section" aria-label="Quality check">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-surface/90 p-4 shadow-sm sm:p-5">
        <div className="flex items-center gap-3 flex-wrap">
            <span
              className={cn(
                'px-2 py-0.5 rounded text-[11px] font-bold font-mono border tracking-wider',
                isPass
                  ? 'bg-status-pass-bg text-status-pass-text border-status-pass-border'
                  : 'bg-status-revise-bg text-status-revise-text border-status-revise-border'
              )}
            >
              {isPass ? 'QUALITY CHECKED' : 'FOLLOW-UP INCLUDED'}
            </span>
            <span className="text-sm text-txt-secondary">
              {isPass
                ? 'This brief was checked for evidence and an appropriately confident decision.'
                : 'The brief includes the follow-up needed before a stronger decision can be made.'}
            </span>
        </div>
      </div>
    </section>
  );
}
