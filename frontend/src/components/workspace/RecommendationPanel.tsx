'use client';

import React from 'react';
import { TextWithCitations } from './TextWithCitations';
import { cn } from '@/lib/utils';
import type { ProductRecommendation } from '@/types/domain';

export interface RecommendationPanelProps {
  recommendation: ProductRecommendation;
  onSelectCitation?: (id: string) => void;
}

type SuccessMeasure = {
  measure: string;
  baseline?: string;
  target?: string;
  review?: string;
};

function parseSuccessMeasure(metric: string): SuccessMeasure {
  const parts = metric.split('|').map((part) => part.trim()).filter(Boolean);
  if (parts.length < 2) return { measure: metric };

  const fields: SuccessMeasure = { measure: parts[0] };
  for (const part of parts.slice(1)) {
    const [label, ...value] = part.split(':');
    const normalizedLabel = label.trim().toLowerCase();
    const normalizedValue = value.join(':').trim();
    if (!normalizedValue) continue;
    if (normalizedLabel === 'baseline') fields.baseline = normalizedValue;
    if (normalizedLabel === 'target') fields.target = normalizedValue;
    if (normalizedLabel === 'review' || normalizedLabel === 'check-in') fields.review = normalizedValue;
  }
  return fields;
}

export function RecommendationPanel({
  recommendation,
  onSelectCitation,
}: RecommendationPanelProps) {
  const {
    recommendation: recText,
    recommendation_type,
    confidence,
    success_metrics = [],
    risks = [],
  } = recommendation;

  const confidenceConfig = {
    high: {
      label: 'HIGH',
      pillClass: 'bg-status-pass-bg text-status-pass-text border-status-pass-border',
    },
    medium: {
      label: 'MEDIUM',
      pillClass: 'bg-amber-50 text-amber-800 border-amber-300',
    },
    low: {
      label: 'LOW',
      pillClass: 'bg-status-revise-bg text-status-revise-text border-status-revise-border',
    },
  }[confidence.toLowerCase() as 'high' | 'medium' | 'low'] || {
    label: confidence.toUpperCase(),
    pillClass: 'bg-surface-subtle text-txt-secondary border-border',
  };

  // Implementation categories are useful metadata, but should never lead the decision.
  const recTypeLabelMap: Record<string, string> = {
    technical_remediation: 'Recommended approach',
    technical_fix_and_ux_enhancement: 'Recommended approach',
    feature_improvement: 'Recommended approach',
    ux_improvement: 'Recommended approach',
    process_improvement: 'Recommended approach',
    investigation_required: 'Investigation needed',
    no_action_required: 'No immediate action',
    monitor: 'Monitor',
  };

  const formattedRecType = recommendation_type
    ? (recTypeLabelMap[recommendation_type.toLowerCase()] ??
       recommendation_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()))
    : 'Recommended action';

  return (
    <section
      className="editorial-section"
      aria-labelledby="recommendation-heading"
    >
      <div className="mb-4 flex items-center gap-3">
        <span className="font-mono text-xs font-bold text-txt-muted">01</span>
        <h2 id="recommendation-heading" className="text-xl font-black tracking-[-0.03em] text-txt-primary">
          Recommendation
        </h2>
      </div>
      <div className="relative overflow-hidden rounded-[28px] border border-[#2d3029] bg-[#171915] p-6 text-white shadow-[0_24px_65px_rgba(23,25,21,0.18)] sm:p-8">
        <div className="pointer-events-none absolute -right-16 -top-20 h-52 w-52 rounded-full bg-[#c8f46b]/20 blur-3xl" aria-hidden="true" />
        <div
          className="relative text-base font-medium leading-relaxed text-white sm:text-lg"
        >
          <TextWithCitations text={recText} onSelectCitation={onSelectCitation} />
        </div>

        <div className="relative mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-white/15 pt-4">
          <span className="rounded-full border border-[#c8f46b]/50 bg-[#c8f46b]/10 px-2.5 py-1 font-mono text-[11px] font-bold tracking-wider text-[#c8f46b]">
            {formattedRecType}
          </span>
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold text-white/70">Confidence:</span>
            <span className={cn('px-2.5 py-0.5 rounded font-bold font-mono text-[11px] border tracking-wider', confidenceConfig.pillClass)}>
              {confidenceConfig.label}
            </span>
          </div>
        </div>

        {/* Decision outcomes and watch-outs */}
        {(success_metrics.length > 0 || risks.length > 0) && (
          <div className="relative mt-6 grid grid-cols-1 gap-5 border-t border-white/15 pt-6 md:grid-cols-2">
            {/* Success measures */}
            {success_metrics.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-white">
                  <span className="w-1.5 h-1.5 rounded-full bg-status-pass-text" />
                  How success will be measured
                </h3>
                <div className="space-y-2">
                  {success_metrics.map((metric, idx) => {
                    const measure = parseSuccessMeasure(metric);
                    return (
                      <div key={idx} className="rounded-2xl border border-white/15 bg-white/10 p-3.5 text-xs">
                        <p className="font-semibold leading-relaxed text-white"><TextWithCitations text={measure.measure} onSelectCitation={onSelectCitation} /></p>
                        {(measure.baseline || measure.target || measure.review) && (
                          <dl className="mt-2 grid grid-cols-1 gap-1 text-white/70">
                            {measure.baseline && <div><dt className="inline font-medium text-white">Baseline: </dt><dd className="inline">{measure.baseline}</dd></div>}
                            {measure.target && <div><dt className="inline font-medium text-white">Target: </dt><dd className="inline">{measure.target}</dd></div>}
                            {measure.review && <div><dt className="inline font-medium text-white">Check-in: </dt><dd className="inline">{measure.review}</dd></div>}
                          </dl>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Decision watch-outs */}
            {risks.length > 0 && (
              <div className="space-y-2">
                <h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-white">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600" />
                  Decision watch-outs
                </h3>
                <ul className="space-y-2 text-xs leading-relaxed text-white/70">
                  {risks.map((risk, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-txt-muted select-none">•</span>
                      <span>
                        <TextWithCitations text={risk} onSelectCitation={onSelectCitation} />
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
