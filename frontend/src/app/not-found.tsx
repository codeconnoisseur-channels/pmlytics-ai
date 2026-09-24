import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/primitives/Button';
import { EmptyState } from '@/components/primitives/EmptyState';

export default function NotFound() {
  return (
    <AppShell headerTitle="404 Not Found">
      <div className="py-12">
        <EmptyState
          title="Page Not Found"
          description="The requested page or product investigation could not be found."
          action={
            <Link href="/investigations">
              <Button size="sm">Return to Launchpad</Button>
            </Link>
          }
        />
      </div>
    </AppShell>
  );
}
