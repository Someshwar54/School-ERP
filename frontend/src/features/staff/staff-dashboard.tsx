"use client";

import Link from "next/link";
import { Alert, Card, DataState, EmptyState, PageHeader, Stat } from "@/components/ui";
import { AnnouncementList } from "@/features/common/announcements";
import { useApiQuery } from "@/lib/api/query";
import { formatDate, titleCase } from "@/lib/format";
import { staffApi } from "@/services/staff";

/** Home for non-teaching staff: attendance, leave and duties. */
export function StaffDashboard() {
  const state = useApiQuery(staffApi.dashboard());
  return (
    <DataState state={state}>
      {(d) => (
        <>
          <PageHeader
            title={`Welcome, ${d.profile.name.split(" ")[0]}`}
            description={`${d.profile.designation} · ${d.profile.department} · ${d.profile.staff_code}`}
          />
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat
              label="Present this month"
              value={d.attendance_this_month.present ?? 0}
              hint={
                Object.entries(d.attendance_this_month)
                  .filter(([k]) => k !== "present")
                  .map(([k, v]) => `${titleCase(k)}: ${v}`)
                  .join(" · ") || undefined
              }
            />
            <Stat label="Pending leave requests" value={d.pending_leave} />
            <Stat label="Open duties" value={d.duties.length} />
          </div>
          <Alert tone="info" className="mt-5">
            Your menu shows only the modules enabled for your role. Student marks, complaints, salaries and bank details are not available
            to this account.
          </Alert>
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <Card
              title="Assigned duties"
              action={
                <Link href="/erp/staff/duties" className="text-sm text-brand hover:underline">
                  All duties
                </Link>
              }
            >
              {d.duties.length === 0 ? (
                <EmptyState title="No open duties" />
              ) : (
                <ul className="divide-y divide-line text-sm">
                  {d.duties.map((x) => (
                    <li key={x.id} className="py-2">
                      {x.title} <span className="text-muted">· {formatDate(x.duty_date)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card title="Announcements">
              <AnnouncementList items={d.announcements} />
            </Card>
          </div>
        </>
      )}
    </DataState>
  );
}
