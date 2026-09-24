'use client';

import React from 'react';
import Link from 'next/link';
import { Menu, Plus, LogOut } from 'lucide-react';
import { BrandLogo } from '@/components/brand/BrandLogo';
import { signOut } from '@/app/auth/actions';

export interface HeaderProps {
  onToggleMobileMenu?: () => void;
  title?: string;
  actions?: React.ReactNode;
  isAuthenticated?: boolean;
}

export function Header({ onToggleMobileMenu, title, actions, isAuthenticated = false }: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-topbar shrink-0 items-center justify-between border-b border-border bg-surface/90 px-4 backdrop-blur-xl md:px-7">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleMobileMenu}
          className="flex h-10 w-10 touch-manipulation items-center justify-center rounded-full text-txt-secondary hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary md:hidden"
          aria-label="Open mobile menu"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>

        <Link href="/" className="group flex items-center gap-2 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2">
          <BrandLogo markClassName="h-9 w-9" className="[&>span]:hidden sm:[&>span]:inline" />
        </Link>

        {title && (
          <div className="hidden md:flex items-center gap-2 pl-3 border-l border-border text-sm text-txt-secondary font-medium">
            <span>/</span>
            <span className="text-txt-primary font-semibold truncate max-w-[300px]">{title}</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        {actions || (
          <Link
            href="/investigations"
            className="inline-flex h-9 touch-manipulation items-center justify-center gap-1.5 rounded-full bg-brand-primary px-3.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
          >
            <Plus className="w-3.5 h-3.5" aria-hidden="true" />
            <span>New investigation</span>
          </Link>
        )}
        {isAuthenticated ? (
          <form action={signOut}>
            <button
              type="submit"
              className="inline-flex h-9 touch-manipulation items-center justify-center gap-1.5 rounded-full border border-border-strong bg-surface px-3 text-sm font-semibold text-txt-primary transition-colors hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2"
            >
              <LogOut className="h-3.5 w-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </form>
        ) : null}
      </div>
    </header>
  );
}
