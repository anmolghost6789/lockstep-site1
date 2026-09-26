'use client';

import * as React from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { zipSync, strToU8 } from 'fflate';
import {
  ArrowLeft,
  Check,
  ChevronDown,
  ChevronRight,
  Code2,
  Copy,
  Database,
  Download,
  Eye,
  FileText,
  Folder,
  FolderOpen,
  Globe,
  Info,
  Layers,
  Package,
  Play,
  ScrollText,
  Terminal,
  X,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { CodeFile, MarkdownFile } from '@/components/site/skill-viewer';
import type { FileChange } from '@/lib/registry/diff';
import { isImage, mimeFor } from '@/lib/registry/groups';
import { ChangesPanel } from './changes';
import { ReviewForm } from './client';
import { statusPill } from './ui';

type File = { path: string; content: string; encoding?: 'utf8' | 'base64' };
type Connector = { name: string; transport: 'remote' | 'local'; endpoint: string; host: string | null; allowListed: boolean | null };

export interface PackDetailProps {
  slug: string;
  name: string;
  description: string;
  publisher: string;
  icon: string;
  kind: 'pack' | 'skill';
  updatedAgo: string;
  version: { id: string; version: string; status: 'pending' | 'approved' | 'rejected'; note: string; submittedBy: string; submittedAt: string; reviewedBy: string | null; reviewNote: string | null; sha256: string };
  versions: { id: string; version: string; status: string; date: string; latestApproved: boolean }[];
  files: File[];
  skills: { name: string; description: string; path: string }[];
  connectors: Connector[];
  sendsData: boolean;
  categories: string[];
  examples: string[];
  stats: { projects: number; runs: number };
  apiUrl: string;
  registryUrl: string;
  canEdit: boolean;
  canReview: boolean;
  ownSubmission: boolean;
  changes: FileChange[] | null;
  fromVersion: string | null;
  banner: { kind: 'ok' | 'warn' | 'error'; text: string } | null;
}

const ICONS: Record<string, React.ElementType> = { layers: Layers, database: Database, package: Package, 'file-text': FileText };
type Tab = 'overview' | 'contents' | 'skills' | 'connectors' | 'changes';

const b64ToBytes = (b64: string) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
const initials = (s: string) => s.replace(/[^a-zA-Z0-9]+/g, ' ').trim().split(' ').map((w) => w[0]).join('').slice(0, 2).toUpperCase();

/* -------------------------------------------------------------------------- */
/* Page                                                                        */
/* -------------------------------------------------------------------------- */

export function PackDetail(p: PackDetailProps) {
  const router = useRouter();
  const params = useSearchParams();
  const initialTab = (params.get('tab') as Tab) ?? (p.version.status === 'pending' && p.changes?.length ? 'changes' : 'overview');
  const [tab, setTab] = React.useState<Tab>(initialTab);
  const [file, setFile] = React.useState<string | null>(params.get('file'));
  const [installOpen, setInstallOpen] = React.useState(false);
  const Icon = ICONS[p.icon] ?? Package;

  const go = (t: Tab, f?: string) => {
    setTab(t);
    if (f) setFile(f);
    const q = new URLSearchParams(params.toString());
    q.set('tab', t);
    if (f) q.set('file', f);
    else if (t !== 'contents') q.delete('file');
    router.replace(`?${q.toString()}`, { scroll: false });
  };

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'contents', label: 'Contents', count: p.files.length },
    { id: 'skills', label: 'Skills', count: p.skills.length },
    { id: 'connectors', label: 'Connectors', count: p.connectors.length },
    ...(p.changes && p.changes.length ? [{ id: 'changes' as Tab, label: 'Changes', count: p.changes.length }] : []),
  ];

  return (
    <div className="mx-auto max-w-[1180px]">
      <Link href="/registry" className="inline-flex items-center gap-1.5 text-[14px] text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100">
        <ArrowLeft className="size-4" /> Packs and skills
      </Link>

      {/* Header */}
      <div className="mt-6 flex items-start gap-4">
        <span className="grid size-14 shrink-0 place-items-center rounded-2xl border border-black/[0.08] bg-neutral-50 text-neutral-800 dark:border-white/[0.09] dark:bg-[#0B0B0D] dark:text-neutral-200">
          <Icon className="size-6" strokeWidth={1.6} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-[22px] font-semibold tracking-[-0.3px] text-neutral-900 dark:text-neutral-50">{p.name}</h1>
            {p.version.status !== 'approved' && (
              <span className={cn('rounded-full px-2.5 py-0.5 font-mono text-[11px]', statusPill[p.version.status])}>{p.version.status}</span>
            )}
          </div>
          <p className="mt-0.5 text-[14.5px] text-neutral-500 dark:text-neutral-400">
            by {p.publisher} · {p.version.version} · {p.skills.length} {p.skills.length === 1 ? 'skill' : 'skills'} · updated {p.updatedAgo}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {p.canEdit && (
            <Link href={`/registry/skills/${p.slug}/edit?v=${p.version.id}`} className="inline-flex h-10 items-center rounded-xl px-4 text-[14.5px] text-neutral-800 shadow-[0_0_0_1px_rgba(0,0,0,0.1)] hover:bg-neutral-50 dark:text-neutral-200 dark:shadow-[0_0_0_1px_rgba(255,255,255,0.14)] dark:hover:bg-white/[0.05]">
              Edit
            </Link>
          )}
          <button
            type="button"
            onClick={() => setInstallOpen(true)}
            disabled={p.version.status !== 'approved'}
            title={p.version.status !== 'approved' ? 'Only approved versions can be installed' : undefined}
            className="inline-flex h-10 items-center rounded-xl bg-neutral-900 px-5 text-[14.5px] font-medium text-white hover:bg-neutral-800 disabled:opacity-40 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
          >
            Add
          </button>
        </div>
      </div>

      {p.banner && (
        <div
          role="status"
          className={cn(
            'mt-5 rounded-xl border px-4 py-3 text-[13.5px]',
            p.banner.kind === 'ok' && 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300',
            p.banner.kind === 'warn' && 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300',
            p.banner.kind === 'error' && 'border-red-200 bg-red-50 text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300',
          )}
        >
          {p.banner.text}
        </div>
      )}

      {/* Tabs */}
      <div role="tablist" aria-label="Pack sections" className="mt-6 flex gap-1 overflow-x-auto border-b border-black/[0.08] dark:border-white/[0.09]">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            type="button"
            onClick={() => go(t.id)}
            className={cn(
              '-mb-px whitespace-nowrap border-b-2 px-4 py-3 text-[15px] transition-colors',
              tab === t.id ? 'border-neutral-900 font-medium text-neutral-900 dark:border-white dark:text-neutral-50' : 'border-transparent text-neutral-500 hover:text-neutral-800 dark:text-neutral-400 dark:hover:text-neutral-200',
            )}
          >
            {t.label}
            {t.count !== undefined && <span className="text-neutral-400 dark:text-neutral-500"> · {t.count}</span>}
          </button>
        ))}
      </div>

      <div className="py-8">
        {tab === 'overview' && <Overview {...p} onSkill={(path) => go('contents', path)} />}
        {tab === 'contents' && <Contents {...p} file={file} onFile={(f) => go('contents', f)} />}
        {tab === 'skills' && <Skills skills={p.skills} onOpen={(path) => go('contents', path)} kind={p.kind} />}
        {tab === 'connectors' && <Connectors connectors={p.connectors} />}
        {tab === 'changes' && p.changes && (
          <div className="space-y-4">
            {p.version.status === 'pending' && p.canReview && <ReviewForm id={p.version.id} ownSubmission={p.ownSubmission} />}
            <ChangesPanel fromVersion={p.fromVersion ?? ''} changes={p.changes} />
          </div>
        )}
      </div>

      {installOpen && <InstallDialog {...p} onClose={() => setInstallOpen(false)} />}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Overview                                                                    */
