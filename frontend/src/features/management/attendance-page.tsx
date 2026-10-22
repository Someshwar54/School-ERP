"use client";

import { ChartPanel, lineTrace } from "@/components/charts/chart";
import { Card, DataState, EmptyState, PageHeader, Stat, Table, Td } from "@/components/ui";
import { formatDate, formatPercent } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { managementApi } from "@/services/management";

export function ManagementAttendancePage() {
  const state = useApiQuery(managementApi.attendance());
  return (
    <>
      <PageHeader
        title="Student and staff attendance"
        description="Holidays and weekly offs are excluded. Days without a register are reported as missing records, not absences."
      />
      <DataState state={state}>
        {(d) => (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <Stat label="Latest student attendance" value={formatPercent(d.trend.at(-1)?.percent)} />
              <Stat
                label={`Students below ${d.threshold_percent}%`}
                value={d.students_below_threshold}
                tone={d.students_below_threshold ? "warning" : "good"}
                hint="Year to date (class teachers follow up individually)"
              />
              <Stat
                label="Missing registers (10 school days)"
                value={d.missing_registers.length}
                tone={d.missing_registers.length ? "warning" : "good"}
              />
            </div>
            <div className="grid gap-6 lg:grid-cols-2">
              <Card title="Student attendance, last 30 school days">
                <ChartPanel
                  label="Daily student attendance"
                  data={[
                    lineTrace(
                      d.trend.map((t) => formatDate(t.day, { day: "numeric", month: "short" })),
                      d.trend.map((t) => t.percent),
                      "Students",
                      "%",
                    ),
                  ]}
                  layout={{ yaxis: { range: [80, 100], ticksuffix: "%", gridcolor: "#eef0f3" } }}
                  headers={["Day", "Attendance"]}
                  rows={d.trend.map((t) => [t.day, formatPercent(t.percent)])}
                />
              </Card>
              <Card title="Staff attendance, last 15 school days">
                <ChartPanel
                  label="Daily staff attendance"
                  data={[
                    lineTrace(
                      d.staff_trend.map((t) => formatDate(t.day, { day: "numeric", month: "short" })),
                      d.staff_trend.map((t) => t.percent),
                      "Staff",
                      "%",
                    ),
                  ]}
                  layout={{ yaxis: { range: [70, 100], ticksuffix: "%", gridcolor: "#eef0f3" } }}
                  headers={["Day", "Attendance"]}
                  rows={d.staff_trend.map((t) => [t.day, formatPercent(t.percent)])}
                />
              </Card>
            </div>
            <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
              <Card title="By class (year to date)" padded={false}>
                <Table headers={["Class", "Attendance", "Present", "Late", "Absent", "Authorised", "Days"]} caption="Attendance by class">
                  {d.by_section.map((s) => (
                    <tr key={s.section}>
                      <Td className="font-medium">{s.section}</Td>
                      <Td>{formatPercent(s.percent)}</Td>
                      <Td>{s.present}</Td>
                      <Td>{s.late}</Td>
                      <Td>{s.absent}</Td>
                      <Td>{s.approved_leave + s.excused}</Td>
                      <Td>{s.recorded_days}</Td>
                    </tr>
                  ))}
                </Table>
              </Card>
              <Card title="Missing daily registers">
                {d.missing_registers.length === 0 ? (
                  <EmptyState title="All registers taken" />
                ) : (
                  <ul className="divide-y divide-line text-sm">
                    {d.missing_registers.map((m) => (
                      <li key={`${m.section}${m.day}`} className="py-2">
                        Class {m.section} · {formatDate(m.day)}
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>
          </div>
        )}
      </DataState>
    </>
  );
}
