import { ArrowRight, Check, FileCheck2, GitPullRequest, KeyRound, Layers } from 'lucide-react';

import { AnimateEnter } from '@/app/home/AnimateEnter';
import { PILOT_HREF, PILOT_LABEL } from '@/lib/site';
import { SectionLabel } from './section-label';
import { ShiftLoop } from './shift-loop';

const H2 = 'font-spectral text-[28px] leading-[1.15] tracking-[-1px] text-[#2d2f2e] dark:text-neutral-100 sm:text-[32px]';
const LEAD = 'max-w-[560px] font-inter text-[15px] leading-[1.6] text-[#646464] dark:text-neutral-400';

/* 2. The shift: the same lifecycle on a different engine, told as a loop you can flip. */
export function ShiftSection() {
  return (
    <section id="shift" className="container scroll-mt-16 py-20">
      <AnimateEnter duration={0.55} className="flex flex-col gap-3">
        <SectionLabel>The shift</SectionLabel>
        <h2 className={H2}>
          Same lifecycle.
          <br />
          A different engine.
        </h2>
        <p className={LEAD}>
          Software still moves from requirements to release. What changes is who does the work, and whether anyone can prove who approved
          each step.
        </p>
      </AnimateEnter>
      <AnimateEnter duration={0.55} delay={0.08} className="mt-10">
        <ShiftLoop />
      </AnimateEnter>
    </section>
  );
}

/* 4. Why teams trust it: four points instead of four sections. */
const TRUST = [
  { icon: GitPullRequest, title: 'Approvals by named people, in GitHub', body: 'Each phase ends as a pull request. CODEOWNERS routes it to the right team, and authors can’t approve their own work.' },
  { icon: FileCheck2, title: 'Evidence your auditors can use', body: 'Every phase leaves a versioned artifact and a traceable approval history you can export for audit.' },
  { icon: KeyRound, title: 'Runs on the Copilot you already have', body: 'No new model contract and no keys on laptops. Your existing Copilot policies still apply.' },
  { icon: Layers, title: 'Skill packs you control', body: 'Reviewed, versioned packs in a registry you can host yourself. Nothing reaches developers until it’s approved.' },
];

export function TrustSection() {
  return (
    <section id="trust" className="container scroll-mt-16 py-20">
      <AnimateEnter duration={0.55} className="flex flex-col gap-3">
        <SectionLabel>Why teams trust it</SectionLabel>
        <h2 className={H2}>Built for teams whose work gets audited</h2>
      </AnimateEnter>
      <div className="mt-10 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
        {TRUST.map(({ icon: Icon, title, body }, i) => (
          <AnimateEnter key={title} duration={0.55} delay={i * 0.05}>
            <div className="h-full rounded-2xl border border-black/[0.08] bg-white p-5 shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]">
              <span className="grid size-9 place-items-center rounded-lg bg-neutral-100 text-neutral-800 dark:bg-white/[0.07] dark:text-neutral-200">
                <Icon className="size-4" />
              </span>
              <h3 className="mt-4 font-spectral text-[19px] leading-[1.25] tracking-[-0.4px] text-[#080808] dark:text-neutral-100">{title}</h3>
              <p className="mt-2 font-inter text-[14px] leading-[1.6] text-neutral-600 dark:text-neutral-400">{body}</p>
            </div>
          </AnimateEnter>
        ))}
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
