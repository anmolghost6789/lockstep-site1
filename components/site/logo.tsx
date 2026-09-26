/** Lockstep mark: three rising steps. Placeholder until you have a real logo. */
export function LogoMark(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden {...props}>
      <path d="M2 22V15h6v7H2Z" />
      <path d="M9 22V9h6v13H9Z" opacity="0.75" />
      <path d="M16 22V2h6v20h-6Z" opacity="0.5" />
    </svg>
  );
}
