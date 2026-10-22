"use client";

import { useState } from "react";
import { useSession } from "@/features/auth/use-session";
import { Alert, Badge, Card, DataState, PageHeader, Pager, Table, Td } from "@/components/ui";
import { formatDateTime, titleCase } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { managementApi } from "@/services/management";

export function ManagementReportsPage() {
  const { can } = useSession();
  const [page, setPage] = useState(1);
  const enquiries = useApiQuery(can("admissions.view") ? managementApi.enquiries(page) : null);
  return (
    <>
      <PageHeader title="Reports and analytics" description="Operational reports. Scheduled and exported reports are planned." />
      <Alert tone="info" className="mb-5">
        PDF/Excel exports and scheduled email reports are not connected in this prototype. They will run as background jobs so large reports
        do not slow the portal.
      </Alert>
      {can("admissions.view") ? (
        <Card title="Admission enquiries (from the public website)" padded={false}>
          <DataState state={enquiries}>
            {(d) => (
              <>
                <Table
                  headers={["Received", "Parent", "Contact", "Grade", "Message", "Status"]}
                  empty={d.items.length === 0}
                  caption="Admission enquiries"
                >
                  {d.items.map((e) => (
                    <tr key={e.id}>
                      <Td>{formatDateTime(e.created_at)}</Td>
                      <Td className="font-medium">{e.parent_name}</Td>
                      <Td>
                        {e.email}
                        <span className="block text-xs text-muted">{e.phone}</span>
                      </Td>
                      <Td>{e.grade_sought}</Td>
                      <Td className="text-muted">{e.message ?? ""}</Td>
                      <Td>
                        <Badge tone={e.status === "new" ? "info" : "neutral"}>{titleCase(e.status)}</Badge>
                      </Td>
                    </tr>
                  ))}
                </Table>
                <div className="px-4 pb-3">
                  <Pager page={d.page} pageSize={d.page_size} total={d.total} onPage={setPage} />
                </div>
              </>
            )}
          </DataState>
        </Card>
      ) : (
        <Alert tone="neutral">
          Admission enquiries are not available for your role. Aggregated analytics are on the Executive Overview.
        </Alert>
      )}
    </>
  );
}
