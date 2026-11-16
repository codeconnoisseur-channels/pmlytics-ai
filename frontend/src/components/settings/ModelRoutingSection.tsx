'use client';

import React from 'react';
import { Cpu, Sparkles, Zap, Award } from 'lucide-react';
import type { ModelRoutingConfig, RoutingPreset } from '@/lib/settings-store';
import { PRESET_MODELS } from '@/lib/settings-store';

export interface ModelRoutingSectionProps {
  config: ModelRoutingConfig;
  onChange: (patch: Partial<ModelRoutingConfig>) => void;
}

const SUGGESTED_MODELS = [
  'openai/gpt-5.4',
  'openai/gpt-4.1-mini',
  'openai/gpt-5.4-mini',
  'anthropic/claude-sonnet-4.6',
  'anthropic/claude-haiku-3.5',
  'google/gemini-2.5-pro',
  'google/gemini-2.5-flash',
  'deepseek/deepseek-chat',
  'deepseek/deepseek-reasoner',
  'astra',
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

  const handleModelChange = (roleKey: keyof Omit<ModelRoutingConfig, 'preset'>, value: string) => {
    onChange({
      preset: 'custom',
      [roleKey]: value,
    });
  };

  return (
    <div className="space-y-6">
      <datalist id="suggested-models">
        {SUGGESTED_MODELS.map((m) => (
          <option key={m} value={m} />
        ))}
      </datalist>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-txt-primary flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-primary" aria-hidden="true" />
            <span>Model per Task</span>
          </h2>
          <p className="text-xs text-txt-muted mt-0.5">
            Select or type any model ID (e.g. OpenAI, Anthropic, Gemini, Astra, or custom).
          </p>
        </div>

        {/* Subtle Quick Presets Bar */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] text-txt-muted mr-1">Quick presets:</span>
          <button
            type="button"
            onClick={() => handleSelectPreset('budget')}
            className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
              config.preset === 'budget'
                ? 'bg-brand-primary text-white border-brand-primary font-semibold'
                : 'bg-surface text-txt-secondary border-border hover:bg-surface-subtle'
            }`}
          >
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3" /> Fast / Low Cost
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleSelectPreset('balanced')}
            className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
              config.preset === 'balanced'
                ? 'bg-brand-primary text-white border-brand-primary font-semibold'
                : 'bg-surface text-txt-secondary border-border hover:bg-surface-subtle'
            }`}
          >
            <span className="flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Balanced
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleSelectPreset('frontier')}
            className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
              config.preset === 'frontier'
                ? 'bg-brand-primary text-white border-brand-primary font-semibold'
                : 'bg-surface text-txt-secondary border-border hover:bg-surface-subtle'
            }`}
          >
            <span className="flex items-center gap-1">
              <Award className="w-3 h-3" /> Frontier Max
            </span>
          </button>
        </div>
      </div>

      {/* 4 Agent Roles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* 1. Planning */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-bold text-txt-primary">
              1. Planning & Decomposition
            </label>
            <span className="text-[10px] text-txt-muted">Structures inquiry</span>
          </div>
          <div className="relative">
            <input
              type="text"
              list="suggested-models"
              value={config.plannerModel}
              onChange={(e) => handleModelChange('plannerModel', e.target.value)}
              placeholder="e.g. openai/gpt-4.1-mini, astra..."
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
            />
          </div>
          <p className="text-[11px] text-txt-muted mt-1.5">
            Formulates the structured diagnostic plan and determines required data sources.
          </p>
        </div>

        {/* 2. Specialist Gathering */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-bold text-txt-primary">
              2. Specialist Evidence Gathering
            </label>
            <span className="text-[10px] text-txt-muted">Zendesk, Jira, PostHog</span>
          </div>
          <div className="relative">
            <input
              type="text"
              list="suggested-models"
              value={config.specialistModel}
              onChange={(e) => handleModelChange('specialistModel', e.target.value)}
              placeholder="e.g. openai/gpt-4.1-mini, google/gemini-2.5-flash..."
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
            />
          </div>
          <p className="text-[11px] text-txt-muted mt-1.5">
            Executes tool queries across customer support tickets, telemetry, and issues.
          </p>
        </div>

        {/* 3. PM Synthesis */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-bold text-txt-primary">
              3. PM Synthesis & Decision Brief
            </label>
            <span className="text-[10px] text-txt-muted">Product judgment</span>
          </div>
          <div className="relative">
            <input
              type="text"
              list="suggested-models"
              value={config.pmModel}
              onChange={(e) => handleModelChange('pmModel', e.target.value)}
              placeholder="e.g. openai/gpt-5.4, anthropic/claude-sonnet-4.6..."
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
            />
          </div>
          <p className="text-[11px] text-txt-muted mt-1.5">
            Delivers executive recommendations, confidence score, and action plan.
          </p>
        </div>

        {/* 4. Critic Review */}
        <div className="rounded-xl border border-border bg-surface p-4 shadow-xs">
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-bold text-txt-primary">
              4. Critic Review & Verification
            </label>
            <span className="text-[10px] text-txt-muted">Rigor check</span>
          </div>
          <div className="relative">
            <input
              type="text"
              list="suggested-models"
              value={config.criticModel}
              onChange={(e) => handleModelChange('criticModel', e.target.value)}
              placeholder="e.g. openai/gpt-5.4-mini, astra..."
              className="w-full h-9 rounded-lg border border-border bg-canvas px-3 text-xs font-mono text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
            />
          </div>
          <p className="text-[11px] text-txt-muted mt-1.5">
            Challenges ungrounded claims, missing evidence, and contradictions.
          </p>
        </div>
      </div>
    </div>
  );
}
