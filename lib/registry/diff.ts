/** Small, dependency-free line diff for reviewing edits between two versions of a pack. */
export type DiffLine = { type: 'same' | 'add' | 'remove'; text: string };

const MAX_LINES = 3000;

export function lineDiff(before: string, after: string): DiffLine[] | null {
  const a = before.split('\n');
  const b = after.split('\n');
  if (a.length > MAX_LINES || b.length > MAX_LINES) return null;
  // Longest common subsequence table, then walk it to produce the edit script.
  const n = a.length, m = b.length;
  const dp: Uint16Array[] = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out: DiffLine[] = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) { out.push({ type: 'same', text: a[i] }); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { out.push({ type: 'remove', text: a[i] }); i++; }
    else { out.push({ type: 'add', text: b[j] }); j++; }
  }
  while (i < n) out.push({ type: 'remove', text: a[i++] });
  while (j < m) out.push({ type: 'add', text: b[j++] });
  return out;
}

/** Collapse long unchanged runs, keeping a few lines of context around each change. */
export function withContext(lines: DiffLine[], context = 3): (DiffLine | { type: 'gap'; count: number })[] {
  const keep = new Array(lines.length).fill(false);
  lines.forEach((l, i) => {
    if (l.type !== 'same') for (let k = Math.max(0, i - context); k <= Math.min(lines.length - 1, i + context); k++) keep[k] = true;
  });
  const out: (DiffLine | { type: 'gap'; count: number })[] = [];
  let gap = 0;
  lines.forEach((l, i) => {
    if (keep[i]) {
      if (gap) out.push({ type: 'gap', count: gap });
      gap = 0;
      out.push(l);
    } else gap++;
  });
  if (gap) out.push({ type: 'gap', count: gap });
  return out;
}

export type FileChange = { path: string; kind: 'added' | 'removed' | 'changed'; binary: boolean; adds: number; removes: number; lines: ReturnType<typeof withContext> | null };

export function compareVersions(
  base: { path: string; content: string; encoding?: string }[],
  next: { path: string; content: string; encoding?: string }[],
): FileChange[] {
  const A = new Map(base.map((f) => [f.path, f]));
  const B = new Map(next.map((f) => [f.path, f]));
  const changes: FileChange[] = [];
  for (const [path, f] of B) {
    const old = A.get(path);
    const binary = f.encoding === 'base64';
    if (!old) {
      const lines = binary ? null : withContext(f.content.split('\n').map((t) => ({ type: 'add' as const, text: t })), 3);
      changes.push({ path, kind: 'added', binary, adds: binary ? 0 : f.content.split('\n').length, removes: 0, lines });
    } else if (old.content !== f.content) {
      const d = binary ? null : lineDiff(old.content, f.content);
      changes.push({ path, kind: 'changed', binary, adds: d ? d.filter((l) => l.type === 'add').length : 0, removes: d ? d.filter((l) => l.type === 'remove').length : 0, lines: d ? withContext(d) : null });
    }
  }
  for (const [path, f] of A) if (!B.has(path)) changes.push({ path, kind: 'removed', binary: f.encoding === 'base64', adds: 0, removes: f.encoding === 'base64' ? 0 : f.content.split('\n').length, lines: null });
  return changes.sort((x, y) => x.path.localeCompare(y.path));
}
