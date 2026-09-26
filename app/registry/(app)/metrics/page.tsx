import { requireUser } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';
import { summarise } from '@/lib/registry/benchmarks';
import { NumberTicker } from '@/components/motion/number-ticker';
import { SectionLabel } from '@/components/site/section-label';
import { card, h1 } from '@/components/registry/ui';
import { cn } from '@/lib/utils';

const pct = (x: number | null) => (x == null ? '–' : `${Math.round(x * 100)}%`);
const hrs = (x: number | null) => (x == null ? '–' : x < 1 ? `${Math.round(x * 60)} min` : `${x.toFixed(1)} h`);
const LABEL: Record<string, string> = {
  'discover-define': '01 Discover', 'architect-design': '02 Design', 'build-orchestrate': '03 Build',
  'evaluate-validate': '04 Evaluate', 'release-operate': '05 Release', 'observe-evolve': '06 Observe',
};

export default async function MetricsPage() {
  await requireUser('publisher');
  const rows = await store().listTelemetry(500);
  const m = summarise(rows);

  return (
    <>
      <div className="flex flex-col gap-3">
        <SectionLabel>Metrics</SectionLabel>
        <h1 className={h1}>How delivery is going</h1>
        <p className="max-w-[640px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
          Metrics that projects send with <code className="font-mono text-[12.5px]">metrics.py push</code>. Numbers and IDs only: no artifact text,
          code, prompts or personal data ever reach this page.
        </p>
      </div>

      {rows.length === 0 ? (
        <div className={cn(card, 'mt-8 p-6')}>
          <p className="text-[14px] font-medium text-neutral-900 dark:text-neutral-100">No runs reported yet.</p>
          <p className="mt-2 text-[13.5px] leading-[1.6] text-neutral-600 dark:text-neutral-400">From a project using the ADLC pack, create an API token in Settings, then run:</p>
          <pre className="mt-3 overflow-x-auto rounded-lg bg-neutral-50 p-3 font-mono text-[12px] text-neutral-800 dark:bg-white/[0.04] dark:text-neutral-200">
            python3 .claude/skills/adlc/scripts/metrics.py push --registry https://your-registry --token lsk_…
          </pre>
        </div>
      ) : (
        <>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {[
              ['Runs reported', m.totals.runs, ''],
              ['Projects', m.totals.projects, ''],
              ['Evaluations passed', m.totals.evalPassRate == null ? null : Math.round(m.totals.evalPassRate * 100), '%'],
              ['Success criteria met', m.totals.scMetRate == null ? null : Math.round(m.totals.scMetRate * 100), '%'],
              ['Policy blocks', m.totals.policyBlocks, ''],
            ].map(([label, value, suffix]) => (
              <div key={label as string} className={cn(card, 'p-4')}>
                <p className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400">{label}</p>
                <p className="mt-2 font-spectral text-[32px] leading-none text-[#080808] dark:text-neutral-100">
                  {value == null ? '–' : <NumberTicker value={value as number} suffix={suffix as string} />}
                </p>
              </div>
            ))}
          </div>

          <section className="mt-10">
            <h2 className="mb-3 text-[16px] font-medium text-neutral-900 dark:text-neutral-100">By phase (medians across runs)</h2>
            <div className={cn(card, 'overflow-x-auto')}>
              <table className="w-full min-w-[640px] text-left text-[13px]">
                <thead className="bg-neutral-50 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-500 dark:bg-white/[0.03]">
                  <tr>
                    <th className="px-4 py-2.5 font-medium">Phase</th>
                    <th className="px-4 py-2.5 font-medium">Time in phase</th>
                    <th className="px-4 py-2.5 font-medium">Waiting for approval</th>
                    <th className="px-4 py-2.5 font-medium">Gates rejected</th>
                    <th className="px-4 py-2.5 font-medium">Samples</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black/[0.06] dark:divide-white/[0.07]">
                  {m.phases.map((p) => (
                    <tr key={p.id}>
                      <td className="px-4 py-2.5 font-medium text-neutral-900 dark:text-neutral-100">{LABEL[p.id]}</td>
                      <td className="px-4 py-2.5 tabular-nums text-neutral-700 dark:text-neutral-300">{hrs(p.timeInPhase)}</td>
                      <td className="px-4 py-2.5 tabular-nums text-neutral-700 dark:text-neutral-300">{hrs(p.approvalWait)}</td>
                      <td className="px-4 py-2.5 tabular-nums text-neutral-700 dark:text-neutral-300">{pct(p.rejectionRate)}</td>
                      <td className="px-4 py-2.5 tabular-nums text-neutral-500">{p.samples}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="mt-10">
            <h2 className="mb-1 text-[16px] font-medium text-neutral-900 dark:text-neutral-100">Projects, benchmarked</h2>
            <p className="mb-3 text-[13px] text-neutral-500">Each project’s latest run, compared with the median time of completed runs across every project in this registry ({hrs(m.totals.elapsedMedian)}). Runs still in progress are shown but not benchmarked.</p>
            <div className={cn(card, 'overflow-x-auto')}>
              <table className="w-full min-w-[760px] text-left text-[13px]">
                <thead className="bg-neutral-50 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-500 dark:bg-white/[0.03]">
                  <tr>
                    <th className="px-4 py-2.5 font-medium">Project</th>
                    <th className="px-4 py-2.5 font-medium">Pack</th>
                    <th className="px-4 py-2.5 font-medium">Status</th>
                    <th className="px-4 py-2.5 font-medium">Run time</th>
                    <th className="px-4 py-2.5 font-medium">vs median</th>
                    <th className="px-4 py-2.5 font-medium">Approval wait</th>
                    <th className="px-4 py-2.5 font-medium">Evaluation</th>
                    <th className="px-4 py-2.5 font-medium">Criteria met</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black/[0.06] dark:divide-white/[0.07]">
                  {m.projects.map((p) => (
                    <tr key={p.project}>
                      <td className="px-4 py-2.5">
                        <span className="font-mono text-[12px] text-neutral-900 dark:text-neutral-100">{p.project}</span>
                        <span className="block text-[11.5px] text-neutral-500">{p.source}</span>
                      </td>
                      <td className="px-4 py-2.5 font-mono text-[12px] text-neutral-600 dark:text-neutral-400">{p.pack}</td>
                      <td className="px-4 py-2.5 text-neutral-700 dark:text-neutral-300">{p.status}</td>
                      <td className="px-4 py-2.5 tabular-nums text-neutral-700 dark:text-neutral-300">{hrs(p.elapsed)}</td>
                      <td className={cn('px-4 py-2.5 tabular-nums', p.vsMedian == null ? 'text-neutral-500' : p.vsMedian <= 0 ? 'text-emerald-700 dark:text-emerald-400' : 'text-amber-700 dark:text-amber-400')}>
                        {p.vsMedian == null ? '–' : `${p.vsMedian <= 0 ? '' : '+'}${Math.round(p.vsMedian * 100)}%`}
                      </td>
                      <td className="px-4 py-2.5 tabular-nums text-neutral-700 dark:text-neutral-300">{hrs(p.approvalWait)}</td>
                      <td className="px-4 py-2.5 text-neutral-700 dark:text-neutral-300">{p.verdict ?? '–'}</td>
                      <td className="px-4 py-2.5 tabular-nums text-neutral-700 dark:text-neutral-300">{p.scMet}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {m.agents.length > 0 && (
            <section className="mt-10">
              <h2 className="mb-3 text-[16px] font-medium text-neutral-900 dark:text-neutral-100">Agents used</h2>
              <div className="flex flex-wrap gap-2">
                {m.agents.map(([a, n]) => (
                  <span key={a} className="rounded-full border border-black/10 px-3 py-1 font-mono text-[12px] text-neutral-700 dark:border-white/10 dark:text-neutral-300">
                    {a} <span className="text-neutral-400">· {n} runs</span>
                  </span>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </>
  );
}
