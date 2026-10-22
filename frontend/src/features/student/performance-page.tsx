"use client";

import { barTrace, ChartPanel } from "@/components/charts/chart";
import { Badge, Card, DataState, EmptyState, PageHeader, Stat, Table, Td } from "@/components/ui";
import { formatPercent } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { studentApi } from "@/services/student";

export function StudentPerformancePage() {
  const state = useApiQuery(studentApi.performance());
  return (
    <>
      <PageHeader
        title="Academic performance"
        description="Calculated only from results the school has published. Absences and missing marks are excluded from averages."
      />
      <DataState state={state}>
        {(d) =>
          d.insufficient_data ? (
            <EmptyState title="Not enough published results yet" text="Your performance summary will appear once results are published." />
          ) : (
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-3">
                <Stat label="Overall average" value={formatPercent(d.overall_percent)} />
                <Stat label="Subjects" value={d.subjects.length} />
                <Stat label="Published assessments" value={Math.max(...d.subjects.map((s) => s.assessments))} />
              </div>
              <Card title="Average by subject">
                <ChartPanel
                  label="Average percentage by subject"
                  data={[
                    barTrace(
                      d.subjects.map((s) => s.subject),
                      d.subjects.map((s) => s.average_percent),
                      "Average %",
                    ),
                  ]}
                  layout={{ yaxis: { range: [0, 100], ticksuffix: "%", gridcolor: "#eef0f3" } }}
                  headers={["Subject", "Average"]}
                  rows={d.subjects.map((s) => [s.subject, formatPercent(s.average_percent)])}
                />
              </Card>
              <Card title="Subject details" padded={false}>
                <Table
                  headers={["Subject", "Average", ...d.subjects[0].trend.map((t) => t.assessment), "Note"]}
                  caption="Subject performance by assessment"
                >
                  {d.subjects.map((s) => (
                    <tr key={s.subject}>
                      <Td className="font-medium">{s.subject}</Td>
                      <Td>{formatPercent(s.average_percent)}</Td>
                      {s.trend.map((t, i) => (
                        <Td key={i}>{formatPercent(t.percent)}</Td>
                      ))}
                      <Td>{s.insufficient_data ? <Badge tone="warning">Limited data</Badge> : null}</Td>
                    </tr>
                  ))}
                </Table>
              </Card>
            </div>
          )
        }
      </DataState>
    </>
  );
}
