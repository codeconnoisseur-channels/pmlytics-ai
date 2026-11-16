'use client';

import { useState } from 'react';
import { Check, Eye, EyeOff, X } from 'lucide-react';
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
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-txt-secondary">Password requirements:</p>
              {password.length > 0 && requirements.every((r) => r.met) ? (
                <span className="text-[11px] font-semibold text-emerald-600 flex items-center gap-1">
                  <Check className="h-3 w-3 stroke-[3]" /> All requirements met
                </span>
              ) : null}
            </div>
            <ul className="mt-2 grid grid-cols-1 gap-1.5 sm:grid-cols-2">
              {requirements.map((requirement) => {
                const isMet = requirement.met;
                const hasTyped = password.length > 0;

                return (
                  <li
                    key={requirement.label}
                    className={cn(
                      'flex items-center gap-1.5 text-xs transition-colors',
                      isMet
                        ? 'text-emerald-700 font-medium'
                        : hasTyped
                        ? 'text-rose-600'
                        : 'text-txt-muted'
                    )}
                  >
                    <span
                      className={cn(
                        'flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-colors',
                        isMet
                          ? 'border-emerald-300 bg-emerald-50 text-emerald-600'
                          : hasTyped
                          ? 'border-rose-300 bg-rose-50 text-rose-500'
                          : 'border-border bg-surface text-txt-muted/60'
                      )}
                      aria-hidden="true"
                    >
                      {isMet ? (
                        <Check className="h-2.5 w-2.5 stroke-[2.5]" />
                      ) : (
                        <X className="h-2.5 w-2.5 stroke-[2.5]" />
                      )}
                    </span>
                    <span>{requirement.label}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}
      </div>
    </div>
  );
}
