'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, Search, X } from 'lucide-react';
import { SourceBadge, type EvidenceSourceType } from '@/components/primitives/SourceBadge';
import { cn } from '@/lib/utils';
import type { EvidenceLedgerItem, EvidenceSupportingRecord } from '@/types/domain';

const SOURCE_ORDER: EvidenceSourceType[] = ['zendesk', 'posthog', 'jira'];

const SOURCE_COPY: Record<EvidenceSourceType, { tab: string; empty: string; records: string }> = {
  zendesk: {
    tab: 'Customer support',
    empty: 'No matching customer conversations were returned for this investigation.',
    records: 'customer conversation',
  },
  posthog: {
    tab: 'Product analytics',
    empty: 'No product analytics records were available for this investigation.',
    records: 'metric record',
  },
  jira: {
    tab: 'Engineering',
    empty: 'No matching engineering issues were returned for this investigation.',
    records: 'engineering issue',
  },
};

const AUDIT_TIME_FORMATTER = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
  timeZone: 'UTC',
});

function formatAuditTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : `${AUDIT_TIME_FORMATTER.format(date)} UTC`;
}

function recordMatches(record: EvidenceSupportingRecord, query: string): boolean {
  const attributes = Object.entries(record.attributes ?? {}).flat().join(' ').toLowerCase();
  return (
    record.source_reference.toLowerCase().includes(query) ||
    record.title.toLowerCase().includes(query) ||
    record.excerpt.toLowerCase().includes(query) ||
    (record.status ?? '').toLowerCase().includes(query) ||
    attributes.includes(query)
  );
}

export interface EvidenceLedgerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidenceLedger: Record<string, EvidenceLedgerItem>;
  selectedEvidenceId?: string | null;
  onClearSelectedEvidence?: () => void;
  canonicalIdMap?: Record<string, string>;
}

