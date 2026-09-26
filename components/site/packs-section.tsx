import fs from 'node:fs';
import path from 'node:path';
import Link from 'next/link';
import { ArrowRight, ArrowUpRight, Blocks, DraftingCompass, FileText, Hammer, Landmark, Layers, Pill, Search, ShieldPlus } from 'lucide-react';

import { AnimateEnter } from '@/app/home/AnimateEnter';
import { cn } from '@/lib/utils';
import { CardCaption, SectionLabel } from './section-label';

/** Counts a shipped pack's files and skills at build time, so the page never drifts from the packs. */
function packStats(rel: string) {
  const root = path.join(process.cwd(), rel);
  if (!fs.existsSync(root)) return { files: 0, skills: 0 };
  let files = 0;
  const walk = (dir: string) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      if (e.name === '__pycache__' || e.name === 'node_modules') continue;
      const full = path.join(dir, e.name);
      if (e.isDirectory()) walk(full);
      else files++;
    }
  };
  walk(root);
  // Claude Code projects keep skills in .claude/skills; Claude Code plugins keep them in skills/.
  const skills = ['.claude/skills', 'skills']
    .map((rel) => path.join(root, rel))
    .filter((dir) => fs.existsSync(dir))
    .reduce((n, dir) => n + fs.readdirSync(dir).filter((d) => fs.existsSync(path.join(dir, d, 'SKILL.md'))).length, 0);
  return { files, skills };
}

type Status = 'Available' | 'In development' | 'Built in pilots';

