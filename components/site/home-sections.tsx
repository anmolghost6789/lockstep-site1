import { ArrowRight, Check, FileCheck2, Gauge, GitBranch, KeyRound, ShieldCheck, UserCheck } from 'lucide-react';

import { AnimateEnter } from '@/app/home/AnimateEnter';
import { PILOT_HREF, PILOT_LABEL } from '@/lib/site';
import { SectionLabel } from './section-label';
import { GateAuditTable } from './gate-audit-table';

const H2 = 'font-spectral text-[28px] leading-[1.15] tracking-[-1px] text-[#2d2f2e] dark:text-neutral-100 sm:text-[32px]';
const LEAD = 'max-w-[560px] font-inter text-[15px] leading-[1.6] text-[#646464] dark:text-neutral-400';

/* Governance: the controls that run with every phase, next to the evidence they leave behind. */
const CONTROLS = [
  { icon: UserCheck, title: 'Named-role approvals', body: 'The right team approves every phase in a pull request. Authors can’t approve their own work.' },
  { icon: ShieldCheck, title: 'Policy checks before every gate', body: 'Secrets, personal data, licences and SBOM evidence are checked before anyone is asked to approve.' },
  { icon: GitBranch, title: 'Traceability end to end', body: 'Every requirement is traced to the units, tests, metrics and release that satisfy it.' },
  { icon: Gauge, title: 'Evaluated against the spec', body: 'Thresholds come from the approved requirements, and the evaluator never built the code it tests.' },
  { icon: KeyRound, title: 'Approved tools and models only', body: 'MCP servers and models are allow-listed per phase. Runs on your Copilot, with no keys on laptops.' },
  { icon: FileCheck2, title: 'Evidence on demand', body: 'A tamper-evident log of every decision, exportable for SOC 2, ISO 27001 and ISO 42001 reviews.' },
];

export function GovernanceSection() {
  return (
    <section id="governance" className="container scroll-mt-16 py-20">
      <AnimateEnter duration={0.55} className="flex flex-col gap-3">
        <SectionLabel>Governance</SectionLabel>
        <h2 className={H2}>
          Governance that runs with the work, <br className="hidden sm:block" />
          not after it
        </h2>
        <p className={LEAD}>
          Every phase is checked, approved and recorded as it happens, so the evidence your risk and audit teams need already exists
          when they ask for it.
        </p>
      </AnimateEnter>
      <div className="mt-10 grid gap-8 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-10">
        <ul className="grid gap-x-6 gap-y-6 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          {CONTROLS.map(({ icon: Icon, title, body }, i) => (
            <AnimateEnter key={title} duration={0.5} delay={i * 0.04}>
              <li className="flex gap-3.5">
                <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-neutral-900 text-white dark:bg-white dark:text-neutral-900">
                  <Icon className="size-4" />
                </span>
                <div>
                  <h3 className="font-inter text-[15px] font-semibold text-[#080808] dark:text-neutral-100">{title}</h3>
                  <p className="mt-1 font-inter text-[13.5px] leading-[1.55] text-neutral-600 dark:text-neutral-400">{body}</p>
                </div>
              </li>
            </AnimateEnter>
          ))}
        </ul>
        <AnimateEnter duration={0.55} delay={0.1} className="min-w-0">
          <p className="mb-2.5 flex items-center gap-2 font-mono text-[11px] font-medium uppercase tracking-[0.04em] text-neutral-500 dark:text-neutral-400">
            <span aria-hidden className="h-[7px] w-[7px] border-l-2 border-t-2 border-[#f9452d] dark:border-[#E1F435]" />
            Audit log · every decision attributed
          </p>
          <GateAuditTable />
        </AnimateEnter>
      </div>
    </section>
  );
}

/* 5. The pilot offer: the one call to action. */
const WEEKS = [
  ['Week 1', 'Set up approvals, packs and your Copilot, with your platform team.'],
  ['Weeks 2–4', 'Take one real project from requirements to an evaluated build.'],
  ['Weeks 5–6', 'Release to a small group, observe, and review the results together.'],
];
const OUTCOMES = ['A working release of your project', 'Approval history your risk team can inspect', 'Cycle time compared with your baseline', 'A go / no-go decision on wider rollout'];

export function PilotSection() {
  return (
    <section id="pilot" className="container scroll-mt-16 py-20">
      <AnimateEnter duration={0.55}>
        <div className="overflow-hidden rounded-3xl bg-neutral-900 text-white dark:border dark:border-white/[0.09] dark:bg-[#0B0B0D]">
          <div className="grid gap-10 p-8 sm:p-10 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:p-12">
            <div>
              <span className="flex items-center gap-2.5 font-mono text-[12px] font-medium uppercase text-neutral-300">
                <span aria-hidden className="block size-[9px] -rotate-90 border-b-2 border-r-2 border-[#f9452d] dark:border-[#E1F435]" />
                The pilot
              </span>
              <h2 className="mt-3 font-spectral text-[32px] leading-[1.1] tracking-[-1px] sm:text-[40px]">
                One real project.
                <br />
                Four to six weeks.
              </h2>
              <ol className="mt-8 space-y-4">
                {WEEKS.map(([when, what]) => (
                  <li key={when} className="grid grid-cols-[92px_minmax(0,1fr)] gap-4">
                    <span className="font-mono text-[12px] uppercase tracking-[0.04em] text-[#f9452d] dark:text-[#E1F435]">{when}</span>
                    <span className="font-inter text-[15px] leading-[1.55] text-neutral-300">{what}</span>
                  </li>
                ))}
              </ol>
            </div>
            <div className="flex flex-col justify-between gap-8 rounded-2xl bg-white/[0.06] p-6">
              <div>
                <p className="font-inter text-[14px] font-medium text-neutral-300">What you have at the end</p>
                <ul className="mt-4 space-y-3">
                  {OUTCOMES.map((o) => (
                    <li key={o} className="flex gap-3 font-inter text-[15px] leading-[1.5] text-white">
                      <Check className="mt-1 size-4 shrink-0 text-[#f9452d] dark:text-[#E1F435]" strokeWidth={2.5} />
                      {o}
                    </li>
                  ))}
                </ul>
              </div>
              <a
                href={PILOT_HREF}
                className="group inline-flex h-12 items-center justify-center gap-2 rounded-full bg-white px-6 font-inter text-[15px] font-medium text-neutral-900 transition-[transform,background-color] duration-200 hover:bg-neutral-100 active:scale-[0.98]"
              >
                {PILOT_LABEL}
                <ArrowRight className="size-4 transition-transform duration-200 group-hover:translate-x-0.5" />
              </a>
            </div>
          </div>
        </div>
      </AnimateEnter>
    </section>
  );
}
