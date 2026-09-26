import 'server-only';

import crypto from 'node:crypto';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

import { store, type Role, type User } from './store';
import { ensureSeeded } from './seed';

const COOKIE = 'ls_session';
const MAX_AGE = 60 * 60 * 12; // 12 hours
const RANK: Record<Role, number> = { viewer: 0, publisher: 1, admin: 2 };

function secret(): string {
  const s = process.env.SESSION_SECRET;
  if (s && s.length >= 32) return s;
  if (process.env.NODE_ENV === 'production') {
    throw new Error('SESSION_SECRET must be set to at least 32 characters in production.');
  }
  return 'dev-only-session-secret-change-me-please-000';
}

export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `scrypt:${salt}:${hash}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const [, salt, hash] = stored.split(':');
  if (!salt || !hash) return false;
  const test = crypto.scryptSync(password, salt, 64);
  const expected = Buffer.from(hash, 'hex');
  return expected.length === test.length && crypto.timingSafeEqual(expected, test);
}

function sign(payload: string): string {
  return crypto.createHmac('sha256', secret()).update(payload).digest('base64url');
}

export async function createSession(user: User) {
  const payload = Buffer.from(JSON.stringify({ uid: user.id, exp: Date.now() + MAX_AGE * 1000 })).toString('base64url');
  (await cookies()).set(COOKIE, `${payload}.${sign(payload)}`, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: MAX_AGE,
  });
}

export async function destroySession() {
  (await cookies()).delete(COOKIE);
}

export async function currentUser(): Promise<User | null> {
  await ensureSeeded();
  const raw = (await cookies()).get(COOKIE)?.value;
  if (!raw) return null;
  const [payload, sig] = raw.split('.');
  if (!payload || !sig) return null;
  const expected = sign(payload);
  if (expected.length !== sig.length || !crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(sig))) return null;
  const { uid, exp } = JSON.parse(Buffer.from(payload, 'base64url').toString());
  if (Date.now() > exp) return null;
  return store().getUser(uid);
}

export async function requireUser(min: Role = 'viewer'): Promise<User> {
  const user = await currentUser();
  if (!user) redirect('/registry/login');
  if (RANK[user.role] < RANK[min]) redirect('/registry?denied=1');
  return user;
}

export const can = (user: User, min: Role) => RANK[user.role] >= RANK[min];

export function hashToken(token: string): string {
  return crypto.createHash('sha256').update(token).digest('hex');
}

/** Bearer-token check for the extension-facing API. */
export async function authenticateToken(header: string | null) {
  await ensureSeeded();
  const token = header?.match(/^Bearer\s+(.+)$/i)?.[1]?.trim();
  if (!token) return null;
  const found = await store().findTokenByHash(hashToken(token));
  if (found) await store().touchToken(found.id);
  return found;
}
