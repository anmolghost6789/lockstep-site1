import 'server-only';

import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

import { store } from './store';
import { hashPassword } from './auth';
import { validateSkill } from './validate';

/** Packs shipped with the site and imported on first run. */
const SEED_PACKS = ['adlc-agent', 'packs/discovery-agent', 'packs/requirements-agent', 'packs/design-agent', 'packs/build-agent'];
const BINARY = /\.(png|jpe?g|gif|webp|ico|pdf|xlsx|xlsm|xls|docx|pptx|zip|gz|woff2?|ttf)$/i;
let seeding: Promise<void> | null = null;

function readDir(dir: string, base = dir): { path: string; content: string; encoding: 'utf8' | 'base64' }[] {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (e.name === '__pycache__' || e.name === '.DS_Store' || e.name === 'node_modules') return [];
    const full = path.join(dir, e.name);
    if (e.isDirectory()) return readDir(full, base);
    const rel = path.relative(base, full).split(path.sep).join('/');
    const binary = BINARY.test(e.name);
    return [{ path: rel, content: fs.readFileSync(full).toString(binary ? 'base64' : 'utf8'), encoding: binary ? 'base64' : 'utf8' }];
  });
}

export function digest(files: { path: string; content: string; encoding?: string }[]): string {
  const h = crypto.createHash('sha256');
  // Code-point order, not locale order, so the checksum is identical on every server and in the Python client.
  for (const f of [...files].sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0))) h.update(f.path).update('\0').update(f.encoding ?? 'utf8').update('\0').update(f.content).update('\0');
  return h.digest('hex');
}

/**
 * First-run setup: creates the admin from ADMIN_EMAIL / ADMIN_PASSWORD, and imports the
 * packs shipped with the site (adlc-agent/ and packs/) as approved version 1.0.0.
 */
export function ensureSeeded(): Promise<void> {
  return (seeding ??= (async () => {
    const s = store();
    if ((await s.countUsers()) === 0 && process.env.ADMIN_EMAIL && process.env.ADMIN_PASSWORD) {
      await s.createUser({ email: process.env.ADMIN_EMAIL, name: 'Administrator', role: 'admin', passwordHash: hashPassword(process.env.ADMIN_PASSWORD) });
      await s.audit({ actor: 'system', action: 'user.created', target: process.env.ADMIN_EMAIL, detail: 'Initial administrator' });
    }
    // Import any shipped pack the registry doesn't have yet, so new packs appear in existing registries too.
    const existing = new Set((await s.listSkills()).map((k) => k.slug));
    let imported = 0;
    for (const rel of SEED_PACKS) {
      const dir = path.join(process.cwd(), rel);
      if (!fs.existsSync(dir)) continue;
      const files = readDir(dir);
      const manifestFile = files.find((f) => f.path === 'lockstep-pack.json');
      const version = (manifestFile && JSON.parse(manifestFile.content).version) || '1.0.0';
      const v = validateSkill(files, version, null);
      if (existing.has(v.name)) continue;
      if (!v.ok) {
        console.error(`Registry seed: ${rel} failed validation`, v.errors);
        continue;
      }
      const ts = new Date().toISOString();
      await s.upsertSkill({ slug: v.name, name: v.name, description: v.description, createdBy: 'system', createdAt: ts });
      await s.createVersion({
        slug: v.name, version, status: 'approved', files: v.files, frontmatter: v.frontmatter,
        sha256: digest(v.files), note: 'Initial pack', submittedBy: 'system', submittedAt: ts,
        reviewedBy: 'system', reviewedAt: ts, reviewNote: 'Shipped with Lockstep',
      });
      imported++;
    }
    if (imported) await s.audit({ actor: 'system', action: 'registry.seeded', target: 'packs', detail: `Imported ${imported} shipped pack(s)` });
  })().catch((e) => { seeding = null; throw e; }));
}
