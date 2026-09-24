import React from 'react';
import { Button } from '@/components/primitives/Button';
import { Sparkles, Loader2, AlertCircle, X } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface InvestigationComposerProps {
  query: string;
  onChangeQuery: (value: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  error?: string | null;
  onClearError?: () => void;
  textareaRef?: React.RefObject<HTMLTextAreaElement | null>;
  startDate?: string;
  endDate?: string;
  onChangeStartDate?: (value: string) => void;
  onChangeEndDate?: (value: string) => void;
}

export function InvestigationComposer({
  query,
  onChangeQuery,
  onSubmit,
  isSubmitting,
  error,
  onClearError,
  textareaRef,
  startDate = '',
  endDate = '',
  onChangeStartDate,
  onChangeEndDate,
}: InvestigationComposerProps) {
  const trimmed = query.trim();
  const isValid = trimmed.length > 0 && trimmed.length <= 2000;
  const isOverLimit = query.length > 2000;

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Ctrl+Enter or Cmd+Enter submits
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (isValid && !isSubmitting) {
        e.preventDefault();
        onSubmit();
      }
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isValid && !isSubmitting) {
      onSubmit();
    }
  };

  return (
    <form
      onSubmit={handleFormSubmit}
      className="rounded-[28px] border border-border bg-surface p-5 shadow-[0_18px_55px_rgba(25,31,17,0.06)] sm:p-8"
      aria-labelledby="composer-heading"
    >
      <div className="mx-auto max-w-2xl text-center">
        <h1 id="composer-heading" className="text-balance text-3xl font-black tracking-[-0.04em] text-txt-primary sm:text-4xl">
          What would you like to investigate?
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-pretty text-sm leading-6 text-txt-secondary">
          Ask a product question. PMLytics AI will examine customer support, product analytics, and engineering context before recommending what to do next.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="mt-6 flex items-start justify-between gap-2 rounded-xl border border-status-danger-border bg-status-danger-bg/40 p-3 text-xs text-status-danger-text"
        >
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
            <span>{error}</span>
          </div>
          {onClearError && (
            <button
              type="button"
              onClick={onClearError}
              className="flex h-8 w-8 items-center justify-center rounded-full text-status-danger-text hover:bg-white/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-status-danger-text"
              aria-label="Dismiss error"
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          )}
        </div>
      )}

      <div className="mt-7 space-y-2">
        <label htmlFor="investigation-query" className="sr-only">
          Product question to investigate
        </label>
        <textarea
          ref={textareaRef}
          id="investigation-query"
          name="query"
          value={query}
          onChange={(e) => {
            onChangeQuery(e.target.value);
            if (error && onClearError) {
              onClearError();
            }
          }}
          onKeyDown={handleKeyDown}
          disabled={isSubmitting}
          rows={3}
          maxLength={2000}
          placeholder="e.g. Why did checkout conversion drop for Android users this week?"
          className={cn(
            'w-full min-h-[132px] resize-y rounded-2xl border p-4 text-base leading-7 text-txt-primary transition-[border-color,box-shadow,background-color]',
            'bg-white placeholder:text-txt-disabled focus:outline-none focus:ring-2 focus:ring-brand-primary',
            isOverLimit ? 'border-status-danger-border' : 'border-border'
          )}
          aria-describedby="query-counter"
        />

        <div className="flex justify-end pt-1">
          <div className="flex items-center justify-end gap-3">
            <span
              id="query-counter"
              className={cn(
                'text-xs font-mono',
                isOverLimit
                  ? 'text-status-danger-text font-semibold'
                  : query.length > 1800
                  ? 'text-status-warn-text font-medium'
                  : 'text-txt-muted'
              )}
            >
              {query.length} / 2000
            </span>

            <Button
              type="submit"
              disabled={!isValid || isSubmitting}
              className="gap-1.5 shrink-0"
              aria-busy={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />
                  <span>Starting…</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-[#c8f46b]" aria-hidden="true" />
                  <span>Start Investigation</span>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <fieldset className="mt-6 rounded-2xl bg-surface-subtle/70 p-4">
        <legend className="text-sm font-semibold text-txt-primary">Date range <span className="font-normal text-txt-muted">(optional)</span></legend>
        <p className="mb-3 mt-1 text-xs text-txt-secondary">
          Focus the investigation on a period you choose. Leave blank to use all available data.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="text-xs text-txt-secondary space-y-1">
            <span>From</span>
            <input
              type="date"
              value={startDate}
              max={endDate || undefined}
              onChange={(event) => onChangeStartDate?.(event.target.value)}
              disabled={isSubmitting}
              className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm text-txt-primary focus:outline-none focus:ring-2 focus:ring-brand-primary"
            />
          </label>
          <label className="text-xs text-txt-secondary space-y-1">
            <span>To</span>
            <input
              type="date"
              value={endDate}
              min={startDate || undefined}
              onChange={(event) => onChangeEndDate?.(event.target.value)}
              disabled={isSubmitting}
              className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm text-txt-primary focus:outline-none focus:ring-2 focus:ring-brand-primary"
            />
          </label>
        </div>
      </fieldset>
    </form>
  );
}
