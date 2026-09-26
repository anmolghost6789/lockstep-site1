'use client';

import * as React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  ArrowUpRight,
  BarChart3,
  Check,
  CheckCircle2,
  Clock3,
  Pause,
  Play,
  Copy,
  Download,
  DraftingCompass,
  FileCode2,
  Hammer,
  Package,
  Rocket,
  Search,
  ShieldCheck,
  SquareCheckBig,
  UserCheck,
  X,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { TreeNav, type TreeNavItem } from '@/components/spectrumui/tree-nav';
import { AnimateEnter } from '@/app/home/AnimateEnter';
import { BorderBeam } from 'border-beam';
import { useReducedMotion } from 'motion/react';
import { StatusTracker } from '@/components/spectrumui/blocks/ai-assistants/status-tracker';
import { TextStates } from '@/components/spectrumui/text-states';
import { NumberTicker } from '@/components/motion/number-ticker';
import { useSurfaceTheme } from '@/components/spectrumui/use-surface-theme';
import type { PhaseSkill, SkillFile } from '@/lib/skills';
import { CardCaption } from './section-label';

export interface PhaseCardData {
  id: string;
  caption: string;
  icon: keyof typeof ICONS;
  title: string;
  points: string[];
  gate: string;
  role: string;
  output: string;
  file: string;
}

const ICONS = { Search, DraftingCompass, Hammer, SquareCheckBig, Rocket, BarChart3 };

const CARD ='rounded-2xl border border-black/[0.08] bg-white shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]';
/** Replace with your published extension id. The link only works where the extension is installed. */
const VSCODE_URI = (path: string) => `vscode://lockstep.adlc/open?path=${encodeURIComponent(path)}`;

/* -------------------------------------------------------------------------- */
/* Phase grid                                                                  */
/* -------------------------------------------------------------------------- */

