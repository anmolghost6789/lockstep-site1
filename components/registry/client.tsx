'use client';

import * as React from 'react';
import { useActionState } from 'react';
import { strFromU8, unzipSync } from 'fflate';
import { AlertTriangle, Check, Copy, Download, FileCode2, FolderUp, KeyRound, Upload } from 'lucide-react';

import { cn } from '@/lib/utils';
import { CodeFile, MarkdownFile } from '@/components/site/skill-viewer';
import { TreeNav, type TreeNavItem } from '@/components/spectrumui/tree-nav';
import {
  createToken,
  createUser,
  login,
  reviewVersion,
  submitSkill,
  type FormState,
} from '@/app/registry/actions';
import { card, hint, input, label, primary, secondary, textarea } from './ui';
import { groupFiles, isImage, mimeFor } from '@/lib/registry/groups';

interface RegistryFile {
  path: string;
  content: string;
  encoding?: 'utf8' | 'base64';
}

const b64ToBytes = (b64: string) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
const formatBytes = (n: number) => (n < 1024 ? `${n} B` : n < 1024 * 1024 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`);

/* -------------------------------------------------------------------------- */
/* File viewer                                                                 */
/* -------------------------------------------------------------------------- */

export function FileViewer({ files }: { files: RegistryFile[] }) {
  const groups = React.useMemo(() => groupFiles(files), [files]);
  const first = groups[0]?.files[0]?.file;
  const [active, setActive] = React.useState(first?.path);
  const file = files.find((f) => f.path === active) ?? first;
  const [copied, setCopied] = React.useState(false);
  if (!file) return null;
  const binary = file.encoding === 'base64';
  const size = binary ? Math.floor((file.content.length * 3) / 4) : new Blob([file.content]).size;

  function download() {
    const blob = binary ? new Blob([b64ToBytes(file!.content)], { type: mimeFor(file!.path) }) : new Blob([file!.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file!.path.split('/').pop() as string;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className={cn(card, 'grid min-h-[560px] overflow-hidden lg:grid-cols-[270px_minmax(0,1fr)]')}>
      <nav aria-label="Files" className="max-h-[260px] overflow-y-auto border-b border-black/[0.06] bg-neutral-50/60 px-3 py-4 dark:border-white/[0.07] dark:bg-white/[0.02] lg:max-h-[780px] lg:border-b-0 lg:border-r">
        <p className="mb-3 px-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">
          {files.length} {files.length === 1 ? 'file' : 'files'}
        </p>
        {groups.map((g) => (
          <div key={g.key} className="mb-4">
            <p className="mb-1 px-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">{g.label}</p>
            <TreeNav
              items={g.files.map<TreeNavItem>((x) => ({ label: x.label, href: `#${x.file.path}` }))}
              activeHref={g.files.some((x) => x.file.path === file.path) ? `#${file.path}` : undefined}
              followHover={false}
              onSelect={(item, e) => {
                e.preventDefault();
                setActive(item.href.slice(1));
              }}
              className="[&_a]:font-mono [&_a]:text-[12px]"
            />
          </div>
        ))}
      </nav>
      <div className="flex min-w-0 flex-col">
        <div className="flex flex-wrap items-center gap-2 border-b border-black/[0.06] px-5 py-2.5 dark:border-white/[0.07]">
          <FileCode2 className="size-3.5 shrink-0 text-neutral-400" />
          <span className="min-w-0 flex-1 truncate font-mono text-[12px] text-neutral-700 dark:text-neutral-300">{file.path}</span>
          <span className="font-mono text-[11px] text-neutral-400">{formatBytes(size)}</span>
          {!binary && (
            <button
              type="button"
              onClick={async () => {
                await navigator.clipboard.writeText(file.content);
                setCopied(true);
                setTimeout(() => setCopied(false), 1400);
              }}
              className="inline-flex h-7 items-center gap-1.5 rounded-full border border-black/10 px-2.5 text-[12px] font-medium text-neutral-700 hover:bg-neutral-50 dark:border-white/10 dark:text-neutral-300 dark:hover:bg-white/[0.05]"
            >
              {copied ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          )}
          <button
            type="button"
            onClick={download}
            className="inline-flex h-7 items-center gap-1.5 rounded-full border border-black/10 px-2.5 text-[12px] font-medium text-neutral-700 hover:bg-neutral-50 dark:border-white/10 dark:text-neutral-300 dark:hover:bg-white/[0.05]"
          >
            <Download className="size-3.5" />
            Download
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
          {binary ? (
            isImage(file.path) ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={`data:${mimeFor(file.path)};base64,${file.content}`} alt={file.path} className="max-h-[520px] max-w-full rounded-lg border border-black/[0.08] dark:border-white/[0.09]" />
            ) : (
              <div className="grid min-h-[300px] place-items-center text-center">
                <div>
                  <FileCode2 className="mx-auto size-8 text-neutral-300 dark:text-neutral-600" />
                  <p className="mt-3 text-[14px] font-medium text-neutral-900 dark:text-neutral-100">{file.path.split('/').pop()}</p>
                  <p className="mt-1 text-[13px] text-neutral-500">Binary file, {formatBytes(size)}. Download it to open.</p>
                  <button type="button" onClick={download} className={cn(secondary, 'mt-4')}>
                    <Download className="size-4" />
                    Download
                  </button>
                </div>
              </div>
            )
          ) : file.path.endsWith('.md') ? (
            <MarkdownFile source={file.content} />
          ) : (
            <CodeFile source={file.content} />
          )}
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Shared bits                                                                 */
/* -------------------------------------------------------------------------- */

