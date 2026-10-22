"use client";

import { CheckCircle2, Pause, Play, RotateCcw, StepForward } from "lucide-react";
import { useCallback, useState, type FormEvent } from "react";
import { Alert, Badge, Button, Card, Checkbox, DataState, Dialog, EmptyState, Field, Input, PageHeader, Textarea } from "@/components/ui";
import { TOPIC_TONE } from "@/domain/status";
import { validateReason } from "@/domain/validation";
import { AssignmentPicker } from "@/features/teacher/assignment-picker";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDate, titleCase } from "@/lib/format";
import { teacherApi, type Assignment, type LessonPrompt, type Topic } from "@/services/teacher";

const TOPIC_INVALIDATES = ["/teacher/topics", "/teacher/lesson-prompts", "/teacher/dashboard"];

/** One shared mutation for all topic transitions; every topic view refreshes from the cache afterwards. */
function useTopicAction() {
  return useApiMutation(teacherApi.topicAction, { invalidates: TOPIC_INVALIDATES });
}

export function TeacherTopicsPage() {
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const onChange = useCallback((x: Assignment) => setAssignment(x), []);
  const prompts = useApiQuery(teacherApi.lessonPrompts());
  const topics = useApiQuery(assignment ? teacherApi.topics(assignment) : null);

  return (
    <>
      <PageHeader
        title="Lesson progression"
        description="Track which topics have been delivered. Completing a topic records delivery only — it is not evidence that every student has mastered it."
      />
      <Card title="Today's lessons" className="mb-6">
        <DataState state={prompts}>
          {(list) =>
            list.length === 0 ? (
              <EmptyState title="No timetabled periods today" />
            ) : (
              <ul className="grid gap-3 md:grid-cols-2">
                {list.map((p) => (
                  <PromptCard key={p.timetable_entry_id} prompt={p} />
                ))}
              </ul>
            )
          }
        </DataState>
      </Card>
      <div className="space-y-5">
        <AssignmentPicker value={assignment} onChange={onChange} />
        {assignment && (
          <DataState state={topics}>
            {(d) => (
              <div className="grid gap-5 xl:grid-cols-[1fr_20rem]">
                <Card
                  title={`Class ${assignment.section} · ${assignment.subject}`}
                  action={
                    <span className="text-sm text-muted">
                      {d.completed} of {d.total} delivered
                    </span>
                  }
                  padded={false}
                >
                  <ol className="divide-y divide-line">
                    {d.topics.map((t) => (
                      <TopicRow key={t.id} topic={t} />
                    ))}
                  </ol>
                </Card>
                <AddTopic assignment={assignment} />
              </div>
            )}
          </DataState>
        )}
      </div>
    </>
  );
}

function PromptCard({ prompt }: { prompt: LessonPrompt }) {
  const action = useTopicAction();
  const [confirming, setConfirming] = useState(false);
  const run = (topic: Topic, name: "start" | "continue" | "keep_pending") =>
    void action.run({ topicId: topic.id, action: name, timetable_entry_id: prompt.timetable_entry_id }).catch(() => null);
  const t = prompt.current_topic;
  return (
    <li className="rounded-brand border border-line p-4">
      <p className="text-xs text-muted">
        Period {prompt.period_no} · Class {prompt.section} · {prompt.subject}
      </p>
      {t ? (
        <>
          <p className="mt-1 font-medium">In progress: {t.title}</p>
          <p className="text-xs text-muted">
            {t.periods_used} of {t.planned_periods} planned periods used
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" variant="secondary" icon={<StepForward className="size-4" aria-hidden />} onClick={() => run(t, "continue")}>
              Continue topic
            </Button>
            <Button size="sm" variant="secondary" icon={<Pause className="size-4" aria-hidden />} onClick={() => run(t, "keep_pending")}>
              Keep pending
            </Button>
            <Button size="sm" icon={<CheckCircle2 className="size-4" aria-hidden />} onClick={() => setConfirming(true)}>
              Mark complete…
            </Button>
          </div>
          <CompleteDialog open={confirming} topic={t} timetableEntryId={prompt.timetable_entry_id} onClose={() => setConfirming(false)} />
        </>
      ) : prompt.next_topic ? (
        <>
          <p className="mt-1 font-medium">Next: {prompt.next_topic.title}</p>
          <Button
            size="sm"
            className="mt-3"
            icon={<Play className="size-4" aria-hidden />}
            onClick={() => run(prompt.next_topic as Topic, "start")}
          >
            Start topic
          </Button>
        </>
      ) : (
        <p className="mt-1 text-sm text-muted">No planned topics remain.</p>
      )}
      {action.error && (
        <Alert tone="error" className="mt-2">
          {action.error.message}
        </Alert>
      )}
    </li>
  );
}

