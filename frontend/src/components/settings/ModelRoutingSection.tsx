'use client';

import React from 'react';
import { Cpu, Sliders, Sparkles, Zap, ShieldAlert, Award } from 'lucide-react';
import type { ModelRoutingConfig, RoutingPreset } from '@/lib/settings-store';
import { PRESET_MODELS } from '@/lib/settings-store';
import { cn } from '@/lib/utils';

export interface ModelRoutingSectionProps {
  config: ModelRoutingConfig;
  onChange: (patch: Partial<ModelRoutingConfig>) => void;
}

const AVAILABLE_MODELS = [
  { value: 'openai/gpt-4.1-mini', label: 'GPT-4.1 Mini (Fast & Cheap)', provider: 'OpenAI' },
  { value: 'openai/gpt-5.4-mini', label: 'GPT-5.4 Mini (Strong Reasoning)', provider: 'OpenAI' },
  { value: 'openai/gpt-5.4', label: 'GPT-5.4 (Frontier Product Judgment)', provider: 'OpenAI' },
  { value: 'anthropic/claude-haiku-3.5', label: 'Claude Haiku 3.5 (Fast Analysis)', provider: 'Anthropic' },
  { value: 'anthropic/claude-sonnet-4.6', label: 'Claude Sonnet 4.6 (Frontier PM Benchmark)', provider: 'Anthropic' },
  { value: 'google/gemini-2.5-flash', label: 'Gemini 2.5 Flash (Ultra High-Speed)', provider: 'Google' },
  { value: 'google/gemini-2.5-pro', label: 'Gemini 2.5 Pro (Deep Context Window)', provider: 'Google' },
  { value: 'deepseek/deepseek-chat', label: 'DeepSeek-V3 (Cost-Effective)', provider: 'DeepSeek' },
  { value: 'deepseek/deepseek-reasoner', label: 'DeepSeek-R1 (Deep Reasoning)', provider: 'DeepSeek' },
];

