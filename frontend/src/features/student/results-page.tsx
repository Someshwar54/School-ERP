"use client";

import { Badge, Card, DataState, EmptyState, PageHeader, Table, Td } from "@/components/ui";
import { formatDate, formatPercent } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { studentApi } from "@/services/student";

export function StudentResultsPage() {
  const state = useApiQuery(studentApi.results());
  return (
    <>
      <PageHeader
        title="Examinations and results"
        description="Only results published by the school are shown. Unpublished marks remain hidden until released."
      />
      <DataState state={state}>
        {(d) =>
          d.exams.length === 0 ? (
            <EmptyState title="No published results yet" />
          ) : (
            <div className="space-y-6">
              {[...d.exams].reverse().map((exam) => (
                <Card
                  key={exam.assessment}
                  title={`${exam.assessment} · ${formatDate(exam.held_on)}`}
                  action={
                    <span className="text-sm text-muted">
                      Total {exam.total} / {exam.maximum} ({formatPercent(exam.percent)})
                    </span>
                  }
                  padded={false}
                >
                  <Table headers={["Subject", "Marks", "Percentage", "Grade", "Remarks"]} caption={`${exam.assessment} results`}>
                    {exam.subjects.map((s) => (
                      <tr key={s.subject}>
                        <Td className="font-medium">{s.subject}</Td>
                        <Td>
                          {s.status === "absent" ? (
                            <Badge tone="warning">Absent</Badge>
                          ) : s.status === "not_recorded" ? (
                            <Badge>Not recorded</Badge>
                          ) : (
                            `${s.marks_obtained} / ${s.max_marks}`
                          )}
                        </Td>
                        <Td>{formatPercent(s.percent)}</Td>
                        <Td>{s.grade ?? "—"}</Td>
                        <Td className="text-muted">{s.remarks ?? ""}</Td>
                      </tr>
                    ))}
                  </Table>
                </Card>
              ))}
            </div>
          )
        }
      </DataState>
    </>
  );
}
