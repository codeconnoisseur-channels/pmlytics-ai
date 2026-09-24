import React from 'react';
import { ArrowRight, Check, Search, Sparkles, Target, Waypoints } from 'lucide-react';

const steps = [
  {
    number: '01',
    title: 'Ask',
    description: 'Submit the product question and choose the period you want to investigate.',
    icon: Search,
  },
  {
    number: '02',
    title: 'Gather',
    description: 'Review relevant customer conversations, product behaviour, and engineering context.',
    icon: Waypoints,
  },
  {
    number: '03',
    title: 'Synthesize',
    description: 'Compare the evidence across sources and identify the clearest explanation.',
    icon: Sparkles,
  },
  {
    number: '04',
    title: 'Challenge',
    description: 'Test the recommendation for unsupported claims, conflicting evidence, and excessive confidence.',
    icon: Check,
  },
  {
    number: '05',
    title: 'Decide',
    description: 'Receive a recommended action, success measures, and a traceable evidence trail.',
    icon: Target,
  },
];

export function WorkflowSection() {
  return (
    <section className="scroll-mt-20 border-b border-black/10 bg-[#f4f5f2] py-20 sm:py-28" id="how-it-works">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="mx-auto max-w-[780px] text-center">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[#6c7168]">How It Works</p>
          <h2 className="mt-4 text-balance text-3xl font-black leading-[1.05] tracking-[-0.045em] text-[#171915] sm:text-5xl">
            From product question to confident next step.
          </h2>
          <p className="mx-auto mt-5 max-w-[680px] text-pretty text-base leading-7 text-[#62675f]">
            PMLytics follows a structured investigation process while keeping the final experience focused on the decision your team needs to make.
          </p>
        </div>

        <div className="relative mt-14">
          <ol className="relative grid gap-3 lg:grid-cols-[minmax(0,1fr)_28px_minmax(0,1fr)_28px_minmax(0,1fr)_28px_minmax(0,1fr)_28px_minmax(0,1fr)] lg:gap-2">
            {steps.map(({ number, title, description, icon: Icon }, index) => (
              <React.Fragment key={number}>
                <li className="group relative rounded-[22px] border border-black/10 bg-[#fbfcf9] p-5 transition-[transform,box-shadow] hover:-translate-y-1 hover:shadow-[0_22px_45px_-36px_rgba(23,25,21,0.8)] lg:min-h-[270px] lg:p-5">
                  <div className={`relative z-10 flex h-14 w-14 items-center justify-center rounded-2xl border border-black/10 ${index === steps.length - 1 ? 'bg-[#c8f46b] text-[#171915]' : 'bg-white text-[#565b53]'}`}>
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <p className="mt-7 font-mono text-[10px] font-bold tracking-[0.16em] text-[#8a8f86]">{number}</p>
                  <h3 className="mt-2 text-xl font-black tracking-[-0.03em] text-[#171915]">{title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[#62675f]">{description}</p>
                </li>
                {index < steps.length - 1 ? (
                  <li className="hidden items-center justify-center lg:flex" aria-hidden="true">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full border border-black/10 bg-white text-[#747970]">
                      <ArrowRight className="h-3.5 w-3.5" />
                    </span>
                  </li>
                ) : null}
              </React.Fragment>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
