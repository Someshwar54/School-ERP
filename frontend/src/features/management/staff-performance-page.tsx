"use client";

import { useState, type FormEvent } from "react";
import { Alert, Badge, Button, Card, DataState, Field, Input, PageHeader, Select, Table, Td, Textarea } from "@/components/ui";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDateTime, formatPercent } from "@/lib/format";
import { managementApi, type Evaluation, type RubricCriterion, type TeacherEvidence } from "@/services/management";

const EVALUATION_INVALIDATES = ["/management/evaluations", "/management/teachers"];

export function StaffPerformancePage() {
  const evidence = useApiQuery(managementApi.teacherEvidence());
  const evaluations = useApiQuery(managementApi.evaluations());
  return (
    <>
      <PageHeader
        title="Teacher and staff performance"
        description="An evidence framework to support human review. The system never assigns an employment rating on its own."
      />
      <div className="space-y-6">
        <DataState state={evidence}>
          {(d) => (
            <>
              <Alert tone="info" title="How to read this">
                {d.guidance}
              </Alert>
              <EvidenceTable evidence={d} />
            </>
          )}
        </DataState>
        <DataState state={evaluations}>
          {(e) => (
            <div className="grid gap-6 xl:grid-cols-[1fr_24rem]">
              <Card title={`Evaluations · ${e.rubric.name}`}>
                <ul className="space-y-4">
                  {e.items.map((ev) => (
                    <EvaluationCard key={ev.id} evaluation={ev} criteria={e.rubric.criteria} canManage={e.can_manage} />
                  ))}
                </ul>
              </Card>
              {e.can_manage && evidence.data && <NewEvaluation teachers={evidence.data.teachers} criteria={e.rubric.criteria} />}
            </div>
          )}
        </DataState>
      </div>
    </>
  );
}

function EvidenceTable({ evidence }: { evidence: TeacherEvidence }) {
  return (
    <Card title={`Evidence summary · ${formatPercent(evidence.year_elapsed_percent)} of the academic year elapsed`} padded={false}>
      <Table
        headers={[
          "Teacher",
          "Department",
          "Classes",
          "Curriculum delivered",
          "Pending topics",
          "Class average (context)",
          "Topic feedback",
          "Evaluations",
        ]}
        caption="Teacher evidence"
      >
        {evidence.teachers.map((t) => (
          <tr key={t.staff_id}>
            <Td className="font-medium">
              {t.name}
              <span className="block text-xs font-normal text-muted">{t.staff_code}</span>
            </Td>
            <Td>{t.department}</Td>
            <Td>{t.assignments}</Td>
            <Td>{formatPercent(t.curriculum_delivery_percent)}</Td>
            <Td>{t.topics_pending}</Td>
            <Td className="text-muted">{formatPercent(t.class_average_percent_context)}</Td>
            <Td>
              {t.topic_feedback_average !== null ? (
                `${t.topic_feedback_average}/5 (${t.topic_feedback_responses})`
              ) : (
                <span className="text-xs text-muted">Too few responses</span>
              )}
            </Td>
            <Td>{t.evaluations}</Td>
          </tr>
        ))}
      </Table>
    </Card>
  );
}

