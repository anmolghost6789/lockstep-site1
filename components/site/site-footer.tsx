import Link from 'next/link';

import { LogoMark } from './logo';
import { ThemeToggle } from '@/components/theme-toggle';
import { PILOT_HREF } from '@/lib/site';

const LINKS = [
  { label: 'How it works', href: '/#how' },
  { label: 'Pricing', href: '/pricing' },
  { label: 'Packs', href: '/packs' },
  { label: 'Registry sign-in', href: '/registry' },
  { label: 'Contact', href: PILOT_HREF },
];

export function SiteFooter() {
  return (
    <footer className="w-full border-t border-black/[0.06] dark:border-white/[0.07]">
      <div className="container-frame">
        <div className="container flex flex-col gap-6 py-10 md:flex-row md:items-center md:justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-neutral-900 p-1.5 dark:bg-white">
              <LogoMark className="h-full w-full text-white dark:text-neutral-900" />
            </span>
            <span className="font-mono text-sm font-medium uppercase tracking-[0.5px] text-foreground/80">Lockstep</span>
          </Link>
          <nav aria-label="Footer" className="flex flex-wrap items-center gap-x-6 gap-y-2">
            {LINKS.map((l) => (
              <Link key={l.label} href={l.href} className="font-inter text-sm font-medium text-neutral-600 transition-colors hover:text-[#f9452d] dark:text-neutral-400 dark:hover:text-[#E1F435]">
                {l.label}
              </Link>
            ))}
          </nav>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <p className="font-mono text-xs font-medium uppercase tracking-[0.28px] text-neutral-500">© 2026 Lockstep</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
