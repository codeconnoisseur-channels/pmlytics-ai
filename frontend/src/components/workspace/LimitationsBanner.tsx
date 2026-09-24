'use client';

import React from 'react';
import { Info } from 'lucide-react';
import { TextWithCitations } from './TextWithCitations';

export interface LimitationsBannerProps {
  limitations?: string[];
  onSelectCitation?: (id: string) => void;
}

export function LimitationsBanner({ limitations, onSelectCitation }: LimitationsBannerProps) {
  if (!limitations || limitations.length === 0) return null;

  return (
    <section className="editorial-section" aria-labelledby="limitations-heading">
      <div className="flex items-start gap-4 rounded-2xl border border-border bg-surface/90 p-5 shadow-sm sm:p-6">
        <div className="w-8 h-8 rounded-full bg-surface-subtle text-txt-muted flex items-center justify-center flex-shrink-0 mt-0.5" aria-hidden="true">
          <Info className="w-4 h-4 text-brand-primary" />
        </div>

        <div className="space-y-2 flex-grow">
          <h3 id="limitations-heading" className="text-sm font-bold text-txt-primary tracking-tight">
            What still needs validation
          </h3>

          <ul className="space-y-1.5 text-xs text-txt-secondary leading-relaxed list-disc list-inside">
            {limitations.map((lim, idx) => (
              <li key={idx} className="marker:text-txt-muted">
                <TextWithCitations text={lim} onSelectCitation={onSelectCitation} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
