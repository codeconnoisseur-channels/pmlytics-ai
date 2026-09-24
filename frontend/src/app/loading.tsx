import { AppShell } from '@/components/layout/AppShell';
import { LoadingSkeleton } from '@/components/primitives/LoadingSkeleton';

export default function Loading() {
  return (
    <AppShell headerTitle="Loading…">
      <div className="py-8 space-y-4 max-w-reading mx-auto">
        <LoadingSkeleton className="h-8 w-1/2" />
        <LoadingSkeleton className="h-24 w-full" />
        <LoadingSkeleton className="h-40 w-full" />
      </div>
    </AppShell>
  );
}
