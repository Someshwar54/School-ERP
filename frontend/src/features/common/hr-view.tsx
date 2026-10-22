"use client";

import { useState } from "react";
import { Alert, Badge, Button, Card, DataState, Input, PageHeader, Pager, Select, Table, Tabs, Td } from "@/components/ui";
import { LEAVE_TONE } from "@/domain/status";
import { useSession } from "@/features/auth/use-session";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { formatDate, formatMoney, titleCase } from "@/lib/format";
import { hrApi } from "@/services/hr";

type Tab = "directory" | "leave" | "payroll";

/** HR module. Tabs appear per permission; the backend enforces each endpoint independently. */
export function HrView() {
  const { can } = useSession();
  const tabs: { key: Tab; label: string }[] = [
    ...(can("hr.view") ? [{ key: "directory" as const, label: "Staff directory" }] : []),
    ...(can("hr.view") || can("approvals.decide_leave") ? [{ key: "leave" as const, label: "Leave requests" }] : []),
    ...(can("payroll.view") ? [{ key: "payroll" as const, label: "Payroll" }] : []),
  ];
  const [picked, setTab] = useState<Tab | null>(null);
  const current = picked ?? tabs[0]?.key ?? null;
  return (
    <>
      <PageHeader
        title="HR and payroll"
        description="Salaries are visible only to roles with payroll permission, and every payroll view is audited."
      />
      <Tabs label="HR sections" tabs={tabs} active={current} onChange={setTab} />
      {tabs.length === 0 && <Alert tone="info">Your role does not include HR or payroll access.</Alert>}
      {current === "directory" && <StaffDirectory />}
      {current === "leave" && <LeaveApprovals canDecide={can("approvals.decide_leave")} />}
      {current === "payroll" && <Payroll />}
    </>
  );
}

function StaffDirectory() {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const state = useApiQuery(hrApi.directory(q, page));
  return (
    <Card
      title="Staff directory"
      padded={false}
      action={
        <Input
          className="w-56"
          placeholder="Search name, ID, department"
          aria-label="Search staff"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
        />
      }
    >
      <DataState state={state}>
        {(d) => (
          <>
            <Table
              headers={["ID", "Name", "Designation", "Department", "Type", "Joined"]}
              empty={d.items.length === 0}
              caption="Staff directory"
            >
              {d.items.map((s) => (
                <tr key={s.id}>
                  <Td>{s.staff_code}</Td>
                  <Td className="font-medium">
                    {s.name}
                    <span className="block text-xs font-normal text-muted">{s.email}</span>
                  </Td>
                  <Td>{s.designation}</Td>
                  <Td>{s.department}</Td>
                  <Td>{titleCase(s.staff_type)}</Td>
                  <Td>{formatDate(s.joining_date)}</Td>
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

export function LeaveApprovals({ canDecide }: { canDecide: boolean }) {
  const [status, setStatus] = useState("pending");
  const state = useApiQuery(hrApi.leaveRequests(status));
  const decide = useApiMutation(hrApi.decideLeave, { invalidates: ["/hr/leave-requests", "/management/overview"] });
  const [notice, setNotice] = useState<string | null>(null);

  async function onDecide(id: string, decision: "approved" | "rejected") {
    setNotice(null);
    if (await decide.run({ id, decision }).catch(() => null)) setNotice(`Request ${decision}.`);
  }

  return (
    <Card
      title="Leave requests"
      padded={false}
      action={
        <Select aria-label="Filter by status" className="w-36" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
          <option value="">All</option>
        </Select>
      }
    >
      {(notice || decide.error) && (
        <div className="p-4 pb-0">
          <Alert tone={decide.error ? "error" : "success"}>{decide.error?.message ?? notice}</Alert>
        </div>
      )}
      <DataState state={state}>
        {(rows) => (
          <Table headers={["Staff", "Type", "Dates", "Reason", "Status", ""]} empty={rows.length === 0} caption="Leave requests">
            {rows.map((r) => (
              <tr key={r.id}>
                <Td className="font-medium">{r.staff_name}</Td>
                <Td>{titleCase(r.leave_type)}</Td>
                <Td>
                  {formatDate(r.starts_on)} – {formatDate(r.ends_on)} ({r.days}d)
                </Td>
                <Td className="text-muted">{r.reason}</Td>
                <Td>
                  <Badge tone={LEAVE_TONE[r.status]}>{titleCase(r.status)}</Badge>
                </Td>
                <Td>
                  {canDecide &&
                    r.status === "pending" &&
                    (r.is_own ? (
                      <span className="text-xs text-muted">Own request</span>
                    ) : (
                      <span className="flex gap-1">
                        <Button size="sm" onClick={() => void onDecide(r.id, "approved")}>
                          Approve
                        </Button>
                        <Button size="sm" variant="secondary" onClick={() => void onDecide(r.id, "rejected")}>
                          Reject
                        </Button>
                      </span>
                    ))}
                </Td>
              </tr>
            ))}
          </Table>
        )}
      </DataState>
    </Card>
  );
}

function Payroll() {
  const state = useApiQuery(hrApi.payroll());
  return (
    <Card title="Payroll (current compensation)" padded={false}>
      <div className="p-4 pb-0">
        <Alert tone="warning">
          Confidential. Your access to this page is recorded in the audit log. Payroll processing and payslips are not connected in this
          prototype.
        </Alert>
      </div>
      <DataState state={state}>
        {(rows) => (
          <Table headers={["ID", "Name", "Designation", "Grade", "Monthly gross", "Effective", "Bank"]} caption="Payroll">
            {rows.map((r) => (
              <tr key={r.staff_code}>
                <Td>{r.staff_code}</Td>
                <Td className="font-medium">{r.name}</Td>
                <Td>{r.designation}</Td>
                <Td>{r.pay_grade}</Td>
                <Td>{formatMoney(r.monthly_gross)}</Td>
                <Td>{formatDate(r.effective_from)}</Td>
                <Td>{r.bank_account ?? "—"}</Td>
              </tr>
            ))}
          </Table>
        )}
      </DataState>
    </Card>
  );
}
