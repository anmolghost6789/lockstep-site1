import { Suspense } from 'react';
import { notFound } from 'next/navigation';
import { headers } from 'next/headers';

import { requireUser, can } from '@/lib/registry/auth';
import { store } from '@/lib/registry/store';
import { compareVersions } from '@/lib/registry/diff';
import { compareSemver } from '@/lib/registry/validate';
import { packStats, packView, timeAgo } from '@/lib/registry/pack-view';
import { PackDetail, type PackDetailProps } from '@/components/registry/pack-detail';

const shortDate = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });

export default async function SkillPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ v?: string; reviewed?: string; edited?: string }>;
}) {
  const user = await requireUser();
  const { slug } = await params;
  const { v, reviewed, edited } = await searchParams;
  const skill = await store().getSkill(slug);
  if (!skill) notFound();
  const all = await store().listVersions(slug);
  const versions = can(user, 'publisher') ? all : all.filter((x) => x.status === 'approved');
  if (versions.length === 0) notFound();
  const latestApproved = versions.find((x) => x.status === 'approved');
  const selected = versions.find((x) => x.id === v) ?? latestApproved ?? versions[0];

  // The version this one replaces, so reviewers see exactly what changed.
  const previous = all
    .filter((x) => x.id !== selected.id && compareSemver(x.version, selected.version) < 0)
    .sort((a, b) => compareSemver(b.version, a.version))[0];
  const view = packView(selected, skill.createdBy);
  const stats = packStats(slug, await store().listTelemetry(1000));

  const host = (await headers()).get('host') ?? 'your-registry';
  const proto = host.startsWith('localhost') || host.startsWith('127.') ? 'http' : 'https';
  const registryUrl = `${proto}://${host}`;

  let banner: PackDetailProps['banner'] = null;
  if (edited && selected.status === 'pending') banner = { kind: 'ok', text: `Saved as ${selected.version}. It’s waiting for an admin other than you to approve it.` };
  else if (reviewed && selected.status === reviewed)
    banner = reviewed === 'approved' ? { kind: 'ok', text: `Approved. Extensions can now install ${selected.version}.` } : { kind: 'warn', text: 'Rejected. The submitter can see your note.' };
  else if (selected.status === 'rejected' && selected.reviewNote) banner = { kind: 'error', text: `Rejected by ${selected.reviewedBy}: ${selected.reviewNote}` };
  else if (selected.status === 'pending') banner = { kind: 'warn', text: `${selected.version} is waiting for approval. Open Changes to review what’s different from ${previous?.version ?? 'the previous version'}.` };

  return (
    <Suspense>
      <PackDetail
        slug={slug}
        name={skill.name}
        description={skill.description}
        publisher={view.publisher}
        icon={view.icon}
        kind={(selected.frontmatter as { kind?: string }).kind === 'pack' ? 'pack' : 'skill'}
        updatedAgo={timeAgo(selected.reviewedAt ?? selected.submittedAt)}
        version={{
          id: selected.id, version: selected.version, status: selected.status, note: selected.note, submittedBy: selected.submittedBy,
          submittedAt: selected.submittedAt, reviewedBy: selected.reviewedBy, reviewNote: selected.reviewNote, sha256: selected.sha256,
        }}
        versions={versions.map((x) => ({ id: x.id, version: x.version, status: x.status, date: `synced ${shortDate(x.reviewedAt ?? x.submittedAt)}`, latestApproved: x.id === latestApproved?.id }))}
        files={selected.files}
        skills={view.skills}
        connectors={view.connectors}
        sendsData={view.sendsData}
        categories={view.categories}
        examples={view.examples}
        stats={stats}
        apiUrl={`${registryUrl}/api/registry/skills/${slug}?version=${selected.version}`}
        registryUrl={registryUrl}
        canEdit={can(user, 'publisher')}
        canReview={can(user, 'admin')}
        ownSubmission={selected.submittedBy === user.email}
        changes={previous ? compareVersions(previous.files, selected.files) : null}
        fromVersion={previous?.version ?? null}
        banner={banner}
      />
    </Suspense>
  );
}
