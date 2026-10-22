"use client";

import { Alert, Badge, Button, Card, DataState, PageHeader, Table, Td } from "@/components/ui";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDate } from "@/lib/format";
import { staffApi } from "@/services/staff";

export function StaffDutiesPage() {
  const state = useApiQuery(staffApi.duties());
  const complete = useApiMutation(staffApi.completeDuty, { invalidates: ["/staff/duties", "/staff/dashboard"] });
  return (
    <>
      <PageHeader title="Assigned duties" />
      {complete.error && (
        <Alert tone="error" className="mb-4">
          {complete.error.message}
        </Alert>
      )}
      <Card padded={false}>
        <DataState state={state}>
          {(rows) => (
            <Table headers={["Date", "Duty", "Status", ""]} empty={rows.length === 0} caption="Duties">
              {rows.map((d) => (
                <tr key={d.id}>
                  <Td>{formatDate(d.duty_date)}</Td>
                  <Td className="font-medium">
                    {d.title}
                    {d.details && <span className="block text-xs font-normal text-muted">{d.details}</span>}
                  </Td>
                  <Td>
                    <Badge tone={d.status === "done" ? "success" : "warning"}>{d.status === "done" ? "Done" : "Assigned"}</Badge>
                  </Td>
                  <Td>
                    {d.status !== "done" && (
                      <Button size="sm" variant="secondary" onClick={() => void complete.run(d.id).catch(() => null)}>
                        Mark done
                      </Button>
                    )}
                  </Td>
                </tr>
              ))}
            </Table>
          )}
        </DataState>
      </Card>
    </>
  );
}
