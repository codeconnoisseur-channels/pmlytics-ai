'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { TextWithCitations } from './TextWithCitations';

export interface TensionsBannerProps {
  tensions?: string[];
  onSelectCitation?: (id: string) => void;
}

export function TensionsBanner({ tensions, onSelectCitation }: TensionsBannerProps) {
  if (!tensions || tensions.length === 0) return null;

  return (
    <section className="editorial-section" aria-labelledby="tensions-heading">
      <div className="rounded-lg bg-amber-50/70 border border-amber-200 p-5 sm:p-6 flex items-start gap-4">
        <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0 mt-0.5" aria-hidden="true">
          <AlertTriangle className="w-4 h-4" />
        </div>

        <div className="space-y-2 flex-grow">
          <h3 id="tensions-heading" className="text-sm font-bold text-amber-900 tracking-tight">
            Where the evidence differs
          </h3>

          <div className="text-xs text-amber-950/90 leading-relaxed space-y-2">
            {tensions.map((tension, idx) => (
              <p key={idx}>
                <TextWithCitations text={tension} onSelectCitation={onSelectCitation} />
              </p>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