export function PhaseGrid({
  cards,
  skills,
  common,
  externalTick,
  externalPaused,
  onTogglePause,
  onBusy,
  hideCards = false,
}: {
  cards: PhaseCardData[];
  skills: PhaseSkill[];
  common: SkillFile[];
  /** When set, the grid follows a run driven elsewhere (the lifecycle stage) instead of its own timer. */
  externalTick?: number;
  externalPaused?: boolean;
  onTogglePause?: () => void;
  onBusy?: (busy: boolean) => void;
  /** Show only the progress rail and the skill panel (the stage above already shows the phases). */
  hideCards?: boolean;
}) {
  const [openId, setOpenId] = React.useState<string | null>(null);
  const active = skills.find((s) => s.id === openId) ?? null;

  // Deep links: /#skill-build-orchestrate opens that phase's skill.
  React.useEffect(() => {
    const fromHash = () => {
      const m = window.location.hash.match(/^#skill-([\w-]+)$/);
      if (m && skills.some((s) => s.id === m[1])) setOpenId(m[1]);
    };
    fromHash();
    window.addEventListener('hashchange', fromHash);
    return () => window.removeEventListener('hashchange', fromHash);
  }, [skills]);

  function open(id: string) {
    setOpenId(id);
    history.replaceState(null, '', `#skill-${id}`);
  }

  function close() {
    setOpenId(null);
    history.replaceState(null, '', window.location.pathname + window.location.search);
  }

  /* ---- Animated run: each phase goes working → waiting for approval → approved, then the next. ---- */
  const STEP_MS = 1400;
  const TOTAL = cards.length * 3;
  const prefersReduced = useReducedMotion();
  // The server can't know the visitor's motion setting, so apply it only after mounting (avoids a hydration mismatch).
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);
  const reduced = mounted && !!prefersReduced;
  const surface = useSurfaceTheme('auto');
  const gridRef = React.useRef<HTMLDivElement>(null);
  const [inView, setInView] = React.useState(false);
  const [pausedState, setPaused] = React.useState(false);
  const [hovering, setHovering] = React.useState(false);
  const [tickState, setTick] = React.useState(-1);
  const driven = externalTick !== undefined;
  const tick = driven ? externalTick : tickState;
  const paused = driven ? !!externalPaused : pausedState;
  React.useEffect(() => {
    onBusy?.(hovering || openId !== null);
  }, [hovering, openId, onBusy]);

  React.useEffect(() => {
    const el = gridRef.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { threshold: 0.25 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const running = !driven && inView && !paused && !hovering && openId === null && !reduced;
  React.useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setTick((v) => (v >= TOTAL + 2 ? 0 : v + 1)), STEP_MS);
    return () => clearInterval(t);
  }, [running, TOTAL]);

  type Step = 'idle' | 'queued' | 'working' | 'waiting' | 'approved';
  const phaseIdx = tick < 0 ? -1 : Math.min(Math.floor(tick / 3), cards.length);
  const stepOf = (i: number): Step => {
    if (tick < 0 || reduced) return 'idle';
    if (tick >= TOTAL) return 'approved';
    if (i < phaseIdx) return 'approved';
    if (i === phaseIdx) return (['working', 'waiting', 'approved'] as const)[tick % 3];
    return 'queued';
  };
  const approvedCount = cards.filter((_, i) => stepOf(i) === 'approved').length;
  const activeCard = tick >= 0 && tick < TOTAL && !reduced ? phaseIdx : -1;
  const trackerIndex = tick >= TOTAL ? cards.length : Math.max(0, phaseIdx);
  const gateText = (card: PhaseCardData, step: Step) =>
    step === 'working' ? 'Agent working…' : step === 'waiting' ? `Waiting for ${card.role}` : step === 'approved' ? `Approved by ${card.role}` : card.gate;

  return (
    <>
      {!reduced && (
        <div className="relative mb-2 flex flex-col gap-4 rounded-2xl border border-black/[0.08] bg-white/80 px-4 py-3.5 shadow-xs backdrop-blur-sm dark:border-white/[0.09] dark:bg-[#0B0B0D]/80 lg:flex-row lg:items-center">
          <StatusTracker
            stages={cards.map((c) => ({ id: c.id, label: c.caption.replace(/^\d+\s+/, '').split(' & ')[0] }))}
            activeIndex={trackerIndex}
            className="max-w-none flex-1"
          />
          <div className="flex items-center gap-4 lg:border-l lg:border-black/[0.06] lg:pl-4 dark:lg:border-white/[0.07]">
            <p className="flex items-baseline gap-1.5 whitespace-nowrap font-inter text-[13px] text-neutral-600 dark:text-neutral-400">
              <span className="font-spectral text-[26px] leading-none text-[#080808] dark:text-neutral-100">
                <NumberTicker value={approvedCount} duration={0.5} />
              </span>
              / {cards.length} gates approved
            </p>
            <button
              type="button"
              onClick={() => (onTogglePause ? onTogglePause() : setPaused((p) => !p))}
              aria-label={paused ? 'Play the lifecycle animation' : 'Pause the lifecycle animation'}
              className="grid size-8 place-items-center rounded-full border border-black/10 text-neutral-600 transition-colors hover:bg-neutral-50 hover:text-neutral-900 dark:border-white/10 dark:text-neutral-400 dark:hover:bg-white/[0.05] dark:hover:text-neutral-100"
            >
              {paused ? <Play className="size-3.5" /> : <Pause className="size-3.5" />}
            </button>
          </div>
        </div>
      )}

      <div
        ref={gridRef}
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
        onFocus={() => setHovering(true)}
        onBlur={() => setHovering(false)}
        className={cn('relative grid gap-x-6 gap-y-10 py-6 md:grid-cols-2 xl:grid-cols-3', hideCards && 'hidden')}
      >
        {cards.map((card, index) => {
          const Icon = ICONS[card.icon];
          const skill = skills.find((s) => s.id === card.id);
          const step = stepOf(index);
          const isActive = activeCard === index;
          return (
            <AnimateEnter key={card.id} duration={0.55} delay={index * 0.05} className="flex flex-col">
              <CardCaption>{card.caption}</CardCaption>
              <BorderBeam
                size="md"
                colorVariant="sunset"
                theme={surface}
                active={isActive}
                strength={1}
                brightness={surface === 'light' ? 1.8 : 1.3}
                glowSize={1.15}
                borderRadius={16}
                className="h-full"
              >
                <button
                  type="button"
                  onClick={() => open(card.id)}
                  aria-haspopup="dialog"
                  aria-label={`Open the ${skill?.command} skill`}
                  className={cn(
                    CARD,
                    'group flex h-full w-full flex-col text-left transition-[border-color,box-shadow,transform,opacity] duration-300 ease-out',
                    'hover:border-black/[0.16] hover:shadow-[0_0_0_1px_rgba(0,0,0,0.04),0_8px_24px_-12px_rgba(0,0,0,0.18)] active:scale-[0.995]',
                    'focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-[#f9452d]/40',
                    isActive && 'shadow-[0_18px_40px_-24px_rgba(249,69,45,0.45)] dark:shadow-[0_18px_40px_-24px_rgba(225,244,53,0.35)]',
                    step === 'queued' && 'opacity-80',
                  )}
                >
                  <div className="flex items-start gap-3 border-b border-black/[0.06] px-4 py-3.5 dark:border-white/[0.07]">
                    <span
                      className={cn(
                        'grid size-8 shrink-0 place-items-center rounded-lg transition-colors duration-300',
                        step === 'approved'
                          ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400'
                          : isActive
                            ? 'bg-[#f9452d]/10 text-[#f9452d] dark:bg-[#E1F435]/10 dark:text-[#E1F435]'
                            : 'bg-neutral-100 text-neutral-700 dark:bg-white/[0.07] dark:text-neutral-300',
                      )}
                    >
                      {step === 'approved' ? <CheckCircle2 className="size-4" /> : <Icon className="size-4" />}
                    </span>
                    <h3 className="font-spectral text-[18px] leading-[1.25] tracking-[-0.4px] text-[#080808] dark:text-neutral-100">{card.title}</h3>
                  </div>
                  <ul className="flex-1 space-y-1.5 px-4 py-3.5">
                    {card.points.map((point, pi) => (
                      <li key={point} className="flex gap-2.5 font-inter text-[13px] leading-[1.5] text-neutral-600 dark:text-neutral-400">
                        <span
                          aria-hidden
                          className={cn(
                            'mt-[7px] size-1 shrink-0 rounded-full transition-colors duration-300',
                            isActive && step === 'working' ? 'animate-pulse bg-[#f9452d] dark:bg-[#E1F435]' : step === 'approved' ? 'bg-emerald-500' : 'bg-neutral-400',
                          )}
                          style={isActive && step === 'working' ? { animationDelay: `${pi * 120}ms` } : undefined}
                        />
                        {point}
                      </li>
                    ))}
                  </ul>
                  <div className="flex items-center justify-between gap-3 border-t border-black/[0.06] px-4 py-2.5 dark:border-white/[0.07]">
                    <span
                      className={cn(
                        'flex min-w-0 items-center gap-1.5 font-inter text-[12px] font-medium',
                        step === 'approved' ? 'text-emerald-700 dark:text-emerald-400' : step === 'waiting' ? 'text-amber-700 dark:text-amber-400' : 'text-neutral-800 dark:text-neutral-200',
                      )}
                    >
                      {step === 'approved' ? (
                        <CheckCircle2 className="size-3.5 shrink-0" />
                      ) : step === 'waiting' ? (
                        <Clock3 className="size-3.5 shrink-0" />
                      ) : step === 'working' ? (
                        <span aria-hidden className="size-2 shrink-0 animate-pulse rounded-full bg-[#f9452d] dark:bg-[#E1F435]" />
                      ) : (
                        <UserCheck className="size-3.5 shrink-0 text-[#f9452d] dark:text-[#E1F435]" />
                      )}
                      <TextStates text={gateText(card, step)} className="truncate" />
                    </span>
                    <span className="flex shrink-0 items-center gap-1 font-mono text-[11px] text-neutral-500 transition-colors group-hover:text-[#f9452d] dark:group-hover:text-[#E1F435]">
                      {skill?.command}
                      <ArrowUpRight className="size-3 transition-transform duration-200 group-hover:-translate-y-px group-hover:translate-x-px" />
                    </span>
                  </div>
                  <div className="rounded-b-2xl bg-neutral-50 px-4 py-3 dark:bg-white/[0.03]">
                    <p className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">Output</p>
                    <p className="mt-0.5 text-[13px] font-semibold text-neutral-900 dark:text-neutral-100">{card.output}</p>
                    <p className="mt-0.5 font-mono text-[11px] text-neutral-500">{card.file}</p>
                  </div>
                </button>
              </BorderBeam>
            </AnimateEnter>
          );
        })}
      </div>

      <Dialog.Root open={active !== null} onOpenChange={(o) => !o && close()}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-[60] bg-white/60 backdrop-blur-[2px] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 dark:bg-black/60" />
          <Dialog.Content
            className={cn('fixed inset-y-0 right-0 z-[61] flex w-full max-w-[1120px] flex-col overflow-hidden border-l border-black/[0.08] bg-white shadow-[-24px_0_60px_-30px_rgba(0,0,0,0.25)] outline-hidden lg:rounded-l-2xl dark:border-white/[0.09] dark:bg-[#0B0B0D] dark:shadow-[-24px_0_60px_-30px_rgba(0,0,0,0.8)]',
              'data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right data-[state=open]:duration-300 data-[state=closed]:duration-200',
            )}
          >
            {active && <SkillSheet key={active.id} skill={active} common={common} />}
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}

/* -------------------------------------------------------------------------- */
/* Sheet                                                                       */
/* -------------------------------------------------------------------------- */

function SkillSheet({ skill, common }: { skill: PhaseSkill; common: SkillFile[] }) {
  const files = React.useMemo(() => [...skill.files, ...common], [skill.files, common]);
  const [activePath, setActivePath] = React.useState(files[0].path);
  const activeFile = files.find((f) => f.path === activePath) ?? files[0];
  const groups = (['Phase', 'Shared', 'Contracts', 'Governance'] as const).map((g) => ({
    group: g,
    items: files.filter((f) => f.group === g),
  }));
  const riskEntries = Object.entries(skill.gate.riskRoles);

  return (
    <>
      {/* Header */}
      <div className="flex items-start gap-4 border-b border-black/[0.06] px-5 pb-4 pt-5 sm:px-6 dark:border-white/[0.07]">
        <div className="min-w-0 flex-1">
          <CardCaption>{`${skill.number} ${skill.label.toLowerCase()} · skill`}</CardCaption>
          <div className="flex flex-wrap items-center gap-3">
            <Dialog.Title className="font-spectral text-[28px] leading-[1.1] tracking-[-1px] text-[#080808] dark:text-neutral-100">
              {skill.command}
            </Dialog.Title>
            <CopyButton text={skill.command} label="Copy command" />
          </div>
          <Dialog.Description className="mt-2 max-w-[720px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
            {skill.description}
          </Dialog.Description>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <a
            href="/adlc-agent.zip"
            download
            className="inline-flex h-8 items-center gap-1.5 rounded-full border border-black/8 bg-neutral-100/70 px-2.5 font-mono text-[11px] uppercase tracking-[0.5px] text-foreground/70 transition-colors hover:bg-neutral-100 hover:text-foreground sm:px-3 dark:border-white/10 dark:bg-neutral-900/70 dark:hover:bg-neutral-900"
          >
            <Package className="size-3.5" />
            <span className="hidden sm:inline">Skill pack</span>
            <span className="sr-only sm:hidden">Download skill pack</span>
          </a>
          <Dialog.Close className="grid size-8 place-items-center rounded-full text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-neutral-900 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-neutral-300 dark:hover:bg-neutral-900 dark:hover:text-neutral-100 dark:focus-visible:ring-neutral-700">
            <X className="size-4" />
            <span className="sr-only">Close</span>
          </Dialog.Close>
        </div>
      </div>

      {/* Enterprise controls for this phase */}
      <div className="grid grid-cols-2 gap-px border-b border-black/[0.06] bg-black/[0.06] lg:grid-cols-4 dark:border-white/[0.07] dark:bg-white/[0.07]">
        <Control label={`Gate ${skill.gate.id}`}>
          <div className="flex flex-wrap gap-1">
            {skill.gate.roles.map((r) => (
              <RolePill key={r}>{r}</RolePill>
            ))}
          </div>
          {riskEntries.length > 0 && (
            <p className="mt-1.5 text-[11.5px] leading-4 text-neutral-500">
              {riskEntries.map(([risk, roles]) => `${risk} risk adds ${roles.join(', ')}`).join('; ')}
            </p>
          )}
        </Control>
        <Control label="Approval controls">
          <p className="flex items-center gap-1.5 text-[12.5px] font-medium text-neutral-800 dark:text-neutral-200">
            <ShieldCheck className="size-3.5 text-emerald-600 dark:text-emerald-400" />
            {skill.gate.separationOfDuties ? 'Separation of duties enforced' : 'Single approver'}
          </p>
          <p className="mt-1 text-[11.5px] leading-4 text-neutral-500">Bound to the artifact hash. Any edit resets the gate.</p>
        </Control>
        <Control label="Policy pack">
          <div className="flex flex-wrap gap-1">
            {skill.policies.map((p) => (
              <span key={p} className="rounded-md bg-neutral-100 px-1.5 py-0.5 font-mono text-[10.5px] text-neutral-600 dark:bg-white/[0.07] dark:text-neutral-400">
                {p}
              </span>
            ))}
          </div>
        </Control>
        <Control label="Writes">
          <p className="font-mono text-[12px] text-neutral-900 dark:text-neutral-100">{skill.artifact}</p>
          <p className="mt-1 text-[11.5px] leading-4 text-neutral-500">
            Model {skill.model}
            {skill.subagents.length > 0 && ` · subagent ${skill.subagents.join(', ')}`}
          </p>
        </Control>
      </div>

      {/* Body */}
      <div className="grid min-h-0 flex-1 grid-rows-[auto_minmax(0,1fr)] lg:grid-cols-[250px_minmax(0,1fr)] lg:grid-rows-1">
        {/* File list */}
        <nav aria-label="Skill files" className="hidden min-h-0 overflow-y-auto border-r border-black/[0.06] bg-neutral-50/60 px-3 py-4 lg:block dark:border-white/[0.07] dark:bg-white/[0.02]">
          {groups.map(({ group, items }) => (
            <div key={group} className="mb-4">
              <p className="mb-1 px-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">{group}</p>
              <TreeNav
                items={items.map<TreeNavItem>((f) => ({ label: f.label, href: `#file-${f.path}` }))}
                activeHref={items.some((f) => f.path === activeFile.path) ? `#file-${activeFile.path}` : undefined}
                followHover={false}
                onSelect={(item, event) => {
                  event.preventDefault();
                  setActivePath(item.href.replace('#file-', ''));
                }}
                className="[&_a]:text-[12.5px]"
              />
            </div>
          ))}
        </nav>

        {/* Mobile file picker */}
        <div className="flex gap-1.5 overflow-x-auto border-b border-black/[0.06] px-4 py-2.5 lg:hidden dark:border-white/[0.07]">
          {files.map((f) => (
            <button
              key={f.path}
              type="button"
              onClick={() => setActivePath(f.path)}
              className={cn('shrink-0 rounded-full border px-3 py-1 font-mono text-[11px]',
                f.path === activeFile.path ? 'border-neutral-900 bg-neutral-900 text-white dark:bg-white dark:text-neutral-900 dark:border-white' : 'border-black/10 text-neutral-600 dark:border-white/10 dark:text-neutral-400',
              )}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Viewer */}
        <div className="flex min-h-0 flex-col">
          <div className="flex flex-wrap items-center gap-2 border-b border-black/[0.06] px-5 py-2.5 sm:px-6 dark:border-white/[0.07]">
            <FileCode2 className="size-3.5 shrink-0 text-neutral-400 dark:text-neutral-500" />
            <span className="min-w-0 flex-1 basis-[calc(100%-2rem)] truncate font-mono text-[12px] text-neutral-700 sm:basis-auto dark:text-neutral-300">{activeFile.path}</span>
            <CopyButton text={activeFile.content} label="Copy" />
            <DownloadButton file={activeFile} />
            <a
              href={VSCODE_URI(activeFile.path)}
              title="Opens in VS Code when the Lockstep extension is installed"
              className="inline-flex h-7 items-center gap-1.5 rounded-full bg-neutral-900 px-3 text-[12px] font-medium text-white transition-colors hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
            >
              Open in VS Code
              <ArrowUpRight className="size-3" />
            </a>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-5 py-6 sm:px-8">
            {activeFile.lang === 'markdown' ? <MarkdownFile source={activeFile.content} /> : <CodeFile source={activeFile.content} />}
          </div>
        </div>
      </div>
    </>
  );
}

function Control({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-white px-5 py-3 sm:px-6 dark:bg-[#0B0B0D]">
      <p className="mb-1.5 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">{label}</p>
      {children}
    </div>
  );
}

function RolePill({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-[#f9452d]/[0.08] px-2 py-0.5 font-mono text-[11px] text-[#c2321e] dark:bg-[#E1F435]/[0.1] dark:text-[#E1F435]">
      <UserCheck className="size-3" />
      {children}
    </span>
  );
}

/* -------------------------------------------------------------------------- */
/* Actions                                                                     */
/* -------------------------------------------------------------------------- */

function CopyButton({ text, label }: { text: string; label: string }) {
  const [done, setDone] = React.useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setDone(true);
        setTimeout(() => setDone(false), 1400);
      }}
      className="inline-flex h-7 items-center gap-1.5 rounded-full border border-black/10 px-2.5 text-[12px] font-medium text-neutral-700 transition-colors hover:bg-neutral-50 dark:border-white/10 dark:text-neutral-300 dark:hover:bg-white/[0.05]"
    >
      {done ? <Check className="size-3.5 text-emerald-600 dark:text-emerald-400" /> : <Copy className="size-3.5" />}
      {done ? 'Copied' : label}
    </button>
  );
}

function DownloadButton({ file }: { file: SkillFile }) {
  return (
    <button
      type="button"
      onClick={() => {
        const url = URL.createObjectURL(new Blob([file.content], { type: 'text/plain;charset=utf-8' }));
        const a = document.createElement('a');
        a.href = url;
        a.download = file.path.split('/').pop() as string;
        a.click();
        URL.revokeObjectURL(url);
      }}
      className="inline-flex h-7 items-center gap-1.5 rounded-full border border-black/10 px-2.5 text-[12px] font-medium text-neutral-700 transition-colors hover:bg-neutral-50 dark:border-white/10 dark:text-neutral-300 dark:hover:bg-white/[0.05]"
    >
      <Download className="size-3.5" />
      Download
    </button>
  );
}

/* -------------------------------------------------------------------------- */
/* Renderers                                                                   */
/* -------------------------------------------------------------------------- */

interface Frontmatter {
  scalars: [string, string][];
  lists: [string, string[]][];
}

function splitFrontmatter(source: string): { fm: Frontmatter | null; body: string } {
  const m = source.match(/^---\n([\s\S]*?)\n---\n?/);
  if (!m) return { fm: null, body: source };
  const scalars: [string, string][] = [];
  const lists: [string, string[]][] = [];
  const lines = m[1].split('\n');
  for (let i = 0; i < lines.length; i++) {
    const kv = lines[i].match(/^([\w-]+):\s*(.*)$/);
    if (!kv) continue;
    const [, key, raw] = kv;
    if (raw === '' || raw === '>-' || raw === '|') {
      const block: string[] = [];
      while (i + 1 < lines.length && /^\s+/.test(lines[i + 1])) block.push(lines[++i].trim());
      if (block.every((b) => b.startsWith('- '))) lists.push([key, block.map((b) => b.slice(2))]);
      else scalars.push([key, block.join(' ')]);
    } else {
      scalars.push([key, raw.replace(/^"|"$/g, '')]);
    }
  }
  return { fm: { scalars, lists }, body: source.slice(m[0].length) };
}

export function MarkdownFile({ source }: { source: string }) {
  const { fm, body } = splitFrontmatter(source);
  return (
    <article className="max-w-[780px]">
      {fm && (
        <div className="mb-8 overflow-hidden rounded-xl border border-black/[0.08] dark:border-white/[0.09]">
          <p className="border-b border-black/[0.06] bg-neutral-50 px-4 py-2 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:border-white/[0.07] dark:bg-white/[0.03] dark:text-neutral-500">
            Frontmatter
          </p>
          <dl className="divide-y divide-black/[0.05] dark:divide-white/[0.06]">
            {fm.scalars
              .filter(([k]) => k !== 'description')
              .map(([k, v]) => (
                <div key={k} className="grid grid-cols-[160px_minmax(0,1fr)] gap-3 px-4 py-2 text-[12.5px]">
                  <dt className="font-mono text-neutral-500">{k}</dt>
                  <dd className="font-mono text-neutral-900 dark:text-neutral-100">{v}</dd>
                </div>
              ))}
            {fm.lists.map(([k, items]) => (
              <div key={k} className="grid grid-cols-[160px_minmax(0,1fr)] gap-3 px-4 py-2 text-[12.5px]">
                <dt className="font-mono text-neutral-500">{k}</dt>
                <dd className="flex flex-wrap gap-1">
                  {items.map((it) => (
                    <span key={it} className="rounded-md bg-neutral-100 px-1.5 py-0.5 font-mono text-[11px] text-neutral-700 dark:bg-white/[0.07] dark:text-neutral-300">
                      {it}
                    </span>
                  ))}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (p) => <h1 className="mb-4 font-spectral text-[30px] leading-[1.15] tracking-[-1px] text-[#080808] dark:text-neutral-100" {...p} />,
          h2: (p) => <h2 className="mb-3 mt-9 border-b border-black/[0.06] pb-2 font-spectral text-[21px] leading-[1.25] tracking-[-0.5px] text-[#080808] dark:border-white/[0.07] dark:text-neutral-100" {...p} />,
          h3: (p) => <h3 className="mb-2 mt-6 text-[15px] font-semibold text-neutral-900 dark:text-neutral-100" {...p} />,
          p: (p) => <p className="my-3 font-inter text-[14px] leading-[1.65] text-neutral-700 dark:text-neutral-300" {...p} />,
          ul: (p) => <ul className="my-3 list-disc space-y-1.5 pl-5 font-inter text-[14px] leading-[1.6] text-neutral-700 marker:text-neutral-400 dark:text-neutral-300" {...p} />,
          ol: (p) => <ol className="my-3 list-decimal space-y-1.5 pl-5 font-inter text-[14px] leading-[1.6] text-neutral-700 marker:font-mono marker:text-[12px] marker:text-neutral-400 dark:text-neutral-300" {...p} />,
          a: (p) => <a className="underline decoration-[#f9452d]/50 underline-offset-2 hover:decoration-[#f9452d] dark:decoration-[#E1F435]/50 dark:hover:decoration-[#E1F435]" {...p} />,
          strong: (p) => <strong className="font-semibold text-neutral-900 dark:text-neutral-100" {...p} />,
          blockquote: (p) => <blockquote className="my-4 border-l-2 border-[#f9452d] pl-4 text-neutral-600 dark:border-[#E1F435] dark:text-neutral-400" {...p} />,
          table: (p) => (
            <div className="my-4 overflow-x-auto rounded-xl border border-black/[0.08] dark:border-white/[0.09]">
              <table className="w-full border-collapse text-left font-inter text-[12.5px]" {...p} />
            </div>
          ),
          thead: (p) => <thead className="bg-neutral-50 dark:bg-white/[0.03]" {...p} />,
          th: (p) => <th className="border-b border-black/[0.08] px-3 py-2 font-medium text-neutral-600 dark:border-white/[0.09] dark:text-neutral-400" {...p} />,
          td: (p) => <td className="border-b border-black/[0.05] px-3 py-2 align-top text-neutral-800 dark:border-white/[0.06] dark:text-neutral-200" {...p} />,
          pre: (p) => <pre className="my-4 overflow-x-auto rounded-xl bg-[#0b0b0d] px-4 dark:border dark:border-white/[0.08] dark:bg-black py-3.5 font-mono text-[12.5px] leading-[1.7] text-neutral-100 [&_code]:bg-transparent [&_code]:p-0 [&_code]:text-inherit" {...p} />,
          code: (p) => <code className="rounded-[5px] bg-neutral-100 px-1 py-px font-mono text-[12.5px] text-neutral-800 dark:bg-white/[0.07] dark:text-neutral-200" {...p} />,
        }}
      >
        {body}
      </ReactMarkdown>
    </article>
  );
}

export function CodeFile({ source }: { source: string }) {
  const lines = source.replace(/\n$/, '').split('\n');
  return (
    <pre className="overflow-x-auto rounded-xl border border-black/[0.08] bg-neutral-50/60 py-3 font-mono text-[12.5px] leading-[1.7] dark:border-white/[0.09] dark:bg-white/[0.02]">
      <code>
        {lines.map((line, i) => (
          <span key={i} className="flex">
            <span aria-hidden className="w-12 shrink-0 select-none pr-4 text-right text-neutral-300 dark:text-neutral-700">
              {i + 1}
            </span>
            <span className="whitespace-pre pr-6 text-neutral-800 dark:text-neutral-200">{line || ' '}</span>
          </span>
        ))}
      </code>
    </pre>
  );
}
