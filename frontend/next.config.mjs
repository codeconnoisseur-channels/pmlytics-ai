/** @type {import('next').NextConfig} */
import path from 'node:path';
import nextEnv from '@next/env';

const { loadEnvConfig } = nextEnv;

// The monorepo keeps shared service configuration in its repository root.
// Only NEXT_PUBLIC_* values are eligible for browser bundling by Next.js.
try {
  loadEnvConfig(path.resolve(process.cwd(), '..'));
} catch {
  // Gracefully fallback when deployed independently (e.g., on Vercel)
}

const rawBackendUrl =
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://127.0.0.1:8000';
const backendUrl = rawBackendUrl.replace(/\/$/, '').replace(/\/api\/v1$/, '');

const nextConfig = {
  reactStrictMode: true,
  // The shared root env is loaded above; explicitly expose public variables so
  // middleware and browser bundles receive the same configuration.
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
      {
        source: '/docs',
        destination: `${backendUrl}/docs`,
      },
      {
        source: '/openapi.json',
        destination: `${backendUrl}/openapi.json`,
      },
    ];
  },
};

export default nextConfig;
