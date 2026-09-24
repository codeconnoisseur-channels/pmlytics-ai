import React from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { InvestigationPreview } from '@/components/landing/InvestigationPreview';

export interface HeroProps {
  isAuthenticated?: boolean;
}

export function Hero({ isAuthenticated = false }: HeroProps) {
  return (
    <section className="relative overflow-hidden border-b border-black/10 bg-[#f4f5f2] pb-20 pt-10 sm:pb-24 sm:pt-14" id="product">
      <div className="marketing-grid pointer-events-none absolute inset-x-0 top-0 h-[620px] opacity-75 [mask-image:linear-gradient(to_bottom,black,transparent)]" aria-hidden="true" />

      <div className="relative mx-auto w-full max-w-[1240px] px-5 sm:px-8">
        <div className="marketing-grid relative mx-auto max-w-[1120px] overflow-hidden rounded-[30px] border border-white/65 bg-white/45 px-5 py-11 text-center shadow-[0_16px_44px_-38px_rgba(23,25,21,0.48)] backdrop-blur-md sm:px-10 sm:py-14 lg:px-20">
          <div className="pointer-events-none absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#c8f46b]/28 blur-3xl" aria-hidden="true" />
          <div className="pointer-events-none absolute inset-x-[12%] bottom-0 h-px bg-gradient-to-r from-transparent via-[#a8dc42] to-transparent" aria-hidden="true" />
          <div className="relative mx-auto max-w-[900px]">
            <h1 className="text-balance text-[clamp(2.2rem,5vw,4.35rem)] font-black leading-[1] tracking-[-0.055em] text-[#171915]">
              Turn scattered product signals into a clear next move.
            </h1>
            <p className="mx-auto mt-5 max-w-[760px] text-pretty text-base leading-7 text-[#5c6159] sm:text-lg sm:leading-8">
              PMLytics AI brings together customer support, product analytics, and engineering
              context to explain what&apos;s happening, recommend what to do next, and show the
              evidence behind the decision.
            </p>

            <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href={isAuthenticated ? '/investigations' : '/auth/signup'}
                className="inline-flex h-12 w-full touch-manipulation items-center justify-center gap-2 rounded-full bg-[#171915] px-6 text-sm font-bold text-white shadow-[0_8px_24px_-12px_rgba(23,25,21,0.8)] transition-[background-color,transform] hover:-translate-y-0.5 hover:bg-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] focus-visible:ring-offset-2 sm:w-auto"
              >
                {isAuthenticated ? 'Start an Investigation' : 'Create Account'}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <Link
                href="/investigations/inv_p12a_scenario_1"
                className="inline-flex h-12 w-full touch-manipulation items-center justify-center rounded-full border border-black/15 bg-white/80 px-6 text-sm font-bold text-[#171915] transition-[background-color,border-color,transform] hover:-translate-y-0.5 hover:border-black/30 hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] sm:w-auto"
              >
                View a Sample Brief
              </Link>
            </div>
          </div>
        </div>

        <div className="mt-12 sm:mt-14">
          <InvestigationPreview />
        </div>
      </div>
    </section>
  );
}
