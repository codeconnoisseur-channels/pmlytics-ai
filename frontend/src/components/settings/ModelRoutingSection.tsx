'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Cpu, ChevronDown, Check, Sparkles, Zap, Award, Search, PlusCircle, CheckCircle2 } from 'lucide-react';
import type { ModelRoutingConfig, RoutingPreset } from '@/lib/settings-store';
import { PRESET_MODELS } from '@/lib/settings-store';
import { cn } from '@/lib/utils';

export interface ModelRoutingSectionProps {
  config: ModelRoutingConfig;
  onChange: (patch: Partial<ModelRoutingConfig>) => void;
}

interface ModelOption {
  value: string;
  label: string;
  provider: 'OpenAI' | 'DeepSeek' | 'Anthropic' | 'Google' | 'Custom';
}

const CURATED_MODELS: ModelOption[] = [
  // OpenAI
  { value: 'openai/gpt-4.1-mini', label: 'GPT-4.1 Mini', provider: 'OpenAI' },
  { value: 'openai/gpt-5.4-mini', label: 'GPT-5.4 Mini', provider: 'OpenAI' },
  { value: 'openai/gpt-5.4', label: 'GPT-5.4 (Frontier Judgment)', provider: 'OpenAI' },
  { value: 'openai/astra', label: 'Astra (OpenAI Next-Gen)', provider: 'OpenAI' },

  // DeepSeek
  { value: 'deepseek/deepseek-chat', label: 'DeepSeek-V3', provider: 'DeepSeek' },
  { value: 'deepseek/deepseek-reasoner', label: 'DeepSeek-R1 (Reasoning)', provider: 'DeepSeek' },

  // Anthropic
  { value: 'anthropic/claude-haiku-3.5', label: 'Claude Haiku 3.5', provider: 'Anthropic' },
  { value: 'anthropic/claude-sonnet-4.6', label: 'Claude Sonnet 4.6 (PM Benchmark)', provider: 'Anthropic' },

  // Google
  { value: 'google/gemini-2.5-flash', label: 'Gemini 2.5 Flash', provider: 'Google' },
  { value: 'google/gemini-2.5-pro', label: 'Gemini 2.5 Pro', provider: 'Google' },
];

interface ModelSelectorProps {
  label: string;
  roleDescription: string;
  value: string;
  onChange: (val: string) => void;
}

