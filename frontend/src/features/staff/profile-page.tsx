"use client";

import { AccountSettings } from "@/features/common/account-settings";
import { Card, DataState } from "@/components/ui";
import { formatDate, titleCase } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { staffApi } from "@/services/staff";

export function StaffProfilePage() {
  const state = useApiQuery(staffApi.profile());
  return (
    <div className="space-y-6">
      <AccountSettings />
      <Card title="Employment profile">
        <DataState state={state}>
          {(p) => (
            <dl className="grid gap-y-2 text-sm sm:grid-cols-[12rem_1fr]">
              {[
                ["Staff ID", p.staff_code],
                ["Name", p.name],
                ["Designation", p.designation],
                ["Department", p.department],
                ["Staff type", titleCase(p.staff_type)],
                ["Joined", formatDate(p.joining_date)],
                ["Qualification", p.qualification ?? "—"],
                ["Work email", p.email ?? "—"],
              ].map(([k, v]) => (
                <div key={k} className="contents">
                  <dt className="text-muted">{k}</dt>
                  <dd className="font-medium">{v}</dd>
                </div>
              ))}
            </dl>
          )}
        </DataState>
        <p className="mt-3 text-xs text-muted">To update employment records, contact HR.</p>
      </Card>
    </div>
  );
}
