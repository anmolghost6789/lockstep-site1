import 'server-only';

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import postgres from 'postgres';

/* -------------------------------------------------------------------------- */
/* Types                                                                       */
/* -------------------------------------------------------------------------- */

export type Role = 'admin' | 'publisher' | 'viewer';
export type VersionStatus = 'pending' | 'approved' | 'rejected';

export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  passwordHash: string;
  createdAt: string;
}

export interface SkillFile {
  path: string;
  content: string;
  encoding?: 'utf8' | 'base64';
}

export interface Skill {
  slug: string;
  name: string;
  description: string;
  createdBy: string;
  createdAt: string;
}

export interface SkillVersion {
  id: string;
  slug: string;
  version: string;
  status: VersionStatus;
  files: SkillFile[];
  frontmatter: Record<string, unknown>;
  sha256: string;
  note: string;
  submittedBy: string;
  submittedAt: string;
  reviewedBy: string | null;
  reviewedAt: string | null;
  reviewNote: string | null;
}

export interface ApiToken {
  id: string;
  name: string;
  prefix: string;
  tokenHash: string;
  createdBy: string;
  createdAt: string;
  lastUsedAt: string | null;
  revoked: boolean;
}

export interface AuditEntry {
  id: string;
  ts: string;
  actor: string;
  action: string;
  target: string;
  detail: string;
}

export interface TelemetryRun {
  id: string;
  receivedAt: string;
  tokenName: string;
  project: string;
  runId: string;
  payload: Record<string, unknown>;
}

export interface SkillSummary extends Skill {
  latestApproved: string | null;
  pending: number;
  versions: number;
  kind: 'skill' | 'pack';
  skillCount: number;
  fileCount: number;
}

export interface Store {
  countUsers(): Promise<number>;
  getUserByEmail(email: string): Promise<User | null>;
  getUser(id: string): Promise<User | null>;
  listUsers(): Promise<User[]>;
  createUser(u: Omit<User, 'id' | 'createdAt'>): Promise<User>;

  listSkills(): Promise<SkillSummary[]>;
  getSkill(slug: string): Promise<Skill | null>;
  upsertSkill(s: Skill): Promise<void>;
  listVersions(slug: string): Promise<SkillVersion[]>;
  getVersion(id: string): Promise<SkillVersion | null>;
  createVersion(v: Omit<SkillVersion, 'id'>): Promise<SkillVersion>;
  reviewVersion(id: string, status: VersionStatus, reviewer: string, note: string): Promise<void>;
  listPending(): Promise<SkillVersion[]>;

  listTokens(): Promise<ApiToken[]>;
  createToken(t: Omit<ApiToken, 'id' | 'createdAt' | 'lastUsedAt' | 'revoked'>): Promise<ApiToken>;
  findTokenByHash(hash: string): Promise<ApiToken | null>;
  touchToken(id: string): Promise<void>;
  revokeToken(id: string): Promise<void>;

  audit(e: Omit<AuditEntry, 'id' | 'ts'>): Promise<void>;
  listAudit(limit: number): Promise<AuditEntry[]>;

  /** Latest metrics per (project, run); a later push for the same run replaces the earlier one. */
  upsertTelemetry(t: Omit<TelemetryRun, 'id' | 'receivedAt'>): Promise<void>;
  listTelemetry(limit: number): Promise<TelemetryRun[]>;
}

const now = () => new Date().toISOString();
const uid = () => crypto.randomUUID();

/* -------------------------------------------------------------------------- */
/* Postgres store (Vercel: set DATABASE_URL from the Neon marketplace add-on) */
/* -------------------------------------------------------------------------- */

