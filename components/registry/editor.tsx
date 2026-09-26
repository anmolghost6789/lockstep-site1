'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Command,
  createSuggestionItems,
  EditorBubble,
  EditorBubbleItem,
  EditorCommand,
  EditorCommandEmpty,
  EditorCommandItem,
  EditorCommandList,
  EditorContent,
  EditorRoot,
  handleCommandNavigation,
  HorizontalRule,
  Placeholder,
  renderItems,
  StarterKit,
  TaskItem,
  TaskList,
  TiptapLink,
  type EditorInstance,
} from 'novel';
import { Markdown } from 'tiptap-markdown';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableHeader from '@tiptap/extension-table-header';
import TableCell from '@tiptap/extension-table-cell';
import {
  AlertTriangle,
  Bold,
  CheckSquare,
  Code,
  Code2,
  FilePlus2,
  Heading1,
  Heading2,
  Heading3,
  Italic,
  List,
  ListOrdered,
  Minus,
  Quote,
  Strikethrough,
  Table as TableIcon,
  Text,
  Trash2,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { saveEdits } from '@/app/registry/actions';
import { mergeEdits, sameContent } from '@/lib/registry/md-preserve';
import { card, input, primary, secondary } from './ui';

export interface EditableFile {
  path: string;
  content: string;
  binary: boolean;
}

/* -------------------------------------------------------------------------- */
/* Markdown helpers                                                            */
/* -------------------------------------------------------------------------- */

function splitFrontmatter(src: string): { fm: string; body: string } {
  const m = src.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/);
  return m ? { fm: m[0], body: src.slice(m[0].length) } : { fm: '', body: src };
}

const bumpPatch = (v: string) => {
  const m = v.match(/^(\d+)\.(\d+)\.(\d+)$/);
  return m ? `${m[1]}.${m[2]}.${Number(m[3]) + 1}` : '1.0.1';
};

/* -------------------------------------------------------------------------- */
/* Novel configuration                                                         */
/* -------------------------------------------------------------------------- */

const suggestionItems = createSuggestionItems([
  { title: 'Text', description: 'Plain paragraph', searchTerms: ['p', 'paragraph'], icon: <Text size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleNode('paragraph', 'paragraph').run() },
  { title: 'Heading 1', description: 'Large section heading', searchTerms: ['title', 'h1'], icon: <Heading1 size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 1 }).run() },
  { title: 'Heading 2', description: 'Section heading', searchTerms: ['subtitle', 'h2'], icon: <Heading2 size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 2 }).run() },
  { title: 'Heading 3', description: 'Small heading', searchTerms: ['h3'], icon: <Heading3 size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setNode('heading', { level: 3 }).run() },
  { title: 'Bullet list', description: 'Unordered list', searchTerms: ['unordered', 'ul'], icon: <List size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleBulletList().run() },
  { title: 'Numbered list', description: 'Ordered steps', searchTerms: ['ordered', 'ol', 'steps'], icon: <ListOrdered size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleOrderedList().run() },
  { title: 'To-do list', description: 'Checklist', searchTerms: ['todo', 'task', 'checkbox'], icon: <CheckSquare size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleTaskList().run() },
  { title: 'Table', description: '3 × 3 table with a header row', searchTerms: ['grid', 'columns'], icon: <TableIcon size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run() },
  { title: 'Quote', description: 'Callout or quotation', searchTerms: ['blockquote'], icon: <Quote size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleNode('paragraph', 'paragraph').toggleBlockquote().run() },
  { title: 'Code block', description: 'Commands or code', searchTerms: ['codeblock', 'shell'], icon: <Code2 size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).toggleCodeBlock().run() },
  { title: 'Divider', description: 'Horizontal rule', searchTerms: ['hr', 'rule'], icon: <Minus size={16} />, command: ({ editor, range }) => editor.chain().focus().deleteRange(range).setHorizontalRule().run() },
]);

const extensions = [
  StarterKit.configure({ horizontalRule: false, dropcursor: { color: '#f9452d', width: 2 } }),
  HorizontalRule,
  Placeholder,
  TiptapLink.configure({ openOnClick: false }),
  TaskList,
  TaskItem.configure({ nested: true }),
  Table.configure({ resizable: false }),
  TableRow,
  TableHeader,
  TableCell,
  Markdown.configure({ html: false, tightLists: true, bulletListMarker: '-', linkify: false, breaks: false, transformPastedText: true }),
  Command.configure({ suggestion: { items: () => suggestionItems, render: renderItems } }),
];

type EditorStorage = { markdown: { getMarkdown: () => string } };
const getMarkdown = (editor: EditorInstance) => (editor.storage as unknown as EditorStorage).markdown.getMarkdown();

