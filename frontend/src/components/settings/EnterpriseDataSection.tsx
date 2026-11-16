'use client';

import React, { useState } from 'react';
import { Database, CheckCircle2, AlertCircle, Building2, ExternalLink, RefreshCw, Layers } from 'lucide-react';
import type { EnterpriseIntegrationsConfig } from '@/lib/settings-store';
import { Button } from '@/components/primitives/Button';
import { cn } from '@/lib/utils';

export interface EnterpriseDataSectionProps {
  config: EnterpriseIntegrationsConfig;
  onChange: (patch: Partial<EnterpriseIntegrationsConfig>) => void;
}

export function EnterpriseDataSection({ config, onChange }: EnterpriseDataSectionProps) {
  const [testStatus, setTestStatus] = useState<Record<string, 'testing' | 'success' | null>>({});

  const isProduction = config.environment === 'production';

  const testIntegration = (id: string) => {
    setTestStatus((prev) => ({ ...prev, [id]: 'testing' }));
    setTimeout(() => {
      setTestStatus((prev) => ({ ...prev, [id]: 'success' }));
      setTimeout(() => {
        setTestStatus((prev) => ({ ...prev, [id]: null }));
      }, 3000);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-txt-primary flex items-center gap-2">
            <Database className="w-5 h-5 text-brand-primary" aria-hidden="true" />
            <span>Enterprise Data Source Integrations</span>
          </h2>
          <p className="text-xs text-txt-secondary mt-1">
            Connect your company&apos;s real Jira, Zendesk, and PostHog accounts to investigate real production problems.
          </p>
        </div>

        {/* Environment Mode Switcher */}
        <div className="inline-flex rounded-lg border border-border bg-surface p-1 self-start sm:self-auto shadow-sm">
          <button
            type="button"
            onClick={() => onChange({ environment: 'sandbox' })}
            className={cn(
              'px-3 py-1 text-xs font-semibold rounded-md transition-colors',
              !isProduction
                ? 'bg-brand-primary text-white shadow-xs'
                : 'text-txt-secondary hover:text-txt-primary'
            )}
          >
            Demo Sandbox
          </button>
          <button
            type="button"
            onClick={() => onChange({ environment: 'production' })}
            className={cn(
              'px-3 py-1 text-xs font-semibold rounded-md transition-colors',
              isProduction
                ? 'bg-brand-primary text-white shadow-xs'
                : 'text-txt-secondary hover:text-txt-primary'
            )}
          >
            Live Enterprise APIs
          </button>
        </div>
      </div>

      {!isProduction ? (
        <div className="rounded-xl border border-brand-border bg-brand-subtle/40 p-4 flex items-start gap-3">
          <Layers className="w-5 h-5 text-brand-primary shrink-0 mt-0.5" />
          <div className="text-xs text-txt-secondary">
            <strong className="text-txt-primary font-semibold">Active Mode: Built-in Pocket Demo Sandbox</strong>
            <p className="mt-0.5 leading-relaxed">
              Investigations query the verified mock datasets (failed transfers, verification drops, debit funding anomalies) on your backend container. Switch to <strong>Live Enterprise APIs</strong> above to connect your team&apos;s real tools.
            </p>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-border-strong bg-surface p-4 flex items-start gap-3 shadow-xs">
          <Building2 className="w-5 h-5 text-brand-primary shrink-0 mt-0.5" />
          <div className="text-xs text-txt-secondary">
            <strong className="text-txt-primary font-semibold">Active Mode: Live Enterprise Connectors</strong>
            <p className="mt-0.5 leading-relaxed">
              PMLytics AI agents query your corporate endpoints using read-only API tokens. Agents have zero autonomous write permissions and cannot edit issues or customer tickets.
            </p>
          </div>
        </div>
      )}

      <div className="grid gap-5">
        {/* 1. Jira Software Cloud */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-txt-primary">Atlassian Jira Software (Cloud)</span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                Engineering Context
              </span>
            </div>
            <a
              href="https://id.atlassian.com/manage-profile/security/api-tokens"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-medium text-brand-primary hover:underline flex items-center gap-1"
            >
              Get Atlassian Token <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Jira Cloud Host URL
              </label>
              <input
                type="text"
                value={config.jira.domain}
                onChange={(e) =>
                  onChange({
                    jira: { ...config.jira, domain: e.target.value },
                  })
                }
                placeholder="https://company.atlassian.net"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Atlassian Service Account Email
              </label>
              <input
                type="email"
                value={config.jira.email}
                onChange={(e) =>
                  onChange({
                    jira: { ...config.jira, email: e.target.value },
                  })
                }
                placeholder="pm-bot@company.com"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Jira API Token
              </label>
              <input
                type="password"
                value={config.jira.apiToken}
                onChange={(e) =>
                  onChange({
                    jira: { ...config.jira, apiToken: e.target.value },
                  })
                }
                placeholder="ATATT3xFfGF0..."
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Default Project Key (Optional)
              </label>
              <input
                type="text"
                value={config.jira.projectKey}
                onChange={(e) =>
                  onChange({
                    jira: { ...config.jira, projectKey: e.target.value },
                  })
                }
                placeholder="CORE, PAY, PROD"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => testIntegration('jira')}
              disabled={!config.jira.domain.trim() || testStatus.jira === 'testing'}
              className="h-8 text-xs"
            >
              {testStatus.jira === 'testing' ? (
                <span className="flex items-center gap-1.5 text-txt-secondary">
                  <RefreshCw className="w-3 h-3 animate-spin" /> Verifying Jira API...
                </span>
              ) : testStatus.jira === 'success' ? (
                <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Jira Cloud Reachable
                </span>
              ) : (
                'Test Jira Connection'
              )}
            </Button>
          </div>
        </div>

        {/* 2. Zendesk Support */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-txt-primary">Zendesk Support</span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                Customer Support Evidence
              </span>
            </div>
            <a
              href="https://support.zendesk.com/hc/en-us/articles/4408889105434"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-medium text-brand-primary hover:underline flex items-center gap-1"
            >
              Zendesk API Docs <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Zendesk Subdomain
              </label>
              <input
                type="text"
                value={config.zendesk.subdomain}
                onChange={(e) =>
                  onChange({
                    zendesk: { ...config.zendesk, subdomain: e.target.value },
                  })
                }
                placeholder="your-company (e.g. acme)"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Agent / Admin Email
              </label>
              <input
                type="email"
                value={config.zendesk.email}
                onChange={(e) =>
                  onChange({
                    zendesk: { ...config.zendesk, email: e.target.value },
                  })
                }
                placeholder="agent@company.com"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Zendesk API Token
              </label>
              <input
                type="password"
                value={config.zendesk.apiToken}
                onChange={(e) =>
                  onChange({
                    zendesk: { ...config.zendesk, apiToken: e.target.value },
                  })
                }
                placeholder="token_..."
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => testIntegration('zendesk')}
              disabled={!config.zendesk.subdomain.trim() || testStatus.zendesk === 'testing'}
              className="h-8 text-xs"
            >
              {testStatus.zendesk === 'testing' ? (
                <span className="flex items-center gap-1.5 text-txt-secondary">
                  <RefreshCw className="w-3 h-3 animate-spin" /> Verifying Zendesk API...
                </span>
              ) : testStatus.zendesk === 'success' ? (
                <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Zendesk Connected
                </span>
              ) : (
                'Test Zendesk Connection'
              )}
            </Button>
          </div>
        </div>

        {/* 3. PostHog Analytics */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-txt-primary">PostHog Analytics</span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                Product Telemetry
              </span>
            </div>
            <a
              href="https://posthog.com/docs/api"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[11px] font-medium text-brand-primary hover:underline flex items-center gap-1"
            >
              PostHog API Keys <ExternalLink className="w-3 h-3" />
            </a>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                PostHog Host
              </label>
              <input
                type="text"
                value={config.posthog.host}
                onChange={(e) =>
                  onChange({
                    posthog: { ...config.posthog, host: e.target.value },
                  })
                }
                placeholder="https://us.posthog.com"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Project ID
              </label>
              <input
                type="text"
                value={config.posthog.projectId}
                onChange={(e) =>
                  onChange({
                    posthog: { ...config.posthog, projectId: e.target.value },
                  })
                }
                placeholder="10492"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">
                Personal API Key
              </label>
              <input
                type="password"
                value={config.posthog.apiKey}
                onChange={(e) =>
                  onChange({
                    posthog: { ...config.posthog, apiKey: e.target.value },
                  })
                }
                placeholder="phx_..."
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary focus:border-brand-primary focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => testIntegration('posthog')}
              disabled={!config.posthog.apiKey.trim() || testStatus.posthog === 'testing'}
              className="h-8 text-xs"
            >
              {testStatus.posthog === 'testing' ? (
                <span className="flex items-center gap-1.5 text-txt-secondary">
                  <RefreshCw className="w-3 h-3 animate-spin" /> Verifying PostHog API...
                </span>
              ) : testStatus.posthog === 'success' ? (
                <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" /> PostHog Connected
                </span>
              ) : (
                'Test PostHog Connection'
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
