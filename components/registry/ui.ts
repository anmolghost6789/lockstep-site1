/** Shared class names for registry UI, matching the Spectrum styling used on the site. */
export const input =
  'h-10 w-full rounded-lg border border-black/[0.1] bg-white px-3 font-inter text-[14px] text-neutral-900 outline-hidden transition-colors placeholder:text-neutral-400 focus:border-neutral-400 dark:border-white/[0.12] dark:bg-neutral-950 dark:text-neutral-100 dark:focus:border-neutral-500';
export const textarea =
  'w-full rounded-lg border border-black/[0.1] bg-white px-3 py-2 font-mono text-[12.5px] text-neutral-900 outline-hidden transition-colors placeholder:text-neutral-400 focus:border-neutral-400 dark:border-white/[0.12] dark:bg-neutral-950 dark:text-neutral-100';
export const label = 'mb-1.5 block font-inter text-[13px] font-medium text-neutral-800 dark:text-neutral-200';
export const hint = 'mt-1 font-inter text-[12px] text-neutral-500 dark:text-neutral-400';
export const primary =
  'inline-flex h-10 items-center justify-center gap-2 rounded-full bg-neutral-900 px-5 font-inter text-[14px] text-white transition-[transform,background-color] duration-150 hover:bg-neutral-800 active:scale-[0.98] disabled:opacity-40 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200';
export const secondary =
  'inline-flex h-10 items-center justify-center gap-2 rounded-full px-5 font-inter text-[14px] text-neutral-900 shadow-[0_0_0_1px_rgba(0,0,0,0.1)] transition-colors hover:bg-neutral-50 dark:text-neutral-100 dark:shadow-[0_0_0_1px_rgba(255,255,255,0.12)] dark:hover:bg-neutral-900';
export const card = 'rounded-2xl border border-black/[0.08] bg-white shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]';
export const h1 = 'font-spectral text-[28px] leading-[1.15] tracking-[-1px] text-[#080808] dark:text-neutral-100';

export const statusPill: Record<string, string> = {
  approved: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400',
  pending: 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400',
  rejected: 'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400',
};