function ModelSelector({ label, roleDescription, value, onChange }: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const filtered = CURATED_MODELS.filter(
    (m) =>
      m.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.value.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.provider.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const isCustomMatch =
    searchTerm.trim() &&
    !CURATED_MODELS.some((m) => m.value.toLowerCase() === searchTerm.trim().toLowerCase());

  const currentOption = CURATED_MODELS.find((m) => m.value === value);

  return (
    <div className="rounded-xl border border-border bg-surface p-4 shadow-xs" ref={containerRef}>
      <div className="flex items-center justify-between mb-1">
        <label className="text-xs font-bold text-txt-primary">{label}</label>
        <span className="text-[10px] text-txt-muted">{roleDescription}</span>
      </div>

      <div className="relative mt-2">
        {/* Visible, clickable Dropdown Button with prominent chevron */}
        <button
          type="button"
          onClick={() => {
            setIsOpen((prev) => !prev);
            setSearchTerm('');
          }}
          className={cn(
            'flex w-full items-center justify-between rounded-lg border bg-canvas px-3 py-2 text-xs font-mono transition-colors text-left focus:outline-none focus:ring-1 focus:ring-brand-primary',
            isOpen ? 'border-brand-primary ring-1 ring-brand-primary' : 'border-border hover:border-border-strong'
          )}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <div className="flex items-center gap-2 truncate">
            {currentOption ? (
              <>
                <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-surface-subtle text-txt-secondary border border-border">
                  {currentOption.provider}
                </span>
                <span className="text-txt-primary truncate font-semibold">{currentOption.label}</span>
                <span className="text-txt-muted text-[11px] truncate hidden sm:inline">({currentOption.value})</span>
              </>
            ) : (
              <>
                <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200">
                  Custom
                </span>
                <span className="text-txt-primary truncate font-semibold">{value || 'Select a model...'}</span>
              </>
            )}
          </div>
          <ChevronDown
            className={cn('h-4 w-4 shrink-0 text-txt-secondary transition-transform ml-2', isOpen && 'rotate-180 text-brand-primary')}
            aria-hidden="true"
          />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute left-0 right-0 z-50 mt-1 max-h-72 origin-top rounded-xl border border-border bg-surface p-1.5 shadow-xl ring-1 ring-black/5 overflow-hidden flex flex-col">
            {/* Search / Custom input bar */}
            <div className="relative mb-1.5 p-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-txt-muted" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search model or type custom ID..."
                className="w-full h-8 pl-8 pr-3 text-xs rounded-lg border border-border bg-canvas text-txt-primary placeholder:text-txt-muted focus:border-brand-primary focus:outline-none"
                autoFocus
              />
            </div>

            {/* If user types custom text not in the list, offer quick selection */}
            {isCustomMatch && (
              <button
                type="button"
                onClick={() => {
                  onChange(searchTerm.trim());
                  setIsOpen(false);
                }}
                className="flex items-center gap-2 rounded-lg bg-brand-subtle/50 px-2.5 py-2 text-xs font-semibold text-brand-primary hover:bg-brand-subtle mb-1 text-left transition-colors"
              >
                <PlusCircle className="h-4 w-4 shrink-0" />
                <span>Use custom model: &quot;<strong>{searchTerm.trim()}</strong>&quot;</span>
              </button>
            )}

            {/* Categorized List */}
            <div className="overflow-y-auto max-h-56 space-y-1 pr-1">
              {['OpenAI', 'DeepSeek', 'Anthropic', 'Google'].map((provider) => {
                const group = filtered.filter((m) => m.provider === provider);
                if (group.length === 0) return null;

                return (
                  <div key={provider} className="pt-1">
                    <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-txt-muted">
                      {provider}
                    </div>
                    {group.map((item) => {
                      const isSelected = item.value === value;
                      return (
                        <button
                          key={item.value}
                          type="button"
                          onClick={() => {
                            onChange(item.value);
                            setIsOpen(false);
                          }}
                          className={cn(
                            'flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs text-left transition-colors',
                            isSelected
                              ? 'bg-brand-primary text-white font-semibold'
                              : 'text-txt-primary hover:bg-surface-subtle'
                          )}
                        >
                          <div className="truncate">
                            <span>{item.label}</span>
                            <span className={cn('text-[11px] ml-1.5 font-mono', isSelected ? 'text-white/80' : 'text-txt-muted')}>
                              {item.value}
                            </span>
                          </div>
                          {isSelected && <Check className="h-3.5 w-3.5 shrink-0 ml-2" />}
                        </button>
                      );
                    })}
                  </div>
                );
              })}

              {filtered.length === 0 && !isCustomMatch && (
                <div className="p-3 text-center text-xs text-txt-muted">
                  No predefined model matched &quot;{searchTerm}&quot;. Type the exact model ID above to use it.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-txt-primary flex items-center gap-2">
            <Cpu className="w-4 h-4 text-brand-primary" aria-hidden="true" />
            <span>Model per Task</span>
          </h2>
          <p className="text-xs text-txt-muted mt-0.5">
            Select or enter any model from OpenAI (including Astra), DeepSeek, Anthropic, Google, or your custom endpoints.
          </p>
        </div>

        {/* Quick Presets Bar */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] text-txt-muted mr-1">Quick stacks:</span>

          <button
            type="button"
            onClick={() => handleSelectPreset('balanced')}
            className={cn(
              'px-2.5 py-1 text-xs rounded-full border transition-colors',
              config.preset === 'balanced'
                ? 'bg-brand-primary text-white border-brand-primary font-semibold shadow-xs'
                : 'bg-surface text-txt-secondary border-border hover:bg-surface-subtle'
            )}
          >
            <span className="flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> OpenAI Standard
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleSelectPreset('deepseek')}
            className={cn(
              'px-2.5 py-1 text-xs rounded-full border transition-colors',
              config.preset === 'deepseek'
                ? 'bg-brand-primary text-white border-brand-primary font-semibold shadow-xs'
                : 'bg-surface text-txt-secondary border-border hover:bg-surface-subtle'
            )}
          >
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-blue-500" /> DeepSeek Stack
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleSelectPreset('anthropic')}
            className={cn(
              'px-2.5 py-1 text-xs rounded-full border transition-colors',
              config.preset === 'anthropic'
                ? 'bg-brand-primary text-white border-brand-primary font-semibold shadow-xs'
                : 'bg-surface text-txt-secondary border-border hover:bg-surface-subtle'
            )}
          >
            <span className="flex items-center gap-1">
              <Award className="w-3 h-3 text-amber-500" /> Anthropic Stack
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleSelectPreset('budget')}
            className={cn(
              'px-2.5 py-1 text-xs rounded-full border transition-colors',
              config.preset === 'budget'
                ? 'bg-brand-primary text-white border-brand-primary font-semibold shadow-xs'
                : 'bg-surface text-txt-secondary border-border hover:bg-surface-subtle'
            )}
          >
            <span className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-emerald-500" /> Fast / Low Cost
            </span>
          </button>
        </div>
      </div>

      {/* 4 Agent Roles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ModelSelector
          label="1. Planning & Task Decomposition"
          roleDescription="Structures diagnostic inquiry"
          value={config.plannerModel}
          onChange={(val) => handleModelChange('plannerModel', val)}
        />

        <ModelSelector
          label="2. Specialist Evidence Gathering"
          roleDescription="Zendesk, Jira, PostHog retrieval"
          value={config.specialistModel}
          onChange={(val) => handleModelChange('specialistModel', val)}
        />

        <ModelSelector
          label="3. PM Synthesis & Decision Brief"
          roleDescription="Executive recommendation & judgment"
          value={config.pmModel}
          onChange={(val) => handleModelChange('pmModel', val)}
        />

        <ModelSelector
          label="4. Critic Review & Verification"
          roleDescription="Rigor, causal check & limitations"
          value={config.criticModel}
          onChange={(val) => handleModelChange('criticModel', val)}
        />
      </div>
    </div>
  );
}
