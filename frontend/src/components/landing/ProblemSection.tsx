import React from 'react';
import { ArrowDownRight, BarChart3, MessageSquareText, Wrench } from 'lucide-react';

const sources = [
  {
    name: 'Customer Support',
    heading: 'Hear the Customer Problem',
    copy: 'Identify recurring complaints, affected customers, and the language people use to describe the experience.',
    sample: '12 conversations describe transfers as pending or missing.',
    icon: MessageSquareText,
    badge: 'Zendesk',
    style: 'bg-[#eaf6f0] border-[#c7e7d8]',
    iconStyle: 'bg-[#176b4b] text-white',
  },
  {
    name: 'Product Analytics',
    heading: 'Measure What Users Do',
    copy: 'Examine conversion, drop-off, failures, timing, and meaningful differences between customer segments.',
    sample: '910 of 920 transfers completed; confirmation lag is concentrated in 2 banks.',
    icon: BarChart3,
    badge: 'PostHog',
    style: 'bg-[#eeeafb] border-[#d9d0f0]',
    iconStyle: 'bg-[#6545a4] text-white',
  },
  {
    name: 'Engineering Context',
    heading: 'Understand What Is Already Known',
    copy: 'Connect the customer problem to relevant incidents, defects, investigations, and delivery work.',
    sample: 'PAY-117 tracks delayed status updates for Bank A and Bank B.',
    icon: Wrench,
    badge: 'Jira',
    style: 'bg-[#eaf0f8] border-[#cbd9ec]',
    iconStyle: 'bg-[#2f5f9f] text-white',
  },
];

export function ProblemSection() {
  return (
    <section className="scroll-mt-20 border-b border-black/10 bg-[#fbfcf9] py-20 sm:py-28" id="features">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="mx-auto max-w-[900px] text-center">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[#6c7168]">One investigation, 3 perspectives</p>
            <h2 className="mx-auto mt-4 max-w-[760px] text-balance text-3xl font-black leading-[1.05] tracking-[-0.045em] text-[#171915] sm:text-5xl">
              Your evidence is scattered. Your decision shouldn&apos;t be.
            </h2>
          </div>
          <p className="mx-auto mt-5 max-w-[780px] text-pretty text-base leading-7 text-[#62675f]">
            Customer conversations reveal what people are experiencing. Product analytics shows
            what they are doing. Engineering issues explain what may already be known or underway.
            PMLytics connects all 3 before recommending what to do next.
          </p>
        </div>

        <div className="mt-12 grid gap-4 lg:grid-cols-3">
          {sources.map(({ name, heading, copy, sample, icon: Icon, badge, style, iconStyle }) => (
            <article
              key={name}
              className={`group relative flex min-h-[360px] flex-col overflow-hidden rounded-[24px] border p-6 transition-[transform,box-shadow] hover:-translate-y-1 hover:shadow-[0_24px_55px_-40px_rgba(23,25,21,0.7)] sm:p-7 ${style}`}
            >
              <div className="flex items-start justify-between gap-4">
                <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${iconStyle}`}>
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span className="rounded-full border border-black/10 bg-white/60 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.12em] text-[#555a52]">
                  {badge}
                </span>
              </div>
              <p className="mt-8 text-xs font-bold text-[#686d64]">{name}</p>
              <h3 className="mt-2 text-balance text-xl font-black tracking-[-0.03em] text-[#171915] sm:text-2xl">{heading}</h3>
              <p className="mt-3 max-w-[560px] text-sm leading-6 text-[#596057]">{copy}</p>
              <div className="mt-auto rounded-2xl border border-black/10 bg-white/70 p-4">
                <div className="flex items-start gap-3">
                  <ArrowDownRight className="mt-0.5 h-4 w-4 shrink-0 text-[#171915]" aria-hidden="true" />
                  <p className="text-xs font-semibold leading-5 text-[#363a34]">{sample}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