function pgStore(url: string): Store {
  const local = /localhost|127\.0\.0\.1/.test(url);
  const sql = postgres(url, { ssl: local ? false : 'require', max: 5, idle_timeout: 20 });
  let ready: Promise<void> | null = null;

  const init = () =>
    (ready ??= (async () => {
      await sql`
        create table if not exists ls_users (
          id text primary key, email text unique not null, name text not null, role text not null,
          password_hash text not null, created_at timestamptz not null default now())`;
      await sql`
        create table if not exists ls_skills (
          slug text primary key, name text not null, description text not null,
          created_by text not null, created_at timestamptz not null default now())`;
      await sql`
        create table if not exists ls_skill_versions (
          id text primary key, slug text not null references ls_skills(slug), version text not null,
          status text not null, files jsonb not null, frontmatter jsonb not null, sha256 text not null,
          note text not null default '', submitted_by text not null, submitted_at timestamptz not null,
          reviewed_by text, reviewed_at timestamptz, review_note text, unique (slug, version))`;
      await sql`
        create table if not exists ls_tokens (
          id text primary key, name text not null, prefix text not null, token_hash text unique not null,
          created_by text not null, created_at timestamptz not null default now(),
          last_used_at timestamptz, revoked boolean not null default false)`;
      await sql`
        create table if not exists ls_telemetry (
          id text primary key, received_at timestamptz not null default now(), token_name text not null,
          project text not null, run_id text not null, payload jsonb not null, unique (project, run_id))`;
      await sql`
        create table if not exists ls_audit (
          id text primary key, ts timestamptz not null default now(), actor text not null,
          action text not null, target text not null, detail text not null default '')`;
    })().catch((e) => {
      // Don't cache a failed start (e.g. the database was briefly unreachable); retry on the next request.
      ready = null;
      throw e;
    }));

  const iso = (d: unknown) => (d ? new Date(d as string).toISOString() : null);
  const toUser = (r: postgres.Row): User => ({
    id: r.id, email: r.email, name: r.name, role: r.role, passwordHash: r.password_hash, createdAt: iso(r.created_at)!,
  });
  const toVersion = (r: postgres.Row): SkillVersion => ({
    id: r.id, slug: r.slug, version: r.version, status: r.status, files: r.files, frontmatter: r.frontmatter,
    sha256: r.sha256, note: r.note, submittedBy: r.submitted_by, submittedAt: iso(r.submitted_at)!,
    reviewedBy: r.reviewed_by, reviewedAt: iso(r.reviewed_at), reviewNote: r.review_note,
  });
  const toToken = (r: postgres.Row): ApiToken => ({
    id: r.id, name: r.name, prefix: r.prefix, tokenHash: r.token_hash, createdBy: r.created_by,
    createdAt: iso(r.created_at)!, lastUsedAt: iso(r.last_used_at), revoked: r.revoked,
  });

  return {
    async countUsers() { await init(); const [r] = await sql`select count(*)::int as n from ls_users`; return r.n; },
    async getUserByEmail(email) { await init(); const [r] = await sql`select * from ls_users where email = ${email.toLowerCase()}`; return r ? toUser(r) : null; },
    async getUser(id) { await init(); const [r] = await sql`select * from ls_users where id = ${id}`; return r ? toUser(r) : null; },
    async listUsers() { await init(); return (await sql`select * from ls_users order by created_at`).map(toUser); },
    async createUser(u) {
      await init();
      const [r] = await sql`insert into ls_users (id, email, name, role, password_hash)
        values (${uid()}, ${u.email.toLowerCase()}, ${u.name}, ${u.role}, ${u.passwordHash}) returning *`;
      return toUser(r);
    },
    async listSkills() {
      await init();
      const rows = await sql`
        select s.*,
          (select v.version from ls_skill_versions v where v.slug = s.slug and v.status = 'approved'
             order by v.submitted_at desc limit 1) as latest_approved,
          (select count(*)::int from ls_skill_versions v where v.slug = s.slug and v.status = 'pending') as pending,
          (select count(*)::int from ls_skill_versions v where v.slug = s.slug) as versions,
          (select v.frontmatter from ls_skill_versions v where v.slug = s.slug
             order by (v.status = 'approved') desc, v.submitted_at desc limit 1) as fm,
          (select jsonb_array_length(v.files) from ls_skill_versions v where v.slug = s.slug
             order by (v.status = 'approved') desc, v.submitted_at desc limit 1) as file_count
        from ls_skills s order by s.slug`;
      return rows.map((r) => ({
        slug: r.slug, name: r.name, description: r.description, createdBy: r.created_by, createdAt: iso(r.created_at)!,
        latestApproved: r.latest_approved, pending: r.pending, versions: r.versions,
        kind: r.fm?.kind === 'pack' ? 'pack' : 'skill',
        skillCount: Array.isArray(r.fm?.skills) ? r.fm.skills.length : 1,
        fileCount: r.file_count ?? 0,
      }));
    },
    async getSkill(slug) {
      await init();
      const [r] = await sql`select * from ls_skills where slug = ${slug}`;
      return r ? { slug: r.slug, name: r.name, description: r.description, createdBy: r.created_by, createdAt: iso(r.created_at)! } : null;
    },
    async upsertSkill(s) {
      await init();
      await sql`insert into ls_skills (slug, name, description, created_by)
        values (${s.slug}, ${s.name}, ${s.description}, ${s.createdBy})
        on conflict (slug) do update set name = excluded.name, description = excluded.description`;
    },
    async listVersions(slug) { await init(); return (await sql`select * from ls_skill_versions where slug = ${slug} order by submitted_at desc`).map(toVersion); },
    async getVersion(id) { await init(); const [r] = await sql`select * from ls_skill_versions where id = ${id}`; return r ? toVersion(r) : null; },
    async createVersion(v) {
      await init();
      const [r] = await sql`insert into ls_skill_versions
        (id, slug, version, status, files, frontmatter, sha256, note, submitted_by, submitted_at, reviewed_by, reviewed_at, review_note)
        values (${uid()}, ${v.slug}, ${v.version}, ${v.status}, ${sql.json(v.files as unknown as postgres.JSONValue)},
          ${sql.json(v.frontmatter as postgres.JSONValue)}, ${v.sha256}, ${v.note}, ${v.submittedBy}, ${v.submittedAt},
          ${v.reviewedBy}, ${v.reviewedAt}, ${v.reviewNote}) returning *`;
      return toVersion(r);
    },
    async reviewVersion(id, status, reviewer, note) {
      await init();
      await sql`update ls_skill_versions set status = ${status}, reviewed_by = ${reviewer}, reviewed_at = now(), review_note = ${note} where id = ${id}`;
    },
    async listPending() { await init(); return (await sql`select * from ls_skill_versions where status = 'pending' order by submitted_at`).map(toVersion); },
    async listTokens() { await init(); return (await sql`select * from ls_tokens order by created_at desc`).map(toToken); },
    async createToken(t) {
      await init();
      const [r] = await sql`insert into ls_tokens (id, name, prefix, token_hash, created_by)
        values (${uid()}, ${t.name}, ${t.prefix}, ${t.tokenHash}, ${t.createdBy}) returning *`;
      return toToken(r);
    },
    async findTokenByHash(hash) { await init(); const [r] = await sql`select * from ls_tokens where token_hash = ${hash} and not revoked`; return r ? toToken(r) : null; },
    async touchToken(id) { await init(); await sql`update ls_tokens set last_used_at = now() where id = ${id}`; },
    async revokeToken(id) { await init(); await sql`update ls_tokens set revoked = true where id = ${id}`; },
    async audit(e) { await init(); await sql`insert into ls_audit (id, actor, action, target, detail) values (${uid()}, ${e.actor}, ${e.action}, ${e.target}, ${e.detail})`; },
    async upsertTelemetry(t) {
      await init();
      await sql`insert into ls_telemetry (id, token_name, project, run_id, payload)
        values (${uid()}, ${t.tokenName}, ${t.project}, ${t.runId}, ${sql.json(t.payload as postgres.JSONValue)})
        on conflict (project, run_id) do update set payload = excluded.payload, received_at = now(), token_name = excluded.token_name`;
    },
    async listTelemetry(limit) {
      await init();
      return (await sql`select * from ls_telemetry order by received_at desc limit ${limit}`).map((r) => ({
        id: r.id, receivedAt: iso(r.received_at)!, tokenName: r.token_name, project: r.project, runId: r.run_id, payload: r.payload,
      }));
    },
    async listAudit(limit) {
      await init();
      return (await sql`select * from ls_audit order by ts desc limit ${limit}`).map((r) => ({
        id: r.id, ts: iso(r.ts)!, actor: r.actor, action: r.action, target: r.target, detail: r.detail,
      }));
    },
  };
}

