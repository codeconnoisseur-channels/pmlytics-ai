'use client';

import React, { useMemo } from 'react';
import { TextWithCitations } from './TextWithCitations';
import { CitationPill } from '@/components/primitives/CitationPill';
import type { StructuredFinding, EvidenceLedgerItem } from '@/types/domain';

export interface EpistemicDeckProps {
  facts: StructuredFinding[];
  inferences: StructuredFinding[];
  hypotheses: StructuredFinding[];
  /** Evidence ledger used to build canonical EV-XXX ID mapping (if canonicalIdMap not provided) */
  evidenceLedger?: Record<string, EvidenceLedgerItem>;
  /** Pre-built canonical ID map from raw internal IDs to EV-NNN display IDs */
  canonicalIdMap?: Record<string, string>;
  onSelectCitation?: (id: string) => void;
}

export function EpistemicDeck({
  facts,
  inferences,
  hypotheses,
  evidenceLedger,
  canonicalIdMap: externalCanonicalIdMap,
  onSelectCitation,
}: EpistemicDeckProps) {
  // Build a stable mapping from raw internal ledger IDs → canonical EV-NNN display IDs
  // If the parent already built this map, use it directly to keep IDs consistent across components.
  const builtCanonicalIdMap = useMemo<Record<string, string>>(() => {
    if (externalCanonicalIdMap) return externalCanonicalIdMap;
    if (!evidenceLedger) return {};
    const entries = Object.keys(evidenceLedger);
    const map: Record<string, string> = {};
    entries.forEach((rawId, idx) => {
      const canonical = `EV-${String(idx + 1).padStart(3, '0')}`;
      map[rawId] = canonical;
    });
    return map;
  }, [evidenceLedger, externalCanonicalIdMap]);

  const canonicalIdMap = builtCanonicalIdMap;

  // Convert an array of raw internal IDs to canonical display IDs
  const toCanonical = (rawIds: string[]): string[] => {
    return rawIds
      .map((id) => canonicalIdMap[id] ?? id)
      // Only surface clean EV-NNN IDs and filter out any remaining internal patterns.
      .filter((id) => /^EV-\d+$/.test(id));
  };

  return (
    <section
      className="editorial-section space-y-4"
      aria-label="Evidence-backed findings"
    >
      <div className="flex items-center gap-3">
        <span className="font-mono text-xs font-bold text-txt-muted">03</span>
        <h2 id="findings-heading" className="text-xl font-black tracking-[-0.03em] text-txt-primary">
          Key findings
        </h2>
      </div>

      <div className="space-y-4">
        {/* 1. Observed Facts (Emerald) */}
        {facts.length > 0 && (
          <div className="space-y-3 rounded-2xl border border-border border-l-4 border-l-epistemic-facts-border bg-surface/90 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-txt-primary border-b border-border/60 pb-2.5">What we know</h3>

            <ul className="space-y-2.5 text-xs text-txt-primary leading-relaxed">
              {facts.map((fact, idx) => {
                const canonicalIds = toCanonical(fact.evidence_ids ?? []);
                // Only show pills from evidence_ids if the statement text doesn't already have [EV-...] markers
                const hasInlineEvidence = /\[EV-\d+\]/.test(fact.statement);
                return (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-txt-muted select-none mt-0.5">•</span>
                    <div className="flex-grow">
                      <TextWithCitations
                        text={fact.statement}
                        canonicalIdMap={canonicalIdMap}
                        onSelectCitation={onSelectCitation}
                      />
                      {!hasInlineEvidence && canonicalIds.length > 0 && (
                        <span className="ml-1.5 inline-flex gap-1">
                          {canonicalIds.map((ev) => (
                            <CitationPill
                              key={ev}
                              evidenceId={ev}
                              onSelectCitation={onSelectCitation}
                            />
                          ))}
                        </span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {/* 2. Analytical Inferences (Blue) */}
        {inferences.length > 0 && (
          <div className="space-y-3 rounded-2xl border border-border border-l-4 border-l-epistemic-inferences-border bg-surface/90 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-txt-primary border-b border-border/60 pb-2.5">What it suggests</h3>

            <ul className="space-y-2.5 text-xs text-txt-primary leading-relaxed">
              {inferences.map((inf, idx) => {
                const canonicalIds = toCanonical(inf.evidence_ids ?? []);
                const hasInlineEvidence = /\[EV-\d+\]/.test(inf.statement);
                return (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-txt-muted select-none mt-0.5">•</span>
                    <div className="flex-grow">
                      <TextWithCitations
                        text={inf.statement}
                        canonicalIdMap={canonicalIdMap}
                        onSelectCitation={onSelectCitation}
                      />
                      {!hasInlineEvidence && canonicalIds.length > 0 && (
                        <span className="ml-1.5 inline-flex gap-1">
                          {canonicalIds.map((ev) => (
                            <CitationPill
                              key={ev}
                              evidenceId={ev}
                              onSelectCitation={onSelectCitation}
                            />
                          ))}
                        </span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {/* 3. Working Hypotheses (Amber) */}
        {hypotheses.length > 0 && (
          <div className="space-y-3 rounded-2xl border border-border border-l-4 border-l-epistemic-hypotheses-border bg-surface/90 p-5 shadow-sm">
            <h3 className="text-sm font-bold text-txt-primary border-b border-border/60 pb-2.5">Possible explanations to test</h3>

            <ul className="space-y-2.5 text-xs text-txt-primary leading-relaxed">
              {hypotheses.map((hyp, idx) => {
                const canonicalIds = toCanonical(hyp.evidence_ids ?? []);
                const hasInlineEvidence = /\[EV-\d+\]/.test(hyp.statement);
                return (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-txt-muted select-none mt-0.5">•</span>
                    <div className="flex-grow">
                      <TextWithCitations
                        text={hyp.statement}
                        canonicalIdMap={canonicalIdMap}
                        onSelectCitation={onSelectCitation}
                      />
                      {!hasInlineEvidence && canonicalIds.length > 0 && (
                        <span className="ml-1.5 inline-flex gap-1">
                          {canonicalIds.map((ev) => (
                            <CitationPill
                              key={ev}
                              evidenceId={ev}
                              onSelectCitation={onSelectCitation}
                            />
                          ))}
                        </span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
