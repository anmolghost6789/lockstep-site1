'use client';

import * as React from 'react';
import { AnimatePresence, motion } from 'motion/react';
import {
  BarChart3,
  CheckCircle2,
  CircleHelp,
  Clock3,
  DraftingCompass,
  FileText,
  Hammer,
  Rocket,
  Search,
  SquareCheckBig,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { TextStates } from '@/components/spectrumui/text-states';
import { NumberTicker } from '@/components/motion/number-ticker';
import { LogoMark } from './logo';

type Mode = 'today' | 'lockstep';

const STAGES = [
  { icon: Search, today: { title: 'Requirements', artifact: 'a doc somewhere', who: 'PM' }, lockstep: { title: 'Requirements agent', artifact: '01-aiprs.md', who: 'product owner' } },
  { icon: DraftingCompass, today: { title: 'Design', artifact: 'a slide deck', who: 'Architect' }, lockstep: { title: 'Architecture agent', artifact: '02-blueprint.md', who: 'architect' } },
  { icon: Hammer, today: { title: 'Build', artifact: 'a pull request', who: 'Developer' }, lockstep: { title: 'Coding agents', artifact: '03-units.yaml', who: 'engineer' } },
  { icon: SquareCheckBig, today: { title: 'Testing', artifact: 'a spreadsheet', who: 'QA' }, lockstep: { title: 'Evaluation agent', artifact: '04-scorecard.json', who: 'QA lead' } },
  { icon: Rocket, today: { title: 'Release', artifact: 'a change ticket', who: 'Ops' }, lockstep: { title: 'Release agent', artifact: '05-release.md', who: 'release manager' } },
  { icon: BarChart3, today: { title: 'Feedback', artifact: 'when someone asks', who: '—' }, lockstep: { title: 'Observability agent', artifact: '06-backlog.md', who: 'product owner' } },
];

// Canvas geometry (scaled to the container). Stages sit on an ellipse, clockwise from top-left.
const W = 1000, H = 540, CX = 500, CY = 270, RX = 405, RY = 205;
const ANGLES = [210, 270, 330, 30, 90, 150];
const pt = (deg: number) => ({ x: CX + RX * Math.cos((deg * Math.PI) / 180), y: CY + RY * Math.sin((deg * Math.PI) / 180) });
const POINTS = ANGLES.map(pt);
const opposite = pt(30);
const PATH = `M ${POINTS[0].x} ${POINTS[0].y} A ${RX} ${RY} 0 1 1 ${opposite.x} ${opposite.y} A ${RX} ${RY} 0 1 1 ${POINTS[0].x} ${POINTS[0].y}`;
const LAP_MS: Record<Mode, number> = { today: 16000, lockstep: 9000 };

function useInView<T extends Element>(threshold = 0.3) {
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

function useReducedMotion() {
  const [r, setR] = React.useState(false);
  React.useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const on = () => setR(mq.matches);
    on();
    mq.addEventListener('change', on);
    return () => mq.removeEventListener('change', on);
  }, []);
  return r;
}

