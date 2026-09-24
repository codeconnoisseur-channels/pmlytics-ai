import React from 'react';
import { cn } from '@/lib/utils';

export function LoadingSkeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded bg-surface-subtle border border-border-light', className)}
      {...props}
    />
  );
}

export function WorkspaceSkeleton() {
  return (
    <div className="space-y-6 max-w-reading mx-auto py-8">
      {/* Evidence placeholders only. The recommendation is not rendered until
          the completed brief is available, avoiding a duplicated decision cue. */}
      <div className="space-y-4">
        <LoadingSkeleton className="h-16 w-full" />
        <LoadingSkeleton className="h-16 w-11/12" />
        <LoadingSkeleton className="h-16 w-4/5" />
      </div>
    </div>
  );
}
