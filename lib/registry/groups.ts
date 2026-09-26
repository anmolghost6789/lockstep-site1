/** Groups a pack's files the way the site's skill viewer does, so large packs stay navigable. */
export interface FileLike {
  path: string;
  encoding?: 'utf8' | 'base64';
}

export interface FileGroup<T extends FileLike> {
  key: string;
  label: string;
  files: { file: T; label: string }[];
}

const SKILL_DIR = /^(?:.*\/)?(?:\.claude\/skills|skills)\/([^/]+)\/(.+)$/;

export function groupFiles<T extends FileLike>(files: T[]): FileGroup<T>[] {
  const groups = new Map<string, FileGroup<T>>();
  const add = (key: string, label: string, file: T, shown: string) => {
    if (!groups.has(key)) groups.set(key, { key, label, files: [] });
    groups.get(key)!.files.push({ file, label: shown });
  };
  const rootSkill = files.some((f) => f.path === 'SKILL.md');
  for (const f of files) {
    const p = f.path;
    const skill = p.match(SKILL_DIR);
    if (rootSkill) add('0-skill', 'Skill', f, p);
    else if (skill) add(`1-skill-${skill[1]}`, `Skill · ${skill[1]}`, f, skill[2]);
    else if (p.startsWith('.claude/agents/')) add('2-agents', 'Subagents', f, p.slice('.claude/agents/'.length));
    else if (p.startsWith('.claude/')) add('3-hooks', 'Hooks & settings', f, p.slice('.claude/'.length));
    else if (!p.includes('/')) add('0-root', 'Pack root', f, p);
    else if (p.startsWith('config/')) add('4-config', 'Governance & config', f, p.slice('config/'.length));
    else if (/^(context|memory|inputs)\//.test(p)) add('5-context', 'Context, memory & inputs', f, p);
    else if (p.startsWith('docs/')) add('6-docs', 'Docs', f, p.slice('docs/'.length));
    else if (p.startsWith('assets/') || f.encoding === 'base64') add('7-assets', 'Assets', f, p);
    else add('8-other', 'Other', f, p);
  }
  const out = [...groups.values()].sort((a, b) => a.key.localeCompare(b.key));
  for (const g of out) {
    const first = ['SKILL.md', 'README.md', 'CLAUDE.md', 'lockstep-pack.json'];
    const rank = (l: string) => (first.includes(l) ? first.indexOf(l) : first.length);
    g.files.sort((a, b) => rank(a.label) - rank(b.label) || a.label.localeCompare(b.label));
  }
  return out;
}

export const isImage = (p: string) => /\.(png|jpe?g|gif|webp)$/i.test(p);
export const mimeFor = (p: string) =>
  /\.png$/i.test(p) ? 'image/png' : /\.jpe?g$/i.test(p) ? 'image/jpeg' : /\.gif$/i.test(p) ? 'image/gif' : /\.webp$/i.test(p) ? 'image/webp'
    : /\.xlsx$/i.test(p) ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : /\.pdf$/i.test(p) ? 'application/pdf' : 'application/octet-stream';
