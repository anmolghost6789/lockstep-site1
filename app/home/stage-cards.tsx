'use client';

import * as React from 'react';
import {
  BookOpenCheck,
  ClipboardCheck,
  FileText,
  FlaskConical,
  GitPullRequest,
  Layers,
  Lightbulb,
  Radar,
  Rocket,
  ScrollText,
  ShieldCheck,
  Waypoints,
} from 'lucide-react';

import { AIChatCard } from '@/components/spectrumui/ai-chat-card';
import { RecentActivity } from '@/components/spectrumui/recent-activity';
import { NavListCard } from '@/components/spectrumui/nav-list-card';
import { FAQTabsCard } from '@/components/spectrumui/faq-tabs-card';
import { AgentPlan } from '@/components/spectrumui/blocks/ai-assistants/agent-plan';
import { ApprovalCard } from '@/components/spectrumui/blocks/ai-assistants/approval-card';
import { AgentSteps } from '@/components/spectrumui/blocks/ai-assistants/agent-steps';
import { DiffView } from '@/components/spectrumui/blocks/ai-assistants/diff-view';

/** 01 Intent: the business goal that starts a cycle. */
export function IntentCard() {
  return (
    <AIChatCard
      title="New intent"
      subtitle="What should the agents build?"
      greeting="Morning, Priya!"
      prompt="Describe a business goal. Lockstep turns it into a requirements spec for you to approve."
      placeholder="Describe the outcome you need…"
      prompts={[
        'Cut KYC review from 3 days to same-day, with an analyst signing off every high-risk case',
        'Triage new insurance claims in minutes, and route anything over $10k to an adjuster',
        'Summarise adverse event reports for the safety team, citing the source for every finding',
        'Answer employee policy questions with citations, and hand anything legal to HR',
      ]}
      className="min-h-[560px]"
    />
  );
}

/** Live feed of the lifecycle agents and the people signing their work. */
export function LifecycleActivity() {
  return (
    <RecentActivity
      title="Lifecycle activity"
      items={[
        { icon: <Lightbulb />, title: 'Requirements Agent', duration: '42s', description: 'Drafted the KYC review spec after 3 clarifying questions', timeAgo: '2M' },
        { icon: <ClipboardCheck />, title: 'Spec Approved', description: 'Priya Nair approved adlc/01-aiprs.md', timeAgo: '4M' },
        { icon: <Layers />, title: 'Architect Agent', duration: '1m', description: 'Proposed a Level-1 plan with 5 units and an ADR for model choice', timeAgo: '9M' },
        { icon: <Waypoints />, title: 'Build Agent', duration: '38s', description: 'Completed bolt 3 of 5: mismatch detector, 11 tests passing', timeAgo: '14M' },
        { icon: <GitPullRequest />, title: 'Code Review', description: 'Tomás Reyes approved the pull request for agents/kyc', timeAgo: '18M' },
        { icon: <FlaskConical />, title: 'Evaluation Agent', duration: '2m', description: 'Ran 400 past cases: accuracy 0.95, zero missed high-risk', timeAgo: '22M' },
        { icon: <ShieldCheck />, title: 'Policy Check', duration: '6s', description: 'Security pack passed, no secrets or PII in prompts', timeAgo: '23M' },
        { icon: <Rocket />, title: 'Release Agent', duration: '51s', description: 'Packaged release with versioned prompts and a runbook', timeAgo: '31M' },
        { icon: <Radar />, title: 'Observability Agent', duration: '12s', description: 'Flagged rising false positives on company names, added to backlog', timeAgo: '1H' },
      ]}
    />
  );
}

/** 02 Level-1 plan the reviewer edits before the build starts. */
export function PlanCard() {
  return (
    <AgentPlan
      title="Level-1 plan"
      runLabel="Approve plan"
      steps={[
        { id: 'intake', title: 'Document intake agent', detail: 'Extracts details from ID, address and company documents.' },
        { id: 'screen', title: 'Watchlist screening', detail: 'Checks sanctions and PEP lists via the approved provider.' },
        { id: 'mismatch', title: 'Mismatch detector', detail: 'Flags inconsistencies across documents, with evidence.' },
        { id: 'case', title: 'Case update via MCP', detail: 'Writes the outcome to the KYC system through an allow-listed server.' },
        { id: 'evals', title: 'Evaluation suite', detail: 'Accuracy, false positives and policy checks on 400 past cases.' },
      ]}
    />
  );
}

