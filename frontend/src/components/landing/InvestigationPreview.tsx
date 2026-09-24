import React from 'react';
import { BrandLogo } from '@/components/brand/BrandLogo';
import {
  BarChart3,
  Check,
  FileText,
  LayoutDashboard,
  MessageSquareText,
  ShieldCheck,
  Target,
  Wrench,
} from 'lucide-react';

const sourceEvidence = [
  {
    name: 'Customer Support',
    detail: '12 customer conversations',
    icon: MessageSquareText,
    color: 'bg-[#e7f6ef] text-[#176b4b]',
  },
  {
    name: 'Product Analytics',
    detail: '920 transfer attempts',
    icon: BarChart3,
    color: 'bg-[#eeeafb] text-[#6545a4]',
  },
  {
    name: 'Engineering',
    detail: 'PAY-117 in progress',
    icon: Wrench,
    color: 'bg-[#e9f0fb] text-[#2f5f9f]',
  },
];

export function InvestigationPreview() {
  return (
    <div className="grid gap-3 lg:grid-cols-[180px_minmax(0,1fr)_180px] lg:grid-rows-2">
      <div className="order-2 grid grid-cols-3 gap-3 lg:order-1 lg:row-span-2 lg:grid-cols-1">
        {sourceEvidence.map(({ name, detail, icon: Icon, color }) => (
          <div key={name} className="min-w-0 rounded-2xl border border-black/10 bg-[#fbfcf9] p-3.5 shadow-[0_12px_30px_-26px_rgba(23,25,21,0.7)] sm:p-4">
            <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${color}`}>
              <Icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <p className="mt-4 text-[11px] font-bold leading-tight text-[#171915] sm:text-xs">{name}</p>
            <p className="mt-1 break-words text-[10px] leading-4 text-[#73786f] sm:text-[11px]">{detail}</p>
          </div>
        ))}
      </div>

      <article className="order-1 overflow-hidden rounded-[22px] border border-black/15 bg-white shadow-[0_30px_70px_-38px_rgba(23,25,21,0.55)] lg:order-2 lg:row-span-2">
        <div className="flex h-12 items-center justify-between border-b border-black/10 bg-[#fbfcf9] px-4 sm:px-5">
          <div className="flex min-w-0 items-center gap-2">
            <BrandLogo showName={false} markClassName="h-7 w-7" />
            <span className="truncate text-xs font-extrabold tracking-tight text-[#171915]" translate="no">PMLytics AI</span>
            <span className="hidden text-[#a5aaa1] sm:inline" aria-hidden="true">/</span>
            <span className="hidden truncate text-xs text-[#73786f] sm:inline">Decision brief</span>
          </div>
          <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-[#e7f6ef] px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-[#176b4b]">
            <ShieldCheck className="h-3 w-3" aria-hidden="true" />
            Completed
          </span>
        </div>

        <div className="grid md:grid-cols-[150px_minmax(0,1fr)]">
          <aside className="hidden border-r border-black/10 bg-[#f7f8f5] p-3 md:block" aria-label="Workspace navigation preview">
            <p className="px-2 pb-2 pt-1 text-[9px] font-black uppercase tracking-[0.15em] text-[#989d94]">Workspace</p>
            <div className="space-y-1 text-[11px]">
              <span className="flex items-center gap-2 rounded-lg bg-white px-2.5 py-2 font-bold text-[#171915] shadow-sm">
                <LayoutDashboard className="h-3.5 w-3.5" aria-hidden="true" /> Overview
              </span>
              <span className="flex items-center gap-2 px-2.5 py-2 text-[#73786f]">
                <FileText className="h-3.5 w-3.5" aria-hidden="true" /> Investigations
              </span>
            </div>
            <div className="mt-8 border-t border-black/10 px-2 pt-4">
              <p className="text-[9px] font-black uppercase tracking-[0.15em] text-[#989d94]">Evidence</p>
              <p className="mt-2 text-[11px] font-semibold text-[#4f544d]">3 source summaries</p>
              <p className="mt-1 text-[10px] leading-4 text-[#7b8078]">17 supporting records</p>
            </div>
          </aside>

          <div className="min-w-0 p-4 sm:p-5 lg:p-6">
            <div className="border-b border-black/10 pb-4">
              <p className="text-[9px] font-black uppercase tracking-[0.16em] text-[#8a8f86]">Product question</p>
              <h2 className="mt-1.5 max-w-[620px] text-pretty text-base font-extrabold leading-snug tracking-[-0.02em] text-[#171915] sm:text-lg">
                Why are customers reporting a surge in failed transfers this week?
              </h2>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-semibold text-[#73786f]">
                <span>98.5s</span><span aria-hidden="true">•</span><span>12 Records</span><span aria-hidden="true">•</span><span>10 to 15 Aug 2026</span>
              </div>
            </div>

            <section className="mt-4 rounded-xl bg-[#171915] p-4 text-white sm:p-5" aria-label="Recommendation preview">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-[10px] font-black uppercase tracking-[0.16em] text-[#c8f46b]">Recommendation</p>
                <div className="flex gap-1.5">
                  <span className="rounded-full bg-white/10 px-2 py-1 text-[9px] font-bold uppercase">Prioritise</span>
                  <span className="rounded-full bg-[#c8f46b] px-2 py-1 text-[9px] font-black text-[#171915]">High</span>
                </div>
              </div>
              <p className="mt-3 text-sm font-bold leading-relaxed sm:text-base">
                Restore transfer-status delivery for Bank A and Bank B.
              </p>
              <p className="mt-2 text-[11px] leading-5 text-white/70 sm:text-xs">
                Give customers a clear pending state and safe status check while the synchronisation fix is delivered.
              </p>
            </section>

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-black/10 bg-[#f7f8f5] p-3.5">
                <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.12em] text-[#62675f]">
                  <Target className="h-3.5 w-3.5" aria-hidden="true" /> How Success Will Be Measured
                </div>
                <p className="mt-2 text-xs font-bold text-[#171915]">p95 confirmation under 30 seconds</p>
                <p className="mt-1 text-[10px] text-[#73786f]">Then 50% fewer status contacts</p>
              </div>
              <div className="rounded-xl border border-black/10 bg-white p-3.5">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[10px] font-black uppercase tracking-[0.12em] text-[#62675f]">Evidence Considered</p>
                  <span className="font-mono text-[9px] font-bold text-[#6545a4]">[EV-002]</span>
                </div>
                <div className="mt-2 space-y-1.5">
                  {['Customer support reviewed', 'Product behaviour measured', 'Engineering work connected'].map((item) => (
                    <p key={item} className="flex items-center gap-1.5 text-[10px] text-[#62675f]">
                      <Check className="h-3 w-3 text-[#5f8f2b]" aria-hidden="true" /> {item}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </article>

      <div className="order-3 rounded-2xl border border-[#aed955] bg-[#c8f46b] p-5 shadow-[0_14px_34px_-24px_rgba(67,90,26,0.8)]">
        <p className="text-[10px] font-black uppercase tracking-[0.14em] text-[#49621f]">Target outcome</p>
        <p className="mt-3 text-4xl font-black tracking-[-0.05em] text-[#171915]">&lt;30s</p>
        <p className="mt-2 text-xs font-semibold leading-5 text-[#374718]">Bank A and Bank B confirmation time</p>
      </div>

      <div className="order-4 rounded-2xl border border-black/10 bg-[#171915] p-5 text-white shadow-[0_14px_34px_-24px_rgba(23,25,21,0.8)]">
        <p className="text-[10px] font-black uppercase tracking-[0.14em] text-white/50">Decision confidence</p>
        <p className="mt-3 text-4xl font-black tracking-[-0.05em] text-[#c8f46b]">High</p>
        <p className="mt-2 text-xs leading-5 text-white/65">Supported across all 3 evidence sources</p>
      </div>
    </div>
  );
}
