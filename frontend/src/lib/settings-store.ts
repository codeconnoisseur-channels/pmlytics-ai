'use client';

import { useState, useEffect, useCallback } from 'react';

export interface CustomEndpointConfig {
  baseUrl: string;
  apiKey: string;
  modelName: string;
}

export interface AIProvidersConfig {
  openaiKey: string;
  anthropicKey: string;
  geminiKey: string;
  deepseekKey: string;
  openrouterKey: string;
  customEndpoint: CustomEndpointConfig;
}

export type RoutingPreset = 'budget' | 'balanced' | 'frontier' | 'custom';

export interface ModelRoutingConfig {
  preset: RoutingPreset;
  plannerModel: string;
  specialistModel: string;
  pmModel: string;
  criticModel: string;
}

export interface JiraConfig {
  enabled: boolean;
  domain: string;
  email: string;
  apiToken: string;
  projectKey: string;
}

export interface ZendeskConfig {
  enabled: boolean;
  subdomain: string;
  email: string;
  apiToken: string;
}

export interface PostHogConfig {
  enabled: boolean;
  host: string;
  projectId: string;
  apiKey: string;
}

export interface EnterpriseIntegrationsConfig {
  environment: 'production' | 'sandbox';
  jira: JiraConfig;
  zendesk: ZendeskConfig;
  posthog: PostHogConfig;
}

export interface SignalsWatchConfig {
  dailyRefresh: boolean;
  weeklyRefresh: boolean;
  hotSignalAlerts: boolean;
  emailDigest: boolean;
  targetEmail: string;
}

export interface UserSettings {
  aiProviders: AIProvidersConfig;
  modelRouting: ModelRoutingConfig;
  integrations: EnterpriseIntegrationsConfig;
  signalsWatch: SignalsWatchConfig;
}

export const PRESET_MODELS: Record<Exclude<RoutingPreset, 'custom'>, Omit<ModelRoutingConfig, 'preset'>> = {
  budget: {
    plannerModel: 'google/gemini-2.5-flash',
    specialistModel: 'openai/gpt-4.1-mini',
    pmModel: 'openai/gpt-4.1-mini',
    criticModel: 'openai/gpt-4.1-mini',
  },
  balanced: {
    plannerModel: 'openai/gpt-4.1-mini',
    specialistModel: 'openai/gpt-4.1-mini',
    pmModel: 'openai/gpt-5.4',
    criticModel: 'openai/gpt-5.4-mini',
  },
  frontier: {
    plannerModel: 'openai/gpt-5.4',
    specialistModel: 'openai/gpt-5.4',
    pmModel: 'openai/gpt-5.4',
    criticModel: 'anthropic/claude-sonnet-4.6',
  },
};

export const DEFAULT_USER_SETTINGS: UserSettings = {
  aiProviders: {
    openaiKey: '',
    anthropicKey: '',
    geminiKey: '',
    deepseekKey: '',
    openrouterKey: '',
    customEndpoint: {
      baseUrl: '',
      apiKey: '',
      modelName: '',
    },
  },
  modelRouting: {
    preset: 'balanced',
    ...PRESET_MODELS.balanced,
  },
  integrations: {
    environment: 'sandbox',
    jira: {
      enabled: false,
      domain: '',
      email: '',
      apiToken: '',
      projectKey: '',
    },
    zendesk: {
      enabled: false,
      subdomain: '',
      email: '',
      apiToken: '',
    },
    posthog: {
      enabled: false,
      host: 'https://us.posthog.com',
      projectId: '',
      apiKey: '',
    },
  },
  signalsWatch: {
    dailyRefresh: true,
    weeklyRefresh: true,
    hotSignalAlerts: true,
    emailDigest: false,
    targetEmail: '',
  },
};

const STORAGE_KEY = 'pmlytics_user_settings_v1';

export function loadSettingsFromStorage(): UserSettings {
  if (typeof window === 'undefined') return DEFAULT_USER_SETTINGS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_USER_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<UserSettings>;
    return {
      aiProviders: { ...DEFAULT_USER_SETTINGS.aiProviders, ...parsed.aiProviders },
      modelRouting: { ...DEFAULT_USER_SETTINGS.modelRouting, ...parsed.modelRouting },
      integrations: {
        ...DEFAULT_USER_SETTINGS.integrations,
        ...parsed.integrations,
        jira: { ...DEFAULT_USER_SETTINGS.integrations.jira, ...parsed.integrations?.jira },
        zendesk: { ...DEFAULT_USER_SETTINGS.integrations.zendesk, ...parsed.integrations?.zendesk },
        posthog: { ...DEFAULT_USER_SETTINGS.integrations.posthog, ...parsed.integrations?.posthog },
      },
      signalsWatch: { ...DEFAULT_USER_SETTINGS.signalsWatch, ...parsed.signalsWatch },
    };
  } catch {
    return DEFAULT_USER_SETTINGS;
  }
}

export function saveSettingsToStorage(settings: UserSettings): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    window.dispatchEvent(new Event('pmlytics_settings_updated'));
  } catch (err) {
    console.error('Failed to save settings:', err);
  }
}

export function useSettingsStore() {
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_USER_SETTINGS);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setSettings(loadSettingsFromStorage());
    setIsLoaded(true);

    const handleUpdate = () => {
      setSettings(loadSettingsFromStorage());
    };

    window.addEventListener('pmlytics_settings_updated', handleUpdate);
    return () => window.removeEventListener('pmlytics_settings_updated', handleUpdate);
  }, []);

  const updateSettings = useCallback((newSettings: UserSettings) => {
    setSettings(newSettings);
    saveSettingsToStorage(newSettings);
  }, []);

  const patchSettings = useCallback((patch: Partial<UserSettings>) => {
    setSettings((current) => {
      const merged: UserSettings = {
        ...current,
        ...patch,
        aiProviders: { ...current.aiProviders, ...patch.aiProviders },
        modelRouting: { ...current.modelRouting, ...patch.modelRouting },
        integrations: {
          ...current.integrations,
          ...patch.integrations,
          jira: { ...current.integrations.jira, ...patch.integrations?.jira },
          zendesk: { ...current.integrations.zendesk, ...patch.integrations?.zendesk },
          posthog: { ...current.integrations.posthog, ...patch.integrations?.posthog },
        },
        signalsWatch: { ...current.signalsWatch, ...patch.signalsWatch },
      };
      saveSettingsToStorage(merged);
      return merged;
    });
  }, []);

  return {
    settings,
    isLoaded,
    updateSettings,
    patchSettings,
  };
}
