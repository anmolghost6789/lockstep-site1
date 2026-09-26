export default function Loading() {
  return (
    <div className="mx-auto max-w-[560px] py-24 text-center" role="status" aria-live="polite">
      <span className="mx-auto block size-6 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-900 dark:border-neutral-700 dark:border-t-neutral-100" />
      <p className="mt-4 text-[14.5px] text-neutral-600 dark:text-neutral-400">Opening the editor…</p>
    </div>
  );
}
