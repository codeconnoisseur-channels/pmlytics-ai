import React from 'react';
import Link from 'next/link';
import { Instagram, Linkedin, Youtube } from 'lucide-react';
import { BrandLogo } from '@/components/brand/BrandLogo';

const footerLinks = [
  { href: '#features', label: 'Product' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#pricing', label: 'Pricing' },
  { href: '#scenarios', label: 'Sample Investigations' },
  { href: '#faq', label: 'FAQ' },
  { href: '/auth/signin', label: 'Sign In' },
];

const socialIcons = [
  { label: 'LinkedIn, coming soon', icon: Linkedin },
  { label: 'Instagram, coming soon', icon: Instagram },
  { label: 'YouTube, coming soon', icon: Youtube },
];

export function LandingFooter() {
  return (
    <footer id="footer" className="border-t border-black/10 bg-[#f4f5f2] py-12" role="contentinfo">
      <div className="mx-auto max-w-[1240px] px-5 sm:px-8">
        <div className="grid gap-10 border-b border-black/10 pb-10 md:grid-cols-[minmax(0,1fr)_auto] md:items-start">
          <div className="max-w-[500px]">
            <Link href="/" className="inline-flex rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]" aria-label="PMLytics AI home">
              <BrandLogo markClassName="h-11 w-11" />
            </Link>
            <p className="mt-5 text-pretty text-sm leading-6 text-[#62675f]">
              Evidence-backed product decisions across customer support, product analytics, and engineering.
            </p>
            <a
              href="mailto:hello@pmlytics.ai"
              className="mt-4 inline-flex rounded text-sm font-bold text-[#171915] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]"
            >
              hello@pmlytics.ai
            </a>
          </div>

          <div className="space-y-7">
            <nav className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm sm:grid-cols-3" aria-label="Footer navigation">
              {footerLinks.map((link) => (
                <Link key={link.href} href={link.href} className="rounded font-semibold text-[#62675f] transition-colors hover:text-[#171915] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]">
                  {link.label}
                </Link>
              ))}
              <span className="font-semibold text-[#9a9f96]" aria-disabled="true" title="Coming soon">
                Terms of Service
              </span>
            </nav>

            <div className="flex items-center gap-2" aria-label="Social media">
              {socialIcons.map(({ label, icon: Icon }) => (
                <span
                  key={label}
                  role="img"
                  aria-label={label}
                  title={label}
                  className="flex h-10 w-10 items-center justify-center rounded-full border border-black/10 bg-white/65 text-[#747970]"
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="pt-6 text-center text-xs text-[#777c74]">
          <p>© 2026 PMLytics AI. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
