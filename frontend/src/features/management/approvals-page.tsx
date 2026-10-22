"use client";

import { useState } from "react";
import { LeaveApprovals } from "@/features/common/hr-view";
import { useSession } from "@/features/auth/use-session";
import { Alert, Card, DataState, Input, PageHeader, Pager, Table, Td } from "@/components/ui";
import { formatDateTime } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { managementApi } from "@/services/management";

export function ApprovalsAuditPage() {
  const { can } = useSession();
  return (
    <>
      <PageHeader title="Approvals and audit" description="Decisions are recorded permanently. The audit log is append-only." />
      <div className="space-y-6">
        {(can("approvals.decide_leave") || can("hr.view")) && <LeaveApprovals canDecide={can("approvals.decide_leave")} />}
        {can("marks.publish") && <Alert tone="info">Result publication is handled from Academic Performance → Assessments.</Alert>}
        {can("audit.view") && <AuditLog />}
      </div>
    </>
  );
}

function AuditLog() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const state = useApiQuery(managementApi.audit(action, page));
  return (
    <Card
      title="Audit log"
      padded={false}
      action={
        <Input
          className="w-56"
          placeholder="Filter, e.g. auth. or marks."
          aria-label="Filter audit actions"
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setPage(1);
          }}
        />
      }
    >
      <DataState state={state}>
        {(d) => (
          <>
            <Table headers={["Time", "Action", "Actor", "Entity", "Details", "IP"]} empty={d.items.length === 0} caption="Audit log">
              {d.items.map((r) => (
                <tr key={r.id}>
                  <Td className="whitespace-nowrap">{formatDateTime(r.created_at)}</Td>
                  <Td>
                    <code className="text-xs">{r.action}</code>
                  </Td>
                  <Td>{r.actor ?? "—"}</Td>
                  <Td className="text-xs text-muted">{r.entity_type ?? ""}</Td>
                  <Td className="max-w-xs truncate text-xs text-muted">{Object.keys(r.details).length ? JSON.stringify(r.details) : ""}</Td>
                  <Td className="text-xs text-muted">{r.ip ?? ""}</Td>
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
  );
}
