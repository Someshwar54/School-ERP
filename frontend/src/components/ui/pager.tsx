/** Previous/next pagination for server-paginated lists. */

export function Pager({ page, pageSize, total, onPage }: { page: number; pageSize: number; total: number; onPage: (p: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <nav className="flex items-center justify-between gap-2 pt-3 text-sm text-muted" aria-label="Pagination">
      <span>
        Page {page} of {pages} · {total} records
      </span>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded-brand border border-line px-3 py-1 disabled:opacity-50"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          Previous
        </button>
        <button
          type="button"
          className="rounded-brand border border-line px-3 py-1 disabled:opacity-50"
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
        >
          Next
        </button>
      </div>
    </nav>
  );
}
