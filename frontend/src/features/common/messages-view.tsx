"use client";

import { useState, type FormEvent } from "react";
import { Alert, Button, Card, DataState, EmptyState, Field, Input, PageHeader, Select, Textarea } from "@/components/ui";
import { hasErrors, validateMessage } from "@/domain/validation";
import { cn } from "@/lib/cn";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDateTime } from "@/lib/format";
import { studentApi } from "@/services/student";
import { teacherApi } from "@/services/teacher";

type Audience = "student" | "teacher";

/** Endpoints per audience; the backend decides which threads each account may see. */
const API = {
  student: { threads: studentApi.threads, thread: studentApi.thread, reply: studentApi.reply, prefix: "/student/messages" },
  teacher: { threads: teacherApi.threads, thread: teacherApi.thread, reply: teacherApi.reply, prefix: "/teacher/messages" },
};

/** Teacher–student conversations, used by both workspaces. */
export function MessagesView({ audience }: { audience: Audience }) {
  const api = API[audience];
  const threads = useApiQuery(api.threads());
  const [selected, setSelected] = useState<string | null>(null);
  const [composing, setComposing] = useState(false);
  const isStudent = audience === "student";

  return (
    <>
      <PageHeader
        title={isStudent ? "Teacher communication" : "Student messages"}
        description={
          isStudent
            ? "Message teachers assigned to your class. Conversations are visible only to you and that teacher."
            : "Messages from students in your assigned classes."
        }
        actions={
          isStudent ? (
            <Button
              onClick={() => {
                setComposing(true);
                setSelected(null);
              }}
            >
              New message
            </Button>
          ) : undefined
        }
      />
      <div className="grid gap-5 lg:grid-cols-[20rem_1fr]">
        <Card title="Conversations" padded={false}>
          <DataState state={threads}>
            {(list) =>
              list.length === 0 ? (
                <div className="p-4">
                  <EmptyState title="No conversations yet" />
                </div>
              ) : (
                <ul className="divide-y divide-line">
                  {list.map((t) => (
                    <li key={t.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setSelected(t.id);
                          setComposing(false);
                        }}
                        className={cn("w-full px-4 py-3 text-left hover:bg-surface", selected === t.id && "bg-brand-soft")}
                      >
                        <p className="text-sm font-medium">{t.subject}</p>
                        <p className="text-xs text-muted">
                          {isStudent ? t.staff_name : t.student_name} · {formatDateTime(t.last_message_at)}
                        </p>
                      </button>
                    </li>
                  ))}
                </ul>
              )
            }
          </DataState>
        </Card>
        {composing ? (
          <ComposeMessage
            onSent={(id) => {
              setComposing(false);
              setSelected(id);
            }}
          />
        ) : selected ? (
          <ThreadPanel audience={audience} id={selected} />
        ) : (
          <EmptyState title="Select a conversation" />
        )}
      </div>
    </>
  );
}

function ThreadPanel({ audience, id }: { audience: Audience; id: string }) {
  const api = API[audience];
  const state = useApiQuery(api.thread(id));
  const [body, setBody] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const reply = useApiMutation(api.reply, { invalidates: [api.prefix] });

  async function send(e: FormEvent) {
    e.preventDefault();
    if (!body.trim()) return setLocalError("Write a message first.");
    setLocalError(null);
    if (await reply.run({ threadId: id, body }).catch(() => null)) setBody("");
  }

  const error = localError ?? reply.error?.message;
  return (
    <Card title={state.data?.subject ?? "Conversation"}>
      <DataState state={state}>
        {(t) => (
          <div className="space-y-4">
            <ul className="space-y-3">
              {t.messages.map((m) => (
                <li
                  key={m.id}
                  className={cn("max-w-[85%] rounded-brand p-3 text-sm", m.mine ? "ml-auto bg-brand text-brand-contrast" : "bg-surface")}
                >
                  <p className="whitespace-pre-wrap">{m.body}</p>
                  <p className={cn("mt-1 text-xs", m.mine ? "text-white/75" : "text-muted")}>
                    {m.sender} · {formatDateTime(m.created_at)}
                  </p>
                </li>
              ))}
            </ul>
            <form onSubmit={send} className="space-y-2">
              {error && <Alert tone="error">{error}</Alert>}
              <Field label="Reply">
                {(p) => <Textarea value={body} onChange={(e) => setBody(e.target.value)} maxLength={4000} {...p} />}
              </Field>
              <Button type="submit" loading={reply.pending}>
                Send reply
              </Button>
            </form>
          </div>
        )}
      </DataState>
    </Card>
  );
}

function ComposeMessage({ onSent }: { onSent: (id: string) => void }) {
  const teachers = useApiQuery(studentApi.teachers());
  const [form, setForm] = useState({ staff_id: "", subject: "", body: "" });
  const [errors, setErrors] = useState<ReturnType<typeof validateMessage>>({});
  const create = useApiMutation(studentApi.createThread, { invalidates: ["/student/messages"] });

  async function submit(e: FormEvent) {
    e.preventDefault();
    const errs = validateMessage(form);
    setErrors(errs);
    if (hasErrors(errs)) return;
    const r = await create.run(form).catch(() => null);
    if (r) onSent(r.id);
  }

  return (
    <Card title="New message">
      <form onSubmit={submit} noValidate className="space-y-4">
        {create.error && <Alert tone="error">{create.error.message}</Alert>}
        <Field label="Teacher" required error={errors.staff_id}>
          {(p) => (
            <Select value={form.staff_id} onChange={(e) => setForm({ ...form, staff_id: e.target.value })} {...p}>
              <option value="">Select a teacher</option>
              {teachers.data?.map((t) => (
                <option key={t.staff_id} value={t.staff_id}>
                  {t.name} — {t.subject}
                  {t.is_class_teacher ? " (Class teacher)" : ""}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field label="Subject" required error={errors.subject}>
          {(p) => <Input value={form.subject} maxLength={160} onChange={(e) => setForm({ ...form, subject: e.target.value })} {...p} />}
        </Field>
        <Field label="Message" required error={errors.body}>
          {(p) => <Textarea value={form.body} maxLength={4000} onChange={(e) => setForm({ ...form, body: e.target.value })} {...p} />}
        </Field>
        <Button type="submit" loading={create.pending}>
          Send message
        </Button>
      </form>
    </Card>
  );
}
