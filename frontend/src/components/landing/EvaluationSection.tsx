import React from 'react';

export function EvaluationSection() {
  const metrics = [
    {
      num: '18 to 20 / 20',
      heading: 'Validation Benchmark',
      detail:
        'All dimension-specific frozen-judge acceptance thresholds passed across three live validation scenarios.',
    },
    {
      num: '100%',
      heading: 'Citation Validity',
      detail:
        'All cited Evidence Ledger IDs resolved to valid records in the final validation runs.',
    },
    {
      num: '109s',
      heading: 'Average Investigation Time',
      detail:
        '109s average investigation time across three final validation runs (10 to 11 model calls).',
    },
    {
      num: '$0.06 to $0.08',
      heading: 'Observed Provider Cost',
      detail:
        '$0.06 to $0.08 observed provider cost per final validation run with zero truncations or retries.',
    },
  ];

  return (
    <section className="py-20 border-b border-border bg-canvas scroll-mt-20" id="evaluation">
      <div className="max-w-[1140px] mx-auto px-6">
        <div className="text-center max-w-[760px] mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-txt-primary tracking-tight mb-3">
            Built to be challenged.
          </h2>
          <p className="text-sm sm:text-base text-txt-secondary leading-relaxed">
            Evaluated against live multi-system scenarios using a frozen judge across five core
            dimensions.
          </p>
        </div>

        {/* 4 Metric Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
          {metrics.map((metric, idx) => (
            <div
              key={idx}
              className="bg-surface border border-border rounded-md p-6 text-center shadow-sm"
            >
              <div className="font-mono text-2xl sm:text-3xl font-extrabold text-brand-primary mb-2 whitespace-nowrap">
                {metric.num}
              </div>
              <h3 className="text-sm font-bold text-txt-primary mb-1.5">{metric.heading}</h3>
              <p className="text-xs text-txt-secondary leading-relaxed">{metric.detail}</p>
            </div>
          ))}
        </div>

        {/* Context Card */}
        <div className="bg-surface border border-brand-border border-l-4 border-l-brand-primary rounded-md p-5 mb-5 flex flex-col gap-2">
          <h3 className="text-sm font-bold text-txt-primary">
            Fresh context for every investigation
          </h3>
          <p className="text-xs text-txt-secondary leading-relaxed">
            New investigations don&apos;t silently inherit conclusions or assumptions from earlier
            ones.
          </p>
        </div>

        {/* Transparency Note */}
        <div className="bg-surface-subtle border border-border rounded-md p-3.5 text-xs text-txt-secondary leading-relaxed flex items-baseline gap-2.5">
          <span className="text-brand-primary font-bold" aria-hidden="true">
            ℹ
          </span>
          <span>
            <strong className="text-txt-primary">Evaluation Methodology:</strong> Benchmarked on
            synthetic fintech scenarios using pinned mock adapters (Zendesk Mock and Jira
            MockServer) to enable 100% reproducible testing. Zero truncations or retries in final
            validation.
          </span>
        </div>
      </div>
    </section>
  );
}
