'use server';

import { headers } from 'next/headers';
import { redirect } from 'next/navigation';
import { createClient } from '@/lib/supabase/server';

function formValue(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === 'string' ? value.trim() : '';
}

function passwordValue(formData: FormData): string {
  const value = formData.get('password');
  return typeof value === 'string' ? value : '';
}

function passwordValidationError(password: string): string | null {
  const missing: string[] = [];
  if (password.length < 8) missing.push('8 or more characters');
  if (!/[A-Z]/.test(password)) missing.push('an uppercase letter');
  if (!/[a-z]/.test(password)) missing.push('a lowercase letter');
  if (!/\d/.test(password)) missing.push('a number');
  return missing.length > 0 ? `Your password needs ${missing.join(', ')}.` : null;
}

function safeNext(value: string): string {
  return value.startsWith('/') && !value.startsWith('//') ? value : '/investigations';
}

function authRedirect(path: string, message: string): never {
  redirect(`${path}?message=${encodeURIComponent(message)}`);
}

export async function signIn(formData: FormData) {
  const email = formValue(formData, 'email');
  const password = passwordValue(formData);
  const next = safeNext(formValue(formData, 'next'));
  if (!email || !password) authRedirect('/auth/signin', 'Enter your email and password.');

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) authRedirect('/auth/signin', 'Email or password is incorrect.');
  redirect(next);
}

export async function signUp(formData: FormData) {
  const email = formValue(formData, 'email');
  const password = passwordValue(formData);
  if (!email) authRedirect('/auth/signup', 'Enter a valid work email.');
  const passwordError = passwordValidationError(password);
  if (passwordError) authRedirect('/auth/signup', passwordError);

  const headerStore = await headers();
  const origin = headerStore.get('origin') ?? 'http://localhost:3000';
  const supabase = await createClient();
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      emailRedirectTo: `${origin}/auth/callback`,
    },
  });
  if (error) authRedirect('/auth/signup', error.message);
  authRedirect('/auth/signin', 'Check your email to confirm your account.');
}

export async function requestPasswordReset(formData: FormData) {
  const email = formValue(formData, 'email');
  if (!email) authRedirect('/auth/forgot-password', 'Enter your email address.');

  const headerStore = await headers();
  const origin = headerStore.get('origin') ?? 'http://localhost:3000';
  const supabase = await createClient();
  await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${origin}/auth/callback?next=/auth/reset-password`,
  });
  authRedirect(
    '/auth/signin',
    'If an account exists for that email, a password reset link has been sent.'
  );
}

export async function updatePassword(formData: FormData) {
  const password = passwordValue(formData);
  const passwordError = passwordValidationError(password);
  if (passwordError) authRedirect('/auth/reset-password', passwordError);
  const supabase = await createClient();
  const { error } = await supabase.auth.updateUser({ password });
  if (error) authRedirect('/auth/reset-password', 'The reset link has expired. Request a new one.');
  redirect('/investigations');
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect('/auth/signin');
}
