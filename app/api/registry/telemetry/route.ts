import { NextResponse } from 'next/server';

import { authenticateToken } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';

export const dynamic = 'force-dynamic';

const SCHEMA = 'lockstep-telemetry-1.0';
// The same fixed schema the client enforces: numbers, IDs and agent/model names only.
const SAFE = new Set(['schema', 'generated_at', 'project', 'run_id', 'pack', 'name', 'version', 'run', 'status', 'elapsed_h', 'phases', 'phase', 'runs',
  'time_in_phase_h', 'approval_wait_h', 'rejections', 'gate_requests', 'denied_approvals', 'build', 'units', 'bolts', 'tests_passed',
  'evaluation', 'verdict', 'cases', 'metrics_total', 'metrics_passed', 'routing', 'agents', 'models', 'policy', 'blocks', 'checks_failed',
  'changes', 'count', 'by_type', 'outcomes', 'success_criteria', 'met']);

function unsafe(v: unknown, path: string): string | null {
  if (Array.isArray(v)) {
    for (const x of v) { const bad = unsafe(x, path); if (bad) return bad; }
    return null;
  }
  if (v && typeof v === 'object') {
    for (const [k, x] of Object.entries(v)) {
      if (path.endsWith('by_type') ? !/^[a-z_]{1,20}$/.test(k) : !SAFE.has(k)) return `unexpected field ${path}.${k}`;
      const bad = unsafe(x, `${path}.${k}`);
      if (bad) return bad;
    }
    return null;
  }
  if (typeof v === 'string' && v.length > 64) return `${path} is too long`;
  return null;
}

/** POST /api/registry/telemetry: opt-in delivery metrics from metrics.py push. */
export async function POST(req: Request) {
  const token = await authenticateToken(req.headers.get('authorization'));
  if (!token) return NextResponse.json({ error: 'A valid API token is required.' }, { status: 401 });
  const raw = await req.text();
  if (raw.length > 64 * 1024) return NextResponse.json({ error: 'Payload too large.' }, { status: 413 });
  let body: Record<string, unknown>;
  try {
    body = JSON.parse(raw);
  } catch {
    return NextResponse.json({ error: 'Invalid JSON.' }, { status: 400 });
  }
  if (body.schema !== SCHEMA) return NextResponse.json({ error: `Expected schema ${SCHEMA}.` }, { status: 400 });
  const bad = unsafe(body, '');
  if (bad) return NextResponse.json({ error: `Rejected: ${bad}. Telemetry may only contain metrics.` }, { status: 400 });
  if (typeof body.project !== 'string' || typeof body.run_id !== 'string') return NextResponse.json({ error: 'project and run_id are required.' }, { status: 400 });
  await store().upsertTelemetry({ tokenName: token.name, project: body.project, runId: body.run_id, payload: body });
  await store().audit({ actor: `token:${token.name}`, action: 'telemetry.received', target: body.project, detail: body.run_id });
  return NextResponse.json({ ok: true });
}
