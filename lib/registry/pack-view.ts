import 'server-only';

import type { SkillVersion, TelemetryRun } from './store';
import { parseFrontmatter } from './validate';

export interface ConnectorView {
  name: string;
  transport: 'remote' | 'local';
  endpoint: string;
  host: string | null;
  allowListed: boolean | null; // null when the pack has no allow-list
}

export interface SkillView {
  name: string;
  description: string;
  path: string; // SKILL.md path
}

export interface PackView {
  publisher: string;
  icon: string;
  categories: string[];
  examples: string[];
  skills: SkillView[];
  connectors: ConnectorView[];
  sendsData: boolean;
}

const read = (v: SkillVersion, path: string) => v.files.find((f) => f.path === path && f.encoding !== 'base64')?.content;

export function packView(v: SkillVersion, createdBy: string): PackView {
  let manifest: Record<string, unknown> = {};
  try {
    manifest = JSON.parse(read(v, 'lockstep-pack.json') ?? '{}');
  } catch {
    manifest = {};
  }

  // Skills: every SKILL.md, root or .claude/skills/<name>/SKILL.md.
  const skills: SkillView[] = v.files
    .filter((f) => f.encoding !== 'base64' && /(^|\/)SKILL\.md$/.test(f.path))
    .map((f) => {
      const fm = parseFrontmatter(f.content)?.data ?? {};
      return { name: String(fm.name ?? f.path.split('/').slice(-2, -1)[0] ?? 'skill'), description: String(fm.description ?? ''), path: f.path };
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  // Connectors: MCP servers declared in .mcp.json, checked against the pack's own allow-list if it ships one.
  let servers: Record<string, { type?: string; url?: string; command?: string; args?: string[] }> = {};
  try {
    servers = JSON.parse(read(v, '.mcp.json') ?? '{}').mcpServers ?? {};
  } catch {
    servers = {};
  }
  let allow: Record<string, unknown> | null = null;
  try {
    const raw = read(v, 'config/governance/mcp_allowlist.json');
    allow = raw ? (JSON.parse(raw).servers ?? {}) : null;
  } catch {
    allow = null;
  }
  const connectors: ConnectorView[] = Object.entries(servers).map(([name, s]) => {
    const remote = !!s.url || s.type === 'http' || s.type === 'sse';
    let host: string | null = null;
    try {
      host = s.url ? new URL(s.url).host : null;
    } catch {
      host = null;
    }
    return {
      name,
      transport: remote ? 'remote' : 'local',
      endpoint: s.url ?? [s.command, ...(s.args ?? [])].filter(Boolean).join(' '),
      host,
      allowListed: allow ? name in allow : null,
    };
  });

  return {
    publisher: String(manifest.publisher ?? createdBy ?? 'Unknown'),
    icon: String(manifest.icon ?? ((v.frontmatter as { kind?: string }).kind === 'pack' ? 'package' : 'file-text')),
    categories: Array.isArray(manifest.categories) ? (manifest.categories as unknown[]).map(String) : [],
    examples: Array.isArray(manifest.examples) ? (manifest.examples as unknown[]).map(String) : [],
    skills,
    connectors,
    sendsData: connectors.some((c) => c.transport === 'remote'),
  };
}

/** Adoption and activity over the last 30 days, from metrics that projects chose to share. */
export function packStats(slug: string, telemetry: TelemetryRun[]) {
  const since = Date.now() - 30 * 24 * 3600 * 1000;
  const recent = telemetry.filter(
    (t) => (t.payload as { pack?: { name?: string } }).pack?.name === slug && new Date(t.receivedAt).getTime() >= since,
  );
  return { projects: new Set(recent.map((t) => t.project)).size, runs: recent.length };
}

export function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return 'just now';
  const m = s / 60, h = m / 60, d = h / 24;
  if (m < 60) return `${Math.floor(m)} min ago`;
  if (h < 24) return `${Math.floor(h)} hour${Math.floor(h) === 1 ? '' : 's'} ago`;
  if (d < 30) return `${Math.floor(d)} day${Math.floor(d) === 1 ? '' : 's'} ago`;
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}
