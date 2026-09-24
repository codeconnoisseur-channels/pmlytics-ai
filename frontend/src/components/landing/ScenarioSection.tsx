import React from 'react';
import Link from 'next/link';
import { ArrowUpRight, BarChart3, MessageSquareText, Wrench } from 'lucide-react';

const scenarios = [
  {
    area: 'Transfers',
    question: 'Why are customers reporting a surge in failed transfers this week?',
    conclusion: 'Prioritise status synchronisation for Bank A and Bank B; the larger problem is delayed confirmation, not failed settlement.',
    decision: 'Prioritise',
    href: '/investigations/inv_p12a_scenario_1',
    style: 'bg-[#171915] text-white border-[#171915]',
    muted: 'text-white/60',
    badge: 'bg-[#c8f46b] text-[#171915]',
  },
  {
    area: 'User Verification',
    question: 'Why did user verification drop off at the identity upload step for new signups?',
    conclusion: 'Test clearer document guidance and a specific retry path, while delivering the small Android camera fix separately.',
    decision: 'Experiment',
    href: '/investigations/inv_p12a_scenario_2',
    style: 'bg-[#eaf6f0] text-[#171915] border-[#c7e7d8]',
    muted: 'text-[#576159]',
    badge: 'bg-white/70 text-[#176b4b]',
  },
  {
    area: 'Wallet Funding',
    question: 'Why are debit card wallet funding transactions failing at elevated rates?',
    conclusion: 'Do not open an incident. Test earlier fee disclosure for higher-value funding attempts.',
    decision: 'Experiment',
    href: '/investigations/inv_p12a_scenario_3',
    style: 'bg-[#eeeafb] text-[#171915] border-[#d9d0f0]',
    muted: 'text-[#5f5870]',
    badge: 'bg-white/70 text-[#6545a4]',
  },
  {
    area: 'Bill Payments',
    question: 'What is causing utility bill payment timeouts during peak month-end settlement?',
    conclusion: 'Treat this as an active electricity-payment incident while keeping unaffected bill categories available.',
    decision: 'Technical Fix',
    href: '/investigations/inv_p12a_scenario_4',
    style: 'bg-[#c8f46b] text-[#171915] border-[#aed955]',
    muted: 'text-[#425220]',
    badge: 'bg-[#171915] text-white',
  },
];

export function ScenarioSection() {
  return (
    <section className="scroll-mt-20 border-b border-black/10 bg-[#f4f5f2] py-20 sm:py-28" id="scenarios">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="grid gap-6 lg:grid-cols-2 lg:items-end">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[#6c7168]">Sample Investigations</p>
            <h2 className="mt-4 max-w-[650px] text-balance text-3xl font-black leading-[1.05] tracking-[-0.045em] text-[#171915] sm:text-5xl">
              Explore completed product investigations.
            </h2>
          </div>
          <p className="max-w-[580px] text-pretty text-base leading-7 text-[#62675f] lg:justify-self-end">
            See how PMLytics approaches different product questions and turns cross-functional evidence into a recommended next step.
          </p>
        </div>

        <div className="mt-14 grid gap-4 md:grid-cols-2">
          {scenarios.map((scenario) => (
            <Link
              key={scenario.area}
              href={scenario.href}
              className={`group flex min-h-[330px] flex-col rounded-[26px] border p-6 transition-[transform,box-shadow] hover:-translate-y-1 hover:shadow-[0_26px_55px_-38px_rgba(23,25,21,0.75)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] focus-visible:ring-offset-2 sm:p-8 ${scenario.style}`}
            >
              <div className="flex items-center justify-between gap-4">
                <span className="text-xs font-black uppercase tracking-[0.14em]">{scenario.area}</span>
                <span className={`rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-wide ${scenario.badge}`}>{scenario.decision}</span>
              </div>
              <h3 className="mt-9 max-w-[540px] text-pretty text-xl font-black leading-snug tracking-[-0.03em] sm:text-2xl">{scenario.question}</h3>
              <p className={`mt-4 max-w-[560px] text-sm leading-6 ${scenario.muted}`}>{scenario.conclusion}</p>
              <div className="mt-auto flex flex-wrap items-end justify-between gap-4 pt-9">
                <div className="flex items-center gap-1.5" aria-label="Evidence from customer support, product analytics, and engineering">
                  {[MessageSquareText, BarChart3, Wrench].map((Icon, index) => (
                    <span key={index} className="flex h-8 w-8 items-center justify-center rounded-full border border-current/15 bg-white/20">
                      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                    </span>
                  ))}
                </div>
                <span className="inline-flex items-center gap-2 text-xs font-black underline decoration-current/30 underline-offset-4">
                  View Decision Brief <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden="true" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
