import Link from 'next/link';

import { requireUser } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';
import { EditorWorkspace } from '@/components/registry/editor';
import { SectionLabel } from '@/components/site/section-label';
import { h1 } from '@/components/registry/ui';
import { cn } from '@/lib/utils';

export const dynamic = 'force-dynamic';

function Missing({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="mx-auto max-w-[560px] py-16 text-center">
      <h1 className="text-[20px] font-semibold text-neutral-900 dark:text-neutral-50">{title}</h1>
      <p className="mt-2 text-[14.5px] text-neutral-600 dark:text-neutral-400">{detail}</p>
      <Link href="/registry" className="mt-6 inline-flex h-10 items-center rounded-full bg-neutral-900 px-5 text-[14px] text-white dark:bg-white dark:text-neutral-900">
        Back to packs and skills
      </Link>
    </div>
  );
}

export default async function EditPage({ params, searchParams }: { params: Promise<{ slug: string }>; searchParams: Promise<{ v?: string }> }) {
  await requireUser('publisher');
  const { slug } = await params;
  const { v } = await searchParams;
  const skill = await store().getSkill(decodeURIComponent(slug));
  if (!skill) return <Missing title="Pack not found" detail={`There is no pack or skill called “${decodeURIComponent(slug)}” in this registry. It may have been imported under a different name.`} />;
  const versions = await store().listVersions(skill.slug);
  const base = versions.find((x) => x.id === v) ?? versions.find((x) => x.status === 'approved') ?? versions[0];
  if (!base) return <Missing title="No version to edit" detail={`“${skill.slug}” has no versions yet. Upload one from Register first.`} />;
  const pending = versions.find((x) => x.status === 'pending');

  return (
    <>
      <Link href={`/registry/skills/${slug}?v=${base.id}`} className="font-mono text-[12px] uppercase tracking-wide text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100">
        ← Back to {slug}
      </Link>
      <div className="mb-6 mt-5 flex flex-col gap-3">
        <SectionLabel>Edit</SectionLabel>
        <h1 className={cn(h1, 'font-mono text-[24px] tracking-[-0.5px]')}>{slug}</h1>
        <p className="max-w-[720px] font-inter text-[14px] leading-[1.6] text-[#646464] dark:text-neutral-400">
          Editing from v{base.version}. Type <kbd className="rounded border border-black/10 px-1 font-mono text-[12px] dark:border-white/15">/</kbd> in the rich editor for
          headings, lists, to-dos, tables and code blocks, or select text to format it. Nothing changes for developers until an admin approves the new version.
        </p>
        {pending && (
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-[13px] text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">
            v{pending.version} is already waiting for approval. You can edit, but saving is blocked until it’s approved or rejected.
          </p>
        )}
      </div>
      <EditorWorkspace
        slug={slug}
        baseVersionId={base.id}
        baseVersion={base.version}
        files={base.files.map((f) => ({ path: f.path, content: f.encoding === 'base64' ? '' : f.content, binary: f.encoding === 'base64' }))}
      />
    </>
  );
}
