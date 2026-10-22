"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import { ChartPanel, lineTrace } from "@/components/charts/chart";
import { Card, DataState, PageHeader, Stat } from "@/components/ui";
import { cn } from "@/lib/cn";
import { formatDate, formatPercent } from "@/lib/format";
import { useTodayISO } from "@/hooks/use-today";
import { shiftMonth, weekdayIndex } from "@/domain/attendance";
import { useApiQuery } from "@/lib/api/query";
import { studentApi, type CalendarDayStatus } from "@/services/student";

/** Presentation of each calendar state (colours are UI concerns; the states come from the API). */
const STATUS: Record<CalendarDayStatus, { label: string; short: string; cls: string }> = {
  present: { label: "Present", short: "P", cls: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  late: { label: "Late arrival", short: "L", cls: "bg-amber-50 text-amber-900 border-amber-200" },
  absent: { label: "Absent", short: "A", cls: "bg-red-50 text-red-800 border-red-200" },
  approved_leave: { label: "Approved leave", short: "AL", cls: "bg-sky-50 text-sky-800 border-sky-200" },
  excused: { label: "Excused absence", short: "EX", cls: "bg-indigo-50 text-indigo-800 border-indigo-200" },
  not_recorded: { label: "Not recorded", short: "–", cls: "bg-white text-muted border-dashed border-line" },
  holiday: { label: "Holiday", short: "H", cls: "bg-surface text-muted border-line" },
  weekly_off: { label: "Weekly off", short: "", cls: "bg-surface text-muted/60 border-line" },
  upcoming: { label: "Upcoming", short: "", cls: "bg-white text-muted/60 border-line" },
  outside_year: { label: "Outside academic year", short: "", cls: "bg-surface text-muted/40 border-line" },
};

export function StudentAttendancePage() {
  const today = useTodayISO();
  const [picked, setMonth] = useState<string | null>(null);
  const month = picked ?? today?.slice(0, 7) ?? null;
  const state = useApiQuery(month ? studentApi.attendance(month) : null);
  const monthLabel = month ? formatDate(`${month}-01`, { month: "long", year: "numeric" }) : "";

  return (
    <>
      <PageHeader
        title="Attendance"
        description="Daily attendance recorded by your class teacher. Holidays and weekly offs are never counted as absences."
      />
      <DataState state={state}>
        {(d) => {
          const firstDow = weekdayIndex(`${d.month}-01`); // Monday-first grid
          return (
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Stat
                  label="This year"
                  value={formatPercent(d.year_summary.percent)}
                  hint={`${d.year_summary.recorded_days} recorded days`}
                  tone={d.year_summary.percent !== null && d.year_summary.percent < d.policy.alert_below_percent ? "warning" : undefined}
                />
                <Stat
                  label={monthLabel}
                  value={formatPercent(d.month_summary.percent)}
                  hint={`${d.month_summary.recorded_days} recorded days`}
                />
                <Stat
                  label="Absences this year"
                  value={d.year_summary.absent}
                  hint={`${d.year_summary.approved_leave + d.year_summary.excused} authorised`}
                />
                <Stat
                  label="Late arrivals"
                  value={d.year_summary.late}
                  hint={d.policy.late_counts_as_present ? "Counted as attended" : "Not counted as attended"}
                />
              </div>
              <Card
                title={monthLabel}
                action={
                  <div className="flex gap-1">
                    <button
                      type="button"
                      className="rounded-brand border border-line p-1.5 hover:bg-surface"
                      onClick={() => setMonth(shiftMonth(d.month, -1))}
                      aria-label="Previous month"
                    >
                      <ChevronLeft className="size-4" aria-hidden />
                    </button>
                    <button
                      type="button"
                      className="rounded-brand border border-line p-1.5 hover:bg-surface"
                      onClick={() => setMonth(shiftMonth(d.month, 1))}
                      aria-label="Next month"
                    >
                      <ChevronRight className="size-4" aria-hidden />
                    </button>
                  </div>
                }
              >
                <div className="grid grid-cols-7 gap-1.5 text-center text-xs" role="grid" aria-label={`Attendance for ${monthLabel}`}>
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((w) => (
                    <div key={w} className="py-1 font-medium text-muted" role="columnheader">
                      {w}
                    </div>
                  ))}
                  {Array.from({ length: firstDow }).map((_, i) => (
                    <div key={`pad${i}`} />
                  ))}
                  {d.days.map((day) => {
                    const s = STATUS[day.status];
                    return (
                      <div
                        key={day.day}
                        role="gridcell"
                        title={`${formatDate(day.day)}: ${day.holiday_name ?? s.label}${day.remark ? ` — ${day.remark}` : ""}`}
                        aria-label={`${formatDate(day.day)}: ${day.holiday_name ?? s.label}`}
                        className={cn(
                          "flex aspect-square flex-col items-center justify-center rounded-md border sm:aspect-auto sm:h-14",
                          s.cls,
                        )}
                      >
                        <span className="text-[11px] opacity-70">{Number(day.day.slice(8))}</span>
                        <span className="font-semibold">{s.short}</span>
                      </div>
                    );
                  })}
                </div>
                <ul className="mt-4 flex flex-wrap gap-3 text-xs">
                  {(["present", "late", "absent", "approved_leave", "excused", "not_recorded", "holiday"] as CalendarDayStatus[]).map(
                    (k) => (
                      <li key={k} className="flex items-center gap-1.5">
                        <span
                          className={cn(
                            "inline-flex h-5 min-w-5 items-center justify-center rounded border px-1 font-semibold",
                            STATUS[k].cls,
                          )}
                        >
                          {STATUS[k].short || " "}
                        </span>
                        {STATUS[k].label}
                      </li>
                    ),
                  )}
                </ul>
                {d.not_recorded_days > 0 && (
                  <p className="mt-3 text-xs text-muted">
                    {d.not_recorded_days} school day(s) this month have no attendance record yet. These are not counted as absences.
                  </p>
                )}
              </Card>
              <Card title="Monthly attendance trend">
                <ChartPanel
                  label="Monthly attendance percentage"
                  data={[
                    lineTrace(
                      d.trend.map((t) => formatDate(`${t.month}-01`, { month: "short", year: "numeric" })),
                      d.trend.map((t) => t.percent),
                      "Attendance",
                      "%",
                    ),
                  ]}
                  layout={{ yaxis: { range: [0, 100], ticksuffix: "%", gridcolor: "#eef0f3" } }}
                  height={240}
                  headers={["Month", "Attendance", "Present", "Late", "Absent", "Authorised"]}
                  rows={d.trend.map((t) => [t.month, formatPercent(t.percent), t.present, t.late, t.absent, t.approved_leave + t.excused])}
                />
              </Card>
            </div>
          );
        }}
      </DataState>
    </>
  );
}