/* -------------------------------------------------------------------------- */

function Overview(p: PackDetailProps & { onSkill: (path: string) => void }) {
  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="min-w-0">
        <div className="grid grid-cols-2 divide-x divide-black/[0.08] dark:divide-white/[0.09]">
          {[
            ['Adoption', p.stats.projects, 'projects reporting · 30 days'],
            ['Activity', p.stats.runs, 'runs reported · 30 days'],
          ].map(([label, value, sub]) => (
            <div key={label as string} className="px-4 text-center">
              <p className="text-[15px] text-neutral-700 dark:text-neutral-300">{label}</p>
              <p className="mt-3 font-spectral text-[34px] leading-none text-neutral-900 dark:text-neutral-50">{value || '—'}</p>
              <p className="mt-3 text-[13.5px] text-neutral-500">{sub}</p>
            </div>
          ))}
        </div>

        <Section title="Description">
          <p className="text-[17px] leading-[1.6] text-neutral-800 dark:text-neutral-200">{p.description}</p>
        </Section>

        {p.version.note && (
          <Section title={`What’s new in ${p.version.version}`}>
            <p className="text-[14.5px] leading-[1.6] text-neutral-600 dark:text-neutral-400">{p.version.note}</p>
          </Section>
        )}

        {p.categories.length > 0 && (
          <Section title="Categories">
            <div className="flex flex-wrap gap-2">
              {p.categories.map((c) => (
                <span key={c} className="rounded-lg bg-neutral-100 px-3 py-1.5 text-[14px] font-medium text-neutral-700 dark:bg-white/[0.07] dark:text-neutral-300">
                  {c}
                </span>
              ))}
            </div>
          </Section>
        )}

        {p.examples.length > 0 && (
          <Section title="Try it">
            <div className="flex flex-col items-start gap-2">
              {p.examples.map((e) => (
                <CopyChip key={e} text={e} />
              ))}
            </div>
          </Section>
        )}

        {p.skills.length > 0 && (
          <Section title="Skills">
            <div className="flex flex-wrap gap-2">
              {p.skills.map((s) => (
                <button key={s.path} type="button" onClick={() => p.onSkill(s.path)} className="rounded-lg border border-black/[0.08] px-3 py-1.5 font-mono text-[13px] text-neutral-700 hover:bg-neutral-50 dark:border-white/[0.09] dark:text-neutral-300 dark:hover:bg-white/[0.04]">
                  /{s.name}
                </button>
              ))}
            </div>
          </Section>
        )}
      </div>

      <aside className="h-fit space-y-4">
        <div className="rounded-2xl border border-black/[0.08] bg-neutral-50/70 p-5 dark:border-white/[0.09] dark:bg-[#0B0B0D]">
          <p className="mb-4 text-[15px] text-neutral-700 dark:text-neutral-300">Connectors & tools</p>
          {p.sendsData && (
            <div className="mb-4 flex items-start gap-3">
              <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-neutral-200/70 dark:bg-white/[0.08]">
                <Globe className="size-4 text-neutral-600 dark:text-neutral-300" />
              </span>
              <p className="flex-1 text-[14.5px] leading-snug text-neutral-800 dark:text-neutral-200">Can send data to other services</p>
              <span title="This pack declares remote MCP servers. Check them against your organisation’s allow-list before adding it.">
                <Info className="size-4 text-neutral-400" />
              </span>
            </div>
          )}
          <ul className="space-y-3.5">
            {p.connectors.map((c) => (
              <li key={c.name} className="flex items-center gap-3">
                <ConnectorBadge name={c.name} />
                <span className="min-w-0 truncate text-[14.5px] text-neutral-800 dark:text-neutral-200">
                  {c.name}
                  <span className="text-neutral-500"> · {c.host ?? 'local'}</span>
                </span>
              </li>
            ))}
            {p.connectors.length === 0 && <li className="text-[14px] text-neutral-500">No connectors. This pack works entirely in your repository.</li>}
          </ul>
        </div>
        <div className="rounded-2xl border border-black/[0.08] p-5 text-[13px] dark:border-white/[0.09]">
          <p className="mb-3 text-[15px] text-neutral-700 dark:text-neutral-300">This version</p>
          <dl className="space-y-2.5">
            <Row k="Submitted by" v={p.version.submittedBy === 'system' ? 'Shipped with Lockstep' : p.version.submittedBy} />
            {p.version.reviewedBy && <Row k={p.version.status === 'rejected' ? 'Rejected by' : 'Approved by'} v={p.version.reviewedBy === 'system' ? 'Built in' : p.version.reviewedBy} />}
            <Row k="Files" v={String(p.files.length)} />
            <Row k="SHA-256" v={`${p.version.sha256.slice(0, 16)}…`} mono />
          </dl>
        </div>
      </aside>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-9">
      <h2 className="mb-3 text-[15px] text-neutral-500 dark:text-neutral-400">{title}</h2>
      {children}
    </section>
  );
}