/** Human gate between phases. */
export function GateCard() {
  return (
    <ApprovalCard
      title="Promote to production?"
      description="All five evaluation thresholds pass. Rollout starts on 10% of new applications with the runbook attached."
      meta="adlc/05-release.md"
      approveLabel="Approve release"
      rejectLabel="Hold"
      approvedMessage="Release approved"
      rejectedMessage="Release held"
    />
  );
}

/** Artifacts and governance, shown as a pair of nav cards. */
export function ArtifactNav() {
  return (
    <div className="grid grid-cols-2 items-start gap-3">
      <NavListCard
        title="Artifacts"
        items={[
          { icon: <FileText />, label: 'AIPRS' },
          { icon: <Layers />, label: 'Blueprint' },
          { icon: <BookOpenCheck />, label: 'Scorecard' },
        ]}
      />
      <NavListCard
        title="Governance"
        items={[
          { icon: <ShieldCheck />, label: 'Policies' },
          { icon: <ScrollText />, label: 'Audit log' },
          { icon: <Waypoints />, label: 'MCP servers' },
        ]}
      />
    </div>
  );
}

/** 03 Bolts: short build-and-test cycles. */
export function BoltsCard() {
  return (
    <div className="w-full rounded-2xl border border-black/[0.08] bg-white p-4 shadow-xs dark:border-white/[0.09] dark:bg-[#0B0B0D]">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-[13px] font-semibold tracking-[-0.1px] text-neutral-900 dark:text-neutral-100">Bolts</h3>
        <span className="font-mono text-[10.5px] tabular-nums text-neutral-400 dark:text-neutral-500">3/5 done</span>
      </div>
      <AgentSteps
        steps={[
          { id: 'b1', name: 'bolt.1 document-intake', status: 'success', startedAt: 0, completedAt: 38_400, args: { tests: 14 }, result: '14 tests pass. Field extraction is 97% accurate on the labelled sample.' },
          {
            id: 'b2',
            name: 'bolt.2 watchlist-screening',
            status: 'success',
            startedAt: 0,
            completedAt: 52_100,
            args: { lists: 2 },
            children: [
              { id: 'b2a', name: 'screen.sanctions', status: 'success', parallel: true, result: 'Consolidated sanctions lists, daily refresh.' },
              { id: 'b2b', name: 'screen.pep', status: 'success', parallel: true, result: 'PEP list via the approved provider.' },
            ],
          },
          { id: 'b3', name: 'bolt.3 mismatch-detector', status: 'success', startedAt: 0, completedAt: 44_700, args: { tests: 11 }, result: 'Every flag cites the documents it compared.' },
          { id: 'b4', name: 'bolt.4 case-update', status: 'running', args: { mcp: 'kyc-system', mode: 'dry-run' } },
          { id: 'b5', name: 'bolt.5 eval-suite', status: 'pending', args: { cases: 400 } },
        ]}
      />
    </div>
  );
}

/** Per-file human review of what the agent wrote. */
export function ReviewCard() {
  return (
    <DiffView
      diffs={[
        {
          id: 'policy',
          path: 'agents/kyc/risk-policy.ts',
          additions: 2,
          deletions: 1,
          lines: [
            { type: 'context', text: 'export const riskPolicy = {' },
            { type: 'remove', text: "  autoApprove: ['low', 'medium']," },
            { type: 'add', text: "  autoApprove: ['low'], // NFR-2" },
            { type: 'add', text: "  approverRole: 'kyc-analyst'," },
            { type: 'context', text: '};' },
          ],
        },
      ]}
    />
  );
}

/** Questions buyers ask, grouped the way reviewers think. */
export function LifecycleFaq() {
  return (
    <FAQTabsCard
      tabs={[
        {
          label: 'Security',
          faqs: [
            { question: 'Does code or data leave our network?', answer: 'Code and artifacts stay in your repos. Model calls go through your existing Copilot plan.' },
            { question: 'Can the agent call any tool?', answer: 'No. It follows Copilot’s MCP registry and allow-list policies.' },
            { question: 'Is every approval recorded?', answer: 'Yes. Gates are pull request reviews, attributed and logged by GitHub.' },
          ],
        },
        {
          label: 'Models',
          faqs: [
            { question: 'Which models are supported?', answer: 'Whatever your Copilot plan provides, including your own configured models.' },
            { question: 'Do we need a second API key?', answer: 'No. Lockstep uses your Copilot connection; there are no keys on laptops.' },
          ],
        },
        {
          label: 'Rollout',
          faqs: [
            { question: 'Do we need all six phases?', answer: 'No. Most teams start with Build and Evaluate, then add the other gates.' },
            { question: 'How long is a pilot?', answer: 'One team, one real intent, four to six weeks.' },
          ],
        },
      ]}
      footerLabel="Talk to our team"
    />
  );
}
