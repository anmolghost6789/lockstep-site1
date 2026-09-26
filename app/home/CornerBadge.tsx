"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";

const bracketBase ="pointer-events-none absolute h-[9px] w-[9px] border-black dark:border-neutral-300";

export function CornerBadge() {
  return (
    <Link
      href="/#how"
      className="group relative inline-flex outline-hidden transition-transform duration-200 ease-out will-change-transform hover:scale-[1.03] active:scale-[0.97]"
      aria-label="Built for GitHub Copilot"
    >
      {/* Crop-mark style corner brackets */}
      <span aria-hidden className={cn(bracketBase, "-left-1 -top-1 border-l-2 border-t-2")} />
      <span aria-hidden className={cn(bracketBase, "-right-1 -top-1 border-r-2 border-t-2")} />
      <span aria-hidden className={cn(bracketBase, "-bottom-1 -left-1 border-b-2 border-l-2")} />
      <span aria-hidden className={cn(bracketBase, "-bottom-1 -right-1 border-b-2 border-r-2")} />

      <span className="inline-flex h-[26px] items-center justify-center gap-1.5 rounded-none bg-[#ececec] dark:bg-neutral-800 px-3 font-regular text-[16px] leading-[24px] text-black dark:text-neutral-100 transition-colors group-hover:bg-neutral-200 dark:group-hover:bg-neutral-700">
        <svg height="14" width="14" viewBox="0 0 24 24" aria-hidden fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <path d="m8 7-5 5 5 5M16 7l5 5-5 5" />
        </svg>
        Built for GitHub Copilot
      </span>
    </Link>
  );
}
