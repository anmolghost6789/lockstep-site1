import Link from 'next/link';

import { ScrambleText } from '@/components/scramble-text';
import { LogoMark } from './logo';
import { PILOT_HREF, PILOT_LABEL } from '@/lib/site';
import { ThemeToggle } from '@/components/theme-toggle';

const NAV = [
  { label: 'How it works', href: '/#how' },
  { label: 'Governance', href: '/#governance' },
  { label: 'Packs', href: '/#packs' },
  { label: 'Pricing', href: '/#pricing' },
  { label: 'Pilot', href: '/#pilot' },
  { label: 'FAQ', href: '/#faq' },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 w-full bg-background/10 backdrop-blur-sm supports-backdrop-filter:bg-background/60">
      <div className="container-frame">
        <div className="container flex h-14 items-center gap-2 md:gap-4">
          <div className="mr-2 flex shrink-0 items-center md:mr-4">
            <Link href="/" className="flex items-center gap-2 md:mr-4 md:gap-2.5 lg:mr-8">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-neutral-900 p-1.5 dark:bg-neutral-100">
                <LogoMark className="h-full w-full text-white dark:text-neutral-900" />
              </div>
              <ScrambleText
                text="Lockstep"
                className="whitespace-nowrap font-mono text-sm font-medium uppercase tracking-[0.5px] text-foreground/80 sm:text-base"
              />
            </Link>
            <nav className="hidden items-center gap-6 font-mono text-[13px] uppercase tracking-wide md:flex xl:gap-8">
              {NAV.map((link) => (
                <Link key={link.href} href={link.href} className="whitespace-nowrap text-foreground/80 transition-colors hover:text-foreground">
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>

          <nav className="ml-auto flex items-center gap-1.5 sm:gap-2">
            <div className="hidden sm:block">
              <ThemeToggle />
            </div>
            <a
              href={PILOT_HREF}
              className="inline-flex h-8 items-center rounded-full bg-neutral-900 px-3 text-xs font-medium text-white shadow-xs transition-colors hover:bg-neutral-800 sm:px-5 sm:text-sm dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
            >
              {PILOT_LABEL}
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
