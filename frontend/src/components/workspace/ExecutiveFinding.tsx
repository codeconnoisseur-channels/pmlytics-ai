'use client';

import React from 'react';
import { TextWithCitations } from './TextWithCitations';

export interface ExecutiveFindingProps {
  problemStatement: string;
  whyItMatters: string;
  affectedUsers: string;
  onSelectCitation?: (id: string) => void;
}

export function ExecutiveFinding({
  problemStatement,
  whyItMatters,
  affectedUsers,
  onSelectCitation,
}: ExecutiveFindingProps) {
  return (
    <section className="editorial-section space-y-4" aria-labelledby="finding-heading">
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs font-bold text-txt-muted">02</span>
        <h2 id="finding-heading" className="text-xl font-black tracking-[-0.03em] text-txt-primary">
          Executive finding
        </h2>
      </div>

      <div className="space-y-5 rounded-2xl border border-border bg-surface/90 p-6 shadow-[0_14px_40px_rgba(25,31,17,0.05)] sm:p-7">
        {/* Lead Problem Statement */}
        <p className="text-sm sm:text-base text-txt-primary leading-relaxed">
          <TextWithCitations text={problemStatement} onSelectCitation={onSelectCitation} />
        </p>

        {/* Why It Matters & Affected Cohort Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-border text-xs">
          <div className="space-y-1">
            <span className="block font-bold text-txt-primary">Why it matters</span>
            <span className="text-txt-secondary leading-relaxed block">
              <TextWithCitations text={whyItMatters} onSelectCitation={onSelectCitation} />
            </span>
          </div>

          <div className="space-y-1">
            <span className="block font-bold text-txt-primary">Affected customers</span>
            <span className="text-txt-secondary leading-relaxed block">
              <TextWithCitations text={affectedUsers} onSelectCitation={onSelectCitation} />
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
