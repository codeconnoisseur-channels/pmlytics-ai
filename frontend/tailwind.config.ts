import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#f4f5f2',
        surface: {
          DEFAULT: '#fbfcf9',
          subtle: '#eef0eb',
          hover: '#e3e6de',
        },
        border: {
          light: '#eceee9',
          DEFAULT: '#dfe2db',
          strong: '#c9cdc4',
          focus: '#171915',
        },
        txt: {
          primary: '#171915',
          secondary: '#62675f',
          muted: '#73786f',
          disabled: '#a0a59c',
        },
        brand: {
          primary: '#171915',
          hover: '#000000',
          subtle: '#eff8df',
          border: '#c8f46b',
        },
        // Source Provenance
        src: {
          zendesk: {
            text: '#047857',
            bg: '#ecfdf5',
            border: '#a7f3d0',
          },
          posthog: {
            text: '#6d28d9',
            bg: '#f5f3ff',
            border: '#ddd6fe',
          },
          jira: {
            text: '#1d4ed8',
            bg: '#eff6ff',
            border: '#bfdbfe',
          },
        },
        // Epistemic Classifications
        epistemic: {
          facts: {
            border: '#10b981',
            bg: '#f0fdf4',
            badgeText: '#065f46',
            badgeBg: '#d1fae5',
          },
          inferences: {
            border: '#3b82f6',
            bg: '#eff6ff',
            badgeText: '#1e40af',
            badgeBg: '#dbeafe',
          },
          hypotheses: {
            border: '#f59e0b',
            bg: '#fffbeb',
            badgeText: '#92400e',
            badgeBg: '#fef3c7',
          },
        },
        // Status Colors
        status: {
          pass: {
            text: '#166534',
            bg: '#dcfce7',
            border: '#bbf7d0',
          },
          warn: {
            text: '#9a3412',
            bg: '#ffedd5',
            border: '#fed7aa',
          },
          danger: {
            text: '#991b1b',
            bg: '#fee2e2',
            border: '#fecaca',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      maxWidth: {
        reading: '840px',
      },
      screens: {
        widescreen: '1600px',
      },
      spacing: {
        'topbar': '68px',
        'sidebar-expanded': '240px',
        'sidebar-collapsed': '64px',
        'drawer-desktop': '420px',
      },
    },
  },
  plugins: [],
};

export default config;
