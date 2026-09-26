'use client';

import { DataTable, type DataTableColumn } from '@/components/spectrumui/data-table';

type ActorKind = 'agent' | 'person';

interface GateEvent {
  id: string;
  time: string;
  actor: string;
  kind: ActorKind;
  action: string;
  artifact: string;
}

const EVENTS: GateEvent[] = [
  { id: 'e14', time: '16:42', actor: 'Priya Nair', kind: 'person', action: 'release.approved', artifact: '05-release.md' },
  { id: 'e13', time: '16:39', actor: 'agent', kind: 'agent', action: 'eval.scored', artifact: '04-scorecard.json' },
  { id: 'e12', time: '16:31', actor: 'Tomás Reyes', kind: 'person', action: 'diff.accepted', artifact: 'risk-policy.ts' },
  { id: 'e11', time: '16:30', actor: 'agent', kind: 'agent', action: 'policy.checked', artifact: 'org/security-pack' },
  { id: 'e10', time: '16:18', actor: 'agent', kind: 'agent', action: 'bolt.completed', artifact: '03-units.yaml' },
  { id: 'e09', time: '15:57', actor: 'agent', kind: 'agent', action: 'mcp.called', artifact: 'kyc-system (dry run)' },
  { id: 'e08', time: '15:40', actor: 'Lena Fischer', kind: 'person', action: 'plan.approved', artifact: '02-blueprint.md' },
  { id: 'e07', time: '15:36', actor: 'agent', kind: 'agent', action: 'plan.proposed', artifact: '02-blueprint.md' },
  { id: 'e06', time: '15:12', actor: 'Lena Fischer', kind: 'person', action: 'adr.signed', artifact: 'adr-004-model-choice.md' },
  { id: 'e05', time: '14:58', actor: 'Priya Nair', kind: 'person', action: 'spec.approved', artifact: '01-aiprs.md' },
  { id: 'e04', time: '14:51', actor: 'agent', kind: 'agent', action: 'spec.revised', artifact: '01-aiprs.md' },
  { id: 'e03', time: '14:44', actor: 'Priya Nair', kind: 'person', action: 'spec.changes_requested', artifact: '01-aiprs.md' },
  { id: 'e02', time: '14:30', actor: 'agent', kind: 'agent', action: 'spec.drafted', artifact: '01-aiprs.md' },
  { id: 'e01', time: '14:21', actor: 'Priya Nair', kind: 'person', action: 'intent.filed', artifact: 'intent-0192' },
];

const columns: DataTableColumn<GateEvent>[] = [
  {
    id: 'time',
    header: 'Time',
    sortable: true,
    value: (row) => row.time,
    cell: (row) => <span className="tabular-nums">{row.time}</span>,
  },
  {
    id: 'actor',
    header: 'Who',
    sortable: true,
    value: (row) => row.actor,
    cell: (row) => (
      <span className="flex items-center gap-2 font-normal">
        <span
          aria-hidden
          className={row.kind === 'agent' ? 'size-2 shrink-0 rounded-full bg-neutral-900 dark:bg-neutral-100' : 'size-2 shrink-0 rounded-full bg-[#f9452d] dark:bg-[#E1F435]'}
        />
        <span className="truncate">{row.kind === 'agent' ? 'Agent' : row.actor}</span>
      </span>
    ),
  },
  {
    id: 'action',
    header: 'Action',
    sortable: true,
    value: (row) => row.action,
    cell: (row) => <span className="font-mono text-xs">{row.action}</span>,
  },
  {
    id: 'kind',
    header: 'Actor',
    hideBelow: 'md',
    value: (row) => row.kind,
    cell: (row) => <span className="text-neutral-500">{row.kind}</span>,
  },
  {
    id: 'artifact',
    header: 'Artifact',
    hideBelow: 'lg',
    value: (row) => row.artifact,
    cell: (row) => <span className="font-mono text-xs">{row.artifact}</span>,
  },
];

export function GateAuditTable() {
  return (
    <DataTable
      data={EVENTS}
      columns={columns}
      rowId={(row) => row.id}
      rowLabel={(row) => `${row.action} at ${row.time}`}
      caption="Gate and agent events for intent 0192, newest first."
      variant="bordered"
      density="compact"
      searchable
      searchPlaceholder="Search events"
      quickFilter={{ columnId: 'kind', label: 'Filter by actor' }}
      stickyHeader
      maxHeight={360}
      defaultSort={{ columnId: 'time', direction: 'desc' }}
    />
  );
}
