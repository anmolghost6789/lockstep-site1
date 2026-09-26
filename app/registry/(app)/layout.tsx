import Link from 'next/link';

import { requireUser, can } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';
import { logout } from '@/app/registry/actions';
import { LogoMark } from '@/components/site/logo';
import { ThemeToggle } from '@/components/theme-toggle';

export const dynamic = 'force-dynamic';

export default async function RegistryLayout({ children }: { children: React.ReactNode }) {
  const user = await requireUser();
  const pending = can(user, 'admin') ? (await store().listPending()).length : 0;
  const links = [
    { href: '/registry', label: 'Skills' },
    ...(can(user, 'publisher') ? [{ href: '/registry/new', label: 'Register' }] : []),
    ...(can(user, 'publisher') ? [{ href: '/registry/metrics', label: 'Metrics' }] : []),
    ...(can(user, 'admin') ? [{ href: '/registry/approvals', label: pending ? `Approvals ${pending}` : 'Approvals' }] : []),
    ...(can(user, 'admin') ? [{ href: '/registry/settings', label: 'Settings' }] : []),
  ];
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-black/[0.06] bg-background/80 backdrop-blur-sm dark:border-white/[0.07]">
        <div className="container-frame">
          <div className="container flex h-14 items-center gap-4">
            <Link href="/registry" className="mr-2 flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-neutral-900 p-1.5 dark:bg-white">
                <LogoMark className="h-full w-full text-white dark:text-neutral-900" />
              </span>
              <span className="font-mono text-sm font-medium uppercase tracking-[0.5px] text-foreground/80">Registry</span>
            </Link>
            <nav className="hidden items-center gap-5 font-mono text-[12.5px] uppercase tracking-wide md:flex" aria-label="Registry">
              {links.map((l) => (
                <Link key={l.href} href={l.href} className="text-foreground/70 transition-colors hover:text-foreground">
                  {l.label}
                </Link>
              ))}
            </nav>
            <div className="ml-auto flex items-center gap-3">
              <div className="hidden sm:block">
                <ThemeToggle />
              </div>
              <span className="hidden text-right lg:block">
                <span className="block text-[12.5px] leading-4 text-neutral-800 dark:text-neutral-200">{user.email}</span>
                <span className="block font-mono text-[10.5px] uppercase text-neutral-500">{user.role}</span>
              </span>
              <form action={logout}>
                <button className="h-8 rounded-full border border-black/8 bg-neutral-100/70 px-3.5 font-mono text-[11.5px] uppercase tracking-[0.5px] text-foreground/70 hover:text-foreground dark:border-white/10 dark:bg-neutral-900/70">
                  Sign out
                </button>
              </form>
            </div>
          </div>
          <nav className="container flex gap-4 overflow-x-auto pb-2 font-mono text-[12px] uppercase md:hidden" aria-label="Registry mobile">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className="whitespace-nowrap text-foreground/70">
                {l.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="container-frame">
        <div className="container py-10">{children}</div>
      </main>
    </div>
  );
}