/** Drives the travelling light: progress 0..1 around the loop, laps completed, and whether it's running. */
function useLoop(mode: Mode, running: boolean) {
  const [progress, setProgress] = React.useState(0);
  const [laps, setLaps] = React.useState(0);
  const state = React.useRef({ p: 0, last: 0 });
  React.useEffect(() => {
    if (!running) return;
    let raf = 0;
    state.current.last = performance.now();
    const tick = (now: number) => {
      const dt = now - state.current.last;
      state.current.last = now;
      let p = state.current.p + dt / LAP_MS[mode];
      if (p >= 1) {
        p -= 1;
        setLaps((l) => l + 1);
      }
      state.current.p = p;
      setProgress(p);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [mode, running]);
  const reset = () => {
    state.current.p = 0;
    setProgress(0);
    setLaps(0);
  };
  return { progress, laps, reset };
}

export function ShiftLoop() {
  const [ref, inView] = useInView<HTMLDivElement>(0.35);
  const reduced = useReducedMotion();
  const [mode, setMode] = React.useState<Mode>('today');
  const [touched, setTouched] = React.useState(false);
  const [hovering, setHovering] = React.useState(false);
  const running = inView && !reduced && !hovering;
  const { progress, laps, reset } = useLoop(mode, running);

  // Tell the story on its own: one lap of "today", then switch to Lockstep, unless the visitor chose.
  React.useEffect(() => {
    if (!touched && mode === 'today' && laps >= 1) {
      setMode('lockstep');
      reset();
    }
  }, [laps, mode, touched, reset]);

  const choose = (m: Mode) => {
    setTouched(true);
    if (m !== mode) {
      setMode(m);
      reset();
    }
  };

  // Which stages the light has passed on this lap (reduced motion: show a finished lap).
  const passed = (i: number) => (reduced ? true : progress >= i / STAGES.length + 0.02);
  const current = reduced ? -1 : Math.min(STAGES.length - 1, Math.floor(progress * STAGES.length));
  const gatesThisLap = STAGES.filter((_, i) => passed(i)).length;
  const approvals = mode === 'lockstep' ? laps * STAGES.length + gatesThisLap : 0;

  return (
    <div ref={ref} onPointerEnter={() => setHovering(true)} onPointerLeave={() => setHovering(false)}>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div role="tablist" aria-label="Compare" className="inline-flex rounded-full border border-black/[0.08] bg-white p-1 shadow-xs dark:border-white/[0.1] dark:bg-[#0B0B0D]">
          {([
            ['today', 'Today'],
            ['lockstep', 'With Lockstep'],
          ] as const).map(([m, label]) => (
            <button
              key={m}
              role="tab"
              aria-selected={mode === m}
              type="button"
              onClick={() => choose(m)}
              className={cn(
                'relative rounded-full px-5 py-2 font-inter text-[14px] font-medium transition-colors',
                mode === m ? 'text-white dark:text-neutral-900' : 'text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100',
              )}
            >
              {mode === m && <motion.span layoutId="shift-pill" className="absolute inset-0 rounded-full bg-neutral-900 dark:bg-white" transition={{ type: 'spring', stiffness: 380, damping: 32 }} />}
              <span className="relative">{label}</span>
            </button>
          ))}
        </div>
        <p className="font-inter text-[14px] text-neutral-500 dark:text-neutral-400">
          <TextStates text={mode === 'today' ? 'Same six stages. Handoffs by email, meetings and tickets.' : 'Same six stages. Agents do the work; people approve every handoff.'} />
        </p>
      </div>

      {/* Desktop: the loop */}
      <div className="hidden md:block">
        <Loop mode={mode} progress={progress} passed={passed} current={current} approvals={approvals} laps={laps} reduced={reduced} />
      </div>

      {/* Phones: a vertical timeline */}
      <div className="md:hidden">
        <Timeline mode={mode} passed={passed} current={current} />
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */

function Loop({ mode, progress, passed, current, approvals, laps, reduced }: { mode: Mode; progress: number; passed: (i: number) => boolean; current: number; approvals: number; laps: number; reduced: boolean }) {
  const boxRef = React.useRef<HTMLDivElement>(null);
  const pathRef = React.useRef<SVGPathElement>(null);
  const [scale, setScale] = React.useState(1);
  const [len, setLen] = React.useState(0);

  React.useEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setScale(el.clientWidth / W));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  React.useEffect(() => setLen(pathRef.current?.getTotalLength() ?? 0), []);

  const pos = len ? pathRef.current!.getPointAtLength(progress * len) : POINTS[0];
  const tail = len * 0.14;
  const lock = mode === 'lockstep';

  return (
    <div ref={boxRef} className="relative w-full overflow-hidden rounded-3xl border border-black/[0.06] bg-neutral-50/60 dark:border-white/[0.07] dark:bg-white/[0.015]" style={{ height: H * scale }}>
      <div aria-hidden className="absolute inset-0 bg-[radial-gradient(circle,var(--color-border)_1px,transparent_1px)] bg-[size:24px_24px] opacity-70" />
      <div className="absolute left-0 top-0" style={{ width: W, height: H, transform: `scale(${scale})`, transformOrigin: '0 0' }}>
        <svg width={W} height={H} className="absolute inset-0" aria-hidden>
          <defs>
            <radialGradient id="shift-glow">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.55" />
              <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
            </radialGradient>
          </defs>
          <path ref={pathRef} d={PATH} fill="none" className="stroke-neutral-300 dark:stroke-neutral-700" strokeWidth={1.5} strokeDasharray="4 6" />
          {!reduced && len > 0 && (
            <g className={cn(lock ? 'text-[#f9452d] dark:text-[#E1F435]' : 'text-neutral-400 dark:text-neutral-500')}>
              <path d={PATH} fill="none" stroke="currentColor" strokeWidth={lock ? 3 : 2} strokeLinecap="round" strokeDasharray={`${tail} ${len}`} strokeDashoffset={-(progress * len - tail)} opacity={0.9} />
              <circle cx={pos.x} cy={pos.y} r={lock ? 26 : 18} fill="url(#shift-glow)" />
              <circle cx={pos.x} cy={pos.y} r={lock ? 6 : 5} fill="currentColor" />
            </g>
          )}
        </svg>

        {/* Centre */}
        <div className="absolute left-1/2 top-1/2 w-[300px] -translate-x-1/2 -translate-y-1/2">
          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, y: 8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.98 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className={cn('rounded-2xl border p-5 text-center shadow-xs', lock ? 'border-black/[0.08] bg-white dark:border-white/[0.1] dark:bg-[#0B0B0D]' : 'border-dashed border-black/15 bg-white/70 dark:border-white/15 dark:bg-white/[0.03]')}
            >
              {lock ? (
                <>
                  <span className="mx-auto flex size-10 items-center justify-center rounded-xl bg-neutral-900 p-2 dark:bg-white">
                    <LogoMark className="h-full w-full text-white dark:text-neutral-900" />
                  </span>
                  <p className="mt-3 font-spectral text-[22px] leading-tight text-[#080808] dark:text-neutral-50">Lockstep</p>
                  <p className="mt-1 font-inter text-[13px] text-neutral-500 dark:text-neutral-400">Orchestrates and governs every handoff</p>
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    <div className="rounded-xl bg-neutral-50 px-2 py-2.5 dark:bg-white/[0.04]">
                      <p className="font-spectral text-[24px] leading-none text-[#080808] dark:text-neutral-50"><NumberTicker value={approvals} duration={0.4} /></p>
                      <p className="mt-1 font-mono text-[9.5px] uppercase tracking-[0.04em] text-neutral-500">approvals recorded</p>
                    </div>
                    <div className="rounded-xl bg-neutral-50 px-2 py-2.5 dark:bg-white/[0.04]">
                      <p className="font-spectral text-[24px] leading-none text-[#080808] dark:text-neutral-50"><NumberTicker value={approvals} duration={0.4} /></p>
                      <p className="mt-1 font-mono text-[9.5px] uppercase tracking-[0.04em] text-neutral-500">artifacts versioned</p>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <span className="mx-auto grid size-10 place-items-center rounded-xl border border-dashed border-black/20 text-neutral-400 dark:border-white/20">
                    <CircleHelp className="size-5" />
                  </span>
                  <p className="mt-3 font-spectral text-[22px] leading-tight text-neutral-700 dark:text-neutral-300">Your team</p>
                  <p className="mt-1 font-inter text-[13px] text-neutral-500 dark:text-neutral-400">Handoffs by email, meetings and tickets</p>
                  <div className="mt-4 rounded-xl bg-neutral-100/80 px-3 py-2.5 dark:bg-white/[0.04]">
                    <p className="font-spectral text-[24px] leading-none text-neutral-500">0</p>
                    <p className="mt-1 font-mono text-[9.5px] uppercase tracking-[0.04em] text-neutral-500">approvals on record</p>
                  </div>
                </>
              )}
            </motion.div>
          </AnimatePresence>
          {laps > 0 && lock && <p className="mt-2 text-center font-mono text-[10px] uppercase tracking-[0.04em] text-neutral-400">cycle {laps + 1}: the backlog became the next intent</p>}
        </div>

        {/* Stages */}
        {STAGES.map((s, i) => {
          const d = lock ? s.lockstep : s.today;
          const done = passed(i);
          const active = i === current;
          const Icon = s.icon;
          return (
            <div key={i} className="absolute w-[236px] -translate-x-1/2 -translate-y-1/2" style={{ left: POINTS[i].x, top: POINTS[i].y }}>
              <motion.div
                animate={{ scale: active ? 1.04 : 1, opacity: lock ? 1 : active ? 1 : 0.82 }}
                transition={{ type: 'spring', stiffness: 260, damping: 24 }}
                className={cn(
                  'rounded-2xl border bg-white p-3.5 shadow-xs dark:bg-[#0B0B0D]',
                  lock ? (active ? 'border-[#f9452d]/50 shadow-[0_10px_30px_-12px_rgba(249,69,45,0.45)] dark:border-[#E1F435]/50 dark:shadow-[0_10px_30px_-12px_rgba(225,244,53,0.35)]' : 'border-black/[0.08] dark:border-white/[0.09]') : 'border-dashed border-black/15 dark:border-white/15',
                )}
              >
                <div className="flex items-center gap-2.5">
                  <span className={cn('grid size-8 shrink-0 place-items-center rounded-lg', lock ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900' : 'bg-neutral-100 text-neutral-500 dark:bg-white/[0.06] dark:text-neutral-400')}>
                    <Icon className="size-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-inter text-[13.5px] font-semibold text-neutral-900 dark:text-neutral-100"><TextStates text={d.title} /></p>
                    <p className="flex items-center gap-1 truncate font-mono text-[11px] text-neutral-500"><FileText className="size-3 shrink-0" /><TextStates text={d.artifact} /></p>
                  </div>
                </div>
                <div className={cn('mt-2.5 flex items-center gap-1.5 rounded-lg px-2 py-1.5 font-inter text-[11.5px] font-medium', gateClass(mode, done, active))}>
                  {lock ? (done ? <CheckCircle2 className="size-3.5 shrink-0" /> : <Clock3 className="size-3.5 shrink-0" />) : <CircleHelp className="size-3.5 shrink-0" />}
                  <TextStates text={gateText(mode, done, active, d.who)} className="truncate" />
                </div>
              </motion.div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function gateText(mode: Mode, done: boolean, active: boolean, who: string) {
  if (mode === 'today') return active ? 'Waiting on email…' : 'No record of approval';
  return done ? `Approved by ${who}` : active ? `Waiting for ${who}` : `Gate: ${who}`;
}

function gateClass(mode: Mode, done: boolean, active: boolean) {
  if (mode === 'today') return active ? 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400' : 'bg-neutral-100 text-neutral-500 dark:bg-white/[0.05] dark:text-neutral-400';
  if (done) return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400';
  if (active) return 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400';
  return 'bg-neutral-100 text-neutral-600 dark:bg-white/[0.05] dark:text-neutral-400';
}

function Timeline({ mode, passed, current }: { mode: Mode; passed: (i: number) => boolean; current: number }) {
  const lock = mode === 'lockstep';
  return (
    <ol className="relative space-y-3 pl-7">
      <span aria-hidden className="absolute bottom-3 left-[11px] top-3 w-px bg-neutral-200 dark:bg-neutral-800" />
      {STAGES.map((s, i) => {
        const d = lock ? s.lockstep : s.today;
        const done = passed(i);
        const active = i === current;
        return (
          <li key={i} className="relative">
            <span
              aria-hidden
              className={cn(
                'absolute -left-7 top-4 grid size-[23px] place-items-center rounded-full border-2 bg-background transition-colors',
                active ? (lock ? 'border-[#f9452d] dark:border-[#E1F435]' : 'border-amber-500') : done && lock ? 'border-emerald-500' : 'border-neutral-300 dark:border-neutral-700',
              )}
            >
              {active && <span className={cn('size-2 rounded-full', lock ? 'bg-[#f9452d] dark:bg-[#E1F435]' : 'bg-amber-500')} />}
            </span>
            <div className={cn('rounded-xl border p-3.5', lock ? 'border-black/[0.08] bg-white dark:border-white/[0.09] dark:bg-[#0B0B0D]' : 'border-dashed border-black/15 dark:border-white/15')}>
              <p className="font-inter text-[14px] font-semibold text-neutral-900 dark:text-neutral-100">{d.title}</p>
              <p className="font-mono text-[11.5px] text-neutral-500">{d.artifact}</p>
              <p className={cn('mt-2 inline-flex rounded-md px-2 py-1 font-inter text-[12px] font-medium', gateClass(mode, done, active))}>{gateText(mode, done, active, d.who)}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
