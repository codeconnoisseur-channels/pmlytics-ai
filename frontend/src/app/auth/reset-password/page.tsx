import { AuthCard } from '@/components/auth/AuthCard';
import { AuthFields } from '@/components/auth/AuthFields';
import { updatePassword } from '../actions';

export default async function ResetPasswordPage({ searchParams }: { searchParams: Promise<{ message?: string }> }) {
  const params = await searchParams;
  return (
    <AuthCard title="Choose a new password" message={params.message} footer="Your password is encrypted and never stored by PMLytics AI.">
      <form action={updatePassword} className="space-y-5">
        <AuthFields includeEmail={false} passwordLabel="New password" passwordMode="new" />
        <button type="submit" className="w-full touch-manipulation rounded-full bg-brand-primary px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2">Update password</button>
      </form>
    </AuthCard>
  );
}
