import React from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

export interface CTASectionProps {
  isAuthenticated?: boolean;
}

export function CTASection({ isAuthenticated = false }: CTASectionProps) {
  return (
    <section className="bg-[#fbfcf9] py-20 sm:py-28">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="marketing-grid relative overflow-hidden rounded-[30px] border border-black/10 bg-[#eef0eb] px-6 py-16 text-center sm:px-12 sm:py-20">
          <div className="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#c8f46b]/30 blur-3xl" aria-hidden="true" />
          <div className="relative mx-auto max-w-[760px]">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[#6c7168]">Your next decision</p>
            <h2 className="mt-4 text-balance text-3xl font-black leading-[1.02] tracking-[-0.05em] text-[#171915] sm:text-5xl">
              Bring your next product question.
            </h2>
            <p className="mx-auto mt-5 max-w-[640px] text-pretty text-base leading-7 text-[#62675f]">
              Get a clear recommendation, measurable success criteria, and the evidence your team needs to move forward with confidence.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Link
                href={isAuthenticated ? '/investigations' : '/auth/signup'}
                className="inline-flex h-12 touch-manipulation items-center justify-center gap-2 rounded-full bg-[#171915] px-6 text-sm font-bold text-white transition-[background-color,transform] hover:-translate-y-0.5 hover:bg-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] focus-visible:ring-offset-2"
              >
                Start an Investigation <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <Link
                href="/investigations/inv_p12a_scenario_1"
                className="inline-flex h-12 touch-manipulation items-center justify-center rounded-full border border-black/15 bg-white px-6 text-sm font-bold text-[#171915] transition-[background-color,border-color,transform] hover:-translate-y-0.5 hover:border-black/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]"
              >
                View a Sample Brief
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
