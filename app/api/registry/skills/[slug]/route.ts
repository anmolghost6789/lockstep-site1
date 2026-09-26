import { NextResponse } from 'next/server';

import { authenticateToken } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';

export const dynamic = 'force-dynamic';

/** GET /api/registry/skills/:name?version=1.2.3 : an approved version's files. Defaults to the latest approved. */
export async function GET(req: Request, { params }: { params: Promise<{ slug: string }> }) {
  if (!(await authenticateToken(req.headers.get('authorization')))) {
    return NextResponse.json({ error: 'A valid API token is required.' }, { status: 401 });
  }
  const { slug } = await params;
  const wanted = new URL(req.url).searchParams.get('version');
  const approved = (await store().listVersions(slug)).filter((v) => v.status === 'approved');
  const v = wanted ? approved.find((x) => x.version === wanted) : approved[0];
  if (!v) return NextResponse.json({ error: 'No approved version found.' }, { status: 404 });
  return NextResponse.json({ name: v.slug, version: v.version, sha256: v.sha256, frontmatter: v.frontmatter, files: v.files });
}
