import Link from 'next/link';
import { Search } from 'lucide-react';

import { requireUser, can } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';
import { SectionLabel } from '@/components/site/section-label';
import { card, h1, input, primary } from '@/components/registry/ui';

export default async function SkillsPage({ searchParams }: { searchParams: Promise<{ q?: string; denied?: string }> }) {
  const user = await requireUser();
  const { q = '', denied } = await searchParams;
  const all = await store().listSkills();
  const visible = all.filter((s) => (can(user, 'publisher') ? true : s.latestApproved));
  const needle = q.trim().toLowerCase();
  const skills = needle ? visible.filter((s) => `${s.name} ${s.description}`.toLowerCase().includes(needle)) : visible;

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-3">
          <SectionLabel>Skill registry</SectionLabel>
          <h1 className={h1}>Packs and skills your agents can use</h1>
          <p className="max-w-[560px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
            A pack is a complete package: skills plus the subagents, hooks, config, templates and docs around them. Everything is versioned and approved before the extension can install it.
          </p>
        </div>
        {can(user, 'publisher') && (
          <Link href="/registry/new" className={primary}>
            Register a pack or skill
          </Link>
        )}
      </div>

      {denied && (
        <p className="mt-6 rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-[13px] text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">
          Your role doesn’t have access to that page.
        </p>
      )}

      <form className="relative mt-8 max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-neutral-400" />
        <input name="q" defaultValue={q} placeholder="Search packs and skills" aria-label="Search packs and skills" className={`${input} pl-9`} />
      </form>

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {skills.map((s) => (
          <Link key={s.slug} href={`/registry/skills/${s.slug}`} className={`${card} group flex flex-col p-5 transition-[border-color,box-shadow] hover:border-black/20 dark:hover:border-white/20`}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <h2 className="truncate font-mono text-[14px] font-medium text-neutral-900 dark:text-neutral-100">{s.name}</h2>
                <p className="mt-0.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-[#f9452d] dark:text-[#E1F435]">
                  {s.kind === 'pack' ? `Pack · ${s.skillCount} skills` : 'Skill'}
                </p>
              </div>
              <span className="shrink-0 font-mono text-[11px] text-neutral-500 dark:text-neutral-400">
                {s.latestApproved ? `v${s.latestApproved}` : 'not approved'}
              </span>
            </div>
            <p className="mt-2 line-clamp-3 flex-1 font-inter text-[13px] leading-[1.55] text-neutral-600 dark:text-neutral-400">{s.description}</p>
            <div className="mt-4 flex items-center gap-2 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">
              <span>{s.versions} {s.versions === 1 ? 'version' : 'versions'}</span>
              <span>· {s.fileCount} files</span>
              {s.pending > 0 && can(user, 'publisher') && (
                <span className="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400">{s.pending} pending</span>
              )}
            </div>
          </Link>
        ))}
        {skills.length === 0 && <p className="text-[14px] text-neutral-500">No skills match “{q}”.</p>}
      </div>
    </>
  );
}
