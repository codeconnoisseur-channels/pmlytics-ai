'use client';

import React from 'react';
import { CitationPill } from '@/components/primitives/CitationPill';

interface TextWithCitationsProps {
  text: string;
  onSelectCitation?: (id: string) => void;
  className?: string;
  /** Optional map from raw internal ledger IDs to canonical EV-NNN display IDs */
  canonicalIdMap?: Record<string, string>;
}

/**
 * Parses bracketed citations in text and replaces them with interactive CitationPill components.
 *
 * Handles two citation formats:
 *   1. [EV-001], canonical display format, rendered directly as a CitationPill
 *   2. [analytics:r0:led_001] or any other internal ID, mapped to EV-NNN via canonicalIdMap
 *      If no mapping exists, the raw bracket text is suppressed (never shown to users).
 */
export function TextWithCitations({
  text,
  onSelectCitation,
  className,
  canonicalIdMap,
}: TextWithCitationsProps) {
  if (!text) return null;

  // Match both [EV-NNN] and any [xxx:yyy:zzz] style internal IDs
  const parts = text.split(/(\[[^\]]+\])/g);

  return (
    <span className={className}>
      {parts.map((part, i) => {
        // Canonical EV-NNN format
        const canonicalMatch = part.match(/^\[(EV-\d+)\]$/);
        if (canonicalMatch) {
          const evId = canonicalMatch[1];
          return (
            <CitationPill
              key={`${evId}-${i}`}
              evidenceId={evId}
              onSelectCitation={onSelectCitation}
              className="mx-0.5 align-baseline"
            />
          );
        }

        // Internal ID format (e.g. [analytics:r0:led_001])
        // Try to map it to a canonical display ID
        const internalMatch = part.match(/^\[(.+)\]$/);
        if (internalMatch) {
          const rawId = internalMatch[1];
          const canonical = canonicalIdMap?.[rawId];
          if (canonical) {
            return (
              <CitationPill
                key={`${canonical}-${i}`}
                evidenceId={canonical}
                onSelectCitation={onSelectCitation}
                className="mx-0.5 align-baseline"
              />
            );
          }
          // No mapping found, suppress the raw internal ID and do not render it.
          return null;
        }

        return <React.Fragment key={i}>{part}</React.Fragment>;
      })}
    </span>
  );
}