function RichEditor({ body, onChange, onRoundTrip }: { body: string; onChange: (md: string) => void; onRoundTrip: (ok: boolean) => void }) {
  // The file as it was when this editor opened, and what the editor produced for it untouched.
  // Edits are merged back onto the original, so untouched parts keep their exact formatting.
  const originalRef = React.useRef(body);
  const baselineRef = React.useRef<string | null>(null);
  return (
    <EditorRoot>
      <EditorContent
        extensions={extensions}
        immediatelyRender={false}
        className="lockstep-editor relative min-h-[460px] w-full"
        editorProps={{
          handleDOMEvents: { keydown: (_view, event) => handleCommandNavigation(event) },
          attributes: { class: 'lockstep-prose focus:outline-hidden max-w-full px-6 py-6 sm:px-8' },
        }}
        onCreate={({ editor }) => {
          editor.commands.setContent(originalRef.current, false);
          baselineRef.current = getMarkdown(editor);
          onRoundTrip(sameContent(originalRef.current, baselineRef.current));
        }}
        onUpdate={({ editor }) => {
          if (baselineRef.current === null) return;
          onChange(mergeEdits(originalRef.current, baselineRef.current, getMarkdown(editor)));
        }}
      >
        <EditorCommand className="z-50 h-auto max-h-[330px] w-72 overflow-y-auto rounded-xl border border-black/[0.08] bg-white px-1 py-2 shadow-lg dark:border-white/[0.1] dark:bg-neutral-950">
          <EditorCommandEmpty className="px-3 py-1.5 text-[13px] text-neutral-500">No matches</EditorCommandEmpty>
          <EditorCommandList>
            {suggestionItems.map((item) => (
              <EditorCommandItem
                key={item.title}
                value={item.title}
                onCommand={(val) => item.command?.(val)}
                className="flex w-full cursor-pointer items-center gap-3 rounded-lg px-2 py-1.5 text-left text-[13px] aria-selected:bg-neutral-100 dark:aria-selected:bg-white/[0.07]"
              >
                <span className="grid size-8 place-items-center rounded-md border border-black/[0.08] bg-white text-neutral-700 dark:border-white/[0.1] dark:bg-neutral-900 dark:text-neutral-300">{item.icon}</span>
                <span>
                  <span className="block font-medium text-neutral-900 dark:text-neutral-100">{item.title}</span>
                  <span className="block text-[11.5px] text-neutral-500">{item.description}</span>
                </span>
              </EditorCommandItem>
            ))}
          </EditorCommandList>
        </EditorCommand>
        <EditorBubble tippyOptions={{ placement: 'top' }} className="flex overflow-hidden rounded-lg border border-black/[0.08] bg-white shadow-lg dark:border-white/[0.1] dark:bg-neutral-950">
          {[
            { name: 'Bold', icon: Bold, run: (e: EditorInstance) => e.chain().focus().toggleBold().run(), active: (e: EditorInstance) => e.isActive('bold') },
            { name: 'Italic', icon: Italic, run: (e: EditorInstance) => e.chain().focus().toggleItalic().run(), active: (e: EditorInstance) => e.isActive('italic') },
            { name: 'Strikethrough', icon: Strikethrough, run: (e: EditorInstance) => e.chain().focus().toggleStrike().run(), active: (e: EditorInstance) => e.isActive('strike') },
            { name: 'Code', icon: Code, run: (e: EditorInstance) => e.chain().focus().toggleCode().run(), active: (e: EditorInstance) => e.isActive('code') },
          ].map((b) => (
            <EditorBubbleItem key={b.name} onSelect={(editor) => b.run(editor)}>
              <button type="button" aria-label={b.name} className="grid size-9 place-items-center text-neutral-700 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-white/[0.07]">
                <b.icon className="size-4" />
              </button>
            </EditorBubbleItem>
          ))}
        </EditorBubble>
      </EditorContent>
    </EditorRoot>
  );
}

function CodeArea({ value, onChange, minRows = 24 }: { value: string; onChange: (v: string) => void; minRows?: number }) {
  return (
    <textarea
      value={value}
      spellCheck={false}
      rows={Math.max(minRows, value.split('\n').length + 2)}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const t = e.currentTarget;
          const { selectionStart: s, selectionEnd: en } = t;
          const next = value.slice(0, s) + '  ' + value.slice(en);
          onChange(next);
          requestAnimationFrame(() => t.setSelectionRange(s + 2, s + 2));
        }
      }}
      className="block w-full resize-y bg-transparent px-6 py-5 font-mono text-[12.5px] leading-[1.7] text-neutral-800 outline-hidden dark:text-neutral-200"
    />
  );
}

/* -------------------------------------------------------------------------- */
/* Workspace                                                                   */
/* -------------------------------------------------------------------------- */

