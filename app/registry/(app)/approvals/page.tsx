import Link from 'next/link';

import { requireUser } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';
import { SectionLabel } from '@/components/site/section-label';
import { card, h1 } from '@/components/registry/ui';

export default async function ApprovalsPage() {
  const user = await requireUser('admin');
  const pending = await store().listPending();
  return (
    <>
      <div className="flex flex-col gap-3">
        <SectionLabel>Approvals</SectionLabel>
        <h1 className={h1}>Waiting for review</h1>
        <p className="max-w-[560px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
          Nothing reaches developers until an admin approves it. You can’t approve your own submissions.
        </p>
      </div>
      <div className={`${card} mt-8 divide-y divide-black/[0.06] dark:divide-white/[0.07]`}>
        {pending.length === 0 && <p className="p-5 text-[14px] text-neutral-500">Nothing is waiting. All submitted versions have been reviewed.</p>}
        {pending.map((v) => (
          <Link key={v.id} href={`/registry/skills/${v.slug}?v=${v.id}`} className="flex flex-wrap items-center gap-x-4 gap-y-1 p-4 transition-colors hover:bg-neutral-50 dark:hover:bg-white/[0.03]">
            <span className="font-mono text-[13.5px] font-medium text-neutral-900 dark:text-neutral-100">{v.slug}</span>
            <span className="font-mono text-[12px] text-neutral-500">v{v.version}</span>
            <span className="text-[13px] text-neutral-600 dark:text-neutral-400">{v.note || 'No change note'}</span>
            <span className="ml-auto text-[12px] text-neutral-500">
              {v.submittedBy}
              {v.submittedBy === user.email ? ' (you)' : ''}
            </span>
          </Link>
        ))}
      </div>
    </>
  );
}
