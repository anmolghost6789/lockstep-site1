'use client';

import * as React from 'react';
import { ArrowRight } from 'lucide-react';
import { useReducedMotion } from 'motion/react';

import { cn } from '@/lib/utils';

type Kind = 'human' | 'step' | 'agent';

/**
 * The "next" delivery flow, with a highlight that travels from intent to production and back,
 * so the handoffs between agents read as a live system rather than a static list.
 */
export function FlowPulse({ nodes, interval = 850 }: { nodes: [string, Kind][]; interval?: number }) {
  const reduced = useReducedMotion();
  const ref = React.useRef<HTMLDivElement>(null);
  const [inView, setInView] = React.useState(false);
  const [active, setActive] = React.useState(-1);

  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { threshold: 0.4 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  React.useEffect(() => {
    if (!inView || reduced || interval >= 60000) return;
    const t = setInterval(() => setActive((i) => (i + 1) % (nodes.length + 2)), interval);
    return () => clearInterval(t);
  }, [inView, reduced, nodes.length, interval]);

  return (
    <div ref={ref} className="flex flex-wrap items-center gap-x-2 gap-y-3">
      {nodes.map(([label, kind], i) => {
        const on = i === active;
        const passed = active > i && active < nodes.length + 1;
        return (
          <span key={label + i} className="inline-flex items-center gap-2">
            <span
              className={cn(
                'inline-flex h-10 items-center whitespace-nowrap rounded-lg px-3.5 font-inter text-[13px] transition-[transform,box-shadow,background-color,color,opacity] duration-300 ease-out',
                kind === 'agent' && 'bg-neutral-900 font-medium text-white dark:bg-neutral-800 dark:text-neutral-100 dark:ring-1 dark:ring-white/10',
                kind === 'human' && 'border border-[#f9452d]/30 bg-[#f9452d]/[0.06] text-[#c2321e] dark:border-[#E1F435]/30 dark:bg-[#E1F435]/[0.08] dark:text-[#E1F435]',
                kind === 'step' && 'border border-black/[0.08] bg-white text-neutral-800 dark:border-white/[0.09] dark:bg-[#0B0B0D] dark:text-neutral-200',
                on && '-translate-y-0.5 scale-[1.04] shadow-[0_0_0_2px_#f9452d,0_10px_24px_-10px_rgba(249,69,45,0.6)] dark:shadow-[0_0_0_2px_#E1F435,0_10px_24px_-10px_rgba(225,244,53,0.5)]',
                !on && active >= 0 && !passed && 'opacity-85',
              )}
            >
              {label}
            </span>
            {i < nodes.length - 1 && (
              <ArrowRight
                aria-hidden
                className={cn(
                  'size-3.5 shrink-0 transition-colors duration-300',
                  passed || on ? 'text-[#f9452d] dark:text-[#E1F435]' : 'text-neutral-400',
                )}
              />
            )}
          </span>
        );
      })}
    </div>
  );
}