function Messages({ state }: { state: FormState }) {
  if (!state.error && !state.errors?.length && !state.ok && !state.warnings?.length) return null;
  return (
    <div className="space-y-2" role="status" aria-live="polite">
      {(state.error || state.errors?.length) && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[13px] text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
          {state.error && <p>{state.error}</p>}
          {state.errors && (
            <ul className="list-disc space-y-0.5 pl-4">
              {state.errors.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      {state.warnings?.length ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3.5 py-2.5 text-[13px] text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">
          {state.warnings.map((w) => (
            <p key={w}>{w}</p>
          ))}
        </div>
      ) : null}
      {state.ok && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3.5 py-2.5 text-[13px] text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300">
          {state.ok}
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Login                                                                       */
/* -------------------------------------------------------------------------- */

export function LoginForm() {
  const [state, action, pending] = useActionState(login, {});
  return (
    <form action={action} className="space-y-4">
      <div>
        <label htmlFor="email" className={label}>Email</label>
        <input id="email" name="email" type="email" autoComplete="email" required defaultValue={state.values?.email} className={input} />
      </div>
      <div>
        <label htmlFor="password" className={label}>Password</label>
        <input id="password" name="password" type="password" autoComplete="current-password" required className={input} />
      </div>
      <Messages state={state} />
      <button type="submit" disabled={pending} className={cn(primary, 'w-full')}>
        {pending ? 'Signing in…' : 'Sign in'}
      </button>
    </form>
  );
}

/* -------------------------------------------------------------------------- */
/* Register a skill                                                            */
/* -------------------------------------------------------------------------- */

const TEXT_EXT = /\.(md|mdx|txt|ya?ml|json|py|ts|tsx|js|mjs|cjs|sh|toml|ini|cfg|csv|html|css|sql|xml|svg|j2|tmpl|template|gitignore|env\.example)$|(^|\/)(\.gitignore|\.mcp\.json|Dockerfile|Makefile|LICENSE|[A-Z_]+)$/i;
const SKIP = /(^|\/)(\.git|node_modules|__pycache__|\.DS_Store|__MACOSX|\.next|\.data)(\/|$)/;

const bytesToB64 = (bytes: Uint8Array) => {
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s);
};

async function readFileList(list: FileList): Promise<RegistryFile[]> {
  const out: RegistryFile[] = [];
  for (const f of Array.from(list)) {
    const rel = (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name;
    if (SKIP.test(rel)) continue;
    if (TEXT_EXT.test(rel)) out.push({ path: rel, content: await f.text(), encoding: 'utf8' });
    else out.push({ path: rel, content: bytesToB64(new Uint8Array(await f.arrayBuffer())), encoding: 'base64' });
  }
  return out;
}

async function readZip(file: File): Promise<RegistryFile[]> {
  const entries = unzipSync(new Uint8Array(await file.arrayBuffer()));
  return Object.entries(entries)
    .filter(([p, data]) => !p.endsWith('/') && data.length > 0 && !SKIP.test(p))
    .map(([p, data]) =>
      TEXT_EXT.test(p) ? { path: p, content: strFromU8(data), encoding: 'utf8' as const } : { path: p, content: bytesToB64(data), encoding: 'base64' as const },
    );
}

export function RegisterForm({ defaultVersion = '1.0.0' }: { defaultVersion?: string }) {
  const [state, action, pending] = useActionState(submitSkill, {});
  const [files, setFiles] = React.useState<RegistryFile[]>([]);
  const [source, setSource] = React.useState('');
  const [pasted, setPasted] = React.useState('');
  const [readError, setReadError] = React.useState('');

  const hasSkillMd = files.some((f) => f.path === 'SKILL.md' || f.path.endsWith('/SKILL.md'));
  const skillCount = files.filter((f) => /(^|\/)SKILL\.md$/.test(f.path)).length;
  const looksLikePack = files.some((f) => /(^|\/)\.claude\/skills\/[^/]+\/SKILL\.md$/.test(f.path) || /(^|\/)lockstep-pack\.json$/.test(f.path));
  const hasManifest = files.some((f) => /(^|\/)lockstep-pack\.json$/.test(f.path));
  const binaries = files.filter((f) => f.encoding === 'base64').length;

  async function onFolder(e: React.ChangeEvent<HTMLInputElement>) {
    setReadError('');
    if (!e.target.files?.length) return;
    const read = await readFileList(e.target.files);
    setFiles(read);
    setSource(`Folder: ${read.length} files`);
    setPasted('');
  }
  async function onZip(e: React.ChangeEvent<HTMLInputElement>) {
    setReadError('');
    const f = e.target.files?.[0];
    if (!f) return;
    try {
      const read = await readZip(f);
      setFiles(read);
      setSource(`${f.name}: ${read.length} files`);
      setPasted('');
    } catch {
      setReadError('That file could not be opened as a .zip archive.');
    }
  }
  function onPaste(v: string) {
    setPasted(v);
    setFiles(v.trim() ? [{ path: 'SKILL.md', content: v, encoding: 'utf8' }] : []);
    setSource(v.trim() ? 'Pasted SKILL.md' : '');
  }

  return (
    <form action={action} className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        <label className={cn(card, 'flex cursor-pointer items-center gap-3 p-4 transition-colors hover:border-black/20 dark:hover:border-white/20')}>
          <span className="grid size-9 place-items-center rounded-lg bg-neutral-100 text-neutral-700 dark:bg-white/[0.07] dark:text-neutral-300">
            <FolderUp className="size-4" />
          </span>
          <span>
            <span className="block text-[14px] font-medium text-neutral-900 dark:text-neutral-100">Upload a folder</span>
            <span className="block text-[12px] text-neutral-500 dark:text-neutral-400">A skill, or a whole pack</span>
          </span>
          <input type="file" multiple className="sr-only" onChange={onFolder} {...({ webkitdirectory: '', directory: '' } as Record<string, string>)} />
        </label>
        <label className={cn(card, 'flex cursor-pointer items-center gap-3 p-4 transition-colors hover:border-black/20 dark:hover:border-white/20')}>
          <span className="grid size-9 place-items-center rounded-lg bg-neutral-100 text-neutral-700 dark:bg-white/[0.07] dark:text-neutral-300">
            <Upload className="size-4" />
          </span>
          <span>
            <span className="block text-[14px] font-medium text-neutral-900 dark:text-neutral-100">Upload a .zip</span>
            <span className="block text-[12px] text-neutral-500 dark:text-neutral-400">A zipped skill or pack</span>
          </span>
          <input type="file" accept=".zip,application/zip" className="sr-only" onChange={onZip} />
        </label>
      </div>

      <div>
        <label htmlFor="paste" className={label}>Or paste a SKILL.md</label>
        <textarea
          id="paste"
          rows={8}
          value={pasted}
          onChange={(e) => onPaste(e.target.value)}
          placeholder={'---\nname: my-skill\ndescription: What this skill does and when to use it.\n---\n\n# My skill\n…'}
          className={textarea}
        />
        <p className={hint}>Single-file skills only. Upload a folder if the skill has templates, scripts or references.</p>
      </div>

      {(source || readError) && (
        <div className={cn(card, 'p-4')}>
          {readError ? (
            <p className="text-[13px] text-red-700 dark:text-red-400">{readError}</p>
          ) : (
            <>
              <div className="flex items-center justify-between gap-3">
                <p className="text-[13px] font-medium text-neutral-900 dark:text-neutral-100">{source}</p>
                {hasSkillMd ? (
                  <span className="inline-flex items-center gap-1 text-[12px] text-emerald-700 dark:text-emerald-400">
                    <Check className="size-3.5" />
                    {looksLikePack ? `Pack with ${skillCount} ${skillCount === 1 ? 'skill' : 'skills'}` : 'SKILL.md found'}
                    {binaries > 0 && `, ${binaries} binary`}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[12px] text-amber-700 dark:text-amber-400"><AlertTriangle className="size-3.5" />No SKILL.md</span>
                )}
              </div>
              <ul className="mt-2 max-h-40 overflow-y-auto font-mono text-[11.5px] text-neutral-500 dark:text-neutral-400">
                {files.slice(0, 60).map((f) => (
                  <li key={f.path}>{f.path}</li>
                ))}
                {files.length > 60 && <li>…and {files.length - 60} more</li>}
              </ul>
            </>
          )}
        </div>
      )}

      {looksLikePack && !hasManifest && (
        <div className="grid gap-4 md:grid-cols-[260px_minmax(0,1fr)]">
          <div>
            <label htmlFor="packName" className={label}>Pack name</label>
            <input id="packName" name="packName" defaultValue={state.values?.name} placeholder="e.g. banking-kyc" className={cn(input, 'font-mono')} />
            <p className={hint}>Lowercase letters, numbers and hyphens.</p>
          </div>
          <div>
            <label htmlFor="packDescription" className={label}>Pack description</label>
            <input id="packDescription" name="packDescription" defaultValue={state.values?.description} maxLength={1024} placeholder="What the pack does and who it is for" className={input} />
            <p className={hint}>Or add a lockstep-pack.json with name and description to the pack.</p>
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-[200px_minmax(0,1fr)]">
        <div>
          <label htmlFor="version" className={label}>Version</label>
          <input id="version" name="version" defaultValue={state.values?.version ?? defaultVersion} pattern="\d+\.\d+\.\d+" required className={cn(input, 'font-mono')} />
          <p className={hint}>Higher than the latest version.</p>
        </div>
        <div>
          <label htmlFor="note" className={label}>What changed</label>
          <input id="note" name="note" maxLength={500} defaultValue={state.values?.note} placeholder="For the reviewer, e.g. Adds EU AI Act record-keeping checks" className={input} />
        </div>
      </div>

      <input type="hidden" name="files" value={JSON.stringify(files)} />
      <Messages state={state} />
      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" disabled={pending || files.length === 0} className={primary}>
          {pending ? 'Submitting…' : 'Submit for approval'}
        </button>
        <p className="text-[12.5px] text-neutral-500 dark:text-neutral-400">An admin other than you approves it before extensions can install it.</p>
      </div>
    </form>
  );
}

/* -------------------------------------------------------------------------- */
/* Review                                                                      */
/* -------------------------------------------------------------------------- */

export function ReviewForm({ id, ownSubmission }: { id: string; ownSubmission: boolean }) {
  const [state, action, pending] = useActionState(reviewVersion, {});
  if (state.ok) return <Messages state={state} />;
  return (
    <form action={action} className={cn(card, 'space-y-3 p-4')}>
      <input type="hidden" name="id" value={id} />
      <p className="text-[14px] font-medium text-neutral-900 dark:text-neutral-100">Review this version</p>
      {ownSubmission ? (
        <p className="text-[13px] text-neutral-600 dark:text-neutral-400">You submitted this version, so another admin has to review it.</p>
      ) : (
        <>
          <textarea name="note" rows={3} placeholder="Note for the submitter (required when rejecting)" className={textarea} />
          <Messages state={state} />
          <div className="flex gap-2">
            <button type="submit" name="decision" value="approve" disabled={pending} className={primary}>Approve</button>
            <button type="submit" name="decision" value="reject" disabled={pending} className={secondary}>Reject</button>
          </div>
        </>
      )}
    </form>
  );
}

/* -------------------------------------------------------------------------- */
/* Settings                                                                    */
/* -------------------------------------------------------------------------- */

export function TokenForm() {
  const [state, action, pending] = useActionState(createToken, {});
  const [copied, setCopied] = React.useState(false);
  return (
    <form action={action} className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <input name="name" placeholder="e.g. Payments team VS Code" maxLength={80} className={cn(input, 'max-w-sm flex-1')} />
        <button type="submit" disabled={pending} className={primary}>
          <KeyRound className="size-4" />
          Create token
        </button>
      </div>
      <Messages state={{ ...state, ok: state.token ? undefined : state.ok }} />
      {state.token && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-500/30 dark:bg-emerald-500/10">
          <p className="text-[13px] text-emerald-800 dark:text-emerald-300">{state.ok}</p>
          <div className="mt-2 flex items-center gap-2">
            <code className="min-w-0 flex-1 truncate rounded-md bg-white px-2 py-1.5 font-mono text-[12px] text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">{state.token}</code>
            <button
              type="button"
              onClick={async () => {
                await navigator.clipboard.writeText(state.token!);
                setCopied(true);
              }}
              className={cn(secondary, 'h-8 px-3 text-[12px]')}
            >
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        </div>
      )}
    </form>
  );
}

export function UserForm() {
  const [state, action, pending] = useActionState(createUser, {});
  return (
    <form action={action} className="grid gap-3 md:grid-cols-2">
      <input name="name" placeholder="Name" defaultValue={state.values?.name} className={input} />
      <input name="email" type="email" placeholder="Email" defaultValue={state.values?.email} className={input} />
      <select name="role" defaultValue={state.values?.role ?? 'publisher'} key={state.values?.role} className={input}>
        <option value="viewer">Viewer: browse approved skills</option>
        <option value="publisher">Publisher: submit skills</option>
        <option value="admin">Admin: approve, tokens, users</option>
      </select>
      <input name="password" type="password" placeholder="Temporary password (12+ characters)" className={input} />
      <div className="md:col-span-2">
        <Messages state={state} />
      </div>
      <div className="md:col-span-2">
        <button type="submit" disabled={pending} className={primary}>Add user</button>
      </div>
    </form>
  );
}
