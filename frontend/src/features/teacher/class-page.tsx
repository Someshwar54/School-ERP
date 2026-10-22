"use client";

import { useState } from "react";
import { useSession } from "@/features/auth/use-session";
import { Alert, Badge, Card, DataState, EmptyState, Field, PageHeader, Select, Spinner, Stat, Table, Td } from "@/components/ui";
import { cn } from "@/lib/cn";
import { formatDate, formatPercent } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { teacherApi } from "@/services/teacher";

export function ClassTeacherPage() {
  const { me } = useSession();
  const sections = me?.workspace.class_teacher_of ?? [];
  const [picked, setPicked] = useState<string | null>(null);
  const section = picked ?? sections[0]?.section_id ?? null;
  const state = useApiQuery(section ? teacherApi.classOverview(section) : null);
  if (!me) return <Spinner />;
  if (!sections.length) return <EmptyState title="You are not assigned as a class teacher" />;
  return (
    <>
      <PageHeader title="My class" description="Class-teacher view across all subjects. Averages use published results only." />
      {sections.length > 1 && (
        <div className="mb-4 max-w-xs">
          <Field label="Class">
            {(p) => (
              <Select value={section ?? ""} onChange={(e) => setPicked(e.target.value)} {...p}>
                {sections.map((s) => (
                  <option key={s.section_id} value={s.section_id}>
                    {s.section}
                  </option>
                ))}
              </Select>
            )}
          </Field>
        </div>
      )}
      <DataState state={state}>
        {(d) => (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label={`Class ${d.section} students`} value={d.students.length} />
              <Stat label="Students needing follow-up" value={d.follow_up.length} tone={d.follow_up.length ? "warning" : "good"} />
              <Stat
                label="Missing records"
                value={d.missing.registers.length + d.missing.assessments.length}
                tone={d.missing.registers.length + d.missing.assessments.length ? "warning" : "good"}
              />
            </div>
            {(d.missing.registers.length > 0 || d.missing.assessments.length > 0) && (
              <Alert tone="warning" title="Missing records">
                <ul className="list-disc pl-4">
                  {d.missing.registers.map((r) => (
                    <li key={r}>Daily register not taken: {formatDate(r)}</li>
                  ))}
                  {d.missing.assessments.map((a) => (
                    <li key={a.assessment_id}>
                      {a.name}: {a.missing} mark(s) missing
                    </li>
                  ))}
                </ul>
              </Alert>
            )}
            <Card title="Follow-up list">
              {d.follow_up.length === 0 ? (
                <EmptyState title="No students below thresholds" />
              ) : (
                <ul className="divide-y divide-line text-sm">
                  {d.follow_up.map((f) => (
                    <li key={f.student_id} className="flex flex-wrap justify-between gap-2 py-2">
                      <span className="font-medium">
                        {f.roll_no}. {f.name}
                      </span>
                      <span className="flex flex-wrap gap-1">
                        {f.reasons.map((r) => (
                          <Badge key={r} tone="warning">
                            {r}
                          </Badge>
                        ))}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-2 text-xs text-muted">
                Thresholds: attendance below {d.thresholds.attendance}%, subject average below {d.thresholds.performance}%.
              </p>
            </Card>
            <Card title="Attendance and performance" padded={false}>
              <Table headers={["Roll", "Student", "Attendance", "Absences", ...d.subjects, "Overall"]} caption="Class overview">
                {d.students.map((s) => (
                  <tr key={s.student_id}>
                    <Td>{s.roll_no}</Td>
                    <Td className="font-medium">{s.name}</Td>
                    <Td
                      className={cn(
                        s.attendance_percent !== null && s.attendance_percent < d.thresholds.attendance && "font-semibold text-amber-800",
                      )}
                    >
                      {formatPercent(s.attendance_percent)}
                    </Td>
                    <Td>{s.absences}</Td>
                    {d.subjects.map((sub) => {
                      const v = s.subject_averages[sub];
                      return (
                        <Td key={sub} className={cn(v !== undefined && v < d.thresholds.performance && "font-semibold text-amber-800")}>
                          {v === undefined ? "—" : formatPercent(v)}
                        </Td>
                      );
                    })}
                    <Td className="font-medium">{formatPercent(s.overall_percent)}</Td>
                  </tr>
                ))}
              </Table>
            </Card>
          </div>
        )}
      </DataState>
    </>
  );
}
