import 'server-only';

import fs from 'node:fs';
import path from 'node:path';

/**
 * Reads the ADLC skill package at build time so the site always shows the exact
 * files that ship in adlc-agent/. Nothing here runs in the browser.
 */

const PACKAGE_DIR = path.join(process.cwd(), 'adlc-agent');

export interface SkillFile {
  path: string;
  label: string;
  group: 'Phase' | 'Contracts' | 'Shared' | 'Governance';
  lang: 'markdown' | 'yaml' | 'json' | 'python';
  content: string;
}

export interface PhaseSkill {
  id: string;
  number: string;
  label: string;
  command: string;
  description: string;
  artifact: string;
  gate: {
    id: string;
    roles: string[];
    riskRoles: Record<string, string[]>;
    separationOfDuties: boolean;
  };
  policies: string[];
  model: string;
  subagents: string[];
  files: SkillFile[];
}

function read(rel: string): string {
  return fs.readFileSync(path.join(PACKAGE_DIR, rel), 'utf8');
}

function langOf(rel: string): SkillFile['lang'] {
  if (rel.endsWith('.md')) return 'markdown';
  if (rel.endsWith('.yaml') || rel.endsWith('.yml')) return 'yaml';
  if (rel.endsWith('.py')) return 'python';
  return 'json';
}

function file(rel: string, label: string, group: SkillFile['group']): SkillFile {
  return { path: rel, label, group, lang: langOf(rel), content: read(rel) };
}

function frontmatterDescription(md: string): string {
  const fm = md.match(/^---\n([\s\S]*?)\n---/);
  if (!fm) return '';
  const block = fm[1].match(/description:\s*>-\n((?:\s{2,}.+\n?)+)/);
  if (block) return block[1].replace(/\s+/g, ' ').trim();
  const line = fm[1].match(/description:\s*"?(.+?)"?\s*$/m);
  return line ? line[1] : '';
}

const SUBAGENTS: Record<string, string[]> = {
  'discover-define': ['requirements-analyst'],
  'architect-design': ['solution-architect'],
  'build-orchestrate': ['bolt-builder'],
  'evaluate-validate': ['adlc-evaluator'],
  'release-operate': ['release-auditor'],
  'observe-evolve': [],
};

export interface SkillPackage {
  phases: PhaseSkill[];
  /** Shared, contract and governance files, sent once rather than per phase. */
  common: SkillFile[];
}

export function getSkillPackage(): SkillPackage {
  const manifest = JSON.parse(read('.claude/skills/adlc/workflow_manifest.json'));
  const roles = JSON.parse(read('config/governance/gate_roles.json'));
  const config = JSON.parse(read('config/project_config.json'));

  const shared: SkillFile[] = [
    file('.claude/skills/adlc/SKILL.md', 'adlc/SKILL.md (shared protocol)', 'Shared'),
    file('CLAUDE.md', 'CLAUDE.md', 'Shared'),
  ];
  const contracts: SkillFile[] = [
    file('.claude/skills/adlc/specs/gate_contract.yaml', 'gate_contract.yaml', 'Contracts'),
    file('.claude/skills/adlc/specs/traceability_contract.yaml', 'traceability_contract.yaml', 'Contracts'),
    file('.claude/skills/adlc/specs/policy_contract.yaml', 'policy_contract.yaml', 'Contracts'),
  ];
  const governance: SkillFile[] = [
    file('config/governance/gate_roles.json', 'gate_roles.json', 'Governance'),
    file('config/governance/mcp_allowlist.json', 'mcp_allowlist.json', 'Governance'),
    file('.claude/hooks/pre_tool_guard.py', 'pre_tool_guard.py (hook)', 'Governance'),
    file('.claude/skills/adlc/scripts/adlc_gate.py', 'adlc_gate.py', 'Governance'),
    file('docs/enterprise-readiness.md', 'enterprise-readiness.md', 'Governance'),
  ];

  const phases = manifest.phases.map((p: Record<string, string>) => {
    const skillPath = p.skill;
    const skill = read(skillPath);
    const gate = roles.gates[p.gate];
    const agents = SUBAGENTS[p.id] ?? [];
    const phaseFiles: SkillFile[] = [
      file(skillPath, 'SKILL.md', 'Phase'),
      file(p.template, p.template.split('/').pop() as string, 'Phase'),
      ...agents.map((a) => file(`.claude/agents/${a}.md`, `agents/${a}.md`, 'Phase')),
    ];
    return {
      id: p.id,
      number: p.number,
      label: p.label,
      command: `/${p.id}`,
      description: frontmatterDescription(skill),
      artifact: p.artifact,
      gate: {
        id: p.gate,
        roles: gate.roles,
        riskRoles: gate.additional_roles_if_risk ?? {},
        separationOfDuties: roles.separation_of_duties,
      },
      policies: config.policy_packs[p.id] ?? [],
      model: config.models[p.id],
      subagents: agents,
      files: phaseFiles,
    } satisfies PhaseSkill;
  });

  return { phases, common: [...shared, ...contracts, ...governance] };
}
