"use client";

import { useState } from "react";
import { barTrace, ChartPanel } from "@/components/charts/chart";
import { Alert, Badge, Button, Card, DataState, PageHeader, Pager, Select, Table, Td } from "@/components/ui";
import { formatDate, formatPercent } from "@/lib/format";
import { assessmentState } from "@/domain/status";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { managementApi } from "@/services/management";

export function ManagementAcademicsPage() {
  const [status, setStatus] = useState("unpublished");
  const [page, setPage] = useState(1);
  const state = useApiQuery(managementApi.academics(status, page));
  // Publishing changes what students see, so refresh management and teacher views of assessments.
  const publish = useApiMutation(managementApi.publishAssessment, { invalidates: ["/management", "/teacher/assessments"] });
  const [notice, setNotice] = useState<string | null>(null);

  async function onPublish(id: string) {
    setNotice(null);
    if (await publish.run(id).catch(() => null)) setNotice("Results published. Students can now see them.");
  }

  return (
    <>
      <PageHeader title="Academic performance" description="School-wide results from published assessments, and the publication queue." />
      <DataState state={state}>
        {(d) => {
          const grades = [...new Set(d.grade_subject.map((g) => g.grade))];
          const subjects = [...new Set(d.grade_subject.map((g) => g.subject))];
          return (
            <div className="space-y-6">
              <div className="grid gap-6 lg:grid-cols-2">
                <Card title="Average score by subject">
                  <ChartPanel
                    label="Average score by subject"
                    data={[
                      barTrace(
                        d.subject_performance.map((s) => s.subject),
                        d.subject_performance.map((s) => s.average_percent),
                        "Average %",
                      ),
                    ]}
                    layout={{ yaxis: { range: [0, 100], ticksuffix: "%", gridcolor: "#eef0f3" } }}
                    headers={["Subject", "Average"]}
                    rows={d.subject_performance.map((s) => [s.subject, formatPercent(s.average_percent)])}
                  />
                </Card>
                <Card title="Score distribution">
                  <ChartPanel
                    label="Score distribution"
                    data={[
                      barTrace(
                        d.score_distribution.map((b) => `${b.range}%`),
                        d.score_distribution.map((b) => b.count),
                        "Marks",
                      ),
                    ]}
                    layout={{ bargap: 0.15 }}
                    headers={["Range", "Count"]}
                    rows={d.score_distribution.map((b) => [b.range, b.count])}
                  />
                </Card>
              </div>
              <Card title="Average by grade and subject" padded={false}>
                <Table headers={["Grade", ...subjects]} caption="Average score by grade and subject">
                  {grades.map((g) => (
                    <tr key={g}>
                      <Td className="font-medium">Grade {g}</Td>
                      {subjects.map((s) => (
                        <Td key={s}>{formatPercent(d.grade_subject.find((x) => x.grade === g && x.subject === s)?.average_percent)}</Td>
                      ))}
                    </tr>
                  ))}
                </Table>
              </Card>
              <Card
                title="Assessments"
                padded={false}
                action={
                  <Select
                    aria-label="Filter assessments"
                    className="w-44"
                    value={status}
                    onChange={(e) => {
                      setStatus(e.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="unpublished">Awaiting publication</option>
                    <option value="published">Published</option>
                    <option value="">All</option>
                  </Select>
                }
              >
                {(notice || publish.error) && (
                  <div className="p-4 pb-0">
                    <Alert tone={publish.error ? "error" : "success"}>{publish.error?.message ?? notice}</Alert>
                  </div>
                )}
                <Table
                  headers={["Assessment", "Class", "Subject", "Date", "Marks entered", "Status", ""]}
                  empty={d.assessments.items.length === 0}
                  caption="Assessments"
                >
                  {d.assessments.items.map((a) => (
                    <tr key={a.id}>
                      <Td className="font-medium">{a.name}</Td>
                      <Td>{a.section}</Td>
                      <Td>{a.subject}</Td>
                      <Td>{formatDate(a.held_on)}</Td>
                      <Td>
                        {a.entered}/{a.enrolled}
                      </Td>
                      <Td>
                        <Badge tone={assessmentState(a).tone}>{assessmentState(a).label}</Badge>
                      </Td>
                      <Td>
                        {d.can_publish && !a.is_published && (
                          <Button size="sm" variant="secondary" disabled={!a.complete} onClick={() => void onPublish(a.id)}>
                            Publish
                          </Button>
                        )}
                      </Td>
                    </tr>
                  ))}
                </Table>
                <div className="px-4 pb-3">
                  <Pager page={d.assessments.page} pageSize={d.assessments.page_size} total={d.assessments.total} onPage={setPage} />
                </div>
              </Card>
            </div>
          );
        }}
      </DataState>
    </>
  );
}
