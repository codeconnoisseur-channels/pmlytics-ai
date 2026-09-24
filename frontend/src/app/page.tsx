import React from 'react';
import { LandingHeader } from '@/components/landing/LandingHeader';
import { Hero } from '@/components/landing/Hero';
import { ProblemSection } from '@/components/landing/ProblemSection';
import { WorkflowSection } from '@/components/landing/WorkflowSection';
import { EvidenceSection } from '@/components/landing/EvidenceSection';
import { EpistemicSection } from '@/components/landing/EpistemicSection';
import { ScenarioSection } from '@/components/landing/ScenarioSection';
import { PricingSection } from '@/components/landing/PricingSection';
import { FAQSection } from '@/components/landing/FAQSection';
import { CTASection } from '@/components/landing/CTASection';
import { LandingFooter } from '@/components/landing/LandingFooter';
import { createClient } from '@/lib/supabase/server';

export const metadata = {
  title: 'PMLytics AI',
  description:
    'Turn customer support, product analytics, and engineering context into a clear, evidence-backed product decision.',
};

export default async function HomePage() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  const isAuthenticated = Boolean(data?.claims?.sub);

  return (
    <div className="marketing-page min-h-screen overflow-x-clip bg-[#f4f5f2] text-[#171915]">
      <a
        href="#main-content"
        className="fixed left-4 top-3 z-[100] -translate-y-20 rounded-full bg-[#171915] px-4 py-2 text-sm font-semibold text-white transition-transform focus:translate-y-0"
      >
        Skip to content
      </a>
      <LandingHeader isAuthenticated={isAuthenticated} />

      <main id="main-content" className="flex-grow" role="main">
        <Hero isAuthenticated={isAuthenticated} />
        <ProblemSection />
        <WorkflowSection />
        <EvidenceSection />
        <EpistemicSection />
        <ScenarioSection />
        <PricingSection isAuthenticated={isAuthenticated} />
        <FAQSection />
        <CTASection isAuthenticated={isAuthenticated} />
      </main>
      <LandingFooter />
    </div>
  );
}
