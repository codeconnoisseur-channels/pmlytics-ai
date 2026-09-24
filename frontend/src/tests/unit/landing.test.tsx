import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { LandingHeader } from '@/components/landing/LandingHeader';
import { Hero } from '@/components/landing/Hero';
import { InvestigationPreview } from '@/components/landing/InvestigationPreview';
import { ProblemSection } from '@/components/landing/ProblemSection';
import { WorkflowSection } from '@/components/landing/WorkflowSection';
import { EvidenceSection } from '@/components/landing/EvidenceSection';
import { EpistemicSection } from '@/components/landing/EpistemicSection';
import { ScenarioSection } from '@/components/landing/ScenarioSection';
import { CTASection } from '@/components/landing/CTASection';
import { LandingFooter } from '@/components/landing/LandingFooter';
import { PricingSection } from '@/components/landing/PricingSection';
import { FAQSection } from '@/components/landing/FAQSection';
import HomePage from '@/app/page';

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: {
      getClaims: vi.fn(async () => ({ data: { claims: null } })),
    },
  })),
}));

describe('Landing Page Components', () => {
  describe('LandingHeader', () => {
    it('renders brand and navigation links', () => {
      render(<LandingHeader />);
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByText('PMLytics AI')).toBeInTheDocument();

      const nav = screen.getByRole('navigation', { name: /primary navigation/i });
      expect(nav).toBeInTheDocument();
      expect(nav).toHaveTextContent('Product');
      expect(nav).toHaveTextContent('How It Works');
      expect(nav).toHaveTextContent('Pricing');
      expect(nav).not.toHaveTextContent('Sample Investigations');
      expect(screen.getByRole('link', { name: 'Sign In' })).toHaveAttribute(
        'href',
        '/auth/signin'
      );
      expect(screen.getByRole('link', { name: 'Create Account' })).toHaveAttribute('href', '/auth/signup');
    });

    it('shows a direct workspace action to authenticated visitors', () => {
      render(<LandingHeader isAuthenticated />);
      expect(screen.getByRole('link', { name: 'Open Workspace' })).toHaveAttribute('href', '/investigations');
      expect(screen.queryByRole('link', { name: 'Sign In' })).not.toBeInTheDocument();
    });

    it('toggles mobile menu and closes on Escape key', () => {
      render(<LandingHeader />);
      const toggleBtn = screen.getByRole('button', { name: /toggle navigation menu/i });
      expect(toggleBtn).toHaveAttribute('aria-expanded', 'false');

      // Open menu
      fireEvent.click(toggleBtn);
      expect(toggleBtn).toHaveAttribute('aria-expanded', 'true');
      const mobileMenu = screen.getByRole('dialog', { name: /mobile navigation menu/i });
      expect(mobileMenu).toBeInTheDocument();

      // Press Escape
      fireEvent.keyDown(window, { key: 'Escape' });
      expect(toggleBtn).toHaveAttribute('aria-expanded', 'false');
      expect(screen.queryByRole('dialog', { name: /mobile navigation menu/i })).not.toBeInTheDocument();
    });
  });

  describe('Hero & InvestigationPreview', () => {
    it('renders hero headline, supporting copy, and CTAs', () => {
      render(<Hero />);
      expect(screen.queryByText(/product decision support/i)).not.toBeInTheDocument();

      expect(
        screen.getByRole('heading', {
          name: /turn scattered product signals into a clear next move/i,
        })
      ).toBeInTheDocument();

      expect(
        screen.getByText(/PMLytics AI brings together customer support, product analytics/i)
      ).toBeInTheDocument();

      expect(screen.getByRole('link', { name: /create account/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /view a sample brief/i })).toBeInTheDocument();
    });

    it('takes authenticated visitors directly to a new investigation', () => {
      render(<Hero isAuthenticated />);
      expect(screen.getByRole('link', { name: /start an investigation/i })).toBeInTheDocument();
    });

    it('renders a workspace-style decision-brief preview without invented execution metadata', () => {
      render(<InvestigationPreview />);
      expect(screen.getByText('PMLytics AI')).toBeInTheDocument();
      expect(screen.getByText('Decision brief')).toBeInTheDocument();
      expect(screen.getByLabelText('Workspace navigation preview')).toBeInTheDocument();
      expect(screen.getByText('Recommendation')).toBeInTheDocument();
      expect(screen.getByText(/why are customers reporting a surge in failed transfers this week/i)).toBeInTheDocument();
      expect(screen.getByText(/Restore transfer-status delivery for Bank A and Bank B/i)).toBeInTheDocument();
      expect(screen.getByText('How Success Will Be Measured')).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /view the full decision brief/i })).not.toBeInTheDocument();
    });
  });

  describe('ProblemSection', () => {
    it('renders cross-system problem cards for Zendesk, PostHog, and Jira', () => {
      render(<ProblemSection />);
      expect(
        screen.getByRole('heading', { name: /your evidence is scattered. your decision shouldn.t be/i })
      ).toBeInTheDocument();
      expect(screen.getByText('Hear the Customer Problem')).toBeInTheDocument();
      expect(screen.getByText('Measure What Users Do')).toBeInTheDocument();
      expect(screen.getByText('Understand What Is Already Known')).toBeInTheDocument();
    });
  });

  describe('WorkflowSection', () => {
    it('renders 5-step progression: Ask, Gather, Synthesize, Challenge, Decide', () => {
      render(<WorkflowSection />);
      expect(
        screen.getByRole('heading', { name: /from product question to confident next step/i })
      ).toBeInTheDocument();
      expect(screen.getByText('Ask')).toBeInTheDocument();
      expect(screen.getByText('Gather')).toBeInTheDocument();
      expect(screen.getByText('Synthesize')).toBeInTheDocument();
      expect(screen.getByText('Challenge')).toBeInTheDocument();
      expect(screen.getByText('Decide')).toBeInTheDocument();
    });
  });

  describe('EvidenceSection', () => {
    it('demonstrates claim to citation to canonical evidence mapping', () => {
      render(<EvidenceSection />);
      expect(
        screen.getByRole('heading', { name: /every recommendation is traceable/i })
      ).toBeInTheDocument();
      expect(screen.getByText('Claim in the Report')).toBeInTheDocument();
      expect(screen.getByText('Evidence Behind It')).toBeInTheDocument();
      expect(screen.getByText('Product Analytics')).toBeInTheDocument();
    });
  });

  describe('EpistemicSection', () => {
    it('renders facts, inferences, and hypotheses cards', () => {
      render(<EpistemicSection />);
      expect(
        screen.getByRole('heading', { name: /see what the evidence proves/i })
      ).toBeInTheDocument();
      expect(screen.getByText('What We Know')).toBeInTheDocument();
      expect(screen.getByText('What It Means')).toBeInTheDocument();
      expect(screen.getByText('What to Test Next')).toBeInTheDocument();
    });
  });

  describe('ScenarioSection & CTASection & Footer', () => {
    it('renders completed sample investigations without fixture-like scenario labels', () => {
      render(<ScenarioSection />);
      expect(
        screen.getByRole('heading', { name: /explore completed product investigations/i })
      ).toBeInTheDocument();
      expect(screen.queryByText(/Scenario 1/i)).not.toBeInTheDocument();
      expect(screen.getByText('Transfers')).toBeInTheDocument();
      expect(screen.getByText('User Verification')).toBeInTheDocument();
      expect(screen.getByText('Wallet Funding')).toBeInTheDocument();
      expect(screen.getByText('Bill Payments')).toBeInTheDocument();

      const links = screen.getAllByRole('link', { name: /view decision brief/i });
      expect(links.map((link) => link.getAttribute('href'))).toEqual([
        '/investigations/inv_p12a_scenario_1',
        '/investigations/inv_p12a_scenario_2',
        '/investigations/inv_p12a_scenario_3',
        '/investigations/inv_p12a_scenario_4',
      ]);
    });

    it('renders CTA section with action buttons', () => {
      render(<CTASection />);
      expect(
        screen.getByRole('heading', { name: /bring your next product question/i })
      ).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /start an investigation/i })).toBeInTheDocument();
    });

    it('renders pricing plans and useful frequently asked questions', () => {
      render(
        <>
          <PricingSection />
          <FAQSection />
        </>
      );
      expect(screen.getByRole('heading', { name: /pricing that scales with your product practice/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Monthly' })).toHaveAttribute('aria-pressed', 'true');
      fireEvent.click(screen.getByRole('button', { name: /Yearly/i }));
      expect(screen.getByRole('button', { name: /Yearly/i })).toHaveAttribute('aria-pressed', 'true');
      expect(screen.getByText('Starter')).toBeInTheDocument();
      expect(screen.getByText('Team')).toBeInTheDocument();
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
      expect(screen.getByText('What if the available evidence is incomplete?')).toBeInTheDocument();
    });

    it('renders footer with brand and legal copyright notice', () => {
      render(<LandingFooter />);
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      expect(screen.getByText('PMLytics AI')).toBeInTheDocument();
      expect(screen.getByText('© 2026 PMLytics AI. All rights reserved.')).toBeInTheDocument();
      expect(screen.getByText('hello@pmlytics.ai')).toBeInTheDocument();
    });
  });

  describe('Full HomePage assembly', () => {
    it('renders all sections in approved sequence on root route', async () => {
      render(await HomePage());
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });
  });
});