export function EvidenceLedgerDrawer({
  isOpen,
  onClose,
  evidenceLedger,
  selectedEvidenceId,
  onClearSelectedEvidence,
  canonicalIdMap,
}: EvidenceLedgerDrawerProps) {
  const [sourceFilter, setSourceFilter] = useState<'all' | EvidenceSourceType>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSources, setExpandedSources] = useState<Set<EvidenceSourceType>>(() => new Set());
  const drawerRef = useRef<HTMLDivElement>(null);

  const groups = useMemo(() => SOURCE_ORDER.map((source) => {
    const items = Object.values(evidenceLedger).filter((item) => item.source_type === source);
    const recordsById = new Map<string, EvidenceSupportingRecord>();
    items.forEach((item) => {
      (item.supporting_records ?? []).forEach((record) => {
        if (!recordsById.has(record.record_id)) recordsById.set(record.record_id, record);
      });
    });
    const findings = Array.from(new Set(items.map((item) => item.finding).filter(Boolean)));
    return { source, items, records: Array.from(recordsById.values()), findings };
  }), [evidenceLedger]);

  const activeSourceCount = groups.filter((group) => group.items.length > 0).length;
  const normalizedSearch = searchQuery.trim().toLowerCase();

  useEffect(() => {
    if (!selectedEvidenceId || !evidenceLedger[selectedEvidenceId]) return;
    const source = evidenceLedger[selectedEvidenceId].source_type;
    setSourceFilter(source);
    setSearchQuery('');
    setExpandedSources((current) => new Set(current).add(source));
  }, [selectedEvidenceId, evidenceLedger]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && isOpen) {
        event.preventDefault();
        onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const visibleGroups = groups
    .filter((group) => sourceFilter === 'all' || group.source === sourceFilter)
    .map((group) => ({
      ...group,
      visibleRecords: normalizedSearch
        ? group.records.filter((record) => recordMatches(record, normalizedSearch))
        : group.records,
    }))
    .filter((group) => {
      if (!normalizedSearch) return true;
      return (
        group.visibleRecords.length > 0 ||
        group.findings.some((finding) => finding.toLowerCase().includes(normalizedSearch)) ||
        SOURCE_COPY[group.source].tab.toLowerCase().includes(normalizedSearch)
      );
    });

  const toggleSource = (source: EvidenceSourceType) => {
    setExpandedSources((current) => {
      const next = new Set(current);
      if (next.has(source)) next.delete(source);
      else next.add(source);
      return next;
    });
  };

  return (
    <>
      <div
        className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm widescreen:hidden"
        onClick={onClose}
        aria-hidden="true"
        data-testid="evidence-ledger-backdrop"
      />

      <aside
        ref={drawerRef}
        className="fixed bottom-0 right-0 top-0 z-50 flex w-full flex-col overscroll-contain border-l border-border bg-surface/95 shadow-[0_30px_90px_rgba(23,25,21,0.22)] backdrop-blur-xl sm:w-[440px] widescreen:top-topbar widescreen:shadow-none"
        aria-label="Evidence Ledger Drawer"
        role="dialog"
        aria-modal="true"
      >
        <div className="space-y-4 border-b border-border bg-surface/90 p-4 backdrop-blur-xl sm:p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-black tracking-[-0.03em] text-txt-primary">Evidence Ledger</h2>
              <p className="mt-1 text-xs text-txt-muted">
                Evidence from {activeSourceCount} source{activeSourceCount === 1 ? '' : 's'}
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-10 w-10 touch-manipulation items-center justify-center rounded-full text-txt-muted hover:bg-surface-subtle hover:text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
              aria-label="Close Evidence Ledger"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>

          <div className="flex gap-1.5 overflow-x-auto pb-0.5 no-scrollbar" role="tablist" aria-label="Filter evidence by source">
            {(['all', ...SOURCE_ORDER] as const).map((source) => {
              const label = source === 'all' ? 'All sources' : SOURCE_COPY[source].tab;
              return (
                <button
                  key={source}
                  type="button"
                  role="tab"
                  aria-selected={sourceFilter === source}
                  onClick={() => {
                    setSourceFilter(source);
                    onClearSelectedEvidence?.();
                  }}
                  className={cn(
                    'min-h-9 touch-manipulation whitespace-nowrap rounded-full px-3 text-xs font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary',
                    sourceFilter === source
                      ? 'bg-brand-primary text-white'
                      : 'bg-surface-subtle text-txt-secondary hover:text-txt-primary'
                  )}
                >
                  {label}
                </button>
              );
            })}
          </div>

          <label className="relative block">
            <span className="sr-only">Search evidence records</span>
            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-txt-muted" aria-hidden="true" />
            <input
              type="search"
              name="evidence-search"
              autoComplete="off"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search tickets, metrics, or issues…"
              className="w-full rounded-xl border border-border bg-white/80 py-2.5 pl-9 pr-3 text-xs text-txt-primary placeholder:text-txt-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
            />
          </label>
        </div>

        <div className="flex-grow space-y-3 overflow-y-auto overscroll-contain p-4 sm:p-5" role="region" aria-label="Evidence sources">
          {visibleGroups.length === 0 ? (
            <p className="py-12 text-center text-sm text-txt-muted">No evidence records match this search.</p>
          ) : visibleGroups.map((group) => {
            const copy = SOURCE_COPY[group.source];
            const isExpanded = expandedSources.has(group.source) || (normalizedSearch.length > 0 && group.visibleRecords.length > 0);
            const selectedItem = selectedEvidenceId ? evidenceLedger[selectedEvidenceId] : null;
            const isSelected = selectedItem?.source_type === group.source;
            const citationLabels = group.items.map(
              (item) => canonicalIdMap?.[item.ledger_entry_id] ?? item.ledger_entry_id
            );
            return (
              <article
                key={group.source}
                id={`source-${group.source}`}
                className={cn(
                  'rounded-2xl border bg-white/80 p-4',
                  isSelected ? 'border-brand-primary ring-2 ring-brand-primary/20' : 'border-border'
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <SourceBadge source={group.source} reference={copy.tab} />
                    <p className="mt-2 text-sm font-bold text-txt-primary">
                      {group.records.length > 0
                        ? `${group.records.length} unique ${copy.records}${group.records.length === 1 ? '' : 's'}`
                        : copy.empty}
                    </p>
                  </div>
                  {citationLabels.length > 0 ? (
                    <span className="flex shrink-0 flex-wrap justify-end gap-1 text-[10px] font-semibold text-txt-muted">
                      {citationLabels.map((label) => <span key={label}>[{label}]</span>)}
                    </span>
                  ) : null}
                </div>

                {group.records.length > 0 ? (
                  <button
                    type="button"
                    onClick={() => toggleSource(group.source)}
                    className="mt-3 flex min-h-10 w-full touch-manipulation items-center justify-between rounded-xl bg-brand-subtle px-3 text-left text-xs font-bold text-brand-primary hover:bg-[#e5f5c7] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
                    aria-expanded={isExpanded}
                    aria-controls={`source-records-${group.source}`}
                  >
                    <span>{isExpanded ? 'Hide records' : 'View records'}</span>
                    <ChevronDown className={cn('h-4 w-4 transition-transform motion-reduce:transition-none', isExpanded && 'rotate-180')} aria-hidden="true" />
                  </button>
                ) : null}

                {isExpanded && group.records.length > 0 ? (
                  <ol id={`source-records-${group.source}`} className="mt-3 space-y-2">
                    {group.visibleRecords.map((record) => {
                      const occurredAt = formatAuditTime(record.occurred_at);
                      return (
                        <li key={`${group.source}-${record.record_id}`} className="space-y-2 rounded-xl border border-border bg-surface p-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                              <p className="text-[10px] font-semibold text-txt-muted">{record.source_reference}</p>
                              <p className="mt-1 break-words text-xs font-bold leading-relaxed text-txt-primary">{record.title}</p>
                            </div>
                            {record.status ? <span className="shrink-0 rounded border border-border bg-surface-subtle px-1.5 py-0.5 text-[10px] font-semibold text-txt-secondary">{record.status}</span> : null}
                          </div>
                          <p className="break-words text-[11px] leading-relaxed text-txt-secondary">{record.excerpt}</p>
                          {Object.keys(record.attributes ?? {}).length > 0 ? (
                            <dl className="flex flex-wrap gap-x-3 gap-y-1 border-t border-border-light pt-2 text-[10px] text-txt-muted">
                              {Object.entries(record.attributes ?? {}).map(([label, value]) => (
                                <div key={label} className="flex gap-1"><dt>{label}:</dt><dd className="font-semibold text-txt-secondary">{value}</dd></div>
                              ))}
                            </dl>
                          ) : null}
                          {occurredAt ? <time dateTime={record.occurred_at ?? undefined} className="block text-[10px] text-txt-muted">{occurredAt}</time> : null}
                        </li>
                      );
                    })}
                  </ol>
                ) : null}
              </article>
            );
          })}
        </div>
      </aside>
    </>
  );
}
