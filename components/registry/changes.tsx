'use client';

import * as React from 'react';
import { ChevronRight } from 'lucide-react';

import { cn } from '@/lib/utils';
import type { FileChange } from '@/lib/registry/diff';
import { card } from './ui';

/** What changed since the previous version, file by file, so approvers review the edit rather than the whole pack. */
export function ChangesPanel({ fromVersion, changes }: { fromVersion: string; changes: FileChange[] }) {
  const [open, setOpen] = React.useState<string | null>(changes[0]?.path ?? null);
  if (!changes.length) return null;
  const adds = changes.reduce((a, c) => a + c.adds, 0);
  const removes = changes.reduce((a, c) => a + c.removes, 0);
  return (
    <div className={cn(card, 'overflow-hidden')}>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-black/[0.06] px-4 py-3 dark:border-white/[0.07]">
        <p className="text-[14px] font-medium text-neutral-900 dark:text-neutral-100">Changes from v{fromVersion}</p>
        <p className="font-mono text-[12px] text-neutral-500">
          {changes.length} {changes.length === 1 ? 'file' : 'files'} · <span className="text-emerald-600 dark:text-emerald-400">+{adds}</span>{' '}
          <span className="text-red-600 dark:text-red-400">−{removes}</span>
        </p>
      </div>
      <ul className="divide-y divide-black/[0.06] dark:divide-white/[0.07]">
        {changes.map((c) => (
          <li key={c.path}>
            <button type="button" onClick={() => setOpen(open === c.path ? null : c.path)} className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-neutral-50 dark:hover:bg-white/[0.03]" aria-expanded={open === c.path}>
              <ChevronRight className={cn('size-3.5 shrink-0 text-neutral-400 transition-transform', open === c.path && 'rotate-90')} />
              <span className="min-w-0 flex-1 truncate font-mono text-[12.5px] text-neutral-800 dark:text-neutral-200">{c.path}</span>
              <span className={cn('rounded-full px-2 py-0.5 font-mono text-[10.5px] uppercase', c.kind === 'added' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' : c.kind === 'removed' ? 'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400' : 'bg-neutral-100 text-neutral-600 dark:bg-white/[0.07] dark:text-neutral-400')}>
                {c.kind}
              </span>
              {!c.binary && (
                <span className="w-20 text-right font-mono text-[11px]">
                  <span className="text-emerald-600 dark:text-emerald-400">+{c.adds}</span> <span className="text-red-600 dark:text-red-400">−{c.removes}</span>
                </span>
              )}
            </button>
            {open === c.path && (
              <div className="overflow-x-auto border-t border-black/[0.06] bg-neutral-50/50 py-2 font-mono text-[12px] leading-[1.65] dark:border-white/[0.07] dark:bg-white/[0.02]">
                {c.binary ? (
                  <p className="px-4 text-neutral-500">Binary file {c.kind}.</p>
                ) : !c.lines ? (
                  <p className="px-4 text-neutral-500">{c.kind === 'removed' ? 'File removed.' : 'Too large to show a line diff.'}</p>
                ) : (
                  c.lines.map((l, i) =>
                    l.type === 'gap' ? (
                      <div key={i} className="px-4 py-0.5 text-neutral-400">⋯ {l.count} unchanged {l.count === 1 ? 'line' : 'lines'}</div>
                    ) : (
                      <div key={i} className={cn('flex whitespace-pre px-4', l.type === 'add' && 'bg-emerald-50 text-emerald-900 dark:bg-emerald-500/10 dark:text-emerald-200', l.type === 'remove' && 'bg-red-50 text-red-900 dark:bg-red-500/10 dark:text-red-200', l.type === 'same' && 'text-neutral-600 dark:text-neutral-400')}>
                        <span aria-hidden className="w-5 shrink-0 select-none">{l.type === 'add' ? '+' : l.type === 'remove' ? '−' : ' '}</span>
                        {l.text || ' '}
                      </div>
                    ),
                  )
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
