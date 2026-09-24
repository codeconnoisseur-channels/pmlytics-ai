import Link from 'next/link';
import type { ReactNode } from 'react';
import { BrandLogo } from '@/components/brand/BrandLogo';

interface AuthCardProps {
  title: string;
  description?: string;
  message?: string;
  children: ReactNode;
  footer: ReactNode;
}

export function AuthCard({ title, description, message, children, footer }: AuthCardProps) {
  return (
    <main className="marketing-grid relative flex min-h-screen items-center justify-center overflow-hidden bg-canvas px-4 py-12">
      <div className="pointer-events-none absolute left-1/2 top-[18%] h-72 w-72 -translate-x-1/2 rounded-full bg-[#c8f46b]/30 blur-[100px]" aria-hidden="true" />
      <section className="relative w-full max-w-md rounded-[28px] border border-white/80 bg-white/75 p-6 shadow-[0_30px_90px_rgba(25,31,17,0.12)] backdrop-blur-xl sm:p-8">
        <Link href="/" className="inline-flex items-center gap-2 rounded-full text-sm font-semibold text-txt-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2">
          <BrandLogo markClassName="h-10 w-10" />
        </Link>
        <div className="mt-8">
          <h1 className="text-balance text-3xl font-black tracking-[-0.04em] text-txt-primary">{title}</h1>
          {description ? (
            <p className="mt-2 text-sm leading-6 text-txt-secondary">{description}</p>
          ) : null}
        </div>
        {message ? (
          <p className="mt-5 rounded-xl border border-brand-border bg-brand-subtle px-3 py-2.5 text-sm text-txt-secondary" role="status">
            {message}
          </p>
        ) : null}
        <div className="mt-6">{children}</div>
        <div className="mt-6 border-t border-border pt-5 text-center text-sm text-txt-secondary">{footer}</div>
      </section>
    </main>
  );
}
