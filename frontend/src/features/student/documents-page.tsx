"use client";

import { FileText, Printer } from "lucide-react";
import { useState } from "react";
import { Alert, Button, Card, DataState, PageHeader, Table, Td } from "@/components/ui";
import { formatPercent } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { studentApi } from "@/services/student";
import { DocumentTable } from "@/features/common/document-table";

export function StudentDocumentsPage() {
  const state = useApiQuery(studentApi.documents());
  const [term, setTerm] = useState<string | null>(null);
  return (
    <>
      <PageHeader title="Documents and report cards" />
      <DataState state={state}>
        {(d) => (
          <div className="space-y-6">
            <Card title="Report cards" className="no-print">
              <ul className="flex flex-wrap gap-3">
                {d.report_cards.map((r) => (
                  <li key={r.term_id}>
                    <Button
                      variant={term === r.term_id ? "primary" : "secondary"}
                      disabled={!r.available}
                      onClick={() => setTerm(r.term_id)}
                      icon={<FileText className="size-4" aria-hidden />}
                    >
                      {r.term} {r.available ? "" : "(not yet available)"}
                    </Button>
                  </li>
                ))}
              </ul>
            </Card>
            {term && <ReportCardView termId={term} />}
            <Card title="School and personal documents" className="no-print" padded={false}>
              <div className="p-4 pb-0">
                <Alert tone="warning">{d.storage_note}</Alert>
              </div>
              <DocumentTable documents={d.documents} />
            </Card>
          </div>
        )}
      </DataState>
    </>
  );
}

function ReportCardView({ termId }: { termId: string }) {
  const state = useApiQuery(studentApi.reportCard(termId));
  return (
    <DataState state={state}>
      {(r) => (
        <Card
          title={`Report card · ${r.term}`}
          action={
            <Button
              variant="secondary"
              size="sm"
              className="no-print"
              onClick={() => window.print()}
              icon={<Printer className="size-4" aria-hidden />}
            >
              Print
            </Button>
          }
        >
          <dl className="mb-4 grid gap-2 text-sm sm:grid-cols-4">
            <div>
              <dt className="text-muted">Student</dt>
              <dd className="font-medium">{r.student.name}</dd>
            </div>
            <div>
              <dt className="text-muted">Student ID</dt>
              <dd className="font-medium">{r.student.student_code}</dd>
            </div>
            <div>
              <dt className="text-muted">Class / Roll</dt>
              <dd className="font-medium">
                {r.student.section} / {r.student.roll_no}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Attendance</dt>
              <dd className="font-medium">
                {formatPercent(r.attendance.percent)} ({r.attendance.recorded_days} days)
              </dd>
            </div>
          </dl>
          <Table headers={["Subject", ...(r.subjects[0]?.trend.map((t) => t.assessment) ?? []), "Average"]} caption="Report card">
            {r.subjects.map((s) => (
              <tr key={s.subject}>
                <Td className="font-medium">{s.subject}</Td>
                {s.trend.map((t, i) => (
                  <Td key={i}>{formatPercent(t.percent)}</Td>
                ))}
                <Td className="font-semibold">{formatPercent(s.average_percent)}</Td>
              </tr>
            ))}
          </Table>
          <p className="mt-3 text-xs text-muted">{r.generated_note}</p>
        </Card>
      )}
    </DataState>
  );
}
