'use client';

import React, { useState } from 'react';
import { Key, Eye, EyeOff, CheckCircle2, ShieldCheck, Zap, Sparkles, Server } from 'lucide-react';
import type { AIProvidersConfig } from '@/lib/settings-store';
import { Button } from '@/components/primitives/Button';

export interface AIProvidersSectionProps {
  config: AIProvidersConfig;
  onChange: (patch: Partial<AIProvidersConfig>) => void;
}

interface ProviderDefinition {
  id: keyof Omit<AIProvidersConfig, 'customEndpoint'>;
  name: string;
  badge: string;
  placeholder: string;
  description: string;
  sampleModels: string;
}

const PROVIDERS: ProviderDefinition[] = [
  {
    id: 'openaiKey',
    name: 'OpenAI',
    badge: 'Frontier',
    placeholder: 'sk-...',
    description: 'Direct OpenAI developer API key for GPT-5.4, GPT-5-mini, and GPT-4.1.',
    sampleModels: 'openai/gpt-5.4, openai/gpt-4.1-mini',
  },
  {
    id: 'anthropicKey',
    name: 'Anthropic Claude',
    badge: 'Frontier',
    placeholder: 'sk-ant-...',
    description: 'Direct Anthropic console key for Claude Sonnet 4.6 and Claude Haiku 3.5.',
    sampleModels: 'anthropic/claude-sonnet-4.6, anthropic/claude-haiku-3.5',
  },
  {
    id: 'geminiKey',
    name: 'Google Gemini',
    badge: 'High Speed',
    placeholder: 'AIza...',
    description: 'Google AI Studio key for high-speed analysis and long context windows.',
    sampleModels: 'google/gemini-2.5-pro, google/gemini-2.5-flash',
  },
  {
    id: 'deepseekKey',
    name: 'DeepSeek',
    badge: 'Cost-Effective',
    placeholder: 'sk-...',
    description: 'DeepSeek API key for DeepSeek-V3 and DeepSeek-R1 reasoning models.',
    sampleModels: 'deepseek/deepseek-chat, deepseek/deepseek-reasoner',
  },
  {
    id: 'openrouterKey',
    name: 'OpenRouter Gateway',
    badge: 'Unified',
    placeholder: 'sk-or-v1-...',
    description: 'Unified inference gateway providing single-key access to 200+ frontier & open models.',
    sampleModels: 'Routes to any model with unified usage tracking',
  },
];

export function AIProvidersSection({ config, onChange }: AIProvidersSectionProps) {
  const [showKey, setShowKey] = useState<Record<string, boolean>>({});
  const [testedProvider, setTestedProvider] = useState<string | null>(null);

  const toggleShow = (id: string) => {
    setShowKey((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleTestKey = (providerName: string, keyVal: string) => {
    if (!keyVal.trim()) return;
    setTestedProvider(providerName);
    setTimeout(() => {
      setTestedProvider(null);
    }, 2500);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-txt-primary flex items-center gap-2">
          <Key className="w-5 h-5 text-brand-primary" aria-hidden="true" />
          <span>AI Models & API Keys (BYOK)</span>
        </h2>
        <p className="text-xs text-txt-secondary mt-1">
          Bring your own API keys. Keys are encrypted and stored in your workspace session. You can connect your direct provider accounts or use OpenRouter for unified billing.
        </p>
      </div>

      <div className="grid gap-4">
        {PROVIDERS.map((provider) => {
          const val = config[provider.id] || '';
          const isVisible = Boolean(showKey[provider.id]);
          const isTested = testedProvider === provider.name;

          return (
            <div
              key={provider.id}
              className="rounded-xl border border-border bg-surface p-4 transition-all hover:border-border-strong shadow-sm"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-txt-primary">{provider.name}</span>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-surface-subtle text-txt-secondary border border-border">
                    {provider.badge}
                  </span>
                  {val && (
                    <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3 h-3" />
                      Configured
                    </span>
                  )}
                </div>

                <div className="text-[11px] text-txt-muted flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-txt-muted" />
                  <span>{provider.sampleModels}</span>
                </div>
              </div>

              <p className="text-xs text-txt-secondary mb-3">{provider.description}</p>

              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <input
                    type={isVisible ? 'text' : 'password'}
                    value={val}
                    onChange={(e) => onChange({ [provider.id]: e.target.value })}
                    placeholder={provider.placeholder}
                    className="w-full h-9 rounded-lg border border-border bg-canvas px-3 pr-9 text-xs font-mono text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none focus:ring-1 focus:ring-brand-primary"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShow(provider.id)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-txt-muted hover:text-txt-primary transition-colors"
                    aria-label={isVisible ? 'Hide key' : 'Show key'}
                  >
                    {isVisible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => handleTestKey(provider.name, val)}
                  disabled={!val.trim()}
                  className="h-9 px-3 text-xs shrink-0"
                >
                  {isTested ? (
                    <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Validated
                    </span>
                  ) : (
                    <span className="flex items-center gap-1">
                      <Zap className="w-3.5 h-3.5 text-txt-muted" /> Test Key
                    </span>
                  )}
                </Button>
              </div>
            </div>
          );
        })}

        {/* Custom OpenAI-Compatible Base URL Card */}
        <div className="rounded-xl border border-dashed border-border-strong bg-surface/50 p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-txt-secondary" />
              <span className="font-semibold text-sm text-txt-primary">Any OpenAI-Compatible Endpoint</span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-subtle text-brand-primary">
                Self-Hosted / Gateway
              </span>
            </div>
          </div>
          <p className="text-xs text-txt-secondary mb-3">
            Connect local servers (Ollama, vLLM, LM Studio) or alternative cloud gateways (Together AI, Groq, Azure OpenAI).
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">Base URL</label>
              <input
                type="text"
                value={config.customEndpoint?.baseUrl || ''}
                onChange={(e) =>
                  onChange({
                    customEndpoint: {
                      baseUrl: e.target.value,
                      apiKey: config.customEndpoint?.apiKey || '',
                      modelName: config.customEndpoint?.modelName || '',
                    },
                  })
                }
                placeholder="https://api.together.xyz/v1"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">API Key (Optional)</label>
              <input
                type="password"
                value={config.customEndpoint?.apiKey || ''}
                onChange={(e) =>
                  onChange({
                    customEndpoint: {
                      baseUrl: config.customEndpoint?.baseUrl || '',
                      apiKey: e.target.value,
                      modelName: config.customEndpoint?.modelName || '',
                    },
                  })
                }
                placeholder="sk-..."
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-txt-secondary mb-1">Model Name</label>
              <input
                type="text"
                value={config.customEndpoint?.modelName || ''}
                onChange={(e) =>
                  onChange({
                    customEndpoint: {
                      baseUrl: config.customEndpoint?.baseUrl || '',
                      apiKey: config.customEndpoint?.apiKey || '',
                      modelName: e.target.value,
                    },
                  })
                }
                placeholder="meta-llama/Llama-3.3-70B-Instruct"
                className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg bg-surface-subtle border border-border p-3 flex items-start gap-2.5 text-xs text-txt-secondary">
        <ShieldCheck className="w-4 h-4 text-brand-primary shrink-0 mt-0.5" />
        <span>
          <strong>Enterprise Key Isolation:</strong> All keys configured here take precedence over server defaults for your session. PMLytics AI never trains on or shares your credentials.
        </span>
      </div>
    </div>
  );
}
