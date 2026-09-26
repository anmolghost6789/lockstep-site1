'use server';

import crypto from 'node:crypto';
import { redirect } from 'next/navigation';
import { revalidatePath } from 'next/cache';

import { store, type Role } from '@/lib/registry/store';
import { createSession, destroySession, hashPassword, hashToken, requireUser, verifyPassword } from '@/lib/registry/auth';
import { ensureSeeded, digest } from '@/lib/registry/seed';
import { compareSemver, validateSkill, type IncomingFile } from '@/lib/registry/validate';

export interface FormState {
  error?: string;
  errors?: string[];
  warnings?: string[];
  ok?: string;
  token?: string;
  /** Submitted values, so a form can keep what the user typed after an error. */
  values?: Record<string, string>;
}

/* ---------------------------------------------------------------- session */

export async function login(_: FormState, form: FormData): Promise<FormState> {
  await ensureSeeded();
  const email = String(form.get('email') ?? '').trim();
  const password = String(form.get('password') ?? '');
  if (!email || !password) return { error: 'Enter your email and password.', values: { email } };
  const user = await store().getUserByEmail(email);
  if (!user || !verifyPassword(password, user.passwordHash)) {
    await store().audit({ actor: email, action: 'login.failed', target: 'registry', detail: '' });
    return { error: 'That email and password don’t match.', values: { email } };
  }
  await createSession(user);
  await store().audit({ actor: user.email, action: 'login', target: 'registry', detail: '' });
  redirect('/registry');
}

export async function logout() {
  await destroySession();
  redirect('/registry/login');
}

/* ---------------------------------------------------------------- skills */

export async function submitSkill(_: FormState, form: FormData): Promise<FormState> {
  const user = await requireUser('publisher');
  const version = String(form.get('version') ?? '').trim();
  const note = String(form.get('note') ?? '').trim().slice(0, 500);
  let files: IncomingFile[];
  try {
    files = JSON.parse(String(form.get('files') ?? '[]'));
    if (!Array.isArray(files)) throw new Error();
  } catch {
    return { error: 'The uploaded files could not be read. Try again.', values: { version, note } };
  }

  // Find the skill's latest version, if it already exists, from the SKILL.md name.
  const packMeta = { name: String(form.get('packName') ?? '').trim(), description: String(form.get('packDescription') ?? '').trim() };
  const pre = validateSkill(files, '0.0.0', null, packMeta);
  const existing = pre.name ? await store().getSkill(pre.name) : null;
  const versions = existing ? await store().listVersions(existing.slug) : [];
  const latest = versions.map((v) => v.version).sort((a, b) => compareSemver(b, a))[0] ?? null;

  const v = validateSkill(files, version, latest, packMeta);
  if (!v.ok) return { errors: v.errors, warnings: v.warnings, values: { version, note, ...packMeta } };
  if (versions.some((x) => x.status === 'pending')) {
    return { errors: [`${v.name} already has a version waiting for approval. Approve or reject it first.`], values: { version, note } };
  }

  const ts = new Date().toISOString();
  await store().upsertSkill({ slug: v.name, name: v.name, description: v.description, createdBy: existing?.createdBy ?? user.email, createdAt: existing?.createdAt ?? ts });
  const created = await store().createVersion({
    slug: v.name, version, status: 'pending', files: v.files, frontmatter: v.frontmatter, sha256: digest(v.files),
    note, submittedBy: user.email, submittedAt: ts, reviewedBy: null, reviewedAt: null, reviewNote: null,
  });
  await store().audit({ actor: user.email, action: 'version.submitted', target: `${v.name}@${version}`, detail: note });
  revalidatePath('/registry');
  redirect(`/registry/skills/${v.name}?v=${created.id}`);
}

export async function reviewVersion(_: FormState, form: FormData): Promise<FormState> {
  const user = await requireUser('admin');
  const id = String(form.get('id') ?? '');
  const decision = String(form.get('decision') ?? '');
  const note = String(form.get('note') ?? '').trim().slice(0, 500);
  const v = await store().getVersion(id);
  if (!v || v.status !== 'pending') return { error: 'This version is no longer waiting for review.' };
  if (v.submittedBy === user.email) {
    await store().audit({ actor: user.email, action: 'review.denied', target: `${v.slug}@${v.version}`, detail: 'separation of duties' });
    return { error: 'You submitted this version, so someone else has to review it.' };
  }
  if (decision === 'reject' && !note) return { error: 'Add a note explaining what needs to change.' };
  if (decision !== 'approve' && decision !== 'reject') return { error: 'Choose approve or reject.' };
  const status = decision === 'approve' ? 'approved' : 'rejected';
  await store().reviewVersion(id, status, user.email, note);
  await store().audit({ actor: user.email, action: `version.${status}`, target: `${v.slug}@${v.version}`, detail: note });
  revalidatePath('/registry');
  redirect(`/registry/skills/${v.slug}?v=${v.id}&reviewed=${status}`);
}

