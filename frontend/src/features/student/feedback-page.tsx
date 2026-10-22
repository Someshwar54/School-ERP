"use client";

import { useState, type FormEvent } from "react";
import { Alert, Badge, Button, Card, Checkbox, DataState, EmptyState, Field, PageHeader, Select, Textarea } from "@/components/ui";
import { FEEDBACK_CATEGORIES, UNDERSTANDING_LEVELS } from "@/domain/options";
import { hasErrors, validateFeedback } from "@/domain/validation";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { titleCase } from "@/lib/format";
import { studentApi, type StudentTopic } from "@/services/student";

export function StudentFeedbackPage() {
  const topics = useApiQuery(studentApi.topics());
  return (
    <>
      <PageHeader
        title="Feedback"
        description="Tell your teachers how well you understood each topic, and share general feedback with the school."
      />
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card title="Topic understanding">
          <p className="mb-3 text-sm text-muted">This helps teachers plan support. It is not a test and does not affect your marks.</p>
          <DataState state={topics}>
            {(list) => (list.length === 0 ? <EmptyState title="No topics started yet" /> : <TopicList topics={list} />)}
          </DataState>
        </Card>
        <GeneralFeedback />
      </div>
    </>
  );
}

function TopicList({ topics }: { topics: StudentTopic[] }) {
  const subjects = [...new Set(topics.map((t) => t.subject))];
  const [subject, setSubject] = useState(subjects[0]);
  return (
    <div className="space-y-3">
      <Field label="Subject">
        {(p) => (
          <Select value={subject} onChange={(e) => setSubject(e.target.value)} {...p}>
            {subjects.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </Select>
        )}
      </Field>
      <ul className="divide-y divide-line">
        {topics
          .filter((t) => t.subject === subject)
          .map((t) => (
            <TopicRow key={t.id} topic={t} />
          ))}
      </ul>
    </div>
  );
}

function TopicRow({ topic }: { topic: StudentTopic }) {
  const [level, setLevel] = useState(String(topic.my_feedback?.understanding ?? ""));
  const [saved, setSaved] = useState(false);
  const save = useApiMutation(studentApi.giveTopicFeedback, { invalidates: ["/student/topics"] });
  const status = save.pending ? "Saving…" : save.error ? "Error" : saved ? "Saved" : "";

  async function choose(value: string) {
    setLevel(value);
    setSaved(false);
    if (value && (await save.run({ topicId: topic.id, understanding: Number(value) }).catch(() => null))) setSaved(true);
  }

  return (
    <li className="flex flex-wrap items-center justify-between gap-3 py-2.5">
      <div>
        <p className="text-sm font-medium">{topic.title}</p>
        <Badge tone={topic.status === "completed" ? "success" : "info"}>{titleCase(topic.status)}</Badge>
      </div>
      <div className="flex items-center gap-2">
        <label className="sr-only" htmlFor={`lvl-${topic.id}`}>
          Understanding of {topic.title}
        </label>
        <Select id={`lvl-${topic.id}`} className="w-40" value={level} onChange={(e) => void choose(e.target.value)}>
          <option value="">Rate…</option>
          {[1, 2, 3, 4, 5].map((n) => (
            <option key={n} value={n}>
              {n} · {UNDERSTANDING_LEVELS[n]}
            </option>
          ))}
        </Select>
        <span className="w-14 text-xs text-muted" aria-live="polite" title={save.error?.message}>
          {status}
        </span>
      </div>
    </li>
  );
}

const EMPTY = { category: "", rating: "", comment: "", is_anonymous: false };

function GeneralFeedback() {
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<ReturnType<typeof validateFeedback>>({});
  const [notice, setNotice] = useState<string | null>(null);
  const create = useApiMutation(studentApi.createFeedback);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs = validateFeedback(form);
    setErrors(errs);
    setNotice(null);
    if (hasErrors(errs)) return;
    const r = await create.run({ ...form, rating: Number(form.rating), comment: form.comment || null }).catch(() => null);
    if (r) {
      setNotice(r.anonymous ? "Thank you. Your feedback was submitted anonymously." : "Thank you for your feedback.");
      setForm(EMPTY);
    }
  }

  return (
    <Card title="General feedback">
      <form onSubmit={submit} noValidate className="space-y-4">
        {notice && <Alert tone="success">{notice}</Alert>}
        {create.error && <Alert tone="error">{create.error.message}</Alert>}
        <Field label="About" required error={errors.category}>
          {(p) => (
            <Select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} {...p}>
              <option value="">Select</option>
              {FEEDBACK_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {titleCase(c)}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Rating" required error={errors.rating}>
          {(p) => (
            <Select value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} {...p}>
              <option value="">Select</option>
              {[5, 4, 3, 2, 1].map((n) => (
                <option key={n} value={n}>
                  {n} / 5
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Comment (optional)">
          {(p) => <Textarea value={form.comment} maxLength={2000} onChange={(e) => setForm({ ...form, comment: e.target.value })} {...p} />}
        </Field>
        <Checkbox
          label="Submit anonymously (your name is not stored)"
          checked={form.is_anonymous}
          onChange={(e) => setForm({ ...form, is_anonymous: e.target.checked })}
        />
        <Button type="submit" loading={create.pending}>
          Send feedback
        </Button>
      </form>
    </Card>
  );
}
