'use client';

import React, { useEffect, useState } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { createClient as createSupabaseClient } from '@/lib/supabase/client';

export interface AppShellProps {
  children: React.ReactNode;
  headerTitle?: string;
  headerActions?: React.ReactNode;
  hideSidebar?: boolean;
  /**
   * When true, removes the default main content padding so that
   * full-bleed layouts (e.g., workspace with sticky header) can
   * control their own spacing without fighting the shell.
   */
  hidePadding?: boolean;
}

export function AppShell({
  children,
  headerTitle,
  headerActions,
  hideSidebar = false,
  hidePadding = false,
}: AppShellProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const supabase = createSupabaseClient();
    let mounted = true;

    void supabase.auth.getSession().then(({ data }) => {
      if (mounted) setIsAuthenticated(Boolean(data.session));
    });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-canvas">
      <Header
        onToggleMobileMenu={() => setIsMobileMenuOpen((prev) => !prev)}
        title={headerTitle}
        actions={headerActions}
        isAuthenticated={isAuthenticated}
      />

      <div className="flex min-h-0 flex-1">
        {!hideSidebar && (
          <Sidebar
            isMobileOpen={isMobileMenuOpen}
            onCloseMobile={() => setIsMobileMenuOpen(false)}
            isAuthenticated={isAuthenticated}
          />
        )}

        <main id="main-content" className="min-h-0 min-w-0 flex-1 overflow-y-auto overscroll-contain">
          {hidePadding ? (
            children
          ) : (
            <div className="p-4 md:p-6 lg:p-8">
              <div className="mx-auto max-w-[1040px]">{children}</div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
