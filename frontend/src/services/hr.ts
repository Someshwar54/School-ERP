/** HR endpoints: directory, leave approvals, payroll (each needs its own permission). */
import { http, withQuery, type Page } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";
import type { Leave } from "./shared";

export interface StaffDirectoryRow {
  id: string;
  staff_code: string;
  name: string;
  designation: string;
  department: string;
  staff_type: string;
  joining_date: string;
  email: string | null;
}

export interface PayrollRow {
  staff_code: string;
  name: string;
  designation: string;
  pay_grade: string;
  monthly_gross: string;
  effective_from: string;
  bank_account: string | null;
}

export const hrApi = {
  directory: (q: string, page: number) => queryDef<Page<StaffDirectoryRow>>(withQuery("/hr/staff", { q, page, page_size: 15 })),
  leaveRequests: (status: string) => queryDef<Leave[]>(withQuery("/hr/leave-requests", { status })),
  payroll: () => queryDef<PayrollRow[]>("/hr/payroll"),
  decideLeave: ({ id, decision }: { id: string; decision: "approved" | "rejected" }) =>
    http.post<{ ok: boolean; status: string }>(`/hr/leave-requests/${id}/decision`, {
      decision,
      comment: decision === "approved" ? "Approved." : "Not approved.",
    }),
};
