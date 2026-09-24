import React from 'react';
import { CheckCircle2, Lightbulb, SearchCheck } from 'lucide-react';

const findings = [
  {
    label: 'What We Know',
    icon: CheckCircle2,
    accent: 'bg-[#176b4b]',
    iconColor: 'text-[#176b4b]',
    cardStyle: 'bg-[#eaf6f0] border-[#c7e7d8]',
    iconStyle: 'bg-white/75',
    text: 'Twelve customer conversations describe transfers as pending or missing, while 910 of 920 observed transfers completed.',
    citation: '[EV-001] [EV-002]',
  },
  {
    label: 'What It Means',
    icon: SearchCheck,
    accent: 'bg-[#2f5f9f]',
    iconColor: 'text-[#2f5f9f]',
    cardStyle: 'bg-[#eaf0f8] border-[#cbd9ec]',
    iconStyle: 'bg-white/75',
    text: 'The customer problem is status uncertainty rather than a broad increase in failed settlement.',
    citation: '[EV-001] [EV-002]',
  },
  {
    label: 'What to Test Next',
    icon: Lightbulb,
    accent: 'bg-[#b47618]',
    iconColor: 'text-[#b47618]',
    cardStyle: 'bg-[#fbf3df] border-[#ead9ae]',
    iconStyle: 'bg-white/75',
    text: 'A clearer pending state may reduce support demand while the synchronisation fix is completed.',
    citation: '[EV-001] [EV-003]',
  },
];

export function EpistemicSection() {
  return (
    <section className="border-b border-black/10 bg-[#fbfcf9] py-20 sm:py-28" id="epistemic">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="mx-auto max-w-[820px] text-center">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[#6c7168]">Clear about certainty</p>
          <h2 className="mt-4 text-balance text-3xl font-black leading-[1.05] tracking-[-0.045em] text-[#171915] sm:text-5xl">
            See what the evidence proves, and where judgment begins.
          </h2>
          <p className="mx-auto mt-5 max-w-[700px] text-pretty text-base leading-7 text-[#62675f]">
            PMLytics separates verified observations from interpretation and questions that still need testing, so confidence never outruns the evidence.
          </p>
        </div>

        <div className="mt-14">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3 px-1">
            <div>
              <p className="text-[10px] font-black uppercase tracking-[0.14em] text-[#7b8078]">Evidence-Backed Findings</p>
              <p className="mt-1 text-sm font-bold text-[#171915]">Transfer status investigation</p>
            </div>
            <span className="rounded-full bg-[#c8f46b] px-3 py-1.5 text-[10px] font-black uppercase tracking-wide text-[#171915]">Decision-ready</span>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {findings.map(({ label, icon: Icon, iconColor, cardStyle, iconStyle, text, citation }) => (
              <article key={label} className={`relative min-w-0 rounded-[24px] border p-6 shadow-[0_18px_42px_-38px_rgba(23,25,21,0.68)] sm:p-7 ${cardStyle}`}>
                <span className={`flex h-11 w-11 items-center justify-center rounded-xl border border-black/10 ${iconStyle}`}>
                  <Icon className={`h-5 w-5 ${iconColor}`} aria-hidden="true" />
                </span>
                <h3 className="mt-5 text-lg font-black tracking-[-0.02em] text-[#171915]">{label}</h3>
                <p className="mt-3 text-sm leading-6 text-[#62675f]">{text}</p>
                <p className="mt-5 break-words font-mono text-[10px] font-bold text-[#858a81]">{citation}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
