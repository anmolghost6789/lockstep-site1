/**
 * Validation for skills submitted to the registry, following the open Agent Skills format
 * (https://agentskills.io/specification): a folder with a SKILL.md at its root, whose YAML
 * frontmatter has a `name` and a `description`.
 */

export interface IncomingFile {
  path: string;
  content: string;
  /** Text files are utf8; images, spreadsheets and other binaries are base64. */
  encoding?: 'utf8' | 'base64';
}

export interface ContainedSkill {
  name: string;
  description: string;
  path: string;
}

export interface ValidationResult {
  ok: boolean;
  errors: string[];
  warnings: string[];
  kind: 'skill' | 'pack';
  name: string;
  description: string;
  skills: ContainedSkill[];
  frontmatter: Record<string, unknown>;
  files: IncomingFile[];
}

const NAME_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const SEMVER_RE = /^(\d+)\.(\d+)\.(\d+)$/;
const MAX_FILES = 400;
// Vercel caps request bodies at about 4.5 MB, so packs stay under 4 MB including base64 overhead.
const MAX_BYTES = 4 * 1024 * 1024;
const SKILL_IN_PACK = /^(?:.*\/)?(?:\.claude\/skills|skills)\/([^/]+)\/SKILL\.md$/;
const SECRET_RE = /(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{36,})/;

export function parseFrontmatter(md: string): { data: Record<string, unknown>; body: string } | null {
  const m = md.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!m) return null;
  const data: Record<string, unknown> = {};
  const lines = m[1].split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const kv = lines[i].match(/^([\w-]+):\s*(.*)$/);
    if (!kv) continue;
    const [, key, raw] = kv;
    if (raw === '' || raw === '>-' || raw === '>' || raw === '|') {
      const block: string[] = [];
      while (i + 1 < lines.length && /^\s+/.test(lines[i + 1])) block.push(lines[++i].trim());
      data[key] = block.every((b) => b.startsWith('- ')) && block.length ? block.map((b) => b.slice(2)) : block.join(' ');
    } else {
      data[key] = raw.replace(/^["']|["']$/g, '');
    }
  }
  return { data, body: md.slice(m[0].length) };
}

export function compareSemver(a: string, b: string): number {
  const pa = a.split('.').map(Number);
  const pb = b.split('.').map(Number);
  for (let i = 0; i < 3; i++) if ((pa[i] ?? 0) !== (pb[i] ?? 0)) return (pa[i] ?? 0) - (pb[i] ?? 0);
  return 0;
}

/** Strip a shared top-level folder (e.g. from a zipped or uploaded folder). */
export function normaliseFiles(files: IncomingFile[]): IncomingFile[] {
  const clean = files
    .map((f) => ({ ...f, path: f.path.replace(/\\/g, '/').replace(/^\.?\/+/, '') }))
    .filter((f) => f.path && !f.path.endsWith('/') && !/(^|\/)(\.DS_Store|__MACOSX|__pycache__)(\/|$)/.test(f.path));
  if (clean.some((f) => f.path === 'SKILL.md' || f.path === 'lockstep-pack.json' || f.path.startsWith('.claude/'))) return clean;
  const tops = new Set(clean.map((f) => f.path.split('/')[0]));
  if (tops.size === 1) {
    const [top] = [...tops];
    const inner = clean.map((f) => ({ ...f, path: f.path.slice(top.length + 1) }));
    if (inner.some((f) => f.path === 'SKILL.md' || f.path === 'lockstep-pack.json' || f.path.startsWith('.claude/'))) return inner;
  }
  return clean;
}

function checkName(name: string, label: string, errors: string[]) {
  if (!name) errors.push(`${label} is missing a name.`);
  else if (name.length > 64 || !NAME_RE.test(name)) errors.push(`${label}: name "${name}" must be 1–64 characters of lowercase letters, numbers and single hyphens.`);
}

/**
 * Validates either a single skill (SKILL.md at the root) or a pack: a package such as a Claude Code
 * project whose skills live in .claude/skills/<name>/SKILL.md, alongside agents, hooks, config and docs.
 * Packs take their name from lockstep-pack.json, or from the name and description given on the form.
 */
