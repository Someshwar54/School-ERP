"use client";

import { useMemo, useState } from "react";
import { Alert, Badge, Button, Card, DataState, Field, Input, PageHeader, Select, Table, Td } from "@/components/ui";
import { ATTENDANCE_OPTIONS, countByStatus, unmarkedCount, weekdayIndex, type AttendanceStatus } from "@/domain/attendance";
import { validateReason } from "@/domain/validation";
import { useSession } from "@/features/auth/use-session";
import { useTodayISO } from "@/hooks/use-today";
import { cn } from "@/lib/cn";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDate, formatDateTime } from "@/lib/format";
import { teacherApi, type Register } from "@/services/teacher";

/** Selected-state colour per status (presentation only). */
const CHECKED_STYLE: Record<AttendanceStatus, string> = {
  present: "peer-checked:bg-emerald-600",
  absent: "peer-checked:bg-red-600",
  late: "peer-checked:bg-amber-500",
  approved_leave: "peer-checked:bg-sky-600",
  excused: "peer-checked:bg-indigo-600",
};

export function TeacherAttendancePage() {
  const { me } = useSession();
  const today = useTodayISO();
  const [day, setDay] = useState<string | null>(null);
  const date = day ?? today;
  const timetable = useApiQuery(teacherApi.timetable());
  const [picked, setChoice] = useState("");

  // Registers this teacher may take on the chosen date: daily (class teacher) + own timetabled periods.
  const options = useMemo(() => {
    const daily = (me?.workspace.class_teacher_of ?? []).map((c) => ({
      key: `${c.section_id}:0`,
      label: `Daily register · Class ${c.section}`,
    }));
    const periods =
      date && timetable.data
        ? timetable.data.entries
            .filter((e) => e.day_of_week === weekdayIndex(date))
            .map((e) => ({ key: `${e.section_id}:${e.period_no}`, label: `Period ${e.period_no} · Class ${e.section} · ${e.subject}` }))
        : [];
    return [...daily, ...periods];
  }, [me, timetable.data, date]);

  const choice = options.some((o) => o.key === picked) ? picked : (options[0]?.key ?? "");
  const [sectionId, periodNo] = choice ? choice.split(":") : [null, null];

  return (
    <>
      <PageHeader
        title="Student attendance"
        description="Class teachers take the daily register. Subject teachers can record attendance for their own timetabled periods."
      />
      <Card>
        <div className="grid gap-4 sm:grid-cols-[12rem_1fr]">
          <Field label="Date">
            {(p) => <Input type="date" value={date ?? ""} max={today ?? undefined} onChange={(e) => setDay(e.target.value)} {...p} />}
          </Field>
          <Field label="Register">
            {(p) => (
              <Select value={choice} onChange={(e) => setChoice(e.target.value)} {...p}>
                {options.length === 0 && <option value="">No registers for this date</option>}
                {options.map((o) => (
                  <option key={o.key} value={o.key}>
                    {o.label}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </div>
      </Card>
      {sectionId && date && <RegisterEditor key={`${choice}-${date}`} sectionId={sectionId} periodNo={Number(periodNo)} day={date} />}
    </>
  );
}

function RegisterEditor({ sectionId, periodNo, day }: { sectionId: string; periodNo: number; day: string }) {
  const state = useApiQuery(teacherApi.register(sectionId, day, periodNo));
  return (
    <div className="mt-5">
      <DataState state={state}>{(r) => <RegisterForm register={r} sectionId={sectionId} periodNo={periodNo} day={day} />}</DataState>
    </div>
  );
}

function RegisterForm({ register, sectionId, periodNo, day }: { register: Register; sectionId: string; periodNo: number; day: string }) {
  const [marks, setMarks] = useState<Record<string, AttendanceStatus | null>>(() =>
    Object.fromEntries(register.students.map((s) => [s.student_id, s.status])),
  );
  const [reason, setReason] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const save = useApiMutation(teacherApi.saveRegister, { invalidates: ["/teacher/attendance", "/teacher/dashboard", "/teacher/class"] });
  const unmarked = unmarkedCount(marks);
  const counts = countByStatus(marks);
  const changed = register.students.some((s) => s.status !== marks[s.student_id]);

  if (!register.instructional) {
    return (
      <Alert tone="info" title="No school on this day">
        This is a holiday or weekly off. Attendance is not recorded and is never counted as an absence.
      </Alert>
    );
  }

  async function submit() {
    setNotice(null);
    const err = unmarked
      ? `Mark all students before submitting (${unmarked} unmarked).`
      : register.submitted && changed
        ? validateReason(reason)
        : null;
    setLocalError(err);
    if (err) return;
    const r = await save
      .run({
        section_id: sectionId,
        day,
        period_no: periodNo,
        reason: reason || null,
        records: register.students.map((s) => ({ student_id: s.student_id, status: marks[s.student_id] as AttendanceStatus })),
      })
      .catch(() => null);
    if (r) {
      setNotice(
        r.action === "attendance.corrected" ? `Register corrected (${r.corrections} change(s) logged in history).` : "Register submitted.",
      );
      setReason("");
    }
  }

  const error = localError ?? save.error?.message;
  return (
    <Card
      title={`${periodNo ? `Period ${periodNo}` : "Daily register"} · ${formatDate(day)}`}
      action={
        register.submitted ? (
          <Badge tone="success">Submitted {formatDateTime(register.submitted_at)}</Badge>
        ) : (
          <Badge tone="warning">Not yet submitted</Badge>
        )
      }
      padded={false}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 text-sm">
        <span className="text-muted">{ATTENDANCE_OPTIONS.map((o) => `${o.label}: ${counts[o.value]}`).join(" · ")}</span>
        {register.editable && (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setMarks(Object.fromEntries(register.students.map((s) => [s.student_id, marks[s.student_id] ?? "present"])))}
          >
            Mark unmarked as present
          </Button>
        )}
      </div>
      {!register.editable && (
        <div className="px-4 pb-3">
          <Alert tone="warning">This register is outside the correction window and is read-only here.</Alert>
        </div>
      )}
      <Table headers={["Roll", "Student", "Status"]} caption="Attendance register">
        {register.students.map((s) => (
          <tr key={s.student_id}>
            <Td>{s.roll_no}</Td>
            <Td className="font-medium">
              {s.name}
              <span className="block text-xs font-normal text-muted">{s.student_code}</span>
            </Td>
            <Td>
              <fieldset className="flex flex-wrap gap-1" disabled={!register.editable}>
                <legend className="sr-only">Attendance for {s.name}</legend>
                {ATTENDANCE_OPTIONS.map((o) => (
                  <label key={o.value} title={o.label}>
                    <input
                      type="radio"
                      className="peer sr-only"
                      name={`st-${s.student_id}`}
                      checked={marks[s.student_id] === o.value}
                      onChange={() => setMarks({ ...marks, [s.student_id]: o.value })}
                      aria-label={o.label}
                    />
                    <span
                      className={cn(
                        "inline-flex h-8 min-w-9 cursor-pointer items-center justify-center rounded-md border border-line px-2 text-xs font-semibold peer-checked:border-transparent peer-checked:text-white peer-focus-visible:ring-2 peer-focus-visible:ring-brand",
                        CHECKED_STYLE[o.value],
                      )}
                    >
                      {o.short}
                    </span>
                  </label>
                ))}
              </fieldset>
            </Td>
          </tr>
        ))}
      </Table>
      {register.editable && (
        <div className="space-y-3 border-t border-line p-4">
          {notice && <Alert tone="success">{notice}</Alert>}
          {error && <Alert tone="error">{error}</Alert>}
          {register.submitted && (
            <Field
              label="Reason for correction"
              hint="Required when changing a submitted register. Corrections are kept in the audit history."
            >
              {(p) => <Input value={reason} maxLength={255} onChange={(e) => setReason(e.target.value)} {...p} />}
            </Field>
          )}
          <Button onClick={() => void submit()} loading={save.pending} disabled={register.submitted && !changed}>
            {register.submitted ? "Save corrections" : "Submit register"}
          </Button>
        </div>
      )}
    </Card>
  );
}
