import Link from 'next/link';
import { AuthCard } from '@/components/auth/AuthCard';
import { requestPasswordReset } from '../actions';

export default async function ForgotPasswordPage({ searchParams }: { searchParams: Promise<{ message?: string }> }) {
  const params = await searchParams;
  return (
    <AuthCard
      title="Reset your password"
      description="Enter your work email and we’ll send a secure reset link."
      message={params.message}
      footer={<Link href="/auth/signin" className="font-semibold text-brand-primary hover:underline">Back to sign in</Link>}
    >
      <form action={requestPasswordReset} className="space-y-5">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-txt-primary">Work email</label>
          <input id="email" name="email" type="email" autoComplete="email" spellCheck={false} required className="mt-1.5 w-full rounded-xl border border-border bg-white/80 px-3.5 py-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary" />
        </div>
        <button type="submit" className="w-full touch-manipulation rounded-full bg-brand-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2">Send reset link</button>
      </form>
    </AuthCard>
  );
}
