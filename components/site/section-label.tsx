/** Spectrum UI's section eyebrow: orange corner mark plus a mono label. */
export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5">
      <span aria-hidden className="-rotate-90">
        <span className="block size-[9px] border-b-2 border-r-2 border-[#f9452d] dark:border-[#E1F435]" />
      </span>
      <span className="font-mono text-[12px] font-medium uppercase leading-[16.8px] text-[#171717] dark:text-neutral-200">{children}</span>
    </div>
  );
}

/** Mono card caption with the corner mark, as used above each hero-stage card. */
export function CardCaption({ children }: { children: React.ReactNode }) {
  return (
    <span className="mb-2.5 flex items-center gap-2 font-mono text-[11px] font-medium uppercase leading-4 tracking-[0.04em] text-neutral-500">
      <span aria-hidden className="h-[7px] w-[7px] border-l-2 border-t-2 border-[#f9452d] dark:border-[#E1F435]" />
      {children}
    </span>
  );
}
