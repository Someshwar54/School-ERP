"use client";

import { useCallback, useState, type FormEvent } from "react";
import { Alert, Badge, Button, Card, Checkbox, DataState, EmptyState, Field, Input, PageHeader, Select, Table, Td } from "@/components/ui";
import { ASSESSMENT_KINDS } from "@/domain/options";
import { assessmentState } from "@/domain/status";
import { invalidMarks, validateAssessment, validateReason } from "@/domain/validation";
import { AssignmentPicker } from "@/features/teacher/assignment-picker";
import { cn } from "@/lib/cn";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDate, titleCase } from "@/lib/format";
import { teacherApi, type Assignment, type MarksSheet } from "@/services/teacher";

const MARK_INVALIDATES = ["/teacher/assessments", "/teacher/dashboard", "/teacher/class"];

export function TeacherMarksPage() {
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const onChange = useCallback((x: Assignment) => {
    setAssignment(x);
    setSelected(null);
  }, []);
  const list = useApiQuery(assignment ? teacherApi.assessments(assignment) : null);

  return (
    <>
      <PageHeader
        title="Assessments and marks"
        description="Enter marks for your assigned classes. Results become visible to students only after the academic office publishes them."
      />
      <div className="space-y-5">
        <AssignmentPicker value={assignment} onChange={onChange} />
        {assignment && (
          <div className="grid gap-5 xl:grid-cols-[22rem_1fr]">
            <div className="space-y-5">
              <Card title="Assessments" padded={false}>
                <DataState state={list}>
                  {(rows) =>
                    rows.length === 0 ? (
                      <div className="p-4">
                        <EmptyState title="No assessments yet" />
                      </div>
                    ) : (
                      <ul className="divide-y divide-line">
                        {rows.map((r) => {
                          const state =
                            r.is_published || r.complete
                              ? assessmentState(r)
                              : { label: `${r.entered}/${r.enrolled}`, tone: "warning" as const };
                          return (
                            <li key={r.id}>
                              <button
                                type="button"
                                onClick={() => setSelected(r.id)}
                                className={cn("w-full px-4 py-3 text-left text-sm hover:bg-surface", selected === r.id && "bg-brand-soft")}
                              >
                                <span className="flex items-center justify-between gap-2">
                                  <span className="font-medium">{r.name}</span>
                                  <Badge tone={state.tone}>{state.label}</Badge>
                                </span>
                                <span className="text-xs text-muted">
                                  {formatDate(r.held_on)} · Max {r.max_marks}
                                </span>
                              </button>
                            </li>
                          );
                        })}
                      </ul>
                    )
                  }
                </DataState>
              </Card>
              <NewAssessment assignment={assignment} onCreated={setSelected} />
            </div>
            {selected ? <MarksEditor key={selected} assessmentId={selected} /> : <EmptyState title="Select an assessment to enter marks" />}
          </div>
        )}
      </div>
    </>
  );
}

const EMPTY_ASSESSMENT = { name: "", kind: "unit_test", max_marks: "25", held_on: "" };

function NewAssessment({ assignment, onCreated }: { assignment: Assignment; onCreated: (id: string) => void }) {
  const [form, setForm] = useState(EMPTY_ASSESSMENT);
  const [localError, setLocalError] = useState<string | null>(null);
  const create = useApiMutation(teacherApi.createAssessment, { invalidates: MARK_INVALIDATES });

  async function submit(e: FormEvent) {
    e.preventDefault();
    const err = validateAssessment(form);
    setLocalError(err);
    if (err) return;
    const r = await create.run({ ...form, section_id: assignment.section_id, subject_id: assignment.subject_id }).catch(() => null);
    if (r) {
      setForm(EMPTY_ASSESSMENT);
      onCreated(r.id);
    }
  }

  const error = localError ?? create.error?.message;
  return (
    <Card title="New assessment">
      <form onSubmit={submit} noValidate className="space-y-3">
        {error && <Alert tone="error">{error}</Alert>}
        <Field label="Name">
          {(p) => <Input value={form.name} maxLength={80} onChange={(e) => setForm({ ...form, name: e.target.value })} {...p} />}
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Type">
            {(p) => (
              <Select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })} {...p}>
                {ASSESSMENT_KINDS.map((k) => (
                  <option key={k} value={k}>
                    {titleCase(k)}
                  </option>
                ))}
              </Select>
            )}
          </Field>
          <Field label="Max marks">
            {(p) => (
              <Input
                type="number"
                min={1}
                max={200}
                value={form.max_marks}
                onChange={(e) => setForm({ ...form, max_marks: e.target.value })}
                {...p}
              />
            )}
          </Field>
        </div>
        <Field label="Date held">
          {(p) => <Input type="date" value={form.held_on} onChange={(e) => setForm({ ...form, held_on: e.target.value })} {...p} />}
        </Field>
        <Button type="submit" loading={create.pending} variant="secondary">
          Create assessment
        </Button>
      </form>
    </Card>
  );
}

