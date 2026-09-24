'use client';

import { useState } from 'react';
import { Check, Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AuthFieldsProps {
  includeEmail?: boolean;
  passwordLabel?: string;
  passwordMode?: 'current' | 'new';
}

const PASSWORD_PATTERN = '(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,}';
const PASSWORD_HELP = 'Use at least 8 characters, including uppercase, lowercase, and a number.';

export function AuthFields({
  includeEmail = true,
  passwordLabel = 'Password',
  passwordMode = 'current',
}: AuthFieldsProps) {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const isNewPassword = passwordMode === 'new';
  const requirements = [
    { label: '8 or more characters', met: password.length >= 8 },
    { label: 'One uppercase letter', met: /[A-Z]/.test(password) },
    { label: 'One lowercase letter', met: /[a-z]/.test(password) },
    { label: 'One number', met: /\d/.test(password) },
  ];

  return (
    <div className="space-y-4">
      {includeEmail ? (
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-txt-primary">Work email</label>
          <input
            id="email"
            name="email"
            type="email"
            spellCheck={false}
            autoComplete="email"
            required
            className="mt-1.5 w-full rounded-xl border border-border bg-white/80 px-3.5 py-3 text-sm text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
          />
        </div>
      ) : null}
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-txt-primary">{passwordLabel}</label>
        <div className="relative mt-1.5">
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            spellCheck={false}
            minLength={isNewPassword ? 8 : undefined}
            pattern={isNewPassword ? PASSWORD_PATTERN : undefined}
            title={isNewPassword ? PASSWORD_HELP : undefined}
            aria-describedby={isNewPassword ? 'password-requirements' : undefined}
            autoComplete={isNewPassword ? 'new-password' : 'current-password'}
            required
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              event.target.setCustomValidity('');
            }}
            onInvalid={(event) => {
              if (isNewPassword && event.currentTarget.validity.patternMismatch) {
                event.currentTarget.setCustomValidity(PASSWORD_HELP);
              }
            }}
            className="w-full rounded-xl border border-border bg-white/80 px-3.5 py-3 pr-12 text-sm text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
          />
          <button
            type="button"
            onClick={() => setShowPassword((visible) => !visible)}
            className="absolute inset-y-0 right-0 flex w-11 touch-manipulation items-center justify-center rounded-r-xl text-txt-muted hover:text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-primary"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            aria-pressed={showPassword}
          >
            {showPassword ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>

        {isNewPassword ? (
          <div id="password-requirements" className="mt-3" aria-live="polite">
            <p className="text-xs font-medium text-txt-secondary">Your password must include:</p>
            <ul className="mt-2 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
              {requirements.map((requirement) => (
                <li
                  key={requirement.label}
                  className={cn(
                    'flex items-center gap-1.5 text-xs',
                    requirement.met ? 'text-status-pass-text' : 'text-txt-muted'
                  )}
                >
                  <span
                    className={cn(
                      'flex h-4 w-4 items-center justify-center rounded-full border',
                      requirement.met
                        ? 'border-status-pass-border bg-status-pass-bg'
                        : 'border-border bg-surface'
                    )}
                    aria-hidden="true"
                  >
                    {requirement.met ? <Check className="h-2.5 w-2.5" /> : null}
                  </span>
                  {requirement.label}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}
