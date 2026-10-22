"use client";

import { useState, type FormEvent } from "react";
import { Alert, Badge, Button, Card, DataState, Field, Input, PageHeader, Select, Table, Td, Textarea } from "@/components/ui";
import { LEAVE_TYPES } from "@/domain/options";
import { LEAVE_TONE } from "@/domain/status";
import { hasErrors, validateLeave } from "@/domain/validation";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDate, titleCase } from "@/lib/format";
import { staffApi } from "@/services/staff";

const EMPTY = { leave_type: "casual", starts_on: "", ends_on: "", reason: "" };
const INVALIDATES = ["/staff/leave", "/staff/dashboard", "/hr/leave-requests"];

export function StaffLeavePage() {
  const state = useApiQuery(staffApi.leave());
  const request = useApiMutation(staffApi.requestLeave, { invalidates: INVALIDATES });
  const cancel = useApiMutation(staffApi.cancelLeave, { invalidates: INVALIDATES });
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<ReturnType<typeof validateLeave>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const error = request.error ?? cancel.error;

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs = validateLeave(form);
    setErrors(errs);
    setNotice(null);
    if (hasErrors(errs)) return;
    if (await request.run(form).catch(() => null)) {
      setNotice("Leave request submitted for approval.");
      setForm(EMPTY);
    }
  }

  return (
    <>
      <PageHeader
        title="Leave requests"
        description="Requests are approved by authorised HR or management staff. Leave balances are not tracked in this prototype."
      />
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <Card title="Request leave">
          <form onSubmit={submit} noValidate className="space-y-3">
            {notice && <Alert tone="success">{notice}</Alert>}
            {error && <Alert tone="error">{error.message}</Alert>}
            <Field label="Type">
              {(p) => (
                <Select value={form.leave_type} onChange={(e) => setForm({ ...form, leave_type: e.target.value })} {...p}>
                  {LEAVE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {titleCase(t)}
                    </option>
                  ))}
                </Select>
              )}
            </Field>
            <Field label="From" required error={errors.starts_on}>
              {(p) => <Input type="date" value={form.starts_on} onChange={(e) => setForm({ ...form, starts_on: e.target.value })} {...p} />}
            </Field>
            <Field label="To" required error={errors.ends_on}>
              {(p) => <Input type="date" value={form.ends_on} onChange={(e) => setForm({ ...form, ends_on: e.target.value })} {...p} />}
            </Field>
            <Field label="Reason" required error={errors.reason}>
              {(p) => (
                <Textarea
                  className="min-h-16"
                  value={form.reason}
                  maxLength={500}
                  onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  {...p}
                />
              )}
            </Field>
            <Button type="submit" loading={request.pending}>
              Submit request
            </Button>
          </form>
        </Card>
        <Card title="My requests" padded={false}>
          <DataState state={state}>
            {(rows) => (
              <Table headers={["Type", "Dates", "Days", "Status", ""]} empty={rows.length === 0} caption="Leave requests">
                {rows.map((r) => (
                  <tr key={r.id}>
                    <Td>{titleCase(r.leave_type)}</Td>
                    <Td>
                      {formatDate(r.starts_on)} – {formatDate(r.ends_on)}
                      <span className="block text-xs text-muted">{r.reason}</span>
                    </Td>
                    <Td>{r.days}</Td>
                    <Td>
                      <Badge tone={LEAVE_TONE[r.status]}>{titleCase(r.status)}</Badge>
                      {r.decision_comment && <span className="block text-xs text-muted">{r.decision_comment}</span>}
                    </Td>
                    <Td>
                      {r.status === "pending" && (
                        <Button size="sm" variant="ghost" onClick={() => void cancel.run(r.id).catch(() => null)}>
                          Cancel
                        </Button>
                      )}
                    </Td>
                  </tr>
                ))}
              </Table>
            )}
          </DataState>
        </Card>
      </div>
    </>
  );
}
