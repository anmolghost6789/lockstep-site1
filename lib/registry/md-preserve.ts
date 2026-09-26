import { lineDiff } from './diff';

/**
 * Keep a file's original Markdown layout when the rich editor re-serialises it, so an edit only
 * changes what the person actually changed. Fixes the serializer's style (entities, padded list
 * numbers, table separators) and then reverts any blank-line churn inside unchanged regions.
 */
export function preserveStyle(original: string, serialized: string): string {
  let out = serialized;

  // 1. Serializer escapes that change the raw text; restore them outside code.
  out = mapOutsideCode(out, (t) => t.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&'));

  // 2. Ordered lists with 10+ items get right-aligned numbers (" 1."); undo if the source doesn't pad.
  if (!/^ \d\. /m.test(original)) out = out.replace(/^ (\d\. )/gm, '$1');

  // 3. Table separator rows: match the source's compact style (|---|) if that's what it uses.
  if (/^\|(?:\s*:?-{3,}:?\s*\|)+\s*$/m.test(original) && !/^\|(?: :?-{3,}:? \|)+\s*$/m.test(original)) {
    out = out.replace(/^\|(?:\s*:?-{3,}:?\s*\|)+\s*$/gm, (row) => '|' + row.split('|').slice(1, -1).map((c) => c.trim()).join('|') + '|');
  }

  // 4. Blank lines: keep the source's layout wherever the surrounding content is unchanged.
  const a = original.replace(/\n$/, '');
  const b = out.replace(/\n$/, '');
  const d = lineDiff(a, b);
  if (d) {
    const neighbourSame = (i: number, step: number) => {
      for (let k = i + step; k >= 0 && k < d.length; k += step) {
        if (d[k].text.trim() !== '') return d[k].type === 'same';
      }
      return true; // start or end of file
    };
    const kept: string[] = [];
    d.forEach((l, i) => {
      const blank = l.text.trim() === '';
      if (l.type === 'same') kept.push(l.text);
      else if (l.type === 'add') {
        if (!(blank && neighbourSame(i, -1) && neighbourSame(i, 1))) kept.push(l.text);
      } else if (blank && neighbourSame(i, -1) && neighbourSame(i, 1)) kept.push(l.text);
    });
    out = kept.join('\n');
  }

  // 5. Trailing newline, as in the source.
  out = out.replace(/\n*$/, '');
  return original.endsWith('\n') ? out + '\n' : out;
}

function mapOutsideCode(md: string, fn: (text: string) => string): string {
  const parts = md.split(/(^```[\s\S]*?^```\s*$)/m);
  return parts
    .map((part, i) => (i % 2 === 1 ? part : part.split(/(`[^`\n]*`)/).map((seg, j) => (j % 2 === 1 ? seg : fn(seg))).join('')))
    .join('');
}

/** Serializer fixes applied before merging, so edited blocks read like the rest of the file. */
function tidy(original: string, md: string): string {
  let out = mapOutsideCode(md, (t) => t.replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&'));
  if (!/^ \d\. /m.test(original)) out = out.replace(/^ (\d\. )/gm, '$1');
  if (/^\|(?:-{3,}\|)+\s*$/m.test(original)) {
    out = out.replace(/^\|(?:\s*:?-{3,}:?\s*\|)+\s*$/gm, (row) => '|' + row.split('|').slice(1, -1).map((c) => c.trim()).join('|') + '|');
  }
  return out;
}

/**
 * Three-way merge for rich-text editing. `baseline` is what the editor produced for the untouched file;
 * `current` is what it produces now. Only the blocks that changed between the two are taken from the
 * editor; everything else is copied from `original` byte for byte, so formatting never churns.
 */
export function mergeEdits(original: string, baseline: string, current: string): string {
  const O = original.replace(/\n$/, '').split('\n');
  const S0 = tidy(original, baseline).replace(/\n*$/, '').split('\n');
  const S1 = tidy(original, current).replace(/\n*$/, '').split('\n');
  const dOS = lineDiff(O.join('\n'), S0.join('\n'));
  const dSS = lineDiff(S0.join('\n'), S1.join('\n'));
  if (!dOS || !dSS) return preserveStyle(original, current); // very large files: fall back to layout preservation

  // Which baseline lines were removed, and which new lines were inserted before each baseline line.
  const removed = new Set<number>();
  const inserts = new Map<number, string[]>();
  let s = 0;
  for (const l of dSS) {
    if (l.type === 'same') s++;
    else if (l.type === 'remove') removed.add(s++);
    else inserts.set(s, [...(inserts.get(s) ?? []), l.text]);
  }
  const touched = (from: number, to: number) => {
    for (let k = from; k < to; k++) if (removed.has(k)) return true;
    for (let k = from + 1; k < to; k++) if (inserts.has(k)) return true;
    return false;
  };
  const current1 = (from: number, to: number) => {
    const out: string[] = [];
    for (let k = from; k < to; k++) {
      if (k > from) out.push(...(inserts.get(k) ?? []));
      if (!removed.has(k)) out.push(S0[k]);
    }
    return out;
  };

  // Walk the original-vs-baseline alignment: identical lines map 1:1, formatting-only differences form blocks.
  const out: string[] = [];
  const emitted = new Set<number>();
  const insertsAt = (k: number) => {
    if (emitted.has(k)) return [];
    emitted.add(k);
    return inserts.get(k) ?? [];
  };
  let o = 0;
  s = 0;
  let i = 0;
  while (i < dOS.length) {
    if (dOS[i].type === 'same') {
      out.push(...insertsAt(s));
      if (!removed.has(s)) out.push(O[o]);
      o++; s++; i++;
      continue;
    }
    const oStart = o, sStart = s;
    while (i < dOS.length && dOS[i].type !== 'same') {
      if (dOS[i].type === 'remove') o++;
      else s++;
      i++;
    }
    out.push(...insertsAt(sStart));
    if (touched(sStart, s)) {
      out.push(...current1(sStart, s));
      for (let k = sStart + 1; k < s; k++) emitted.add(k);
    }
    else out.push(...O.slice(oStart, o));
  }
  out.push(...insertsAt(s));
  const text = out.join('\n');
  return original.endsWith('\n') ? text + '\n' : text;
}

/** Word-level comparison that ignores Markdown punctuation and layout: does the editor keep all the content? */
export function sameContent(a: string, b: string): boolean {
  const words = (t: string) => t.replace(/\\([^\w\s])/g, '$1').replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&').replace(/[*_`#>|\-:]+/g, ' ').split(/\s+/).filter(Boolean).join(' ');
  return words(a) === words(b);
}