/** Completion requires an explicit checkbox; Cancel, Esc or the backdrop never complete a topic. */
function CompleteDialog({
  open,
  topic,
  timetableEntryId,
  onClose,
}: {
  open: boolean;
  topic: Topic;
  timetableEntryId?: string;
  onClose: () => void;
}) {
  const [confirmed, setConfirmed] = useState(false);
  const [startNext, setStartNext] = useState(true);
  const [notes, setNotes] = useState("");
  const action = useTopicAction();
  const close = () => {
    setConfirmed(false);
    action.reset();
    onClose();
  };

  async function complete() {
    const ok = await action
      .run({
        topicId: topic.id,
        action: "complete",
        confirm: confirmed,
        start_next: startNext,
        notes: notes || null,
        timetable_entry_id: timetableEntryId ?? null,
      })
      .catch(() => null);
    if (ok) close();
  }

  return (
    <Dialog
      open={open}
      title="Mark topic as complete?"
      onClose={close}
      footer={
        <>
          <Button variant="secondary" onClick={close}>
            Cancel — keep in progress
          </Button>
          <Button onClick={() => void complete()} disabled={!confirmed} loading={action.pending}>
            Confirm completion
          </Button>
        </>
      }
    >
      <p>
        <strong>{topic.title}</strong>
      </p>
      <p className="text-muted">
        Completion records that the content was delivered. It does not mean every student has mastered the topic; use topic feedback and
        assessments for that.
      </p>
      {action.error && <Alert tone="error">{action.error.message}</Alert>}
      <Checkbox
        label="I confirm this topic's content has been fully delivered"
        checked={confirmed}
        onChange={(e) => setConfirmed(e.target.checked)}
      />
      <Checkbox label="Start the next planned topic" checked={startNext} onChange={(e) => setStartNext(e.target.checked)} />
      <Field label="Notes (optional)">
        {(p) => <Textarea className="min-h-16" value={notes} onChange={(e) => setNotes(e.target.value)} {...p} />}
      </Field>
    </Dialog>
  );
}

function TopicRow({ topic }: { topic: Topic }) {
  const action = useTopicAction();
  const [confirming, setConfirming] = useState(false);
  const [reopening, setReopening] = useState(false);
  const [reason, setReason] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  async function run(name: "start" | "keep_pending" | "reopen") {
    if (name === "reopen") {
      const err = validateReason(reason);
      setLocalError(err);
      if (err) return;
    }
    if (await action.run({ topicId: topic.id, action: name, notes: name === "reopen" ? reason : null }).catch(() => null))
      setReopening(false);
  }

  const error = localError ?? action.error?.message;
  return (
    <li className="px-4 py-3" data-testid={`topic-${topic.sequence}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-medium">
            {topic.sequence}. {topic.title}
          </p>
          <p className="text-xs text-muted">
            {topic.periods_used}/{topic.planned_periods} periods
            {topic.started_on && ` · started ${formatDate(topic.started_on)}`}
            {topic.completed_on && ` · delivered ${formatDate(topic.completed_on)}`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone={TOPIC_TONE[topic.status]}>{titleCase(topic.status)}</Badge>
          {(topic.status === "planned" || topic.status === "pending") && (
            <Button size="sm" variant="secondary" onClick={() => void run("start")}>
              Start
            </Button>
          )}
          {topic.status === "in_progress" && (
            <>
              <Button size="sm" variant="secondary" onClick={() => void run("keep_pending")}>
                Keep pending
              </Button>
              <Button size="sm" onClick={() => setConfirming(true)}>
                Mark complete…
              </Button>
            </>
          )}
          {topic.status === "completed" && (
            <Button size="sm" variant="ghost" icon={<RotateCcw className="size-3.5" aria-hidden />} onClick={() => setReopening(true)}>
              Reopen
            </Button>
          )}
        </div>
      </div>
      {reopening && (
        <div className="mt-2 flex flex-wrap items-end gap-2">
          <div className="flex-1">
            <Field label="Reason for reopening">{(p) => <Input value={reason} onChange={(e) => setReason(e.target.value)} {...p} />}</Field>
          </div>
          <Button size="sm" onClick={() => void run("reopen")}>
            Reopen topic
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setReopening(false)}>
            Cancel
          </Button>
        </div>
      )}
      {error && (
        <Alert tone="error" className="mt-2">
          {error}
        </Alert>
      )}
      <CompleteDialog open={confirming} topic={topic} onClose={() => setConfirming(false)} />
    </li>
  );
}

function AddTopic({ assignment }: { assignment: Assignment }) {
  const [title, setTitle] = useState("");
  const [periods, setPeriods] = useState("4");
  const [localError, setLocalError] = useState<string | null>(null);
  const add = useApiMutation(teacherApi.addTopic, { invalidates: TOPIC_INVALIDATES });

  async function submit(e: FormEvent) {
    e.preventDefault();
    const err = title.trim().length < 3 ? "Enter a topic title (3+ characters)." : null;
    setLocalError(err);
    if (err) return;
    if (
      await add
        .run({ section_id: assignment.section_id, subject_id: assignment.subject_id, title, planned_periods: Number(periods) })
        .catch(() => null)
    )
      setTitle("");
  }

  const error = localError ?? add.error?.message;
  return (
    <Card title="Add planned topic">
      <form onSubmit={submit} noValidate className="space-y-3">
        {error && <Alert tone="error">{error}</Alert>}
        <Field label="Topic title">
          {(p) => <Input value={title} maxLength={160} onChange={(e) => setTitle(e.target.value)} {...p} />}
        </Field>
        <Field label="Planned periods">
          {(p) => <Input type="number" min={1} max={60} value={periods} onChange={(e) => setPeriods(e.target.value)} {...p} />}
        </Field>
        <Button type="submit" variant="secondary" loading={add.pending}>
          Add topic
        </Button>
      </form>
    </Card>
  );
}
