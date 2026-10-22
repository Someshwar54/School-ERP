"use client";

import Link from "next/link";
import { AnnouncementList } from "@/features/common/announcements";
import { Card, DataState, EmptyState, PageHeader, Stat } from "@/components/ui";
import { formatDate, formatMoney, formatPercent } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { studentApi } from "@/services/student";

export function StudentDashboardPage() {
  const state = useApiQuery(studentApi.dashboard());
  return (
    <DataState state={state} loadingLabel="Loading your dashboard…">
      {(d) => {
        const time = (p: number) => d.periods.find((x) => x.period_no === p);
        return (
          <>
            <PageHeader
              title={`Hello, ${d.student.name.split(" ")[0]}`}
              description={`${d.student.student_code} · Class ${d.student.section ?? "—"} · Roll no. ${d.student.roll_no ?? "—"}`}
            />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Stat
                label="Attendance this year"
                value={formatPercent(d.attendance.percent)}
                hint={`${d.attendance.recorded_days} recorded school days`}
                tone={d.attendance.percent !== null && d.attendance.percent < 75 ? "warning" : undefined}
              />
              <Stat label="Days absent" value={d.attendance.absent} hint={`${d.attendance.late} late arrivals`} />
              <Stat
                label="Outstanding fees"
                value={formatMoney(d.fees.outstanding)}
                hint={d.fees.next_due ? `Due ${formatDate(d.fees.next_due.due_on)}` : "Nothing due"}
                tone={Number(d.fees.outstanding) > 0 ? "warning" : "good"}
              />
              <Stat label="Classes today" value={d.today_classes.length} hint="See full timetable" />
            </div>
            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <Card
                title="Today's classes"
                action={
                  <Link href="/erp/student/timetable" className="text-sm text-brand hover:underline">
                    Timetable
                  </Link>
                }
              >
                {d.today_classes.length === 0 ? (
                  <EmptyState title="No classes today" />
                ) : (
                  <ol className="divide-y divide-line">
                    {d.today_classes.map((c) => (
                      <li key={c.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                        <span className="w-24 shrink-0 text-muted">
                          {time(c.period_no)?.starts_at}–{time(c.period_no)?.ends_at}
                        </span>
                        <span className="flex-1 font-medium">{c.subject}</span>
                        <span className="text-right text-muted">
                          {c.teacher ?? ""}
                          {c.room ? ` · ${c.room}` : ""}
                        </span>
                      </li>
                    ))}
                  </ol>
                )}
              </Card>
              <Card
                title="Recent published results"
                action={
                  <Link href="/erp/student/results" className="text-sm text-brand hover:underline">
                    All results
                  </Link>
                }
              >
                {d.recent_results.length === 0 ? (
                  <EmptyState title="No published results yet" />
                ) : (
                  <ul className="divide-y divide-line">
                    {d.recent_results.map((r, i) => (
                      <li key={i} className="flex items-center justify-between gap-3 py-2 text-sm">
                        <span>
                          <span className="font-medium">{r.subject}</span> <span className="text-muted">· {r.assessment}</span>
                        </span>
                        <span className="text-right">
                          {r.status === "absent"
                            ? "Absent"
                            : r.marks_obtained !== null
                              ? `${r.marks_obtained}/${r.max_marks}`
                              : "Not recorded"}
                          {r.grade && <span className="ml-2 text-muted">{r.grade}</span>}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
              <Card
                title="Announcements"
                action={
                  <Link href="/erp/student/announcements" className="text-sm text-brand hover:underline">
                    View all
                  </Link>
                }
              >
                <AnnouncementList items={d.announcements} />
              </Card>
              <Card
                title="Upcoming events"
                action={
                  <Link href="/erp/student/events" className="text-sm text-brand hover:underline">
                    View all
                  </Link>
                }
              >
                {d.events.length === 0 ? (
                  <EmptyState title="No upcoming events" />
                ) : (
                  <ul className="divide-y divide-line">
                    {d.events.map((e) => (
                      <li key={e.id} className="py-2 text-sm">
                        <p className="font-medium">{e.title}</p>
                        <p className="text-muted">
                          {formatDate(e.starts_at)} · {e.location}
                        </p>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>
          </>
        );
      }}
    </DataState>
  );
}
