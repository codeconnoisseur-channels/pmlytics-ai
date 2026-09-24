import Link from 'next/link';
import { AuthCard } from '@/components/auth/AuthCard';
import { AuthFields } from '@/components/auth/AuthFields';
import { signUp } from '../actions';

export default async function SignUpPage({ searchParams }: { searchParams: Promise<{ message?: string }> }) {
  const params = await searchParams;
  return (
    <AuthCard
      title="Create your workspace account"
      message={params.message}
      footer={<>Already have an account? <Link href="/auth/signin" className="font-semibold text-brand-primary hover:underline">Sign in</Link></>}
    >
      <form action={signUp} className="space-y-5">
        <AuthFields passwordMode="new" />
        <button type="submit" className="w-full touch-manipulation rounded-full bg-brand-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2">
          Create account
        </button>
      </form>
    </AuthCard>
  );
}
