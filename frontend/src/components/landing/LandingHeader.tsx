'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import { BrandLogo } from '@/components/brand/BrandLogo';

export interface LandingHeaderProps {
  isAuthenticated?: boolean;
}

const navItems = [
  { href: '#features', label: 'Product' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#pricing', label: 'Pricing' },
];

export function LandingHeader({ isAuthenticated = false }: LandingHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const toggleButtonRef = useRef<HTMLButtonElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && mobileMenuOpen) {
        event.preventDefault();
        setMobileMenuOpen(false);
        toggleButtonRef.current?.focus();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileMenuOpen]);

  useEffect(() => {
    if (!mobileMenuOpen || !mobileMenuRef.current) return;
    const focusableElements = mobileMenuRef.current.querySelectorAll<HTMLElement>(
      'a, button:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    if (focusableElements.length === 0) return;
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    firstElement.focus();

    function trapFocus(event: KeyboardEvent) {
      if (event.key !== 'Tab') return;
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    const menu = mobileMenuRef.current;
    menu.addEventListener('keydown', trapFocus);
    return () => menu.removeEventListener('keydown', trapFocus);
  }, [mobileMenuOpen]);

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <header className="sticky top-0 z-50 border-b border-black/10 bg-[#f4f5f2]/90 backdrop-blur-xl" role="banner">
      <div className="mx-auto flex h-[68px] w-full max-w-[1240px] items-center justify-between px-5 sm:px-8">
        <Link
          href="/"
          className="group flex items-center gap-2.5 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]"
          aria-label="PMLytics AI home"
        >
          <BrandLogo markClassName="h-10 w-10" />
        </Link>

        <nav className="hidden items-center gap-8 md:flex" aria-label="Primary navigation">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded text-[13px] font-semibold text-[#62675f] transition-colors hover:text-[#171915] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <Link
              href="/investigations"
              className="hidden h-10 items-center rounded-full bg-[#171915] px-4 text-sm font-semibold text-white transition-colors hover:bg-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] focus-visible:ring-offset-2 md:inline-flex"
            >
              Open Workspace
            </Link>
          ) : (
            <div className="hidden items-center gap-2 md:flex">
              <Link
                href="/auth/signin"
                className="rounded-full px-3 py-2 text-sm font-semibold text-[#4f544d] transition-colors hover:text-[#171915] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]"
              >
                Sign In
              </Link>
              <Link
                href="/auth/signup"
                className="inline-flex h-10 items-center rounded-full bg-[#171915] px-4 text-sm font-semibold text-white transition-colors hover:bg-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] focus-visible:ring-offset-2"
              >
                Create Account
              </Link>
            </div>
          )}

          <button
            ref={toggleButtonRef}
            type="button"
            className="flex h-11 w-11 touch-manipulation items-center justify-center rounded-full border border-black/15 text-[#171915] transition-colors hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] md:hidden"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-menu"
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" aria-hidden="true" />
            ) : (
              <Menu className="h-5 w-5" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      {mobileMenuOpen ? (
        <div
          ref={mobileMenuRef}
          id="mobile-nav-menu"
          role="dialog"
          aria-modal="true"
          aria-label="Mobile navigation menu"
          className="absolute left-0 right-0 top-full z-50 flex overscroll-contain border-b border-black/10 bg-[#f4f5f2] px-5 py-5 shadow-xl md:hidden"
        >
          <nav className="flex w-full flex-col gap-1" aria-label="Mobile navigation">
            {navItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={closeMenu}
                className="rounded-lg px-3 py-3 text-sm font-semibold text-[#171915] transition-colors hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915]"
              >
                {item.label}
              </a>
            ))}
            {isAuthenticated ? (
              <Link
                href="/investigations"
                onClick={closeMenu}
                className="mt-3 flex h-11 w-full items-center justify-center rounded-full bg-[#171915] text-sm font-semibold text-white"
              >
                Open Workspace
              </Link>
            ) : (
              <div className="mt-3 grid gap-2">
                <Link
                  href="/auth/signin"
                  onClick={closeMenu}
                  className="flex h-11 items-center justify-center rounded-full border border-black/15 bg-white text-sm font-semibold text-[#171915] hover:border-black/30"
                >
                  Sign In
                </Link>
                <Link
                  href="/auth/signup"
                  onClick={closeMenu}
                  className="flex h-11 items-center justify-center rounded-full bg-[#171915] text-sm font-semibold text-white"
                >
                  Create Account
                </Link>
              </div>
            )}
          </nav>
        </div>
      ) : null}
    </header>
  );
}
