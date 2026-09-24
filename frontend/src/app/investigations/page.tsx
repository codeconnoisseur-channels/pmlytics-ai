'use client';

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import {
  InvestigationComposer,
} from '@/components/launchpad';
import {
  useCreateInvestigation,
} from '@/hooks/useInvestigations';
import { ApiError } from '@/lib/api-client';
import { buildUtcDateScope } from '@/lib/investigation-scope';

function formatApiErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 400) {
      if (
        typeof err.details === 'object' &&
        err.details &&
        'detail' in err.details
      ) {
        return String((err.details as any).detail);
      }
      return 'Please enter a valid product question (between 1 and 2,000 characters).';
    }
    if (err.status === 409) {
      return 'An investigation conflict occurred. Please retry.';
    }
    if (err.status === 429) {
      return 'Too many concurrent investigations. Please wait a moment and try again.';
    }
    if (err.status >= 500) {
      return 'Investigation service error. Please check server logs and try again.';
    }
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return 'Failed to start investigation. Please check network connection and try again.';
}

export default function InvestigationsPage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [submitError, setSubmitError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const createMutation = useCreateInvestigation();

  const handleSubmit = async () => {
    const trimmed = query.trim();
    if (!trimmed || trimmed.length > 2000) return;
    if ((startDate && !endDate) || (!startDate && endDate)) {
      setSubmitError('Choose both a start and end date, or leave the date range blank.');
      return;
    }

    setSubmitError(null);
    try {
      const scope = startDate && endDate
        ? buildUtcDateScope(startDate, endDate)
        : undefined;
      const res = await createMutation.mutateAsync({ user_query: trimmed, scope });
      if (res?.investigation_id) {
        router.push(`/investigations/${encodeURIComponent(res.investigation_id)}`);
      }
    } catch (err: unknown) {
      setSubmitError(formatApiErrorMessage(err));
    }
  };

  return (
    <AppShell headerTitle="Investigations">
      <div className="mx-auto max-w-[860px] py-4 sm:py-8">
        <InvestigationComposer
          query={query}
          onChangeQuery={setQuery}
          onSubmit={handleSubmit}
          isSubmitting={createMutation.isPending}
          error={submitError}
          onClearError={() => setSubmitError(null)}
          textareaRef={textareaRef}
          startDate={startDate}
          endDate={endDate}
          onChangeStartDate={setStartDate}
          onChangeEndDate={setEndDate}
        />
      </div>
    </AppShell>
  );
}