function EvaluationCard({
  evaluation: ev,
  criteria,
  canManage,
}: {
  evaluation: Evaluation;
  criteria: RubricCriterion[];
  canManage: boolean;
}) {
  const [comment, setComment] = useState("");
  const [scores, setScores] = useState<Record<string, string>>(() =>
    Object.fromEntries(criteria.map((c) => [c.key, ev.scores[c.key]?.toString() ?? ""])),
  );
  const [notice, setNotice] = useState<string | null>(null);
  const score = useApiMutation(managementApi.scoreEvaluation, { invalidates: EVALUATION_INVALIDATES });
  const finalize = useApiMutation(managementApi.finalizeEvaluation, { invalidates: EVALUATION_INVALIDATES });
  const draft = ev.status === "draft";
  const error = score.error ?? finalize.error;

  async function saveScores() {
    setNotice(null);
    const filled = Object.fromEntries(
      Object.entries(scores)
        .filter(([, v]) => v !== "")
        .map(([k, v]) => [k, Number(v)]),
    );
    if (await score.run({ id: ev.id, scores: filled }).catch(() => null)) setNotice("Scores saved.");
  }

  return (
    <li className="rounded-brand border border-line p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold">
          {ev.staff_name} · {ev.period_label}
        </p>
        <Badge tone={draft ? "warning" : "success"}>
          {draft ? "Draft — under human review" : `Finalised ${formatDateTime(ev.finalized_at)}`}
        </Badge>
      </div>
      <p className="mt-1 text-sm text-muted">Evidence: {ev.evidence_notes}</p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {criteria.map((c) => (
          <label key={c.key} className="flex items-center justify-between gap-2 text-sm" title={c.description}>
            <span>{c.label}</span>
            {draft && canManage ? (
              <Select
                className="w-20"
                value={scores[c.key]}
                onChange={(e) => setScores({ ...scores, [c.key]: e.target.value })}
                aria-label={c.label}
              >
                <option value="">—</option>
                {Array.from({ length: c.max_score + 1 }, (_, i) => (
                  <option key={i} value={i}>
                    {i}
                  </option>
                ))}
              </Select>
            ) : (
              <span className="font-medium">
                {ev.scores[c.key] ?? "—"} / {c.max_score}
              </span>
            )}
          </label>
        ))}
      </div>
      {ev.reviewer_comment && (
        <p className="mt-2 text-sm">
          <span className="font-medium">Reviewer:</span> {ev.reviewer_comment}
        </p>
      )}
      {notice && !error && (
        <Alert tone="success" className="mt-3">
          {notice}
        </Alert>
      )}
      {error && (
        <Alert tone="error" className="mt-3">
          {error.message}
        </Alert>
      )}
      {draft && canManage && (
        <div className="mt-3 space-y-2 border-t border-line pt-3">
          <Button size="sm" variant="secondary" loading={score.pending} onClick={() => void saveScores()}>
            Save scores
          </Button>
          <Field label="Reviewer comment (required to finalise)">
            {(p) => <Textarea className="min-h-16" value={comment} onChange={(e) => setComment(e.target.value)} {...p} />}
          </Field>
          <Button
            size="sm"
            disabled={comment.trim().length < 10}
            loading={finalize.pending}
            onClick={() => void finalize.run({ id: ev.id, reviewer_comment: comment }).catch(() => null)}
          >
            Finalise evaluation
          </Button>
          <p className="text-xs text-muted">Every criterion must be scored. You cannot finalise your own evaluation.</p>
        </div>
      )}
    </li>
  );
}

const EMPTY_EVALUATION = { staff_id: "", period_label: "", evidence_notes: "" };

function NewEvaluation({ teachers, criteria }: { teachers: TeacherEvidence["teachers"]; criteria: RubricCriterion[] }) {
  const [form, setForm] = useState(EMPTY_EVALUATION);
  const [localError, setLocalError] = useState<string | null>(null);
  const create = useApiMutation(managementApi.createEvaluation, { invalidates: EVALUATION_INVALIDATES });

  async function submit(e: FormEvent) {
    e.preventDefault();
    const err =
      !form.staff_id || form.period_label.trim().length < 3 || form.evidence_notes.trim().length < 10
        ? "Choose a teacher, a period label and at least 10 characters of evidence."
        : null;
    setLocalError(err);
    if (err) return;
    if (await create.run(form).catch(() => null)) setForm(EMPTY_EVALUATION);
  }

  const error = localError ?? create.error?.message;
  return (
    <Card title="Start an evaluation">
      <form onSubmit={submit} noValidate className="space-y-3">
        {error && <Alert tone="error">{error}</Alert>}
        <Field label="Teacher">
          {(p) => (
            <Select value={form.staff_id} onChange={(e) => setForm({ ...form, staff_id: e.target.value })} {...p}>
              <option value="">Select</option>
              {teachers.map((t) => (
                <option key={t.staff_id} value={t.staff_id}>
                  {t.name}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Period">
          {(p) => (
            <Input
              placeholder="e.g. 2026-27 mid-year"
              value={form.period_label}
              onChange={(e) => setForm({ ...form, period_label: e.target.value })}
              {...p}
            />
          )}
        </Field>
        <Field label="Supporting evidence" hint={`Rubric: ${criteria.map((c) => c.label).join(", ")}`}>
          {(p) => <Textarea value={form.evidence_notes} onChange={(e) => setForm({ ...form, evidence_notes: e.target.value })} {...p} />}
        </Field>
        <Button type="submit" variant="secondary" loading={create.pending}>
          Create draft
        </Button>
      </form>
    </Card>
  );
}