export function ModelRoutingSection({ config, onChange }: ModelRoutingSectionProps) {
  const handleSelectPreset = (preset: RoutingPreset) => {
    if (preset === 'custom') {
      onChange({ preset: 'custom' });
    } else {
      onChange({
        preset,
        ...PRESET_MODELS[preset],
      });
    }
  };

  const handleCustomModelChange = (roleKey: keyof Omit<ModelRoutingConfig, 'preset'>, modelValue: string) => {
    onChange({
      preset: 'custom',
      [roleKey]: modelValue,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-txt-primary flex items-center gap-2">
          <Cpu className="w-5 h-5 text-brand-primary" aria-hidden="true" />
          <span>Model Routing per Agent Task</span>
        </h2>
        <p className="text-xs text-txt-secondary mt-1">
          Optimize your budget and investigation latency by routing high-volume evidence gathering to fast mini models and reserving frontier reasoning for the final PM synthesis.
        </p>
      </div>

      {/* Preset Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          type="button"
          onClick={() => handleSelectPreset('budget')}
          className={cn(
            'flex flex-col text-left rounded-xl border p-3.5 transition-all',
            config.preset === 'budget'
              ? 'border-brand-primary bg-brand-subtle/30 ring-1 ring-brand-primary shadow-sm'
              : 'border-border bg-surface hover:border-border-strong'
          )}
        >
          <div className="flex items-center justify-between w-full mb-1">
            <span className="font-bold text-sm text-txt-primary">Budget / Fast</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-xs text-txt-secondary mb-2">
            Uses high-speed Flash & Mini models for all agents. Lowest cost and fastest completion.
          </p>
          <div className="mt-auto text-[11px] font-mono text-txt-muted">
            Est. &lt; $0.01 per run
          </div>
        </button>

        <button
          type="button"
          onClick={() => handleSelectPreset('balanced')}
          className={cn(
            'flex flex-col text-left rounded-xl border p-3.5 transition-all relative',
            config.preset === 'balanced'
              ? 'border-brand-primary bg-brand-subtle/30 ring-1 ring-brand-primary shadow-sm'
              : 'border-border bg-surface hover:border-border-strong'
          )}
        >
          <div className="absolute -top-2 right-3 px-2 py-0.5 rounded-full bg-brand-primary text-white text-[9px] font-bold uppercase tracking-wider">
            Recommended
          </div>
          <div className="flex items-center justify-between w-full mb-1">
            <span className="font-bold text-sm text-txt-primary">Balanced (Standard)</span>
            <Sparkles className="w-4 h-4 text-brand-primary" />
          </div>
          <p className="text-xs text-txt-secondary mb-2">
            Mini models for data gathering, frontier GPT-5.4 exclusively for PM synthesis.
          </p>
          <div className="mt-auto text-[11px] font-mono text-txt-muted">
            Est. ~$0.04 per run
          </div>
        </button>

        <button
          type="button"
          onClick={() => handleSelectPreset('frontier')}
          className={cn(
            'flex flex-col text-left rounded-xl border p-3.5 transition-all',
            config.preset === 'frontier'
              ? 'border-brand-primary bg-brand-subtle/30 ring-1 ring-brand-primary shadow-sm'
              : 'border-border bg-surface hover:border-border-strong'
          )}
        >
          <div className="flex items-center justify-between w-full mb-1">
            <span className="font-bold text-sm text-txt-primary">Frontier Maximum</span>
            <Award className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-xs text-txt-secondary mb-2">
            Uses frontier GPT-5.4 & Claude Sonnet for every step. Highest reasoning depth.
          </p>
          <div className="mt-auto text-[11px] font-mono text-txt-muted">
            Est. ~$0.20 per run
          </div>
        </button>
      </div>

      {/* Task Assignment Selectors */}
      <div className="rounded-xl border border-border bg-surface p-4 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-txt-secondary" />
            <span className="font-semibold text-sm text-txt-primary">Role-Based Model Assignment</span>
          </div>
          {config.preset === 'custom' && (
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-surface-subtle text-txt-primary border border-border">
              Custom Assignment
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-txt-primary mb-1">
              1. Planning & Task Decomposition
            </label>
            <p className="text-[11px] text-txt-muted mb-2">
              Analyzes user question, defines time boundaries, and dispatches specialist tasks.
            </p>
            <select
              value={config.plannerModel}
              onChange={(e) => handleCustomModelChange('plannerModel', e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
            >
              {AVAILABLE_MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  [{m.provider}] {m.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-txt-primary mb-1">
              2. Specialist Evidence Gathering
            </label>
            <p className="text-[11px] text-txt-muted mb-2">
              Runs Zendesk searches, PostHog telemetry queries, and Jira issue inspections.
            </p>
            <select
              value={config.specialistModel}
              onChange={(e) => handleCustomModelChange('specialistModel', e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
            >
              {AVAILABLE_MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  [{m.provider}] {m.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-txt-primary mb-1">
              3. PM Synthesis & Decision Brief
            </label>
            <p className="text-[11px] text-txt-muted mb-2">
              Translates verified facts into strategic product judgment, action items, and confidence calibration.
            </p>
            <select
              value={config.pmModel}
              onChange={(e) => handleCustomModelChange('pmModel', e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
            >
              {AVAILABLE_MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  [{m.provider}] {m.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-txt-primary mb-1">
              4. Critic Review & Rigor Check
            </label>
            <p className="text-[11px] text-txt-muted mb-2">
              Identifies causal leaps, ungrounded claims, and tensions before finalizing the brief.
            </p>
            <select
              value={config.criticModel}
              onChange={(e) => handleCustomModelChange('criticModel', e.target.value)}
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs text-txt-primary focus:border-brand-primary focus:outline-none"
            >
              {AVAILABLE_MODELS.map((m) => (
                <option key={m.value} value={m.value}>
                  [{m.provider}] {m.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
