'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Check,
  FileText,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Pencil,
  Plus,
  Trash2,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  useDeleteInvestigation,
  useRecentInvestigations,
  useRenameInvestigation,
} from '@/hooks/useInvestigations';
import type { InvestigationStatusResponse } from '@/types/domain';

export interface SidebarProps {
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
  isAuthenticated?: boolean;
}

const TERMINAL_STATUSES = new Set([
  'completed',
  'partial',
  'failed',
  'cancelled',
  'recovery_required',
]);

export function Sidebar({
  isMobileOpen = false,
  onCloseMobile,
  isAuthenticated = false,
}: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<InvestigationStatusResponse | null>(null);
  const { data: investigations, isLoading } = useRecentInvestigations(isAuthenticated);
  const renameMutation = useRenameInvestigation();
  const deleteMutation = useDeleteInvestigation();

  useEffect(() => {
    const saved = localStorage.getItem('pmlytics_sidebar_collapsed');
    if (saved !== null) setCollapsed(saved === 'true');
  }, []);

  useEffect(() => {
    const closeMenus = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpenMenuId(null);
        setRenamingId(null);
        setDeleteTarget(null);
      }
    };
    window.addEventListener('keydown', closeMenus);
    return () => window.removeEventListener('keydown', closeMenus);
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((current) => {
      const next = !current;
      localStorage.setItem('pmlytics_sidebar_collapsed', String(next));
      return next;
    });
  };

  const saveRename = async (investigationId: string) => {
    const displayName = renameValue.trim();
    if (!displayName) return;
    try {
      await renameMutation.mutateAsync({ id: investigationId, displayName });
      setRenamingId(null);
      setOpenMenuId(null);
    } catch {
      // Keep the editor open so the user can retry without losing the name.
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    const id = deleteTarget.investigation_id;
    try {
      await deleteMutation.mutateAsync(id);
      setDeleteTarget(null);
      setOpenMenuId(null);
      if (pathname === `/investigations/${encodeURIComponent(id)}`) {
        router.push('/investigations');
      }
    } catch {
      // The dialog remains open and displays the mutation error.
    }
  };

  return (
    <>
      {isMobileOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/35 backdrop-blur-sm md:hidden"
          onClick={onCloseMobile}
          aria-label="Close navigation menu"
        />
      ) : null}

      <aside
        className={cn(
          'fixed top-topbar z-40 flex h-[calc(100vh-var(--spacing-topbar,68px))] shrink-0 flex-col border-r border-border bg-surface/95 shadow-xl backdrop-blur-xl transition-[width,transform] duration-200 motion-reduce:transition-none md:sticky md:shadow-none',
          collapsed ? 'w-sidebar-collapsed' : 'w-sidebar-expanded',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        <div className="flex items-center justify-end px-3 pb-1 pt-3">
          <button
            type="button"
            onClick={toggleCollapsed}
            className="hidden h-9 w-9 touch-manipulation items-center justify-center rounded-full text-txt-muted transition-colors hover:bg-surface-subtle hover:text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary md:flex"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeftOpen className="h-4 w-4" aria-hidden="true" /> : <PanelLeftClose className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col px-3 pb-3">
          <nav className="space-y-1" aria-label="Main Navigation">
            <Link
              href="/investigations"
              onClick={onCloseMobile}
              className={cn(
                'flex min-h-11 touch-manipulation items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary',
                pathname?.startsWith('/investigations')
                  ? 'bg-brand-primary font-semibold text-white shadow-sm'
                  : 'text-txt-secondary hover:bg-surface-subtle hover:text-txt-primary',
                collapsed && 'justify-center px-2'
              )}
              title="Investigations"
            >
              <FileText className={cn('h-4 w-4 shrink-0', pathname?.startsWith('/investigations') && 'text-[#c8f46b]')} aria-hidden="true" />
              {!collapsed ? <span>Investigations</span> : null}
            </Link>
          </nav>

          {isAuthenticated && !collapsed ? (
            <div className="mt-5 flex min-h-0 flex-1 flex-col border-t border-border pt-4">
              <div className="mb-2 flex items-center justify-between px-2">
                <p className="text-[10px] font-black uppercase tracking-[0.14em] text-txt-muted">Recent</p>
                <Link
                  href="/investigations"
                  onClick={onCloseMobile}
                  className="flex h-8 w-8 items-center justify-center rounded-full text-txt-muted hover:bg-surface-subtle hover:text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
                  aria-label="Start a new investigation"
                  title="New investigation"
                >
                  <Plus className="h-4 w-4" aria-hidden="true" />
                </Link>
              </div>

              <div className="min-h-0 flex-1 space-y-1 overflow-y-auto overscroll-contain pr-1">
                {isLoading ? (
                  <p className="px-2 py-3 text-xs text-txt-muted">Loading investigations…</p>
                ) : investigations?.length ? (
                  investigations.map((investigation) => {
                    const id = investigation.investigation_id;
                    const href = `/investigations/${encodeURIComponent(id)}`;
                    const isCurrent = pathname === href;
                    const isComplete = investigation.status === 'completed' || investigation.status === 'partial';
                    const isFailed = investigation.status === 'failed';
                    const isTerminal = TERMINAL_STATUSES.has(investigation.status);
                    const label = investigation.display_name || investigation.user_query;

                    return (
                      <div key={id} className="relative">
                        {renamingId === id ? (
                          <form
                            className="rounded-xl border border-brand-border bg-white p-2"
                            onSubmit={(event) => {
                              event.preventDefault();
                              void saveRename(id);
                            }}
                          >
                            <label htmlFor={`rename-${id}`} className="sr-only">Investigation name</label>
                            <input
                              id={`rename-${id}`}
                              name="display_name"
                              value={renameValue}
                              onChange={(event) => setRenameValue(event.target.value)}
                              maxLength={120}
                              className="w-full rounded-lg border border-border-strong bg-white px-2.5 py-2 text-xs text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
                            />
                            <div className="mt-2 flex justify-end gap-1">
                              {renameMutation.isError ? <span className="mr-auto self-center text-[10px] text-status-danger-text" role="alert">Could not rename</span> : null}
                              <button type="button" onClick={() => setRenamingId(null)} className="flex h-8 w-8 items-center justify-center rounded-full text-txt-muted hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary" aria-label="Cancel rename">
                                <X className="h-3.5 w-3.5" aria-hidden="true" />
                              </button>
                              <button type="submit" disabled={!renameValue.trim() || renameMutation.isPending} className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-primary text-white hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 disabled:opacity-50" aria-label="Save investigation name">
                                <Check className="h-3.5 w-3.5" aria-hidden="true" />
                              </button>
                            </div>
                          </form>
                        ) : (
                          <>
                            <Link
                              href={href}
                              onClick={onCloseMobile}
                              className={cn(
                                'group flex min-h-11 items-start gap-2.5 rounded-xl px-2.5 py-2 pr-10 text-xs leading-5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary',
                                isCurrent ? 'bg-surface-subtle font-semibold text-txt-primary' : 'text-txt-secondary hover:bg-surface-subtle hover:text-txt-primary'
                              )}
                              title={label}
                            >
                              <span className={cn('mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full', isComplete && 'bg-status-pass-text', isFailed && 'bg-status-danger-text', !isComplete && !isFailed && 'animate-pulse bg-[#2563eb]')} aria-hidden="true" />
                              <span className="line-clamp-2">{label}</span>
                            </Link>
                            <button
                              type="button"
                              onClick={() => setOpenMenuId((current) => current === id ? null : id)}
                              className="absolute right-1.5 top-1.5 flex h-8 w-8 items-center justify-center rounded-full text-txt-muted hover:bg-white hover:text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
                              aria-label={`More options for ${label}`}
                              aria-expanded={openMenuId === id}
                            >
                              <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
                            </button>
                            {openMenuId === id ? (
                              <div role="menu" className="absolute right-1 top-10 z-50 w-36 rounded-xl border border-border bg-white p-1.5 shadow-xl">
                                <button
                                  type="button"
                                  role="menuitem"
                                  onClick={() => {
                                    setRenameValue(label);
                                    setRenamingId(id);
                                    setOpenMenuId(null);
                                  }}
                                  className="flex min-h-9 w-full items-center gap-2 rounded-lg px-2.5 text-left text-xs font-semibold text-txt-primary hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
                                >
                                  <Pencil className="h-3.5 w-3.5" aria-hidden="true" /> Rename
                                </button>
                                <button
                                  type="button"
                                  role="menuitem"
                                  disabled={!isTerminal}
                                  onClick={() => {
                                    setDeleteTarget(investigation);
                                    setOpenMenuId(null);
                                  }}
                                  className="flex min-h-9 w-full items-center gap-2 rounded-lg px-2.5 text-left text-xs font-semibold text-status-danger-text hover:bg-status-danger-bg/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-status-danger-text disabled:cursor-not-allowed disabled:opacity-45"
                                  title={isTerminal ? 'Delete investigation' : 'Stop this investigation before deleting it'}
                                >
                                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" /> Delete
                                </button>
                              </div>
                            ) : null}
                          </>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="px-2 py-3 text-xs leading-5 text-txt-muted">Your investigations will appear here.</p>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </aside>

      {deleteTarget ? (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/40 px-4 backdrop-blur-sm">
          <section role="dialog" aria-modal="true" aria-labelledby="delete-investigation-title" className="w-full max-w-sm rounded-3xl border border-border bg-surface p-6 shadow-2xl">
            <h2 id="delete-investigation-title" className="text-lg font-black tracking-[-0.02em] text-txt-primary">Delete this investigation?</h2>
            <p className="mt-2 text-sm leading-6 text-txt-secondary">This permanently removes the report and its investigation history. This action cannot be undone.</p>
            <p className="mt-3 line-clamp-2 rounded-xl bg-surface-subtle px-3 py-2 text-xs font-semibold text-txt-primary">{deleteTarget.display_name || deleteTarget.user_query}</p>
            {deleteMutation.isError ? <p className="mt-3 text-sm text-status-danger-text" role="alert">The investigation could not be deleted. Please try again.</p> : null}
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" onClick={() => setDeleteTarget(null)} className="min-h-10 rounded-full border border-border-strong px-4 text-sm font-semibold text-txt-primary hover:bg-surface-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary">Cancel</button>
              <button type="button" onClick={() => void confirmDelete()} disabled={deleteMutation.isPending} className="min-h-10 rounded-full bg-status-danger-text px-4 text-sm font-semibold text-white hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-status-danger-text focus-visible:ring-offset-2 disabled:opacity-60">
                {deleteMutation.isPending ? 'Deleting…' : 'Delete investigation'}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </>
  );
}
