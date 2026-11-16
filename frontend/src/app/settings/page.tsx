'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Save, CheckCircle2, Shield, SlidersHorizontal } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/primitives/Button';
import { useSettingsStore } from '@/lib/settings-store';
import { AIProvidersSection } from '@/components/settings/AIProvidersSection';
import { ModelRoutingSection } from '@/components/settings/ModelRoutingSection';
import { EnterpriseDataSection } from '@/components/settings/EnterpriseDataSection';
import { SignalsWatchSection } from '@/components/settings/SignalsWatchSection';

export default function SettingsPage() {
  const { settings, patchSettings } = useSettingsStore();
  const [activeTab, setActiveTab] = useState<'ai' | 'routing' | 'integrations' | 'signals'>('ai');
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = () => {
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
    }, 2500);
  };

  return (
    <AppShell headerTitle="Settings & Integrations">
      <div className="mx-auto max-w-[1040px] px-4 py-8 sm:px-6">
        {/* Top Header Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6 mb-6">
          <div>
            <Link
              href="/investigations"
              className="inline-flex items-center gap-1.5 text-xs text-txt-secondary hover:text-txt-primary mb-2 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Investigations</span>
            </Link>
            <h1 className="text-2xl font-black text-txt-primary tracking-tight">
              Workspace Settings & Integrations
            </h1>
            <p className="text-xs text-txt-secondary mt-1">
              Configure your custom model keys (BYOK), route models per agent role, connect company systems, and customize discovery cadences.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <Button
              type="button"
              variant="primary"
              size="md"
              onClick={handleSave}
              className="gap-2 text-xs h-9 px-4"
            >
              {isSaved ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-white" />
                  <span>Settings Saved</span>
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  <span>Save Changes</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-border mb-8 overflow-x-auto gap-1">
          <button
            type="button"
            onClick={() => setActiveTab('ai')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'ai'
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-txt-secondary hover:text-txt-primary'
            }`}
          >
            AI Models & BYOK
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('routing')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'routing'
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-txt-secondary hover:text-txt-primary'
            }`}
          >
            Model per Task
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('integrations')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'integrations'
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-txt-secondary hover:text-txt-primary'
            }`}
          >
            Enterprise Data Sources
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('signals')}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'signals'
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-txt-secondary hover:text-txt-primary'
            }`}
          >
            Signals & Watch (Automation)
          </button>
        </div>

        {/* Tab Content */}
        <div className="pb-16">
          {activeTab === 'ai' && (
            <AIProvidersSection
              config={settings.aiProviders}
              onChange={(patch) =>
                patchSettings({
                  aiProviders: { ...settings.aiProviders, ...patch },
                })
              }
            />
          )}

          {activeTab === 'routing' && (
            <ModelRoutingSection
              config={settings.modelRouting}
              onChange={(patch) =>
                patchSettings({
                  modelRouting: { ...settings.modelRouting, ...patch },
                })
              }
            />
          )}

          {activeTab === 'integrations' && (
            <EnterpriseDataSection
              config={settings.integrations}
              onChange={(patch) =>
                patchSettings({
                  integrations: { ...settings.integrations, ...patch },
                })
              }
            />
          )}

          {activeTab === 'signals' && (
            <SignalsWatchSection
              config={settings.signalsWatch}
              onChange={(patch) =>
                patchSettings({
                  signalsWatch: { ...settings.signalsWatch, ...patch },
                })
              }
            />
          )}
        </div>
      </div>
    </AppShell>
  );
}
