import { NextResponse } from 'next/server';

import { authenticateToken } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';

export const dynamic = 'force-dynamic';

/** GET /api/registry/skills: approved packs and skills, with their latest approved version. */
export async function GET(req: Request) {
  if (!(await authenticateToken(req.headers.get('authorization')))) {
    return NextResponse.json({ error: 'A valid API token is required.' }, { status: 401 });
  }
  const skills = await store().listSkills();
  const out = [];
  for (const s of skills) {
    if (!s.latestApproved) continue;
    const v = (await store().listVersions(s.slug)).find((x) => x.status === 'approved' && x.version === s.latestApproved)!;
    const fm = v.frontmatter as { kind?: string; skills?: { name: string; description: string; path: string }[] };
    out.push({ name: s.name, kind: fm.kind ?? 'skill', description: s.description, version: v.version, sha256: v.sha256, files: v.files.length, skills: fm.skills ?? [] });
  }
  return NextResponse.json({ skills: out });
}
