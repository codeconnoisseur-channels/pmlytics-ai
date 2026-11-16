'use client';

import React from 'react';
import { BellRing, Calendar, Mail, AlertTriangle, Clock, Radio } from 'lucide-react';
import type { SignalsWatchConfig } from '@/lib/settings-store';
import { cn } from '@/lib/utils';

export interface SignalsWatchSectionProps {
  config: SignalsWatchConfig;
  onChange: (patch: Partial<SignalsWatchConfig>) => void;
}

export function SignalsWatchSection({ config, onChange }: SignalsWatchSectionProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-txt-primary flex items-center gap-2">
            <Radio className="w-5 h-5 text-brand-primary" aria-hidden="true" />
            <span>Signals & Watch (Automation Cadence)</span>
          </h2>
          <p className="text-xs text-txt-secondary mt-1">
            Automate continuous product discovery. Monitor error rates, customer tickets, and engineering backlogs automatically on a recurring schedule.
          </p>
        </div>

        <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
          Beta / In-Progress
        </span>
      </div>

      <div className="grid gap-3">
        {/* 1. Daily Refresh */}
        <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-4 shadow-sm">
          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-txt-secondary shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-sm text-txt-primary">Daily Morning Refresh</div>
              <p className="text-xs text-txt-secondary mt-0.5">
                Automatically scans Zendesk tickets and PostHog funnels every morning at 08:00 for new emerging trends.
              </p>
            </div>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.dailyRefresh}
              onChange={(e) => onChange({ dailyRefresh: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-surface-subtle peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary border border-border" />
          </label>
        </div>

        {/* 2. Weekly Refresh */}
        <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-4 shadow-sm">
          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-txt-secondary shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-sm text-txt-primary">Weekly Discovery Synthesis</div>
              <p className="text-xs text-txt-secondary mt-0.5">
                Aggregates a Monday morning decision brief comparing this week&apos;s product performance against baseline metrics.
              </p>
            </div>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.weeklyRefresh}
              onChange={(e) => onChange({ weeklyRefresh: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-surface-subtle peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary border border-border" />
          </label>
        </div>

        {/* 3. Hot Signals Alert */}
        <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-4 shadow-sm">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-sm text-txt-primary">Critical Spike Alerts</div>
              <p className="text-xs text-txt-secondary mt-0.5">
                Immediate notification if user verification drop-offs or payment failures surge by &gt; 15% within 1 hour.
              </p>
            </div>
          </div>

          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={config.hotSignalAlerts}
              onChange={(e) => onChange({ hotSignalAlerts: e.target.checked })}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-surface-subtle peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary border border-border" />
          </label>
        </div>

        {/* 4. Email Digest */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-start gap-3">
              <Mail className="w-5 h-5 text-txt-secondary shrink-0 mt-0.5" />
              <div>
                <div className="font-semibold text-sm text-txt-primary">Email Digest Delivery</div>
                <p className="text-xs text-txt-secondary mt-0.5">
                  Sends formatted decision summaries directly to product stakeholders.
                </p>
              </div>
            </div>

            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={config.emailDigest}
                onChange={(e) => onChange({ emailDigest: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-surface-subtle peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-border after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary border border-border" />
            </label>
          </div>

          {config.emailDigest && (
            <div className="pt-2 border-t border-border">
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Recipient Email Address
              </label>
              <input
                type="email"
                value={config.targetEmail}
                onChange={(e) => onChange({ targetEmail: e.target.value })}
                placeholder="pm-lead@company.com"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none max-w-md"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
