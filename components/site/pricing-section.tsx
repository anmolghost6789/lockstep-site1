import Link from 'next/link';
import { Check } from 'lucide-react';

import { AnimateEnter } from '@/app/home/AnimateEnter';
import { cn } from '@/lib/utils';
import { PILOT_HREF } from '@/lib/site';
import { CardCaption, SectionLabel } from './section-label';

type Tier = {
  id: string;
  name: string;
  price: string;
  unit: string;
  logic: string;
  blurb: string;
  cta: string;
  href: string;
  features: string[];
  highlight?: boolean;
  addon?: boolean;
  note?: string;
};

const TIERS: Tier[] = [
  {
    id: 'team',
    name: 'Team',
    price: '$19',
    unit: 'per developer / month',
    logic: 'Per developer',
    blurb: 'The core harness, workflows and approvals for one engineering team.',
    cta: 'Book a pilot',
    href: PILOT_HREF,
    highlight: true,
    features: [
      'Core harness: @lockstep in Copilot Chat',
      'Six-phase workflows, from intent to production',
      'Named-role approvals via CODEOWNERS and branch protection',
      'ADLC and data-engineering packs',
      'Approvers who only review are free',
    ],
  },
  {
    id: 'business',
    name: 'Business',
    price: 'Platform + seats',
    unit: 'annual or monthly',
    logic: 'Platform fee + seats',
    blurb: 'For engineering organisations running several teams on one governed process.',
    cta: 'Talk to us',
    href: PILOT_HREF,
    features: [
      'Everything in Team',
      'Delivery metrics for every phase and gate',
      'Policy packs, set once for the organisation',
      'Analytics across teams and intents',
      'Org controls: roles, required packs, publish approval',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Annual contract',
    unit: 'volume pricing',
    logic: 'Annual contract',
    blurb: 'For enterprises that need evidence, governance and control at scale.',
    cta: 'Contact sales',
    href: PILOT_HREF,
    features: [
      'Everything in Business',
      'Benchmarking across teams and against baselines',
      'Compliance evidence and audit exports',
      'Governance: SSO, central policy, waivers',
      'Private deployment: registry in your environment',
      'Pilot, onboarding and support SLA',
    ],
  },
  {
    id: 'regulated-packs',
    name: 'Regulated packs',
    price: 'Add-on',
    unit: 'premium, per pack / year',
    logic: 'Add-on / premium',
    blurb: 'Industry controls on top of Business or Enterprise, kept current as rules change.',
    cta: 'Ask about packs',
    href: PILOT_HREF,
    addon: true,
    note: 'In development with design partners',
    features: [
      'Pharma: GxP software validation evidence',
      'Banking: model risk and KYC controls',
      'Insurance: claims and underwriting controls',
      'Evaluation suites and evidence mappings per pack',
      'Quarterly updates as regulations change',
    ],
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="container scroll-mt-16 py-16">
      <AnimateEnter duration={0.55} className="flex flex-col gap-3">
        <SectionLabel>Pricing</SectionLabel>
        <h2 className="font-spectral text-[24px] leading-[28.8px] tracking-[-1px] text-[#2d2f2e] dark:text-neutral-100">
          From one team
          <br />
          to the whole organisation
        </h2>
        <p className="max-w-[548px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
          Four layers: start with a team, grow into the organisation, add regulated controls when you need them. This is planned
          pricing for general availability; early-access teams start with a paid pilot that converts into their first year.
        </p>
      </AnimateEnter>

      <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {TIERS.map((tier, index) => (
          <AnimateEnter key={tier.id} duration={0.55} delay={index * 0.06} className="flex flex-col">
            <CardCaption>{tier.highlight ? `${tier.id} · start here` : tier.addon ? `${tier.id} · add-on` : tier.id}</CardCaption>
            <article
              className={cn(
                'flex h-full flex-col rounded-2xl border bg-white p-6 shadow-xs dark:bg-[#0B0B0D]',
                tier.highlight
                  ? 'border-neutral-900 ring-1 ring-neutral-900 dark:border-[#E1F435]/70 dark:ring-[#E1F435]/40'
                  : tier.addon
                    ? 'border-dashed border-[#f9452d]/50 bg-[#f9452d]/[0.03] dark:border-[#E1F435]/40 dark:bg-[#E1F435]/[0.03]'
                    : 'border-black/[0.08] dark:border-white/[0.09]',
              )}
            >
              {tier.note && (
                <span className="mb-3 inline-flex w-fit items-center rounded-full border border-[#f9452d]/50 px-2.5 py-0.5 font-inter text-[11px] font-medium text-[#c2321e] dark:border-[#E1F435]/50 dark:text-[#E1F435]">
                  {tier.note}
                </span>
              )}
              <h3 className="font-spectral text-[22px] leading-none tracking-[-0.5px] text-[#080808] dark:text-neutral-100">{tier.name}</h3>
              <p className="mt-2 min-h-[40px] font-inter text-[13px] leading-[1.5] text-neutral-600 dark:text-neutral-400">{tier.blurb}</p>
              <div className="mt-5 flex min-h-[44px] flex-wrap items-end gap-x-2 gap-y-1">
                <span
                  className={cn(
                    'font-spectral leading-none text-[#080808] dark:text-neutral-100',
                    tier.price.startsWith('$') ? 'whitespace-nowrap text-[40px] tracking-[-1.5px]' : 'text-[27px] tracking-[-0.8px]',
                  )}
                >
                  {tier.price}
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.04em] text-neutral-500 dark:text-neutral-400">{tier.unit}</span>
              </div>
              <p className="mt-2 font-inter text-[12px] text-neutral-500 dark:text-neutral-400">
                Pricing logic: <span className="font-medium text-neutral-800 dark:text-neutral-200">{tier.logic}</span>
              </p>
              <Link
                href={tier.href}
                className={cn(
                  'mt-6 inline-flex h-11 w-full items-center justify-center rounded-full font-inter text-[15px] transition-[transform,background-color] duration-200 ease-out active:scale-[0.98]',
                  tier.highlight
                    ? 'bg-neutral-900 text-white hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200'
                    : 'bg-white text-black shadow-[0_0_0_1px_rgba(0,0,0,0.08)] hover:bg-neutral-50 dark:bg-neutral-900 dark:text-white dark:shadow-[0_0_0_1px_rgba(255,255,255,0.1)] dark:hover:bg-neutral-800',
                )}
              >
                {tier.cta}
              </Link>
              <ul className="mt-6 space-y-2.5 border-t border-black/[0.06] pt-5 dark:border-white/[0.07]">
                {tier.features.map((f) => (
                  <li key={f} className="flex gap-2.5 font-inter text-[13px] leading-[1.5] text-neutral-700 dark:text-neutral-300">
                    <Check className="mt-[3px] size-3.5 shrink-0 text-[#f9452d] dark:text-[#E1F435]" strokeWidth={2.5} />
                    {f}
                  </li>
                ))}
              </ul>
            </article>
          </AnimateEnter>
        ))}
      </div>

      <p className="mt-6 max-w-[760px] font-inter text-[12.5px] leading-[1.6] text-neutral-500 dark:text-neutral-400">
        Prices in USD, excluding taxes. Requires GitHub Copilot Business or Enterprise. Phases use your Copilot models and count towards your Copilot usage, which Lockstep reports per phase. Regulated packs are added to Business or Enterprise. Metrics, analytics and benchmarking arrive with general availability.
      </p>
    </section>
  );
}
