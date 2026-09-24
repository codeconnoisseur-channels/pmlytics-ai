export function getSupabaseConfig() {
  const configuredUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!configuredUrl || !publishableKey) {
    throw new Error(
      'Supabase authentication is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY.'
    );
  }

  const url = configuredUrl.replace(/\/$/, '').replace(/\/rest\/v1$/, '');
  return { url, publishableKey };
}
