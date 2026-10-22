"use client";

import { Alert, Card, DataState, EmptyState, PageHeader, Stat, Table, Td } from "@/components/ui";
import { formatDate, titleCase } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { staffApi } from "@/services/staff";

export function StaffAttendancePage() {
  const state = useApiQuery(staffApi.attendance());
  return (
    <>
      <PageHeader title="My attendance" description="Your attendance as recorded by the school office this month." />
      <DataState state={state}>
        {(d) => (
          <div className="space-y-5">
            <Alert tone="info">{d.note}</Alert>
            <div className="grid gap-4 sm:grid-cols-4">
              {["present", "late", "on_leave", "absent"].map((k) => (
                <Stat key={k} label={titleCase(k)} value={d.summary[k] ?? 0} />
              ))}
            </div>
            <Card title={formatDate(`${d.month}-01`, { month: "long", year: "numeric" })} padded={false}>
              {d.days.length === 0 ? (
                <div className="p-4">
                  <EmptyState title="No records this month" />
                </div>
              ) : (
                <Table headers={["Date", "Status", "Check-in", "Check-out"]} caption="Staff attendance">
                  {d.days.map((r) => (
                    <tr key={r.day}>
                      <Td>{formatDate(r.day)}</Td>
                      <Td>{titleCase(r.status)}</Td>
                      <Td>{r.check_in?.slice(0, 5) ?? "—"}</Td>
                      <Td>{r.check_out?.slice(0, 5) ?? "—"}</Td>
                    </tr>
                  ))}
                </Table>
              )}
            </Card>
          </div>
        )}
      </DataState>
    </>
  );
}
