"use client";

import { useState, type FormEvent } from "react";
import { Alert, Button, Card, Checkbox, DataState, Field, Input, PageHeader, Select, Textarea } from "@/components/ui";
import { COMPLAINT_CATEGORIES } from "@/domain/options";
import { hasErrors, validateComplaint } from "@/domain/validation";
import { ComplaintList } from "@/features/common/complaint-list";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { titleCase } from "@/lib/format";
import { studentApi } from "@/services/student";

const EMPTY = { category: "", subject: "", description: "", is_confidential: false };

export function StudentComplaintsPage() {
  const state = useApiQuery(studentApi.complaints());
  const create = useApiMutation(studentApi.createComplaint, { invalidates: ["/student/complaints"] });
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<ReturnType<typeof validateComplaint>>({});
  const [notice, setNotice] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs = validateComplaint(form);
    setErrors(errs);
    setNotice(null);
    if (hasErrors(errs)) return;
    const r = await create.run(form).catch(() => null);
    if (r) {
      setNotice(`Submitted as ${r.reference_no}. Routed to: ${r.routed_to}.`);
      setForm(EMPTY);
    }
  }

  return (
    <>
      <PageHeader
        title="Complaints and requests"
        description="Raise a concern with the school. Confidential matters go directly to school management, never to an individual teacher."
      />
      <div className="grid gap-6 lg:grid-cols-[1fr_1.3fr]">
        <Card title="New complaint or request">
          <form onSubmit={submit} noValidate className="space-y-4">
            {notice && <Alert tone="success">{notice}</Alert>}
            {create.error && <Alert tone="error">{create.error.message}</Alert>}
            <Field label="Category" required error={errors.category}>
              {(p) => (
                <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} {...p}>
                  <option value="">Select a category</option>
                  {COMPLAINT_CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {titleCase(c)}
                    </option>
                  ))}
                </Select>
              )}
            </Field>
            <Field label="Subject" required error={errors.subject}>
              {(p) => <Input value={form.subject} maxLength={160} onChange={(e) => setForm({ ...form, subject: e.target.value })} {...p} />}
            </Field>
            <Field label="Details" required error={errors.description}>
              {(p) => (
                <Textarea
                  value={form.description}
                  maxLength={4000}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  {...p}
                />
              )}
            </Field>
            <Checkbox
              label="Keep this confidential (only authorised management will see it)"
              checked={form.is_confidential}
              onChange={(e) => setForm({ ...form, is_confidential: e.target.checked })}
            />
            <Button type="submit" loading={create.pending}>
              Submit
            </Button>
          </form>
        </Card>
        <Card title="My complaints and requests">
          <DataState state={state}>{(items) => <ComplaintList items={items} />}</DataState>
        </Card>
      </div>
    </>
  );
}
