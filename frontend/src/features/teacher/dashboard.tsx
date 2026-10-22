"use client";

import Link from "next/link";
import { Card, DataState, EmptyState, PageHeader, Stat } from "@/components/ui";
import { AnnouncementList } from "@/features/common/announcements";
import { useApiQuery } from "@/lib/api/query";
import { formatDate } from "@/lib/format";
import { teacherApi } from "@/services/teacher";

/** Teacher home: today's periods, pending academic tasks, duties and announcements. */
export function TeacherDashboard() {
  const state = useApiQuery(teacherApi.dashboard());
  return (
    <DataState state={state} loadingLabel="Loading your dashboard…">
      {(d) => (
        <>
          <PageHeader
            title="Teacher dashboard"
            description={`${d.assignments.length} class-subject assignments${d.class_teacher_of.length ? ` · Class teacher of ${d.class_teacher_of.map((c) => c.section).join(", ")}` : ""}`}
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Stat label="Periods today" value={d.today_periods.length} />
            <Stat
              label="Missing registers"
              value={d.pending.missing_registers.length}
              tone={d.pending.missing_registers.length ? "warning" : "good"}
              hint="Your class, last 2 weeks"
            />
            <Stat
              label="Incomplete marks"
              value={d.pending.incomplete_assessments.length}
              tone={d.pending.incomplete_assessments.length ? "warning" : "good"}
            />
            <Stat label="Open complaints assigned" value={d.pending.assigned_complaints} />
          </div>
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <Card
              title="Today's periods"
              action={
                <Link href="/erp/staff/topics" className="text-sm text-brand hover:underline">
                  Lesson progression
                </Link>
              }
            >
              {d.today_periods.length === 0 ? (
                <EmptyState title="No periods today" />
              ) : (
                <ol className="divide-y divide-line text-sm">
                  {d.today_periods.map((p) => (
                    <li key={p.timetable_entry_id} className="flex flex-wrap justify-between gap-2 py-2">
                      <span>
                        <span className="text-muted">P{p.period_no}</span> ·{" "}
                        <span className="font-medium">
                          {p.section} {p.subject}
                        </span>
                      </span>
                      <span className="text-muted">
                        {p.current_topic
                          ? `In progress: ${p.current_topic.title}`
                          : p.next_topic
                            ? `Next: ${p.next_topic.title}`
                            : "No planned topic"}
                      </span>
                    </li>
                  ))}
                </ol>
              )}
            </Card>
            <Card title="Pending academic tasks">
              {d.pending.missing_registers.length === 0 && d.pending.incomplete_assessments.length === 0 ? (
                <EmptyState title="Nothing pending" />
              ) : (
                <ul className="space-y-2 text-sm">
                  {d.pending.missing_registers.map((m) => (
                    <li key={m.day}>
                      <Link href="/erp/staff/attendance" className="text-brand hover:underline">
                        Daily register missing: {m.section}, {formatDate(m.day)}
                      </Link>
                    </li>
                  ))}
                  {d.pending.incomplete_assessments.map((a) => (
                    <li key={a.assessment_id}>
                      <Link href="/erp/staff/marks" className="text-brand hover:underline">
                        {a.name} ({a.section}): {a.missing} mark(s) missing
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card title="Announcements">
              <AnnouncementList items={d.announcements} />
            </Card>
            <Card title="Upcoming duties">
              {d.duties.length === 0 ? (
                <EmptyState title="No duties assigned" />
              ) : (
                <ul className="divide-y divide-line text-sm">
                  {d.duties.map((x) => (
                    <li key={x.title} className="py-2">
                      {x.title} <span className="text-muted">· {formatDate(x.duty_date)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </>
      )}
    </DataState>
  );
}