function MarksEditor({ assessmentId }: { assessmentId: string }) {
  const state = useApiQuery(teacherApi.marks(assessmentId));
  return <DataState state={state}>{(s) => <MarksForm sheet={s} />}</DataState>;
}

function MarksForm({ sheet }: { sheet: MarksSheet }) {
  const a = sheet.assessment;
  const max = Number(a.max_marks);
  const [rows, setRows] = useState(() =>
    Object.fromEntries(sheet.students.map((s) => [s.student_id, { marks: s.marks_obtained ?? "", absent: s.is_absent }])),
  );
  const [reason, setReason] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const save = useApiMutation(teacherApi.saveMarks, { invalidates: MARK_INVALIDATES });
  const invalid = new Set(invalidMarks(Object.fromEntries(Object.entries(rows).map(([id, r]) => [id, r.marks])), max));

  async function submit() {
    setNotice(null);
    const err = invalid.size
      ? `Marks must be between 0 and ${max} (${invalid.size} invalid).`
      : a.is_published
        ? validateReason(reason)
        : null;
    setLocalError(err);
    if (err) return;
    const r = await save
      .run({
        assessmentId: a.id,
        reason: reason || null,
        marks: sheet.students.map((s) => {
          const row = rows[s.student_id];
          return { student_id: s.student_id, is_absent: row.absent, marks_obtained: row.absent || row.marks === "" ? null : row.marks };
        }),
      })
      .catch(() => null);
    if (r) {
      setNotice(`Saved ${r.saved} rows${r.corrections ? `, ${r.corrections} correction(s) recorded in history` : ""}.`);
      setReason("");
    }
  }

  const error = localError ?? save.error?.message;
  return (
    <Card
      title={`${a.name} · Max ${a.max_marks}`}
      action={<Badge tone={a.is_published ? "success" : "neutral"}>{a.is_published ? "Published" : "Not published"}</Badge>}
      padded={false}
    >
      <Table headers={["Roll", "Student", "Marks", "Absent"]} caption="Marks entry">
        {sheet.students.map((s) => {
          const r = rows[s.student_id];
          return (
            <tr key={s.student_id}>
              <Td>{s.roll_no}</Td>
              <Td className="font-medium">{s.name}</Td>
              <Td>
                <Input
                  aria-label={`Marks for ${s.name}`}
                  aria-invalid={invalid.has(s.student_id)}
                  inputMode="decimal"
                  className="w-24"
                  disabled={r.absent}
                  value={r.marks}
                  onChange={(e) => setRows({ ...rows, [s.student_id]: { ...r, marks: e.target.value } })}
                />
              </Td>
              <Td>
                <Checkbox
                  label={<span className="sr-only">Absent: {s.name}</span>}
                  checked={r.absent}
                  onChange={(e) =>
                    setRows({ ...rows, [s.student_id]: { marks: e.target.checked ? "" : r.marks, absent: e.target.checked } })
                  }
                />
              </Td>
            </tr>
          );
        })}
      </Table>
      <div className="space-y-3 border-t border-line p-4">
        {notice && <Alert tone="success">{notice}</Alert>}
        {error && <Alert tone="error">{error}</Alert>}
        {a.is_published && (
          <Field label="Reason for correction" hint="Required: these results are already visible to students.">
            {(p) => <Input value={reason} onChange={(e) => setReason(e.target.value)} {...p} />}
          </Field>
        )}
        <Button onClick={() => void submit()} loading={save.pending}>
          Save marks
        </Button>
      </div>
    </Card>
  );
}
