'use client';

import * as React from 'react';
import { motion, useMotionValueEvent, useScroll, useSpring, useTransform, type MotionValue } from 'motion/react';
import { ArrowUpRight, CheckCircle2, FileText, UserCheck } from 'lucide-react';

import { cn } from '@/lib/utils';
import { ApprovalCard } from '@/components/spectrumui/blocks/ai-assistants/approval-card';
import { TextStates } from '@/components/spectrumui/text-states';
import type { PhaseSkill, SkillFile } from '@/lib/skills';
import { PhaseGrid, type PhaseCardData } from './skill-viewer';
import { SCENES, SHORT, trackChip, trackText, type RunStep } from './lifecycle-stage';

// Within each phase (0..1 of its scroll segment): write the artifact, then ask for approval, then approve.
const WRITE_END = 0.5;
const GATE_IN = 0.52;
const APPROVE_AT = 0.78;
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

function usePrefersReducedMotion() {
  const [reduced, setReduced] = React.useState(false);
  React.useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const on = () => setReduced(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return reduced;
}

export function LifecycleScroll({ cards, skills, common, header }: { cards: PhaseCardData[]; skills: PhaseSkill[]; common: SkillFile[]; header: React.ReactNode }) {
  const reduced = usePrefersReducedMotion();
  return (
    <>
      {reduced ? (
        <>
          {header}
          <div className="mt-10">
            <StaticJourney cards={cards} />
          </div>
        </>
      ) : (
        <Journey cards={cards} header={header} />
      )}
      {/* Supplies the skill panel for "Open skill" links (#skill-<id>); its own grid and rail are hidden. */}
      <PhaseGrid cards={cards} skills={skills} common={common} hideCards hideRail externalTick={-1} />
    </>
  );
}

/* -------------------------------------------------------------------------- */
/* Scroll journey                                                              */
/* -------------------------------------------------------------------------- */

function Journey({ cards, header }: { cards: PhaseCardData[]; header: React.ReactNode }) {
  const n = cards.length;
  const ref = React.useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end end'] });
  const smooth = useSpring(scrollYProgress, { stiffness: 140, damping: 30, mass: 0.4 });
  const [pos, setPos] = React.useState(0); // 0..n across the whole journey
  useMotionValueEvent(smooth, 'change', (v) => setPos(Math.min(n - 1e-6, Math.max(0, v * n))));

  const phase = Math.floor(pos);
  const q = pos - phase; // progress inside the current phase
  const stepOf = (i: number): RunStep => {
    if (i < phase) return 'approved';
    if (i > phase) return 'queued';
    return q < WRITE_END ? 'working' : q < APPROVE_AT ? 'waiting' : 'approved';
  };

  return (
    <div ref={ref} className="relative" style={{ height: `${n * 110 + 20}vh` }}>
      <div className="sticky top-14 flex h-[calc(100svh-3.5rem)] flex-col overflow-hidden pb-6 pt-8 sm:pt-12">
        {/* Parallax backdrop: the phase number drifts slower than the content. */}
        <Backdrop progress={smooth} phase={phase} n={n} />

        {/* The section header stays fixed while the phases play out below it. */}
        <div className="relative shrink-0">{header}</div>

        <div className="relative grid flex-1 grid-cols-1 items-center gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:gap-12">
          <PhaseCopy card={cards[phase]} index={phase} q={q} step={stepOf(phase)} />
          <PhaseWork card={cards[phase]} index={phase} q={q} />
        </div>
      </div>
    </div>
  );
}

function Backdrop({ progress, phase, n }: { progress: MotionValue<number>; phase: number; n: number }) {
  const y = useTransform(progress, [0, 1], ['8%', '-18%']);
  const dotsY = useTransform(progress, [0, 1], ['0%', '-12%']);
  return (
    <>
      <motion.div
        aria-hidden
        style={{ y: dotsY }}
        className="pointer-events-none absolute -inset-x-10 -inset-y-40 bg-[radial-gradient(circle,var(--color-border)_1px,transparent_1px)] bg-[size:26px_26px] opacity-60 [mask-image:radial-gradient(ellipse_at_center,black_40%,transparent_75%)]"
      />
      <motion.div aria-hidden style={{ y }} className="pointer-events-none absolute right-[-2%] top-[6%] select-none lg:right-[2%]">
        <motion.span
          key={phase}
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="block font-spectral text-[34vw] leading-none tracking-[-0.06em] text-neutral-900/[0.035] lg:text-[26vw] dark:text-white/[0.04]"
        >
          {String(phase + 1).padStart(2, '0')}
        </motion.span>
      </motion.div>
      <span className="sr-only">
        Phase {phase + 1} of {n}
      </span>
    </>
  );
}

function PhaseCopy({ card, index, q, step }: { card: PhaseCardData; index: number; q: number; step: RunStep }) {
  // Enters from below at the start of its segment, drifts up and fades as the next phase approaches.
  const enter = clamp01(q / 0.14);
  const exit = clamp01((q - 0.9) / 0.1);
  return (
    <motion.div key={card.id} className="relative min-w-0" style={{ opacity: enter * (1 - exit), transform: `translateY(${(1 - enter) * 28 - exit * 28}px)` }}>
      <p className="font-mono text-[12px] uppercase tracking-[0.06em] text-[#f9452d] dark:text-[#E1F435]">
        Phase {String(index + 1).padStart(2, '0')} · {SHORT[card.id]}
      </p>
      <h3 className="mt-3 font-spectral text-[32px] leading-[1.1] tracking-[-1px] text-[#080808] dark:text-neutral-50 sm:text-[42px]">{card.title}</h3>
      <ul className="mt-5 hidden space-y-2 sm:block">
        {card.points.map((p, i) => (
          <li
            key={p}
            className="flex gap-2.5 font-inter text-[15px] leading-[1.55] text-neutral-600 transition-all duration-500 dark:text-neutral-400"
            style={{ opacity: clamp01((q - 0.04 - i * 0.05) / 0.08), transform: `translateX(${(1 - clamp01((q - 0.04 - i * 0.05) / 0.08)) * -10}px)` }}
          >
            <span aria-hidden className="mt-[9px] size-1 shrink-0 rounded-full bg-neutral-400" />
            {p}
          </li>
        ))}
      </ul>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <span className={cn('inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 font-inter text-[13px] font-medium', trackChip(step))}>
          {step === 'approved' ? <CheckCircle2 className="size-3.5" /> : <UserCheck className="size-3.5" />}
          <TextStates text={trackText(card, step)} />
        </span>
        <a href={`#skill-${card.id}`} className="inline-flex items-center gap-1 font-mono text-[12px] text-neutral-500 hover:text-[#f9452d] dark:hover:text-[#E1F435]">
          Open skill <ArrowUpRight className="size-3" />
        </a>
      </div>
    </motion.div>
  );
}

function PhaseWork({ card, index, q }: { card: PhaseCardData; index: number; q: number }) {
  const scene = SCENES[index];
  const written = clamp01(q / WRITE_END);
  const shown = scene.artifact.slice(0, Math.round(scene.artifact.length * written));
  const writing = written < 1;
  const gateIn = clamp01((q - GATE_IN) / 0.1);
  const approved = q >= APPROVE_AT;
  const enter = clamp01(q / 0.12);
  const exit = clamp01((q - 0.92) / 0.08);

  return (
    <div className="relative min-w-0" style={{ opacity: enter * (1 - exit), transform: `translateY(${(1 - enter) * 60 - exit * 40}px)` }}>
      {/* Artifact, written as you scroll */}
      <div className="overflow-hidden rounded-2xl border border-black/[0.08] bg-white shadow-[0_24px_60px_-30px_rgba(0,0,0,0.25)] dark:border-white/[0.09] dark:bg-[#0B0B0D]">
        <div className="flex items-center gap-2 border-b border-black/[0.06] px-4 py-2.5 dark:border-white/[0.07]">
          <FileText className="size-3.5 text-neutral-400" />
          <span className="font-mono text-[12.5px] text-neutral-700 dark:text-neutral-300">{scene.file}</span>
          <span className={cn('ml-auto font-mono text-[10.5px] uppercase tracking-[0.04em]', writing ? 'text-[#f9452d] dark:text-[#E1F435]' : 'text-emerald-600 dark:text-emerald-400')}>
            {writing ? 'writing' : 'written'}
          </span>
        </div>
        <pre className="h-[176px] overflow-hidden whitespace-pre px-4 py-4 font-mono text-[12px] leading-[1.7] text-neutral-800 sm:h-[196px] sm:text-[12.5px] dark:text-neutral-200">
          {shown}
          {writing && <span className="ml-px inline-block h-[14px] w-[7px] translate-y-[2px] animate-pulse bg-[#f9452d] dark:bg-[#E1F435]" />}
        </pre>
      </div>

      {/* The gate slides in once the artifact is written, then gets approved */}
      <div
        inert
        className="relative -mt-6 ml-6 mr-[-4px] sm:ml-16 lg:ml-24"
        style={{ opacity: gateIn, transform: `translate(${(1 - gateIn) * 40}px, ${(1 - gateIn) * 12}px)` }}
      >
        <ApprovalCard
          key={`${card.id}-${approved}`}
          title={scene.gate.title}
          description={scene.gate.description}
          meta={`Pull request · CODEOWNERS: ${card.role}`}
          approveLabel="Approve"
          rejectLabel="Request changes"
          approvedMessage={`Approved by ${card.role}`}
          decision={approved ? 'approved' : null}
          className="max-w-none shadow-[0_24px_60px_-30px_rgba(0,0,0,0.3)]"
        />
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Reduced motion: the same journey, laid out in order, nothing pinned        */
/* -------------------------------------------------------------------------- */

function StaticJourney({ cards }: { cards: PhaseCardData[] }) {
  return (
    <ol className="space-y-10">
      {cards.map((card, i) => (
        <li key={card.id} className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-center lg:gap-12">
          <PhaseCopy card={card} index={i} q={0.5} step="approved" />
          <PhaseWork card={card} index={i} q={0.85} />
        </li>
      ))}
    </ol>
  );
}