function Row({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-neutral-500">{k}</dt>
      <dd className={cn('truncate text-right text-neutral-800 dark:text-neutral-200', mono && 'font-mono text-[12px]')}>{v}</dd>
    </div>
  );
}

function CopyChip({ text }: { text: string }) {
  const [done, setDone] = React.useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setDone(true);
        setTimeout(() => setDone(false), 1400);
      }}
      title="Copy this prompt"
      className="inline-flex items-center gap-2.5 rounded-xl bg-neutral-100 px-4 py-2.5 text-left text-[15px] text-neutral-700 transition-colors hover:bg-neutral-200/70 dark:bg-white/[0.06] dark:text-neutral-300 dark:hover:bg-white/[0.09]"
    >
      {done ? <Check className="size-4 text-emerald-600" /> : <Play className="size-3.5 text-neutral-500" />}“{text}”
    </button>
  );
}

function ConnectorBadge({ name }: { name: string }) {
  return (
    <span className="grid size-8 shrink-0 place-items-center rounded-lg border border-black/[0.08] bg-white font-mono text-[11px] font-semibold text-neutral-700 dark:border-white/[0.1] dark:bg-neutral-900 dark:text-neutral-300">
      {initials(name)}
    </span>
  );
}

/* -------------------------------------------------------------------------- */
/* Contents                                                                    */
/* -------------------------------------------------------------------------- */

