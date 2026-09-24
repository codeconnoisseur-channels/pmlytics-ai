'use client';

import React from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { ErrorState } from '@/components/primitives/ErrorState';

export default function RootError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <AppShell headerTitle="Application Error">
      <div className="py-12">
        <ErrorState
          title="An Unexpected Error Occurred"
          message={error.message || 'The application encountered an unexpected error.'}
          onRetry={reset}
        />
      </div>
    </AppShell>
  );
}
