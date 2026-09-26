'use client';

import * as React from 'react';
import { animate, cubicBezier, motion } from 'motion/react';
import { ArrowUpRight, CheckCircle2, Clock3, FileText } from 'lucide-react';

import { cn } from '@/lib/utils';
import { ApprovalCard } from '@/components/spectrumui/blocks/ai-assistants/approval-card';
import { SkeletonReveal } from '@/components/spectrumui/skeleton-reveal';
import { TextStates } from '@/components/spectrumui/text-states';
import type { PhaseSkill, SkillFile } from '@/lib/skills';
import { PhaseGrid, type PhaseCardData } from './skill-viewer';

/* -------------------------------------------------------------------------- */
/* The run                                                                     */
/* -------------------------------------------------------------------------- */

export type RunStep = 'idle' | 'queued' | 'working' | 'waiting' | 'approved';

interface Beat {
  phase: number;
  step: 'working' | 'waiting' | 'approved' | 'done';
  ms: number;
}

/** What each phase writes and asks for, following the same KYC intent as the hero. */
const SCENES = [
  {
    file: 'adlc/01-aiprs.md',
    artifact: `## Success Criteria
| SC-001 | Median KYC review time | 3 days → same day |

## Non-Functional Requirements
| NFR-002 | High-risk cases need an analyst | 0 exceptions |
| NFR-003 | Watchlist screening recall      | ≥ 0.99       |`,
    gate: { title: 'Approve the requirements spec?', description: '5 user stories, 3 NFRs, and one success measure: same-day median review time.' },
  },
  {
    file: 'adlc/02-blueprint.md',
    artifact: `## Level-1 Plan
| UNIT-001 | Document intake agent | Trace: FR-001 |
| UNIT-002 | Watchlist screening   | Trace: FR-002 |
| UNIT-003 | Mismatch detector     | Trace: FR-003 |

ADR-001  Screening only via the approved provider`,
    gate: { title: 'Approve the blueprint?', description: '3 units, 2 agents, 1 architecture decision. Models from the approved list only.' },
  },
  {
    file: 'adlc/03-units.yaml',
    artifact: `- id: UNIT-002
  status: accepted
  bolts:
    - id: BOLT-004
      goal: sanctions and PEP screening
      tests_passed: 18
      trace: [FR-002, NFR-003]`,
    gate: { title: 'Accept the build?', description: '3 units, 9 bolts, 47 tests passing. Every diff reviewed in its own pull request.' },
  },
  {
    file: 'adlc/04-scorecard.json',
    artifact: `{
  "id": "EVAL-003",
  "name": "watchlist recall",
  "threshold": 0.99,
  "value": 0.994,
  "passed": true,
  "trace": ["NFR-003"]
}`,
    gate: { title: 'Sign the scorecard?', description: 'All 6 metrics pass on 400 past cases. Thresholds taken from the approved spec.' },
  },
  {
    file: 'adlc/05-release.md',
    artifact: `## Deployment Plan
Rollout 10% of new applications behind kyc_agent_v1

## Rollback Plan
Roll back if analyst override rate > 8%

Risk: high → security officer also approves`,
    gate: { title: 'Promote to production?', description: 'Pinned versions, rehearsed rollback, runbook attached. High risk adds a security review.' },
  },
  {
    file: 'adlc/06-backlog.md',
    artifact: `| OBS-001 | Median review time | 5.2 h | SC-001 met |
| OBS-002 | False positives on company names | rising |

| BL-001 | Tune company-name matching | next_intent |`,
    gate: { title: 'Choose the next intent?', description: 'Success criterion met. One drift finding becomes the next intent: BL-001.' },
  },
];

const buildPlan = (phases: number): Beat[] => [
  ...Array.from({ length: phases }, (_, phase) => [
    { phase, step: 'working' as const, ms: 4200 },
    { phase, step: 'waiting' as const, ms: 1700 },
    { phase, step: 'approved' as const, ms: 1500 },
  ]).flat(),
  { phase: phases - 1, step: 'done', ms: 2800 },
];

