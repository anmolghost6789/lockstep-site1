import { ArrowRight, CornerLeftDown } from 'lucide-react';

import { AnimateEnter } from '@/app/home/AnimateEnter';
import { cn } from '@/lib/utils';
import { CardCaption, SectionLabel } from './section-label';
import { FlowPulse } from './flow-pulse';

type Kind = 'human' | 'step' | 'agent';

function Node({ label, kind }: { label: string; kind: Kind }) {
  return (
    <span
      className={cn(
        'inline-flex h-10 items-center rounded-lg px-3.5 font-inter text-[13px] whitespace-nowrap',
        kind === 'agent' && 'bg-neutral-900 font-medium text-white dark:bg-white dark:text-neutral-900',
        kind === 'human' && 'border border-[#f9452d]/30 bg-[#f9452d]/[0.06] text-[#c2321e] dark:border-[#E1F435]/30 dark:bg-[#E1F435]/[0.08] dark:text-[#E1F435]',
        kind === 'step' && 'border border-black/[0.08] bg-white text-neutral-800 dark:border-white/[0.09] dark:bg-[#0B0B0D] dark:text-neutral-200',
      )}
    >
      {label}
    </span>
  );
}

function Flow({ nodes }: { nodes: [string, Kind][] }) {
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-3">
      {nodes.map(([label, kind], i) => (
        <span key={label + i} className="inline-flex items-center gap-2">
          <Node label={label} kind={kind} />
          {i < nodes.length - 1 && <ArrowRight aria-hidden className="size-3.5 shrink-0 text-neutral-400" />}
        </span>
      ))}
    </div>
  );
}

export function HeadingSection() {
  return (
    <section id="direction" className="container scroll-mt-16 py-16">
      <AnimateEnter duration={0.55} className="flex flex-col gap-3">
        <SectionLabel>Where delivery is heading</SectionLabel>
        <h2 className="font-spectral text-[24px] leading-[28.8px] tracking-[-1px] text-[#2d2f2e] dark:text-neutral-100">
          AI is changing how teams deliver software,
          <br />
          not just how they write code
        </h2>
      </AnimateEnter>

      <div className="mt-10 grid gap-6">
        <AnimateEnter duration={0.55}>
          <CardCaption>today</CardCaption>
          <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]">
            <Flow nodes={[['Business', 'human'], ['Developer', 'step'], ['Code', 'step'], ['CI/CD', 'step'], ['Production', 'step']]} />
            <p className="mt-4 font-inter text-[13px] text-neutral-500 dark:text-neutral-400">
              AI helps individual developers write code faster. The delivery process around them stays the same.
            </p>
          </div>
        </AnimateEnter>

        <AnimateEnter duration={0.55} delay={0.06}>
          <CardCaption>next</CardCaption>
          <div className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]">
            <FlowPulse
              nodes={[
                ['Business', 'human'],
                ['Intent', 'step'],
                ['Requirements agents', 'agent'],
                ['Architecture agents', 'agent'],
                ['Coding agents', 'agent'],
                ['Evaluation agents', 'agent'],
                ['Release agents', 'agent'],
                ['Production', 'step'],
                ['Observability agents', 'agent'],
                ['New intent', 'step'],
              ]}
            />
            <p className="mt-4 flex items-center gap-1.5 font-inter text-[13px] text-neutral-500 dark:text-neutral-400">
              <CornerLeftDown aria-hidden className="size-3.5 text-[#f9452d] dark:text-[#E1F435]" />
              The new intent starts the next cycle. Agents do most of the steps; your people decide, approve and steer.
            </p>
          </div>
        </AnimateEnter>

        <AnimateEnter duration={0.55} delay={0.1}>
          <div className="rounded-2xl bg-neutral-900 px-6 py-5 dark:bg-white">
            <p className="font-spectral text-[20px] leading-[1.35] tracking-[-0.4px] text-white dark:text-neutral-900">
              Every arrow is a handoff between agents that has to be orchestrated, evidenced and approved by the right people.
              Lockstep is the system that does that.
            </p>
          </div>
        </AnimateEnter>
      </div>
    </section>
  );
}

const QUESTIONS: { q: string; a: string; where: string; available: boolean }[] = [
  { q: 'What should be built?', a: 'A requirement spec with measurable success criteria, approved by the product owner.', where: 'Phase 01', available: true },
  { q: 'How should it be built?', a: 'A blueprint, Level-1 plan and architecture decisions, approved by an architect.', where: 'Phase 02', available: true },
  { q: 'Which agents can do it?', a: 'Routing work to agents and models by capability, cost and policy.', where: 'Roadmap', available: false },
  { q: 'What evidence is required?', a: 'Policy checks, validation and evaluation thresholds set in the spec.', where: 'Phases 03–04', available: true },
  { q: 'Who approves it?', a: 'Named-role gates as pull request reviews in your GitHub.', where: 'Every phase', available: true },
  { q: 'Did it work?', a: 'Outcome tracking against the success criteria after release.', where: 'Roadmap', available: false },
  { q: 'What happens next?', a: 'An improvement backlog that becomes the next intent.', where: 'Phase 06', available: true },
];

export function QuestionsSection() {
  return (
    <section id="questions" className="container scroll-mt-16 py-16">
      <AnimateEnter duration={0.55} className="flex flex-col gap-3">
        <SectionLabel>What Lockstep answers</SectionLabel>
        <h2 className="font-spectral text-[24px] leading-[28.8px] tracking-[-1px] text-[#2d2f2e] dark:text-neutral-100">
          Seven questions every AI-driven
          <br />
          delivery system has to answer
        </h2>
        <p className="max-w-[560px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
          Five are answered today. Routing and outcome tracking are next, and design partners help shape them.
        </p>
      </AnimateEnter>

      <AnimateEnter duration={0.55} className="mt-10">
        <ol className="divide-y divide-black/[0.06] overflow-hidden rounded-2xl border border-black/[0.08] bg-white shadow-xs dark:divide-white/[0.07] dark:border-white/[0.09] dark:bg-[#0B0B0D]">
          {QUESTIONS.map((item, i) => (
            <li key={item.q} className="grid gap-x-6 gap-y-1 px-5 py-4 md:grid-cols-[32px_minmax(0,0.9fr)_minmax(0,1.6fr)_110px_120px] md:items-center">
              <span className="hidden font-mono text-[12px] text-neutral-400 md:block">{i + 1}</span>
              <span className="font-spectral text-[18px] leading-[1.3] tracking-[-0.4px] text-[#080808] dark:text-neutral-100">{item.q}</span>
              <span className="font-inter text-[13.5px] leading-[1.5] text-neutral-600 dark:text-neutral-400">{item.a}</span>
              <span className="font-mono text-[11px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">{item.where}</span>
              <span className="md:justify-self-end">
                <span
                  className={cn(
                    'inline-flex h-6 items-center rounded-full px-3 font-inter text-[11.5px] font-medium',
                    item.available
                      ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900'
                      : 'border border-[#f9452d]/60 text-[#c2321e] dark:border-[#E1F435]/60 dark:text-[#E1F435]',
                  )}
                >
                  {item.available ? 'Available' : 'Coming next'}
                </span>
              </span>
            </li>
          ))}
        </ol>
      </AnimateEnter>
    </section>
  );
}
