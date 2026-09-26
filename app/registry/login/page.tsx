import Link from 'next/link';
import { redirect } from 'next/navigation';

import { currentUser } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';
import { LoginForm } from '@/components/registry/client';
import { LogoMark } from '@/components/site/logo';
import { card } from '@/components/registry/ui';
import { SectionLabel } from '@/components/site/section-label';

export const dynamic = 'force-dynamic';

export default async function LoginPage() {
  if (await currentUser()) redirect('/registry');
  const noUsers = (await store().countUsers()) === 0;
  return (
    <main className="grid min-h-screen place-items-center px-4 py-16">
      <div className="w-full max-w-[380px]">
        <Link href="/" className="mb-8 flex items-center gap-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-neutral-900 p-1.5 dark:bg-white">
            <LogoMark className="h-full w-full text-white dark:text-neutral-900" />
          </span>
          <span className="font-mono text-sm font-medium uppercase tracking-[0.5px] text-foreground/80">Lockstep</span>
        </Link>
        <SectionLabel>Skill registry</SectionLabel>
        <h1 className="mb-6 mt-3 font-spectral text-[28px] leading-[1.15] tracking-[-1px] text-[#080808] dark:text-neutral-100">Sign in</h1>
        <div className={`${card} p-5`}>
          {noUsers ? (
            <p className="text-[13.5px] leading-[1.6] text-neutral-700 dark:text-neutral-300">
              No users yet. Set <code className="font-mono text-[12.5px]">ADMIN_EMAIL</code> and{' '}
              <code className="font-mono text-[12.5px]">ADMIN_PASSWORD</code> in your environment and reload to create the first administrator.
            </p>
          ) : (
            <LoginForm />
          )}
        </div>
      </div>
    </main>
  );
}