function useInView<T extends Element>(threshold = 0.2) {
  const ref = React.useRef<T>(null);
  const [inView, setInView] = React.useState(false);
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { threshold });
    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);
  return [ref, inView] as const;
}

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

/**
 * One run drives both views: the stage (camera flying across live cards, like the hero)
 * and the grid of phase cards below it.
 */
export function LifecycleShowcase({ cards, skills, common, compact = false }: { cards: PhaseCardData[]; skills: PhaseSkill[]; common: SkillFile[]; compact?: boolean }) {
  const plan = React.useMemo(() => buildPlan(cards.length), [cards.length]);
  const [ref, inView] = useInView<HTMLDivElement>(0.15);
  const reduced = usePrefersReducedMotion();
  const [beat, setBeat] = React.useState(0);
  const [started, setStarted] = React.useState(false);
  const [paused, setPaused] = React.useState(false);
  const [stageBusy, setStageBusy] = React.useState(false);
  const [gridBusy, setGridBusy] = React.useState(false);

  React.useEffect(() => {
    if (inView && !reduced) setStarted(true);
  }, [inView, reduced]);

  const running = started && inView && !paused && !stageBusy && !gridBusy && !reduced;
  React.useEffect(() => {
    if (!running) return;
    const t = setTimeout(() => setBeat((b) => (b + 1) % plan.length), plan[beat].ms);
    return () => clearTimeout(t);
  }, [running, beat, plan]);

  const current = plan[beat];
  const total = cards.length * 3;
  const tick = !started || reduced ? -1 : current.step === 'done' ? total : current.phase * 3 + ['working', 'waiting', 'approved'].indexOf(current.step);

  const stepOf = (i: number): RunStep => {
    if (tick < 0) return 'idle';
    if (tick >= total) return 'approved';
    const phase = Math.floor(tick / 3);
    if (i < phase) return 'approved';
    if (i === phase) return (['working', 'waiting', 'approved'] as const)[tick % 3];
    return 'queued';
  };

  return (
    <div ref={ref}>
      <LifecycleStage
        cards={cards}
        stepOf={stepOf}
        focus={current.step === 'working' ? { phase: current.phase, card: 'artifact' } : { phase: current.phase, card: 'gate' }}
        engaged={started && !reduced}
        reduced={reduced}
        onBusy={setStageBusy}
      />
      <div className="mt-6" />
      <PhaseGrid
        hideCards={compact}
        cards={cards}
        skills={skills}
        common={common}
        externalTick={tick}
        externalPaused={paused}
        onTogglePause={() => setPaused((p) => !p)}
        onBusy={setGridBusy}
      />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Stage cards                                                                 */
/* -------------------------------------------------------------------------- */

const STATUS_TEXT = (card: PhaseCardData, step: RunStep) =>
  step === 'working' ? 'Agent working…' : step === 'waiting' ? `Waiting for ${card.role}` : step === 'approved' || step === 'idle' ? `Approved by ${card.role}` : 'Queued';

function PhaseHeader({ card, step, index }: { card: PhaseCardData; step: RunStep; index: number }) {
  return (
    <a
      href={`#skill-${card.id}`}
      tabIndex={-1}
      className="group block rounded-2xl border border-black/[0.08] bg-white p-4 shadow-xs transition-colors hover:border-black/20 dark:border-white/[0.09] dark:bg-[#0B0B0D] dark:hover:border-white/20"
    >
      <div className="flex items-center justify-between gap-3">
        <span className="font-mono text-[11px] uppercase tracking-[0.04em] text-neutral-400">Phase {String(index + 1).padStart(2, '0')}</span>
        <span
          className={cn(
            'inline-flex h-6 items-center gap-1.5 rounded-full px-2.5 font-inter text-[11.5px] font-medium',
            (step === 'approved' || step === 'idle') && 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400',
            step === 'waiting' && 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400',
            step === 'working' && 'bg-[#f9452d]/10 text-[#c2321e] dark:bg-[#E1F435]/10 dark:text-[#E1F435]',
            step === 'queued' && 'bg-neutral-100 text-neutral-500 dark:bg-white/[0.06] dark:text-neutral-400',
          )}
        >
          {step === 'approved' || step === 'idle' ? <CheckCircle2 className="size-3" /> : step === 'waiting' ? <Clock3 className="size-3" /> : step === 'working' ? <span className="size-1.5 animate-pulse rounded-full bg-current" /> : null}
          <TextStates text={STATUS_TEXT(card, step)} />
        </span>
      </div>
      <h3 className="mt-3 font-spectral text-[21px] leading-[1.2] tracking-[-0.5px] text-[#080808] dark:text-neutral-100">{card.title}</h3>
      <div className="mt-3 flex items-center justify-between">
        <span className="font-inter text-[12.5px] text-neutral-500 dark:text-neutral-400">Gate: {card.role}</span>
        <span className="flex items-center gap-1 font-mono text-[11px] text-neutral-500 group-hover:text-[#f9452d] dark:group-hover:text-[#E1F435]">
          Open skill <ArrowUpRight className="size-3" />
        </span>
      </div>
    </a>
  );
}

function ArtifactCard({ file, text, step, focused }: { file: string; text: string; step: RunStep; focused: boolean }) {
  const [count, setCount] = React.useState(0);
  const writing = step === 'working' && focused;
  const written = step === 'waiting' || step === 'approved' || step === 'idle';

  React.useEffect(() => {
    if (!writing) return;
    setCount(0);
    let raf = 0;
    const startAt = performance.now() + 500; // let the camera land first
    const duration = 3000;
    const tick = (now: number) => {
      const t = Math.min(1, Math.max(0, (now - startAt) / duration));
      setCount(Math.round(text.length * t));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [writing, text]);

  const shown = written ? text : writing ? text.slice(0, count) : '';
  return (
    <div className="overflow-hidden rounded-2xl border border-black/[0.08] bg-white shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]">
      <div className="flex items-center gap-2 border-b border-black/[0.06] px-4 py-2.5 dark:border-white/[0.07]">
        <FileText className="size-3.5 text-neutral-400" />
        <span className="font-mono text-[12px] text-neutral-700 dark:text-neutral-300">{file}</span>
        {writing && <span className="ml-auto font-mono text-[10.5px] uppercase tracking-[0.04em] text-[#f9452d] dark:text-[#E1F435]">writing</span>}
      </div>
      <SkeletonReveal
        loading={step === 'queued'}
        pulseCount={999}
        skeleton={
          <div className="space-y-2.5 px-4 py-4">
            {[92, 70, 84, 60, 76].map((w) => (
              <div key={w} className="h-3 rounded bg-neutral-100 dark:bg-white/[0.06]" style={{ width: `${w}%` }} />
            ))}
          </div>
        }
      >
        <pre className="min-h-[150px] overflow-hidden whitespace-pre px-4 py-4 font-mono text-[11.5px] leading-[1.7] text-neutral-800 dark:text-neutral-200">
          {shown}
          {writing && count < text.length && <span className="ml-px inline-block h-[14px] w-[7px] translate-y-[2px] animate-pulse bg-[#f9452d] dark:bg-[#E1F435]" />}
        </pre>
      </SkeletonReveal>
    </div>
  );
}

function GateCard({ card, index, step }: { card: PhaseCardData; index: number; step: RunStep }) {
  const scene = SCENES[index];
  return (
    // Driven by the run, not by clicks; `inert` keeps its buttons out of the tab order.
    <div inert>
      <ApprovalCard
        title={scene.gate.title}
        description={scene.gate.description}
        meta={`Pull request · CODEOWNERS: ${card.role}`}
        approveLabel="Approve"
        rejectLabel="Request changes"
        approvedMessage={`Approved by ${card.role}`}
        decision={step === 'approved' || step === 'idle' ? 'approved' : null}
        className="max-w-none"
      />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Stage: the hero's camera, sequenced through the lifecycle                   */
/* -------------------------------------------------------------------------- */

type Slot = { x: number; y: number; w: number; h: number };
const COLUMN_W = 450;
const COLUMN_GAP = 56;
const CARD_GAP = 28;
const OFFSETS = [40, 0, 96, 24, 112, 32];
const clamp = (min: number, v: number, max: number) => Math.min(max, Math.max(min, v));
const panEase = cubicBezier(0.65, 0, 0.35, 1);
const flightDuration = (d: number) => clamp(1.1, 0.85 + d / 1100, 2.2);
const flightZoomOut = (d: number) => clamp(0.72, 0.9 - d * 0.00006, 0.9);

function LifecycleStage({
  cards,
  stepOf,
  focus,
  engaged,
  reduced,
  onBusy,
}: {
  cards: PhaseCardData[];
  stepOf: (i: number) => RunStep;
  focus: { phase: number; card: 'artifact' | 'gate' };
  engaged: boolean;
  reduced: boolean;
  onBusy: (busy: boolean) => void;
}) {
  const viewportRef = React.useRef<HTMLDivElement>(null);
  const canvasRef = React.useRef<HTMLDivElement>(null);
  const slotRefs = React.useRef<Record<string, HTMLDivElement | null>>({});
  const [viewport, setViewport] = React.useState({ w: 0, h: 0 });
  const [slots, setSlots] = React.useState<Record<string, Slot> | null>(null);
  const flightRef = React.useRef<ReturnType<typeof animate> | null>(null);
  const shownRef = React.useRef<string | null>(null);
  const canvasW = cards.length * COLUMN_W + (cards.length - 1) * COLUMN_GAP;

  React.useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const measure = () => setViewport({ w: el.clientWidth, h: el.clientHeight });
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  React.useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const measure = () => {
      const next: Record<string, Slot> = {};
      for (const [key, el] of Object.entries(slotRefs.current)) {
        if (!el) continue;
        next[key] = { x: el.offsetLeft + (el.offsetParent as HTMLElement).offsetLeft, y: el.offsetTop, w: el.offsetWidth, h: el.offsetHeight };
      }
      setSlots(next);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(canvas);
    Object.values(slotRefs.current).forEach((el) => el && ro.observe(el));
    return () => ro.disconnect();
  }, []);

  React.useEffect(() => () => flightRef.current?.stop(), []);

  const key = `${focus.phase}-${focus.card}`;
  const measured = viewport.w > 0 && slots !== null;
  // Wide screens show a phase with its neighbours around it; phones fit one column across.
  const scale = !measured ? 0.8 : viewport.w < 640 ? clamp(0.6, (viewport.w - 36) / COLUMN_W, 1) : clamp(0.5, Math.min(viewport.w / 980, viewport.h / 620), 1);
  const target = slots?.[key];

  React.useLayoutEffect(() => {
    const el = canvasRef.current;
    if (!el || !measured || !target) return;
    const cx = viewport.w / 2;
    const cy = viewport.h / 2;
    const setCamera = (x: number, y: number, s: number) => {
      el.style.transform = `translate(${cx - x * s}px, ${cy - y * s}px) scale(${s})`;
    };
    // Look at the focused card, nudged up so the phase header above it stays in view.
    const tx = target.x + target.w / 2;
    const ty = target.y + target.h / 2 - (focus.card === 'artifact' ? 70 : 90);
    flightRef.current?.stop();
    if (!engaged || reduced || shownRef.current === key) {
      setCamera(tx, ty, scale);
    } else {
      const m = getComputedStyle(el).transform;
      const matrix = m !== 'none' ? new DOMMatrix(m) : null;
      const fs = matrix ? matrix.a : scale;
      const fx = matrix ? (cx - matrix.e) / fs : tx;
      const fy = matrix ? (cy - matrix.f) / fs : ty;
      const distance = Math.hypot((tx - fx) * scale, (ty - fy) * scale);
      const depth = scale * (1 - flightZoomOut(distance));
      flightRef.current = animate(0, 1, {
        duration: flightDuration(distance),
        ease: 'linear',
        onUpdate: (t) => {
          const p = panEase(t);
          const dip = Math.sin(Math.PI * t) ** 2;
          setCamera(fx + (tx - fx) * p, fy + (ty - fy) * p, fs + (scale - fs) * p - depth * dip);
        },
      });
    }
    shownRef.current = key;
  }, [key, target, measured, scale, viewport.w, viewport.h, engaged, reduced, focus.card]);

  return (
    <div
      ref={viewportRef}
      aria-hidden
      className="relative h-[520px] overflow-hidden rounded-3xl border border-black/[0.06] bg-neutral-50/40 dark:border-white/[0.07] dark:bg-white/[0.015] sm:h-[620px]"
      onPointerEnter={() => onBusy(true)}
      onPointerLeave={() => onBusy(false)}
    >
      <div
        ref={canvasRef}
        className={cn('absolute left-0 top-0 flex items-start will-change-transform transition-opacity duration-500', measured ? 'opacity-100' : 'opacity-0')}
        style={{ width: canvasW, columnGap: COLUMN_GAP, transformOrigin: '0 0' }}
      >
        <div aria-hidden className="absolute -inset-[1600px] bg-[radial-gradient(circle,var(--color-border)_1px,transparent_1px)] bg-[size:26px_26px] opacity-60" />
        {cards.map((card, i) => {
          const step = stepOf(i);
          const scene = SCENES[i];
          const lit = (part: 'header' | 'artifact' | 'gate') =>
            reduced || !engaged || focus.phase === i && (part === 'header' || part === focus.card);
          const focused = (part: 'artifact' | 'gate') => engaged && !reduced && focus.phase === i && focus.card === part;
          const parts: { part: 'header' | 'artifact' | 'gate'; caption: string; node: React.ReactNode }[] = [
            { part: 'header', caption: card.caption, node: <PhaseHeader card={card} step={step} index={i} /> },
            { part: 'artifact', caption: 'artifact', node: <ArtifactCard file={scene.file} text={scene.artifact} step={step} focused={focused('artifact')} /> },
            { part: 'gate', caption: `g${i + 1} · gate`, node: <GateCard card={card} index={i} step={step} /> },
          ];
          return (
            <div key={card.id} className="relative flex shrink-0 flex-col" style={{ width: COLUMN_W, paddingTop: OFFSETS[i % OFFSETS.length] + 60, rowGap: CARD_GAP }}>
              {parts.map(({ part, caption, node }) => (
                <div
                  key={part}
                  ref={(el) => {
                    if (part !== 'header') slotRefs.current[`${i}-${part}`] = el;
                  }}
                  className="relative"
                  style={{ zIndex: part !== 'header' && focused(part) ? 10 : 1 }}
                >
                  <motion.div
                    initial={false}
                    animate={{ opacity: lit(part) ? 1 : 0.28, scale: part !== 'header' && focused(part) ? 1.04 : 1 }}
                    transition={{ opacity: { duration: 0.8, ease: 'easeInOut' }, scale: { type: 'spring', stiffness: 170, damping: 26 } }}
                  >
                    <span className="mb-2.5 flex items-center gap-2 font-mono text-[11px] font-medium uppercase leading-4 tracking-[0.04em] text-neutral-500 dark:text-neutral-400">
                      <span aria-hidden className="h-[7px] w-[7px] border-l-2 border-t-2 border-[#f9452d] dark:border-[#E1F435]" />
                      {caption}
                    </span>
                    {node}
                  </motion.div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
      {/* soft edges, like the hero's fade into the page */}
      <div aria-hidden className="pointer-events-none absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-background to-transparent" />
      <div aria-hidden className="pointer-events-none absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-background to-transparent" />
      <div aria-hidden className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-background to-transparent" />
    </div>
  );
}
