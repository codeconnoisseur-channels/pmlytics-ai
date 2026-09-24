/** @type {import('next').NextConfig} */
import path from 'node:path';
import nextEnv from '@next/env';

const { loadEnvConfig } = nextEnv;

// The monorepo keeps shared service configuration in its repository root.
// Only NEXT_PUBLIC_* values are eligible for browser bundling by Next.js.
loadEnvConfig(path.resolve(process.cwd(), '..'));

const nextConfig = {
  reactStrictMode: true,
  // The shared root env is loaded above; explicitly expose only the two public
  // Supabase values so middleware and browser bundles receive the same config.
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/:path*',
      },
      {
        source: '/docs',
        destination: 'http://127.0.0.1:8000/docs',
      },
      {
        source: '/openapi.json',
        destination: 'http://127.0.0.1:8000/openapi.json',
      },
    ];
  },
};

export default nextConfig;
