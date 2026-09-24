'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Check } from 'lucide-react';

interface PricingSectionProps {
  isAuthenticated?: boolean;
}

type BillingPeriod = 'monthly' | 'yearly';

interface PricingPlan {
  name: string;
  audience: string;
  monthlyPrice?: number;
  yearlyPrice?: number;
  description: string;
  features: string[];
  cta: string;
  featured?: boolean;
}

const plans: PricingPlan[] = [
  {
    name: 'Starter',
    audience: 'For individuals',
    monthlyPrice: 12,
    yearlyPrice: 10,
    description: 'Investigate important product questions without assembling evidence by hand.',
    features: ['10 investigations each month', 'Decision-ready briefs', 'Traceable evidence'],
    cta: 'Start with Starter',
  },
  {
    name: 'Team',
    audience: 'For collaborative decision-making',
    monthlyPrice: 39,
    yearlyPrice: 31,
    description: 'Create a consistent investigation practice across the people making product decisions.',
    features: ['50 investigations each month', 'Shared investigation history', 'Team onboarding'],
    cta: 'Choose Team',
    featured: true,
  },
  {
    name: 'Enterprise',
    audience: 'Built around your organisation',
    description: 'Shape a custom rollout around your data environment, governance, and operating model.',
    features: ['Custom investigation volume', 'Custom data integrations', 'Security and rollout support'],
    cta: 'Contact Sales',
  },
];

export function PricingSection({ isAuthenticated = false }: PricingSectionProps) {
  const [billingPeriod, setBillingPeriod] = useState<BillingPeriod>('monthly');

  return (
    <section id="pricing" className="scroll-mt-24 border-b border-black/10 bg-[#f4f5f2] py-20 sm:py-28">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="mx-auto max-w-[780px] text-center">
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[#6c7168]">Pricing</p>
          <h2 className="mt-4 text-balance text-3xl font-black leading-[1.05] tracking-[-0.045em] text-[#171915] sm:text-5xl">
            Pricing that scales with your product practice.
          </h2>
          <p className="mx-auto mt-5 max-w-[680px] text-pretty text-base leading-7 text-[#62675f]">
            Start with the essentials for evidence-backed decisions, then add the collaboration and support your organisation needs.
          </p>

          <div className="mx-auto mt-8 inline-flex rounded-full border border-black/10 bg-white p-1 shadow-sm" role="group" aria-label="Billing period">
            <button
              type="button"
              aria-pressed={billingPeriod === 'monthly'}
              onClick={() => setBillingPeriod('monthly')}
              className={`min-h-10 touch-manipulation rounded-full px-5 text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] focus-visible:ring-offset-2 ${billingPeriod === 'monthly' ? 'bg-[#171915] text-white' : 'text-[#62675f] hover:bg-[#f1f3ee] hover:text-[#171915]'}`}
            >
              Monthly
            </button>
            <button
              type="button"
              aria-pressed={billingPeriod === 'yearly'}
              onClick={() => setBillingPeriod('yearly')}
              className={`min-h-10 touch-manipulation rounded-full px-5 text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] focus-visible:ring-offset-2 ${billingPeriod === 'yearly' ? 'bg-[#171915] text-white' : 'text-[#62675f] hover:bg-[#f1f3ee] hover:text-[#171915]'}`}
            >
              Yearly <span className="ml-1 text-[#65872e]">Save 20%</span>
            </button>
          </div>
        </div>

        <div className="mt-12 grid gap-4 lg:grid-cols-3">
          {plans.map((plan) => {
            const price = billingPeriod === 'yearly' ? plan.yearlyPrice : plan.monthlyPrice;
            const href = plan.name === 'Enterprise'
              ? 'mailto:hello@pmlytics.ai?subject=PMLytics%20Enterprise'
              : isAuthenticated
                ? '/investigations'
                : '/auth/signup';
            return (
              <article
                key={plan.name}
                className={`flex min-h-[430px] flex-col rounded-[24px] border p-6 sm:p-7 ${plan.featured ? 'border-[#2d3029] bg-[#171915] text-white shadow-[0_24px_60px_-38px_rgba(23,25,21,0.8)]' : 'border-black/10 bg-[#fbfcf9] text-[#171915]'}`}
              >
                <div>
                  <p className={`text-xs font-bold ${plan.featured ? 'text-[#c8f46b]' : 'text-[#6c7168]'}`}>{plan.audience}</p>
                  <h3 className="mt-3 text-2xl font-black tracking-[-0.035em]">{plan.name}</h3>
                  {price ? (
                    <div className="mt-5 flex items-end gap-2">
                      <span className="text-4xl font-black tracking-[-0.05em]">${price}</span>
                      <span className={`pb-1 text-sm ${plan.featured ? 'text-white/60' : 'text-[#73786f]'}`}>per month</span>
                    </div>
                  ) : null}
                  {price && billingPeriod === 'yearly' ? <p className={`mt-1 text-xs ${plan.featured ? 'text-white/55' : 'text-[#777c74]'}`}>Billed annually</p> : null}
                  <p className={`mt-4 text-sm leading-6 ${plan.featured ? 'text-white/70' : 'text-[#62675f]'}`}>{plan.description}</p>
                </div>

                <ul className={`mt-7 space-y-3 border-t pt-6 text-sm ${plan.featured ? 'border-white/15 text-white/80' : 'border-black/10 text-[#4f544d]'}`}>
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2.5">
                      <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${plan.featured ? 'bg-[#c8f46b] text-[#171915]' : 'bg-[#eff8df] text-[#476017]'}`}>
                        <Check className="h-3 w-3" aria-hidden="true" />
                      </span>
                      {feature}
                    </li>
                  ))}
                </ul>

                <Link
                  href={href}
                  className={`mt-auto inline-flex min-h-11 touch-manipulation items-center justify-center rounded-full px-5 text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${plan.featured ? 'bg-[#c8f46b] text-[#171915] hover:bg-[#d7ff82] focus-visible:ring-[#c8f46b] focus-visible:ring-offset-[#171915]' : 'border border-black/15 bg-white text-[#171915] hover:border-black/30 hover:bg-[#f7f8f5] focus-visible:ring-[#171915]'}`}
                >
                  {isAuthenticated && plan.name !== 'Enterprise' ? 'Open Workspace' : plan.cta}
                </Link>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
