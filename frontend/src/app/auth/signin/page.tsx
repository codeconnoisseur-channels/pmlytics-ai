import Link from 'next/link';
import { AuthCard } from '@/components/auth/AuthCard';
import { AuthFields } from '@/components/auth/AuthFields';
import { signIn } from '../actions';

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ message?: string; next?: string }>;
}) {
  const params = await searchParams;
  return (
    <AuthCard
      title="Sign in to your workspace"
      message={params.message}
      footer={<>New to PMLytics AI? <Link href="/auth/signup" className="font-semibold text-brand-primary hover:underline">Create an account</Link></>}
    >
      <form action={signIn} className="space-y-5">
        <input type="hidden" name="next" value={params.next ?? '/investigations'} />
        <AuthFields />
        <div className="flex justify-end">
          <Link href="/auth/forgot-password" className="text-sm font-medium text-brand-primary hover:underline">Forgot password?</Link>
        </div>
        <button type="submit" className="w-full touch-manipulation rounded-full bg-brand-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2">
          Sign in
        </button>
      </form>
    </AuthCard>
  );
}
