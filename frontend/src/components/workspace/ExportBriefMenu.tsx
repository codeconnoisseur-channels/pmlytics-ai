'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Download, Copy, Printer, Check, Share2, ChevronDown } from 'lucide-react';
import { Button } from '@/components/primitives/Button';
import type { InvestigationDetailResponse } from '@/types/domain';
import {
  generateMarkdownReport,
  generateSummaryClipboardText,
  downloadMarkdownFile,
  copyTextToClipboard,
} from '@/lib/export-utils';

export interface ExportBriefMenuProps {
  detail?: InvestigationDetailResponse | null;
  userQuery: string;
}

export function ExportBriefMenu({ detail, userQuery }: ExportBriefMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleDownloadMarkdown = () => {
    if (!detail) return;
    const content = generateMarkdownReport(detail);
    const sanitizedTitle = userQuery
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .slice(0, 40)
      .replace(/^-|-$/g, '');
    downloadMarkdownFile(`pmlytics-${sanitizedTitle || 'decision-brief'}`, content);
    setIsOpen(false);
  };

  const handleCopySummary = async () => {
    if (!detail) return;
    const summary = generateSummaryClipboardText(detail);
    const success = await copyTextToClipboard(summary);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
    setIsOpen(false);
  };

  const handlePrint = () => {
    setIsOpen(false);
    window.print();
  };

  if (!detail) return null;

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      <Button
        variant="secondary"
        size="sm"
        onClick={() => setIsOpen((prev) => !prev)}
        className="h-8 gap-1.5 text-xs font-medium"
        aria-label="Export or share decision brief"
      >
        <Share2 className="h-3.5 w-3.5 text-txt-secondary" aria-hidden="true" />
        <span>Export</span>
        <ChevronDown className="h-3 w-3 text-txt-muted opacity-70" aria-hidden="true" />
      </Button>

      {isOpen && (
        <div className="absolute right-0 z-50 mt-1.5 w-56 origin-top-right rounded-xl border border-border bg-surface p-1.5 shadow-xl ring-1 ring-black/5 animate-in fade-in-50 zoom-in-95">
          <div className="px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-txt-muted">
            Export Decision Brief
          </div>

          <button
            type="button"
            onClick={handleDownloadMarkdown}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-txt-primary hover:bg-surface-subtle transition-colors text-left"
          >
            <Download className="h-3.5 w-3.5 text-brand-primary" aria-hidden="true" />
            <div>
              <div>Download Markdown</div>
              <div className="text-[10px] text-txt-muted">For Notion, Confluence, Linear</div>
            </div>
          </button>

          <button
            type="button"
            onClick={handleCopySummary}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-txt-primary hover:bg-surface-subtle transition-colors text-left"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
            ) : (
              <Copy className="h-3.5 w-3.5 text-txt-secondary" aria-hidden="true" />
            )}
            <div>
              <div>{copied ? 'Copied to Clipboard!' : 'Copy Summary'}</div>
              <div className="text-[10px] text-txt-muted">Formatted for Slack & Teams</div>
            </div>
          </button>

          <button
            type="button"
            onClick={handlePrint}
            className="flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium text-txt-primary hover:bg-surface-subtle transition-colors text-left"
          >
            <Printer className="h-3.5 w-3.5 text-txt-secondary" aria-hidden="true" />
            <div>
              <div>Print / Save as PDF</div>
              <div className="text-[10px] text-txt-muted">Clean executive layout</div>
            </div>
          </button>
        </div>
      )}
    </div>
  );
}