/* ---------------------------------------------------------------- admin */

export async function createToken(_: FormState, form: FormData): Promise<FormState> {
  const user = await requireUser('admin');
  const name = String(form.get('name') ?? '').trim().slice(0, 80);
  if (!name) return { error: 'Give the token a name, such as the team or environment using it.' };
  const token = `lsk_${crypto.randomBytes(24).toString('hex')}`;
  await store().createToken({ name, prefix: token.slice(0, 10), tokenHash: hashToken(token), createdBy: user.email });
  await store().audit({ actor: user.email, action: 'token.created', target: name, detail: '' });
  revalidatePath('/registry/settings');
  return { ok: 'Token created. Copy it now; it won’t be shown again.', token };
}

export async function revokeToken(form: FormData) {
  const user = await requireUser('admin');
  const id = String(form.get('id') ?? '');
  await store().revokeToken(id);
  await store().audit({ actor: user.email, action: 'token.revoked', target: id, detail: '' });
  revalidatePath('/registry/settings');
}

export async function createUser(_: FormState, form: FormData): Promise<FormState> {
  const admin = await requireUser('admin');
  const email = String(form.get('email') ?? '').trim().toLowerCase();
  const name = String(form.get('name') ?? '').trim();
  const role = String(form.get('role') ?? 'viewer') as Role;
  const password = String(form.get('password') ?? '');
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return { error: 'Enter a valid email address.', values: { email, name, role } };
  if (!name) return { error: 'Enter a name.', values: { email, name, role } };
  if (!['admin', 'publisher', 'viewer'].includes(role)) return { error: 'Choose a role.', values: { email, name, role } };
  if (password.length < 12) return { error: 'Use a temporary password of at least 12 characters.', values: { email, name, role } };
  if (await store().getUserByEmail(email)) return { error: 'A user with that email already exists.', values: { email, name, role } };
  await store().createUser({ email, name, role, passwordHash: hashPassword(password) });
  await store().audit({ actor: admin.email, action: 'user.created', target: email, detail: role });
  revalidatePath('/registry/settings');
  return { ok: `${name} can now sign in as ${role}.` };
}

/* ---------------------------------------------------------------- editing */

export interface EditState {
  error?: string;
  errors?: string[];
}

/**
 * Save edits made in the registry editor as a new pending version. Only changed or new text files are
 * sent; everything else (including binaries) is carried over from the base version, then the whole pack
 * is validated exactly as an upload would be.
 */
export async function saveEdits(input: {
  slug: string;
  baseVersionId: string;
  version: string;
  note: string;
  changed: { path: string; content: string }[];
  removed: string[];
}): Promise<EditState> {
  const user = await requireUser('publisher');
  const skill = await store().getSkill(input.slug);
  const base = await store().getVersion(input.baseVersionId);
  if (!skill || !base || base.slug !== input.slug) return { error: 'That version no longer exists.' };
  if (!input.changed.length && !input.removed.length) return { error: 'There are no changes to save.' };
  if (!input.note.trim()) return { error: 'Describe what changed, for the reviewer.' };
  const versions = await store().listVersions(input.slug);
  if (versions.some((x) => x.status === 'pending')) {
    return { error: `${input.slug} already has a version waiting for approval. Approve or reject it before saving another.` };
  }
  const latest = versions.map((v) => v.version).sort((a, b) => compareSemver(b, a))[0] ?? null;

  const files = new Map(base.files.map((f) => [f.path, { ...f }]));
  for (const p of input.removed) files.delete(p);
  for (const c of input.changed) {
    if (files.get(c.path)?.encoding === 'base64') return { error: `${c.path} is a binary file and can't be edited here.` };
    files.set(c.path, { path: c.path, content: c.content, encoding: 'utf8' });
  }
  const v = validateSkill([...files.values()], input.version.trim(), latest, { name: skill.name, description: skill.description });
  if (!v.ok) return { errors: v.errors };
  if (v.name !== input.slug) return { errors: [`The name in this version is "${v.name}", but you're editing "${input.slug}". Keep the name unchanged.`] };

  const created = await store().createVersion({
    slug: input.slug, version: input.version.trim(), status: 'pending', files: v.files, frontmatter: v.frontmatter,
    sha256: digest(v.files), note: input.note.trim().slice(0, 500), submittedBy: user.email, submittedAt: new Date().toISOString(),
    reviewedBy: null, reviewedAt: null, reviewNote: null,
  });
  await store().upsertSkill({ ...skill, description: v.description || skill.description });
  await store().audit({
    actor: user.email, action: 'version.edited', target: `${input.slug}@${input.version}`,
    detail: `from ${base.version}: ${input.changed.length} changed, ${input.removed.length} removed`,
  });
  revalidatePath('/registry');
  redirect(`/registry/skills/${input.slug}?v=${created.id}&edited=1`);
}