export function validateSkill(
  input: IncomingFile[],
  version: string,
  latestVersion: string | null,
  packMeta?: { name?: string; description?: string },
): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const files = normaliseFiles(input).map((f) => ({ ...f, encoding: f.encoding ?? 'utf8' }) as IncomingFile);
  let name = '';
  let description = '';
  let frontmatter: Record<string, unknown> = {};
  const skills: ContainedSkill[] = [];

  if (!SEMVER_RE.test(version)) errors.push('Version must look like 1.2.3.');
  if (latestVersion && SEMVER_RE.test(version) && compareSemver(version, latestVersion) <= 0) {
    errors.push(`Version must be higher than the latest version, ${latestVersion}.`);
  }
  if (files.length === 0) errors.push('No files received.');
  if (files.length > MAX_FILES) errors.push(`Too many files (${files.length}); the limit is ${MAX_FILES}.`);
  const bytes = files.reduce((n, f) => n + f.content.length, 0);
  if (bytes > MAX_BYTES) errors.push('This upload is larger than 4 MB. Move large assets out of the pack.');
  for (const f of files) {
    if (f.path.includes('..') || f.path.startsWith('/')) errors.push(`Unsafe file path: ${f.path}`);
    if (f.encoding === 'utf8' && f.content.includes('\u0000')) errors.push(`${f.path} looks binary; upload it as a file, not text.`);
  }
  if (files.filter((f) => f.encoding === 'utf8').some((f) => SECRET_RE.test(f.content))) {
    errors.push('The upload appears to contain a secret or private key. Remove it before publishing.');
  }

  const rootSkill = files.find((f) => f.path === 'SKILL.md');
  const readSkill = (file: IncomingFile, label: string) => {
    const fm = parseFrontmatter(file.content);
    if (!fm) {
      errors.push(`${label} must start with YAML frontmatter between --- lines.`);
      return null;
    }
    const n = String(fm.data.name ?? '');
    const d = String(fm.data.description ?? '');
    checkName(n, label, errors);
    if (!d) errors.push(`${label} is missing a description.`);
    else if (d.length > 1024) errors.push(`${label}: description must be 1,024 characters or fewer.`);
    if (!fm.body.trim()) warnings.push(`${label} has no instructions below the frontmatter.`);
    return { data: fm.data, name: n, description: d };
  };

  let kind: 'skill' | 'pack' = 'skill';
  if (rootSkill) {
    const r = readSkill(rootSkill, 'SKILL.md');
    if (r) {
      name = r.name;
      description = r.description;
      frontmatter = { ...r.data, kind: 'skill' };
      skills.push({ name: r.name, description: r.description, path: '' });
    }
  } else {
    const inPack = files.filter((f) => SKILL_IN_PACK.test(f.path));
    const manifestFile = files.find((f) => f.path === 'lockstep-pack.json');
    if (inPack.length === 0 && !manifestFile) {
      errors.push('No SKILL.md found. Upload a skill folder with SKILL.md at its root, or a pack with skills in .claude/skills/<name>/SKILL.md.');
    } else {
      kind = 'pack';
      let manifest: Record<string, unknown> = {};
      if (manifestFile) {
        try {
          manifest = JSON.parse(manifestFile.content);
        } catch {
          errors.push('lockstep-pack.json is not valid JSON.');
        }
      }
      name = String(manifest.name ?? packMeta?.name ?? '').trim();
      description = String(manifest.description ?? packMeta?.description ?? '').trim();
      checkName(name, 'The pack', errors);
      if (!description) errors.push('The pack needs a description: add lockstep-pack.json or fill in the description.');
      else if (description.length > 1024) errors.push('The pack description must be 1,024 characters or fewer.');
      for (const f of inPack.sort((a, b) => a.path.localeCompare(b.path))) {
        const folder = f.path.match(SKILL_IN_PACK)![1];
        const r = readSkill(f, f.path);
        if (!r) continue;
        if (r.name && r.name !== folder) warnings.push(`${f.path}: name "${r.name}" differs from its folder "${folder}".`);
        skills.push({ name: r.name, description: r.description, path: f.path.replace(/\/SKILL\.md$/, '') });
      }
      if (inPack.length === 0) warnings.push('This pack has no skills yet.');
      frontmatter = { kind: 'pack', manifest, skills };
    }
  }
  return { ok: errors.length === 0, errors, warnings, kind, name, description, skills, frontmatter, files };
}
