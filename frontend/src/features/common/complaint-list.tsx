"use client";

import { useState, type FormEvent } from "react";
import { Alert, Badge, Button, EmptyState, Field, Select, Textarea } from "@/components/ui";
import { COMPLAINT_TONE } from "@/domain/status";
import type { ApiMutation } from "@/lib/api/query";
import { formatDateTime, titleCase } from "@/lib/format";
import type { Complaint, ComplaintStatusUpdate } from "@/services/shared";

type UpdateMutation = ApiMutation<{ id: string } & ComplaintStatusUpdate, unknown>;

/** Complaint cards. Pass `update` to let the viewer add notes / change status (the backend re-checks). */
export function ComplaintList({ items, update }: { items: Complaint[]; update?: UpdateMutation }) {
  if (!items.length) return <EmptyState title="No complaints" />;
  return (
    <ul className="space-y-4">
      {items.map((c) => (
        <li key={c.id} className="rounded-brand border border-line bg-white p-4">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-semibold">{c.subject}</p>
            <Badge tone={COMPLAINT_TONE[c.status]}>{titleCase(c.status)}</Badge>
            {c.is_confidential && <Badge tone="error">Confidential</Badge>}
          </div>
          <p className="mt-0.5 text-xs text-muted">
            {c.reference_no} · {titleCase(c.category)} · {formatDateTime(c.created_at)}
            {c.student && ` · ${c.student}`}
            {c.section && ` · Class ${c.section}`}
            {c.assigned_to && ` · Assigned to ${c.assigned_to}`}
          </p>
          <p className="mt-2 text-sm">{c.description}</p>
          {c.updates.length > 0 && (
            <ol className="mt-3 space-y-1.5 border-l-2 border-line pl-3 text-sm">
              {c.updates.map((u, i) => (
                <li key={i}>
                  <span className="text-muted">
                    {formatDateTime(u.created_at)} · {u.author}:
                  </span>{" "}
                  {u.note}
                  {u.new_status && <span className="text-muted"> (→ {titleCase(u.new_status)})</span>}
                </li>
              ))}
            </ol>
          )}
          {update && <ComplaintUpdateForm complaintId={c.id} update={update} />}
        </li>
      ))}
    </ul>
  );
}

function ComplaintUpdateForm({ complaintId, update }: { complaintId: string; update: UpdateMutation }) {
  const [note, setNote] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (note.trim().length < 3) return setError("Add a note of at least 3 characters.");
    setError(null);
    try {
      await update.run({ id: complaintId, note, status: status || null });
      setNote("");
      setStatus("");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form onSubmit={submit} className="mt-3 grid gap-2 border-t border-line pt-3 sm:grid-cols-[1fr_12rem_auto] sm:items-end">
      {error && (
        <div className="sm:col-span-3">
          <Alert tone="error">{error}</Alert>
        </div>
      )}
      <Field label="Add a note">
        {(p) => <Textarea className="min-h-10" value={note} onChange={(e) => setNote(e.target.value)} {...p} />}
      </Field>
      <Field label="Change status">
        {(p) => (
          <Select value={status} onChange={(e) => setStatus(e.target.value)} {...p}>
            <option value="">No change</option>
            <option value="in_review">In review</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
            <option value="open">Re-open</option>
          </Select>
        )}
      </Field>
      <Button type="submit" loading={update.pending}>
        Save
      </Button>
    </form>
  );
}