export function PacksSection() {
  const adlc = packStats('adlc-agent');
  // The data-engineering suite: agents that hand off to each other, from first evidence to production code.
  const suite = [
    { id: 'discovery-agent', icon: Search, name: 'Discovery', body: 'Evidence, open questions and a knowledge layer for the agents after it', ...packStats('packs/discovery-agent') },
    { id: 'requirements-agent', icon: FileText, name: 'Requirements', body: 'BRD, FRD, URS and Jira stories, traced to evidence', ...packStats('packs/requirements-agent') },
    { id: 'design-agent', icon: DraftingCompass, name: 'Design', body: 'STTM, data model, data quality and ER diagrams', ...packStats('packs/design-agent') },
    { id: 'build-agent', icon: Hammer, name: 'Build', body: 'DDL, DML, pipelines, data quality checks and tests', ...packStats('packs/build-agent') },
  ];
  const suiteSkills = suite.reduce((n, a) => n + a.skills, 0);
  const suiteFiles = suite.reduce((n, a) => n + a.files, 0);
  const packs: { id: string; icon: typeof Layers; name: string; body: string; status: Status; meta?: string }[] = [
    {
      id: 'adlc',
      icon: Layers,
      name: 'ADLC lifecycle',
      body: 'The six phases, gates, templates, contracts, policy hooks and subagents behind every Lockstep run.',
      status: 'Available',
      meta: `${adlc.skills} skills · ${adlc.files} files`,
    },
    {
      id: 'banking',
      icon: Landmark,
      name: 'Banking',
      body: 'Model risk management and KYC: documentation, validation and approval trails for models and agents.',
      status: 'In development',
    },
    {
      id: 'life-sciences',
      icon: Pill,
      name: 'Life sciences',
      body: 'Software validation evidence for GxP-regulated systems, mapped to the records quality teams review.',
      status: 'In development',
    },
    {
      id: 'insurance',
      icon: ShieldPlus,
      name: 'Insurance',
      body: 'Claims and underwriting controls: triage rules, referral limits and the evidence adjusters and auditors expect.',
      status: 'In development',
    },
    {
      id: 'your-standards',
      icon: Blocks,
      name: 'Your standards',
      body: 'A private pack encoding your own architecture rules, policies and review checklists.',
      status: 'Built in pilots',
    },
  ];

  return (
    <section id="packs" className="container scroll-mt-16 py-16">
      <AnimateEnter duration={0.55} className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-3">
          <SectionLabel>Packs</SectionLabel>
          <h2 className="font-spectral text-[24px] leading-[28.8px] tracking-[-1px] text-[#2d2f2e] dark:text-neutral-100">
            Domain expertise,
            <br />
            packaged for your agents
          </h2>
          <p className="max-w-[560px] font-inter text-[14px] font-medium leading-[20px] text-[#646464] dark:text-neutral-400">
            Coding agents know how to write code, not how your industry is regulated. Packs add the domain rules, templates, evaluation
            suites and evidence mappings for your field, versioned and approved in the registry before anyone can use them.
          </p>
        </div>
        <Link
          href="/registry"
          className="inline-flex h-10 items-center gap-1.5 rounded-full px-4 font-inter text-[14px] text-neutral-900 shadow-[0_0_0_1px_rgba(0,0,0,0.1)] transition-colors hover:bg-neutral-50 dark:text-neutral-100 dark:shadow-[0_0_0_1px_rgba(255,255,255,0.12)] dark:hover:bg-neutral-900"
        >
          Browse the registry
          <ArrowUpRight className="size-3.5" />
        </Link>
      </AnimateEnter>

      <AnimateEnter duration={0.55} className="mt-10">
        <CardCaption>data-engineering suite</CardCaption>
        <article className="rounded-2xl border border-black/[0.08] bg-white p-5 shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D] sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="max-w-[640px]">
              <h3 className="font-spectral text-[22px] leading-[1.2] tracking-[-0.5px] text-[#080808] dark:text-neutral-100">Data engineering, from first evidence to production code</h3>
              <p className="mt-2 font-inter text-[14px] leading-[1.6] text-neutral-600 dark:text-neutral-400">
                Four agents that hand off to each other. Each one checks its inputs, records what it couldn’t confirm, and produces reviewable
                artifacts the next one builds on.
              </p>
            </div>
            <span className="inline-flex h-6 items-center rounded-full bg-neutral-900 px-2.5 font-inter text-[11px] font-medium text-white dark:bg-white dark:text-neutral-900">Available</span>
          </div>
          <ol className="mt-6 grid gap-3 md:grid-cols-4">
            {suite.map(({ id, icon: Icon, name, body, skills, files }, i) => (
              <li key={id} className="relative">
                <a
                  href={`/registry/skills/${id}`}
                  className="group block h-full rounded-xl border border-black/[0.08] bg-neutral-50/60 p-4 transition-colors hover:border-black/20 dark:border-white/[0.09] dark:bg-white/[0.02] dark:hover:border-white/20"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-neutral-900 text-white dark:bg-white dark:text-neutral-900">
                      <Icon className="size-4" />
                    </span>
                    <span className="font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400">{String(i + 1).padStart(2, '0')}</span>
                  </div>
                  <p className="mt-3 font-inter text-[15px] font-semibold text-neutral-900 dark:text-neutral-100">{name}</p>
                  <p className="mt-1 font-inter text-[13px] leading-[1.5] text-neutral-600 dark:text-neutral-400">{body}</p>
                  <p className="mt-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">
                    {skills} skills · {files} files
                  </p>
                </a>
                {i < suite.length - 1 && (
                  <ArrowRight aria-hidden className="absolute -right-[11px] top-1/2 z-10 hidden size-4 -translate-y-1/2 rounded-full bg-white text-neutral-400 md:block dark:bg-[#0B0B0D]" />
                )}
              </li>
            ))}
          </ol>
          <p className="mt-4 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">
            {suite.length} agents · {suiteSkills} skills · {suiteFiles} files
          </p>
        </article>
      </AnimateEnter>

      <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {packs.map(({ id, icon: Icon, name, body, status, meta }, i) => (
          <AnimateEnter key={id} duration={0.55} delay={i * 0.05} className="flex flex-col">
            <CardCaption>{id}</CardCaption>
            <article className="flex h-full flex-col rounded-2xl border border-black/[0.08] bg-white p-4 shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]">
              <div className="flex items-start justify-between gap-2">
                <span className="grid size-8 place-items-center rounded-lg bg-neutral-100 text-neutral-700 dark:bg-white/[0.07] dark:text-neutral-300">
                  <Icon className="size-4" />
                </span>
                <span
                  className={cn(
                    'inline-flex h-6 items-center whitespace-nowrap rounded-full px-2.5 font-inter text-[11px] font-medium',
                    status === 'Available'
                      ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900'
                      : 'border border-[#f9452d]/60 text-[#c2321e] dark:border-[#E1F435]/60 dark:text-[#E1F435]',
                  )}
                >
                  {status}
                </span>
              </div>
              <h3 className="mt-3 font-spectral text-[18px] leading-[1.25] tracking-[-0.4px] text-[#080808] dark:text-neutral-100">{name}</h3>
              <p className="mt-2 flex-1 font-inter text-[13px] leading-[1.5] text-neutral-600 dark:text-neutral-400">{body}</p>
              {meta && <p className="mt-3 font-mono text-[10.5px] uppercase tracking-[0.04em] text-neutral-400 dark:text-neutral-500">{meta}</p>}
            </article>
          </AnimateEnter>
        ))}
      </div>
      <p className="mt-6 max-w-[760px] font-inter text-[12.5px] leading-[1.6] text-neutral-500 dark:text-neutral-400">
        EU AI Act record-keeping and human-oversight checks are being added to the banking and life-sciences packs. Packs support
        your compliance work; they don’t make you compliant on their own.
      </p>
    </section>
  );
}
