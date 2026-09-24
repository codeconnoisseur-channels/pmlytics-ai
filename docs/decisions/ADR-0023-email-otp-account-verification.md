# ADR-0023: Email OTP account verification

## Status

Superseded, 2026-09-22

## Context

The initial Supabase signup flow sent a confirmation link that opened another browser
page. Product review requested an in-product one-time password flow instead. The system
must retain password authentication and the existing password policy while replacing only
the email-confirmation interaction.

Email addresses must not be placed in verification URLs because URLs can be retained in
browser history, analytics, and infrastructure logs.

## Decision

1. Continue using Supabase Auth and password-based accounts.
2. After signup, send the Supabase confirmation token and route the user to
   `/auth/verify-email`.
3. Verify the token through `supabase.auth.verifyOtp` with the signup verification type.
4. Keep the pending email in a short-lived, HTTP-only, same-site cookie scoped to `/auth`.
   Do not place it in the URL or browser-managed client storage.
5. Accept six to eight numeric digits so the interface remains compatible with hosted and
   locally configured Supabase token lengths.
6. Support explicit code resend and provide clear expired-code feedback.
7. The hosted Supabase Confirm signup email template must display `{{ .Token }}` rather
   than `{{ .ConfirmationURL }}`.

## Consequences

- Account verification remains inside the PMLytics AI experience.
- Password requirements and sign-in behavior do not change.
- The application requires one Supabase dashboard template update before OTP email delivery
  works end to end.
- Password recovery remains link-based because it establishes a secure recovery session
  before a password can be changed.

## Superseding decision

The hosted Supabase project requires custom SMTP before the confirmation email template
can be changed to expose the OTP token. Until that service is configured, signup uses the
standard Supabase confirmation link and the existing `/auth/callback` exchange route.

The password policy, password guidance, protected routes, and account ownership rules are
unchanged. The OTP page, pending-email cookie, token verification action, and resend action
have been removed so the application does not present an authentication path that cannot
work with the current Supabase configuration.
