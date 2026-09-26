import { requireUser } from '@/lib/registry/auth';
import { store, storageKind } from '@/lib/registry/store';
import { revokeToken } from '@/app/registry/actions';
import { TokenForm, UserForm } from '@/components/registry/client';
import { SectionLabel } from '@/components/site/section-label';
import { card, h1 } from '@/components/registry/ui';

const when = (iso: string | null) => (iso ? new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'never');

export default async function SettingsPage() {
  await requireUser('admin');
  const [tokens, users, audit] = await Promise.all([store().listTokens(), store().listUsers(), store().listAudit(30)]);
  return (
    <div className="space-y-12">
      <div className="flex flex-col gap-3">
        <SectionLabel>Settings</SectionLabel>
        <h1 className={h1}>Access and activity</h1>
        <p className="font-inter text-[13px] text-neutral-500">
          Storage: <span className="font-mono">{storageKind() === 'postgres' ? 'Postgres' : 'local files (.data/)'}</span>
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="text-[16px] font-medium text-neutral-900 dark:text-neutral-100">API tokens</h2>
        <p className="max-w-[640px] text-[13.5px] text-neutral-600 dark:text-neutral-400">
          The Lockstep extension uses a token to install approved skills from this registry. Create one per team or environment.
        </p>
        <TokenForm />
        <div className={`${card} divide-y divide-black/[0.06] dark:divide-white/[0.07]`}>
          {tokens.length === 0 && <p className="p-4 text-[13px] text-neutral-500">No tokens yet.</p>}
          {tokens.map((t) => (
            <div key={t.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 p-4 text-[13px]">
              <span className="font-medium text-neutral-900 dark:text-neutral-100">{t.name}</span>
              <span className="font-mono text-[12px] text-neutral-500">{t.prefix}…</span>
              <span className="text-neutral-500">last used {when(t.lastUsedAt)}</span>
              {t.revoked ? (
                <span className="ml-auto font-mono text-[11px] uppercase text-red-600">revoked</span>
              ) : (
                <form action={revokeToken} className="ml-auto">
                  <input type="hidden" name="id" value={t.id} />
                  <button className="font-mono text-[11.5px] uppercase text-neutral-500 hover:text-red-600">Revoke</button>
                </form>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-[16px] font-medium text-neutral-900 dark:text-neutral-100">Users</h2>
        <UserForm />
        <div className={`${card} divide-y divide-black/[0.06] dark:divide-white/[0.07]`}>
          {users.map((u) => (
            <div key={u.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 p-4 text-[13px]">
              <span className="font-medium text-neutral-900 dark:text-neutral-100">{u.name}</span>
              <span className="text-neutral-500">{u.email}</span>
              <span className="ml-auto font-mono text-[11px] uppercase text-neutral-500">{u.role}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-[16px] font-medium text-neutral-900 dark:text-neutral-100">Recent activity</h2>
        <div className={`${card} divide-y divide-black/[0.06] dark:divide-white/[0.07]`}>
          {audit.map((a) => (
            <div key={a.id} className="grid grid-cols-[110px_minmax(0,1fr)] gap-3 p-3.5 text-[12.5px] md:grid-cols-[130px_200px_minmax(0,1fr)]">
              <span className="font-mono text-neutral-500">{when(a.ts)}</span>
              <span className="truncate text-neutral-700 dark:text-neutral-300">{a.actor}</span>
              <span className="col-span-2 font-mono text-neutral-900 md:col-span-1 dark:text-neutral-100">
                {a.action} <span className="text-neutral-500">{a.target}</span>
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