/* -------------------------------------------------------------------------- */
/* File store (local development and self-hosted servers without a database)   */
/* -------------------------------------------------------------------------- */

interface FileDb {
  telemetry?: TelemetryRun[];
  users: User[];
  skills: Skill[];
  versions: SkillVersion[];
  tokens: ApiToken[];
  audit: AuditEntry[];
}

function fileStore(dir: string): Store {
  const file = path.join(dir, 'registry.json');
  const load = (): FileDb => {
    if (!fs.existsSync(file)) return { users: [], skills: [], versions: [], tokens: [], audit: [] };
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  };
  const save = (db: FileDb) => {
    fs.mkdirSync(dir, { recursive: true });
    const tmp = file + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(db, null, 2));
    fs.renameSync(tmp, file);
  };
  const mutate = <T>(fn: (db: FileDb) => T): T => {
    const db = load();
    const out = fn(db);
    save(db);
    return out;
  };

  return {
    async countUsers() { return load().users.length; },
    async getUserByEmail(email) { return load().users.find((u) => u.email === email.toLowerCase()) ?? null; },
    async getUser(id) { return load().users.find((u) => u.id === id) ?? null; },
    async listUsers() { return load().users; },
    async createUser(u) {
      return mutate((db) => {
        if (db.users.some((x) => x.email === u.email.toLowerCase())) throw new Error('A user with that email already exists.');
        const user = { ...u, email: u.email.toLowerCase(), id: uid(), createdAt: now() };
        db.users.push(user);
        return user;
      });
    },
    async listSkills() {
      const db = load();
      return db.skills
        .map((s) => {
          const vs = db.versions.filter((v) => v.slug === s.slug).sort((a, b) => b.submittedAt.localeCompare(a.submittedAt));
          const ref = vs.find((v) => v.status === 'approved') ?? vs[0];
          const fm = (ref?.frontmatter ?? {}) as { kind?: string; skills?: unknown[] };
          return {
            ...s,
            kind: fm.kind === 'pack' ? ('pack' as const) : ('skill' as const),
            skillCount: Array.isArray(fm.skills) ? fm.skills.length : 1,
            fileCount: ref?.files.length ?? 0,
            latestApproved: vs.find((v) => v.status === 'approved')?.version ?? null,
            pending: vs.filter((v) => v.status === 'pending').length,
            versions: vs.length,
          };
        })
        .sort((a, b) => a.slug.localeCompare(b.slug));
    },
    async getSkill(slug) { return load().skills.find((s) => s.slug === slug) ?? null; },
    async upsertSkill(s) {
      mutate((db) => {
        const i = db.skills.findIndex((x) => x.slug === s.slug);
        if (i >= 0) db.skills[i] = { ...db.skills[i], name: s.name, description: s.description };
        else db.skills.push(s);
      });
    },
    async listVersions(slug) {
      return load().versions.filter((v) => v.slug === slug).sort((a, b) => b.submittedAt.localeCompare(a.submittedAt));
    },
    async getVersion(id) { return load().versions.find((v) => v.id === id) ?? null; },
    async createVersion(v) {
      return mutate((db) => {
        if (db.versions.some((x) => x.slug === v.slug && x.version === v.version)) throw new Error('That version already exists.');
        const row = { ...v, id: uid() };
        db.versions.push(row);
        return row;
      });
    },
    async reviewVersion(id, status, reviewer, note) {
      mutate((db) => {
        const v = db.versions.find((x) => x.id === id);
        if (v) Object.assign(v, { status, reviewedBy: reviewer, reviewedAt: now(), reviewNote: note });
      });
    },
    async listPending() { return load().versions.filter((v) => v.status === 'pending').sort((a, b) => a.submittedAt.localeCompare(b.submittedAt)); },
    async listTokens() { return [...load().tokens].reverse(); },
    async createToken(t) {
      return mutate((db) => {
        const tok = { ...t, id: uid(), createdAt: now(), lastUsedAt: null, revoked: false };
        db.tokens.push(tok);
        return tok;
      });
    },
    async findTokenByHash(hash) { return load().tokens.find((t) => t.tokenHash === hash && !t.revoked) ?? null; },
    async touchToken(id) { mutate((db) => { const t = db.tokens.find((x) => x.id === id); if (t) t.lastUsedAt = now(); }); },
    async revokeToken(id) { mutate((db) => { const t = db.tokens.find((x) => x.id === id); if (t) t.revoked = true; }); },
    async audit(e) { mutate((db) => { db.audit.push({ ...e, id: uid(), ts: now() }); }); },
    async listAudit(limit) { return [...load().audit].reverse().slice(0, limit); },
    async upsertTelemetry(t) {
      mutate((db) => {
        db.telemetry = (db.telemetry ?? []).filter((x) => !(x.project === t.project && x.runId === t.runId));
        db.telemetry.push({ ...t, id: uid(), receivedAt: now() });
      });
    },
    async listTelemetry(limit) {
      return [...(load().telemetry ?? [])].sort((a, b) => b.receivedAt.localeCompare(a.receivedAt)).slice(0, limit);
    },
  };
}

/* -------------------------------------------------------------------------- */
/* Selection                                                                   */
/* -------------------------------------------------------------------------- */

const globalForStore = globalThis as unknown as { __lsStore?: Store };

export function store(): Store {
  if (globalForStore.__lsStore) return globalForStore.__lsStore;
  const url = process.env.DATABASE_URL || process.env.POSTGRES_URL;
  if (!url && process.env.VERCEL) {
    throw new Error('Registry storage is not configured. Add a Postgres database (e.g. Neon) and set DATABASE_URL.');
  }
  globalForStore.__lsStore = url ? pgStore(url) : fileStore(process.env.REGISTRY_DATA_DIR || path.join(process.cwd(), '.data'));
  return globalForStore.__lsStore;
}

export const storageKind = () => (process.env.DATABASE_URL || process.env.POSTGRES_URL ? 'postgres' : 'file');
