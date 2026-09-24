import React from 'react';
import { ArrowRight, BarChart3, ChevronDown, ShieldCheck } from 'lucide-react';

const metrics = [
  { label: 'Bank A', value: 'p95 3h 36m' },
  { label: 'Bank B', value: 'p95 3h 46m' },
  { label: 'Other banks', value: 'p95 ~5s' },
];

export function EvidenceSection() {
  return (
    <section className="scroll-mt-20 border-b border-black/10 bg-[#171915] py-20 text-white sm:py-28" id="evidence">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-end">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[#c8f46b]">Built for scrutiny</p>
            <h2 className="mt-4 max-w-[640px] text-balance text-3xl font-black leading-[1.05] tracking-[-0.045em] sm:text-5xl">
              Every recommendation is traceable.
            </h2>
          </div>
          <p className="max-w-[620px] text-pretty text-base leading-7 text-white/65 lg:justify-self-end">
            Open any citation to see the customer conversations, product measurements, and
            engineering issues that support the decision without cluttering the main report.
          </p>
        </div>

        <div className="mt-14 grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_48px_minmax(0,1.1fr)] lg:items-center">
          <article className="rounded-[24px] border border-white/15 bg-white/[0.06] p-6 sm:p-8">
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-white/45">Claim in the Report</p>
            <p className="mt-5 text-pretty text-lg font-semibold leading-8 text-white sm:text-2xl sm:leading-9">
              Transfer failures remain low, but customers wait hours for a status update on Bank A and Bank B routes{' '}
              <span className="whitespace-nowrap rounded-md border border-[#c8f46b]/40 bg-[#c8f46b]/15 px-1.5 py-0.5 font-mono text-xs font-black text-[#c8f46b]">[EV-002]</span>.
            </p>
            <div className="mt-8 flex items-center gap-2 border-t border-white/10 pt-5 text-xs font-bold text-white/60">
              <ShieldCheck className="h-4 w-4 text-[#c8f46b]" aria-hidden="true" />
              Citation remains attached to the final decision
            </div>
          </article>

          <div className="flex h-12 items-center justify-center lg:h-auto" aria-hidden="true">
            <span className="flex h-10 w-10 rotate-90 items-center justify-center rounded-full border border-white/15 bg-white/10 text-[#c8f46b] lg:rotate-0">
              <ArrowRight className="h-4 w-4" />
            </span>
          </div>

          <article className="overflow-hidden rounded-[24px] border border-white/15 bg-[#fbfcf9] text-[#171915] shadow-[0_28px_65px_-34px_rgba(0,0,0,0.8)]">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-black/10 px-5 py-4 sm:px-6">
              <div className="flex items-center gap-2.5">
                <span className="rounded-md bg-[#eeeafb] px-2 py-1 font-mono text-[10px] font-black text-[#6545a4]">[EV-002]</span>
                <span className="inline-flex items-center gap-1.5 text-xs font-bold">
                  <BarChart3 className="h-3.5 w-3.5 text-[#6545a4]" aria-hidden="true" /> Product Analytics
                </span>
              </div>
              <span className="rounded-full bg-[#e7f6ef] px-2.5 py-1 text-[10px] font-black uppercase text-[#176b4b]">High confidence</span>
            </div>

            <div className="p-5 sm:p-6">
              <p className="text-[10px] font-black uppercase tracking-[0.14em] text-[#7b8078]">Evidence Behind It</p>
              <p className="mt-3 text-sm font-bold leading-6 text-[#171915] sm:text-base">
                910 of 920 observed transfers completed, while Bank A and Bank B status confirmation took hours at the 95th percentile.
              </p>

              <div className="mt-5 grid gap-2 sm:grid-cols-3">
                {metrics.map((metric) => (
                  <div key={metric.label} className="rounded-xl border border-black/10 bg-white p-3">
                    <p className="text-[10px] font-semibold text-[#7b8078]">{metric.label}</p>
                    <p className="mt-1 font-mono text-xs font-black tabular-nums text-[#171915]">{metric.value}</p>
                  </div>
                ))}
              </div>

              <div className="mt-5 rounded-xl border border-black/10 bg-[#f1f3ee] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs font-black">Supporting Records</p>
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#62675f]">4 metric details <ChevronDown className="h-3 w-3" aria-hidden="true" /></span>
                </div>
                <p className="mt-2 text-[11px] leading-5 text-[#62675f]">
                  Review the underlying aggregate measurements when deeper validation is needed.
                </p>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