type TreeNode = { name: string; path: string; children: Map<string, TreeNode>; file?: File };

function buildTree(files: File[]): TreeNode {
  const root: TreeNode = { name: '', path: '', children: new Map() };
  for (const f of files) {
    const parts = f.path.split('/');
    let node = root;
    parts.forEach((part, i) => {
      const path = parts.slice(0, i + 1).join('/');
      if (!node.children.has(part)) node.children.set(part, { name: part, path, children: new Map() });
      node = node.children.get(part)!;
      if (i === parts.length - 1) node.file = f;
    });
  }
  return root;
}

function sortedChildren(n: TreeNode) {
  return [...n.children.values()].sort((a, b) => {
    const af = a.file ? 1 : 0, bf = b.file ? 1 : 0;
    return af - bf || a.name.localeCompare(b.name);
  });
}

function Contents(p: PackDetailProps & { file: string | null; onFile: (f: string) => void }) {
  const router = useRouter();
  const tree = React.useMemo(() => buildTree(p.files), [p.files]);
  const defaultFile = p.files.find((f) => f.path === 'README.md')?.path ?? p.files.find((f) => f.path === 'SKILL.md')?.path ?? p.files[0]?.path;
  const current = p.files.find((f) => f.path === p.file) ?? p.files.find((f) => f.path === defaultFile)!;
  const [open, setOpen] = React.useState<Set<string>>(() => {
    const s = new Set<string>();
    for (const c of tree.children.values()) if (!c.file) s.add(c.path);
    const parts = current.path.split('/');
    for (let i = 1; i < parts.length; i++) s.add(parts.slice(0, i).join('/'));
    return s;
  });
  const [view, setView] = React.useState<'preview' | 'code'>('preview');
  const toggle = (path: string) => setOpen((s) => { const n = new Set(s); if (n.has(path)) n.delete(path); else n.add(path); return n; });

  function download() {
    const entries: Record<string, Uint8Array> = {};
    for (const f of p.files) entries[`${p.slug}/${f.path}`] = f.encoding === 'base64' ? b64ToBytes(f.content) : strToU8(f.content);
    const blob = new Blob([zipSync(entries, { level: 6 })], { type: 'application/zip' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${p.slug}-${p.version.version}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const renderNode = (n: TreeNode, depth: number): React.ReactNode =>
    sortedChildren(n).map((c) => {
      const pad = { paddingLeft: 12 + depth * 20 };
      if (c.file) {
        return (
          <button
            key={c.path}
            type="button"
            onClick={() => p.onFile(c.path)}
            style={pad}
            className={cn('block w-full truncate rounded-lg py-2 pr-3 text-left text-[14.5px]', c.path === current.path ? 'bg-neutral-100 font-medium text-neutral-900 dark:bg-white/[0.08] dark:text-neutral-50' : 'text-neutral-700 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-white/[0.04]')}
          >
            {c.name}
          </button>
        );
      }
      const isOpen = open.has(c.path);
      return (
        <div key={c.path}>
          <button type="button" onClick={() => toggle(c.path)} style={pad} className="flex w-full items-center gap-2 rounded-lg py-2 pr-3 text-left text-[14.5px] text-neutral-700 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-white/[0.04]" aria-expanded={isOpen}>
            {isOpen ? <FolderOpen className="size-4 shrink-0 text-neutral-500" /> : <Folder className="size-4 shrink-0 text-neutral-500" />}
            <span className="flex-1 truncate">{c.name}</span>
            {isOpen ? <ChevronDown className="size-4 text-neutral-400" /> : <ChevronRight className="size-4 text-neutral-400" />}
          </button>
          {isOpen && renderNode(c, depth + 1)}
        </div>
      );
    });

  const md = current.path.toLowerCase().endsWith('.md') && current.encoding !== 'base64';
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <label className="relative">
          <span className="sr-only">Version</span>
          <select
            value={p.version.id}
            onChange={(e) => router.push(`?v=${e.target.value}&tab=contents`)}
            className="h-11 appearance-none rounded-xl border border-black/[0.1] bg-transparent pl-4 pr-10 text-[15px] text-neutral-800 dark:border-white/[0.12] dark:text-neutral-200"
          >
            {p.versions.map((v) => (
              <option key={v.id} value={v.id} className="bg-white text-neutral-900 dark:bg-neutral-900 dark:text-neutral-100">
                {p.name} {v.version} · {v.date} · {v.latestApproved ? 'current' : v.status}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-neutral-500" />
        </label>
        <button type="button" onClick={download} aria-label={`Download ${p.slug} ${p.version.version} as a zip`} title="Download as .zip" className="grid size-10 place-items-center rounded-xl text-neutral-600 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-white/[0.06]">
          <Download className="size-5" />
        </button>
      </div>

      <div className="grid min-h-[620px] overflow-hidden rounded-2xl border border-black/[0.08] dark:border-white/[0.09] lg:grid-cols-[340px_minmax(0,1fr)]">
        <nav aria-label="Files" className="max-h-[300px] overflow-y-auto border-b border-black/[0.08] p-3 dark:border-white/[0.09] lg:max-h-[820px] lg:border-b-0 lg:border-r">
          {renderNode(tree, 0)}
        </nav>
        <div className="flex min-w-0 flex-col">
          <div className="flex items-center gap-3 border-b border-black/[0.06] px-5 py-3 dark:border-white/[0.07]">
            <span className="min-w-0 flex-1 truncate font-mono text-[14px] text-neutral-600 dark:text-neutral-400">/{current.path}</span>
            {md && (
              <div className="flex rounded-lg bg-neutral-100 p-0.5 dark:bg-white/[0.06]" role="tablist" aria-label="View">
                {(['preview', 'code'] as const).map((m) => (
                  <button key={m} role="tab" aria-selected={view === m} aria-label={m === 'preview' ? 'Preview' : 'Source'} type="button" onClick={() => setView(m)} className={cn('grid size-8 place-items-center rounded-md', view === m ? 'bg-white text-neutral-900 shadow-xs dark:bg-neutral-800 dark:text-neutral-100' : 'text-neutral-500')}>
                    {m === 'preview' ? <Eye className="size-4" /> : <Code2 className="size-4" />}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
            {current.encoding === 'base64' ? (
              isImage(current.path) ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={`data:${mimeFor(current.path)};base64,${current.content}`} alt={current.path} className="max-h-[520px] max-w-full rounded-lg border border-black/[0.08] dark:border-white/[0.09]" />
              ) : (
                <p className="text-[14px] text-neutral-500">Binary file. Download the pack to open it.</p>
              )
            ) : md && view === 'preview' ? (
              <MarkdownFile source={current.content} />
            ) : (
              <CodeFile source={current.content} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Skills and connectors                                                       */
/* -------------------------------------------------------------------------- */

function Skills({ skills, onOpen, kind }: { skills: PackDetailProps['skills']; onOpen: (path: string) => void; kind: 'pack' | 'skill' }) {
  return (
    <div>
      <p className="mb-5 text-[15.5px] text-neutral-600 dark:text-neutral-400">
        Invoke with <span className="font-mono">@lockstep</span> in Copilot Chat or by typing <span className="font-mono">/</span> in Claude Code, or let the agent use them automatically for relevant tasks.
        {kind === 'pack' && ' Select a skill to read its instructions.'}
      </p>
      <ul className="divide-y divide-black/[0.08] dark:divide-white/[0.09]">
        {skills.map((s) => (
          <li key={s.path}>
            <button type="button" onClick={() => onOpen(s.path)} className="flex w-full items-center gap-4 py-4 text-left hover:bg-neutral-50/60 dark:hover:bg-white/[0.02]">
              <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-neutral-100 text-neutral-700 dark:bg-white/[0.06] dark:text-neutral-300">
                <ScrollText className="size-5" strokeWidth={1.6} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[16px] font-medium text-neutral-900 dark:text-neutral-50">/{s.name}</span>
                <span className="mt-0.5 block truncate text-[15px] text-neutral-500 dark:text-neutral-400">{s.description}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Connectors({ connectors }: { connectors: Connector[] }) {
  return (
    <div>
      <p className="mb-5 text-[15.5px] text-neutral-600 dark:text-neutral-400">Tools and data sources this pack connects to, from its <span className="font-mono">.mcp.json</span>.</p>
      {connectors.length === 0 ? (
        <p className="text-[15px] text-neutral-500">No connectors. This pack works entirely in your repository.</p>
      ) : (
        <ul className="divide-y divide-black/[0.08] dark:divide-white/[0.09]">
          {connectors.map((c) => (
            <li key={c.name} className="flex items-center gap-4 py-4">
              <span className="grid size-12 shrink-0 place-items-center rounded-xl border border-black/[0.08] bg-white font-mono text-[13px] font-semibold text-neutral-700 dark:border-white/[0.1] dark:bg-neutral-900 dark:text-neutral-300">
                {c.transport === 'local' ? <Terminal className="size-5" /> : initials(c.name)}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[16px] font-medium text-neutral-900 dark:text-neutral-50">{c.name}</span>
                <span className="mt-0.5 flex flex-wrap items-center gap-x-2 text-[14.5px] text-neutral-500 dark:text-neutral-400">
                  {c.transport === 'remote' ? `Remote · ${c.host ?? c.endpoint}` : `Local command · ${c.endpoint}`}
                  {c.allowListed !== null && (
                    <>
                      <span aria-hidden>·</span>
                      <span className={c.allowListed ? 'text-emerald-700 dark:text-emerald-400' : 'text-amber-700 dark:text-amber-400'}>
                        {c.allowListed ? 'On the pack’s allow-list' : 'Not on the pack’s allow-list'}
                      </span>
                    </>
                  )}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Install                                                                     */
/* -------------------------------------------------------------------------- */

function InstallDialog(p: PackDetailProps & { onClose: () => void }) {
  const cmd = `python3 .claude/skills/adlc/scripts/pack.py install \\\n  --registry ${p.registryUrl} \\\n  --token <your API token> \\\n  --pack ${p.slug} --version ${p.version.version}`;
  const [copied, setCopied] = React.useState<string | null>(null);
  const copy = async (k: string, t: string) => {
    await navigator.clipboard.writeText(t);
    setCopied(k);
    setTimeout(() => setCopied(null), 1400);
  };
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && p.onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [p]);
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="install-title" className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4 backdrop-blur-[2px]" onClick={p.onClose}>
      <div className="w-full max-w-[620px] rounded-2xl border border-black/[0.08] bg-white p-6 shadow-2xl dark:border-white/[0.1] dark:bg-neutral-950" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="install-title" className="text-[18px] font-semibold text-neutral-900 dark:text-neutral-50">Add {p.name} {p.version.version}</h2>
            <p className="mt-1 text-[14px] text-neutral-500">Installs into the current repository. Your local edits are never overwritten on upgrade.</p>
          </div>
          <button type="button" onClick={p.onClose} aria-label="Close" className="grid size-8 place-items-center rounded-full text-neutral-500 hover:bg-neutral-100 dark:hover:bg-white/[0.06]">
            <X className="size-4" />
          </button>
        </div>
        {[
          ['With the pack manager', cmd],
          ['With the API', `curl -H "Authorization: Bearer <your API token>" \\\n  "${p.apiUrl}"`],
        ].map(([label, text]) => (
          <div key={label} className="mt-5">
            <div className="mb-2 flex items-center justify-between">
              <p className="text-[13.5px] font-medium text-neutral-700 dark:text-neutral-300">{label}</p>
              <button type="button" onClick={() => copy(label, text.replace(/ \\\n\s+/g, ' '))} className="inline-flex items-center gap-1.5 text-[12.5px] text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100">
                {copied === label ? <Check className="size-3.5 text-emerald-600" /> : <Copy className="size-3.5" />}
                {copied === label ? 'Copied' : 'Copy'}
              </button>
            </div>
            <pre className="overflow-x-auto rounded-xl bg-[#0b0b0d] p-4 font-mono text-[12.5px] leading-[1.7] text-neutral-100">{text}</pre>
          </div>
        ))}
        <p className="mt-5 text-[13px] text-neutral-500">Admins create API tokens in Settings. Enterprise clients can point the pack manager at their own registry.</p>
      </div>
    </div>
  );
}