export function EditorWorkspace({ slug, baseVersionId, baseVersion, files }: { slug: string; baseVersionId: string; baseVersion: string; files: EditableFile[] }) {
  const original = React.useMemo(() => new Map(files.map((f) => [f.path, f.content])), [files]);
  const [contents, setContents] = React.useState<Record<string, string>>(() => Object.fromEntries(files.filter((f) => !f.binary).map((f) => [f.path, f.content])));
  const [removed, setRemoved] = React.useState<string[]>([]);
  const textPaths = Object.keys(contents).filter((p) => !removed.includes(p)).sort((a, b) => (a === 'SKILL.md' ? -1 : b === 'SKILL.md' ? 1 : a.localeCompare(b)));
  const [active, setActive] = React.useState(() => textPaths.find((p) => p.endsWith('SKILL.md')) ?? textPaths.find((p) => p.endsWith('README.md')) ?? textPaths[0]);
  const [mode, setMode] = React.useState<Record<string, 'rich' | 'markdown'>>({});
  const [lossy, setLossy] = React.useState<Record<string, boolean>>({});
  const [version, setVersion] = React.useState(bumpPatch(baseVersion));
  const [note, setNote] = React.useState('');
  const [newPath, setNewPath] = React.useState('');
  const [adding, setAdding] = React.useState(false);
  const [filter, setFilter] = React.useState('');
  const [pending, startTransition] = React.useTransition();
  const [result, setResult] = React.useState<{ error?: string; errors?: string[] }>({});

  const changed = textPaths.filter((p) => contents[p] !== original.get(p));
  const dirty = changed.length > 0 || removed.length > 0;

  React.useEffect(() => {
    if (!dirty) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);

  const isMd = active?.toLowerCase().endsWith('.md');
  const fileMode = mode[active] ?? (lossy[active] ? 'markdown' : 'rich');
  const { fm, body } = splitFrontmatter(contents[active] ?? '');
  const setFile = (value: string) => setContents((c) => ({ ...c, [active]: value }));

  function save() {
    setResult({});
    startTransition(async () => {
      const r = await saveEdits({ slug, baseVersionId, version, note, changed: changed.map((p) => ({ path: p, content: contents[p] })), removed });
      if (r) setResult(r);
    });
  }

  const visible = textPaths.filter((p) => !filter || p.toLowerCase().includes(filter.toLowerCase()));
  const binaries = files.filter((f) => f.binary);

  return (
    <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
      {/* File list */}
      <aside className={cn(card, 'flex max-h-[80vh] flex-col overflow-hidden')}>
        <div className="border-b border-black/[0.06] p-3 dark:border-white/[0.07]">
          <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Filter files" aria-label="Filter files" className={cn(input, 'h-8 text-[13px]')} />
        </div>
        <ul className="flex-1 overflow-y-auto p-2">
          {visible.map((p) => (
            <li key={p}>
              <button
                type="button"
                onClick={() => setActive(p)}
                className={cn(
                  'flex w-full items-center justify-between gap-2 rounded-lg px-2.5 py-1.5 text-left font-mono text-[12px]',
                  p === active ? 'bg-neutral-100 text-neutral-900 dark:bg-white/[0.08] dark:text-neutral-100' : 'text-neutral-600 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-white/[0.04]',
                )}
              >
                <span className="truncate">{p}</span>
                {contents[p] !== original.get(p) && <span aria-label={original.has(p) ? 'edited' : 'new'} className="size-1.5 shrink-0 rounded-full bg-[#f9452d] dark:bg-[#E1F435]" />}
              </button>
            </li>
          ))}
          {binaries.length > 0 && (
            <li className="mt-3 px-2.5 pb-1 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400">Binary (read-only)</li>
          )}
          {binaries.map((f) => (
            <li key={f.path} className="truncate px-2.5 py-1 font-mono text-[12px] text-neutral-400">{f.path}</li>
          ))}
        </ul>
        <div className="border-t border-black/[0.06] p-3 dark:border-white/[0.07]">
          {adding ? (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const p = newPath.trim().replace(/^\/+/, '');
                if (!p || p.includes('..') || contents[p] !== undefined) return;
                setContents((c) => ({ ...c, [p]: p.endsWith('.md') ? `# ${p.split('/').pop()?.replace(/\.md$/, '')}\n` : '' }));
                setActive(p);
                setNewPath('');
                setAdding(false);
              }}
              className="flex gap-2"
            >
              <input autoFocus value={newPath} onChange={(e) => setNewPath(e.target.value)} placeholder="path/to/file.md" className={cn(input, 'h-8 font-mono text-[12px]')} />
              <button className={cn(primary, 'h-8 px-3 text-[12px]')}>Add</button>
            </form>
          ) : (
            <button type="button" onClick={() => setAdding(true)} className="flex items-center gap-1.5 text-[12.5px] font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100">
              <FilePlus2 className="size-3.5" /> New file
            </button>
          )}
        </div>
      </aside>

      {/* Editor */}
      <div className="min-w-0 space-y-4">
        {active && (
          <div className={cn(card, 'overflow-hidden')}>
            <div className="flex flex-wrap items-center gap-2 border-b border-black/[0.06] px-4 py-2.5 dark:border-white/[0.07]">
              <span className="min-w-0 flex-1 truncate font-mono text-[12.5px] text-neutral-800 dark:text-neutral-200">{active}</span>
              {isMd && (
                <div className="flex rounded-full border border-black/10 p-0.5 dark:border-white/10" role="tablist" aria-label="Editing mode">
                  {(['rich', 'markdown'] as const).map((m) => (
                    <button
                      key={m}
                      role="tab"
                      aria-selected={fileMode === m}
                      type="button"
                      onClick={() => setMode((s) => ({ ...s, [active]: m }))}
                      className={cn('rounded-full px-3 py-1 text-[12px] font-medium', fileMode === m ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900' : 'text-neutral-600 dark:text-neutral-400')}
                    >
                      {m === 'rich' ? 'Rich' : 'Markdown'}
                    </button>
                  ))}
                </div>
              )}
              {active !== 'SKILL.md' && (
                <button
                  type="button"
                  aria-label={`Delete ${active}`}
                  onClick={() => {
                    if (!confirm(`Remove ${active} from the next version?`)) return;
                    if (original.has(active)) setRemoved((r) => [...r, active]);
                    else setContents((c) => { const n = { ...c }; delete n[active]; return n; });
                    setActive(textPaths.find((p) => p !== active)!);
                  }}
                  className="grid size-8 place-items-center rounded-full text-neutral-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-500/10"
                >
                  <Trash2 className="size-3.5" />
                </button>
              )}
            </div>

            {isMd && lossy[active] && fileMode === 'markdown' && !mode[active] && (
              <p className="flex items-start gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2.5 text-[12.5px] text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />
                This file contains syntax the rich editor can’t represent, so it opened as Markdown to keep every character intact. Switching to Rich is possible, but may simplify that syntax.
              </p>
            )}

            {isMd && fm && (
              <div className="border-b border-black/[0.06] bg-neutral-50/60 dark:border-white/[0.07] dark:bg-white/[0.02]">
                <p className="px-6 pt-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400">Frontmatter</p>
                <CodeArea value={fm.replace(/\n$/, '')} minRows={3} onChange={(v) => setFile(`${v.endsWith('\n') ? v : v + '\n'}${body}`)} />
              </div>
            )}

            {isMd && fileMode === 'rich' ? (
              <RichEditor
                key={active}
                body={body}
                onChange={(md) => setFile(`${fm}${md}`)}
                onRoundTrip={(ok) => {
                  if (!ok && !(active in lossy)) {
                    setLossy((s) => ({ ...s, [active]: true }));
                  } else if (ok) setLossy((s) => ({ ...s, [active]: false }));
                }}
              />
            ) : isMd ? (
              <CodeArea key={`${active}-md`} value={body} onChange={(v) => setFile(`${fm}${v}`)} />
            ) : (
              <CodeArea key={`${active}-code`} value={contents[active] ?? ''} onChange={setFile} />
            )}
          </div>
        )}

        {/* Save */}
        <div className={cn(card, 'space-y-3 p-4')}>
          <div className="flex flex-wrap items-center gap-2 text-[13px] text-neutral-600 dark:text-neutral-400">
            <span className="font-medium text-neutral-900 dark:text-neutral-100">
              {changed.length} changed · {removed.length} removed
            </span>
            <span>from v{baseVersion}. Saving creates a new version that an admin other than you approves.</span>
          </div>
          <div className="grid gap-3 md:grid-cols-[150px_minmax(0,1fr)_auto]">
            <input value={version} onChange={(e) => setVersion(e.target.value)} aria-label="New version" className={cn(input, 'font-mono')} />
            <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} placeholder="What changed, for the reviewer" aria-label="Change note" className={input} />
            <div className="flex gap-2">
              <Link href={`/registry/skills/${slug}?v=${baseVersionId}`} className={secondary}>Cancel</Link>
              <button type="button" onClick={save} disabled={!dirty || pending} className={primary}>
                {pending ? 'Saving…' : 'Save as new version'}
              </button>
            </div>
          </div>
          {(result.error || result.errors?.length) && (
            <div role="status" className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-[13px] text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
              {result.error && <p>{result.error}</p>}
              {result.errors && <ul className="list-disc pl-4">{result.errors.map((e) => <li key={e}>{e}</li>)}</ul>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
