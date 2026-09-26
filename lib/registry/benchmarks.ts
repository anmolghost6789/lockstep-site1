import type { TelemetryRun } from './store';

type Phase = { phase: string; time_in_phase_h: number | null; approval_wait_h: number | null; rejections: number; gate_requests: number };
type Payload = {
  project: string;
  run_id: string;
  pack?: { name?: string; version?: string };
  run?: { status?: string; elapsed_h?: number | null };
  phases?: Phase[];
  evaluation?: { verdict?: string | null; metrics_passed?: number; metrics_total?: number };
  routing?: { agents?: string[]; models?: string[] };
  policy?: { blocks?: number };
  changes?: { count?: number };
  outcomes?: { success_criteria?: number; met?: number };
};

export const PHASE_ORDER = ['discover-define', 'architect-design', 'build-orchestrate', 'evaluate-validate', 'release-operate', 'observe-evolve'];

export function median(xs: number[]): number | null {
  const v = xs.filter((x) => Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2;
}

export function summarise(rows: TelemetryRun[]) {
  const runs = rows.map((r) => r.payload as unknown as Payload);
  const projects = new Set(runs.map((r) => r.project));
  const withVerdict = runs.filter((r) => r.evaluation?.verdict);
  const sc = runs.reduce((a, r) => ({ total: a.total + (r.outcomes?.success_criteria ?? 0), met: a.met + (r.outcomes?.met ?? 0) }), { total: 0, met: 0 });

  const phases = PHASE_ORDER.map((id) => {
    const ps = runs.flatMap((r) => (r.phases ?? []).filter((p) => p.phase === id));
    const requests = ps.reduce((a, p) => a + (p.gate_requests ?? 0), 0);
    const rejections = ps.reduce((a, p) => a + (p.rejections ?? 0), 0);
    return {
      id,
      timeInPhase: median(ps.map((p) => p.time_in_phase_h ?? NaN)),
      approvalWait: median(ps.map((p) => p.approval_wait_h ?? NaN)),
      rejectionRate: requests ? rejections / requests : null,
      samples: ps.filter((p) => p.time_in_phase_h != null).length,
    };
  });

  const agentCounts: Record<string, number> = {};
  for (const r of runs) for (const a of r.routing?.agents ?? []) agentCounts[a] = (agentCounts[a] ?? 0) + 1;

  // Benchmarks compare finished runs only; an in-progress run would drag the median down.
  const done = (p: Payload) => p.run?.status === 'completed';
  const elapsedMedian = median(runs.filter(done).map((r) => r.run?.elapsed_h ?? NaN));
  const latestByProject = new Map<string, { row: TelemetryRun; p: Payload }>();
  for (const row of rows) {
    const p = row.payload as unknown as Payload;
    if (!latestByProject.has(p.project)) latestByProject.set(p.project, { row, p });
  }
  const projectRows = [...latestByProject.values()].map(({ row, p }) => {
    const elapsed = p.run?.elapsed_h ?? null;
    const wait = (p.phases ?? []).reduce((a, x) => a + (x.approval_wait_h ?? 0), 0);
    const vsMedian = done(p) && elapsed != null && elapsedMedian ? (elapsed - elapsedMedian) / elapsedMedian : null;
    return {
      project: p.project,
      source: row.tokenName,
      pack: `${p.pack?.name ?? '?'} ${p.pack?.version ?? ''}`.trim(),
      status: p.run?.status ?? 'unknown',
      elapsed,
      approvalWait: wait,
      verdict: p.evaluation?.verdict ?? null,
      scMet: p.outcomes?.success_criteria ? `${p.outcomes.met ?? 0}/${p.outcomes.success_criteria}` : '-',
      vsMedian,
      receivedAt: row.receivedAt,
    };
  });

  return {
    totals: {
      runs: runs.length,
      projects: projects.size,
      evalPassRate: withVerdict.length ? withVerdict.filter((r) => r.evaluation?.verdict === 'pass').length / withVerdict.length : null,
      scMetRate: sc.total ? sc.met / sc.total : null,
      policyBlocks: runs.reduce((a, r) => a + (r.policy?.blocks ?? 0), 0),
      changes: runs.reduce((a, r) => a + (r.changes?.count ?? 0), 0),
      elapsedMedian,
    },
    phases,
    agents: Object.entries(agentCounts).sort((a, b) => b[1] - a[1]),
    projects: projectRows,
  };
}
