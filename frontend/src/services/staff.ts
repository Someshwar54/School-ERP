/** Staff self-service endpoints (any staff or management account with a staff profile). */
import { http } from "@/lib/api/client";
import { queryDef } from "@/lib/api/query-def";
import type { Announcement, DocumentRecord, Leave } from "./shared";

export interface StaffProfile {
  staff_code: string;
  name: string;
  designation: string;
  department: string;
  staff_type: string;
  joining_date: string;
  qualification: string | null;
  email: string | null;
}

export interface Duty {
  id: string;
  title: string;
  details: string | null;
  duty_date: string;
  status: string;
}

export interface StaffDashboard {
  profile: StaffProfile;
  attendance_this_month: Record<string, number>;
  pending_leave: number;
  duties: Duty[];
  announcements: Announcement[];
}

export interface MyAttendance {
  month: string;
  summary: Record<string, number>;
  days: { day: string; status: string; check_in: string | null; check_out: string | null }[];
  note: string;
}

export interface LeaveInput {
  leave_type: string;
  starts_on: string;
  ends_on: string;
  reason: string;
}

export const staffApi = {
  dashboard: () => queryDef<StaffDashboard>("/staff/dashboard"),
  profile: () => queryDef<StaffProfile>("/staff/profile"),
  attendance: () => queryDef<MyAttendance>("/staff/attendance"),
  leave: () => queryDef<Leave[]>("/staff/leave"),
  duties: () => queryDef<Duty[]>("/staff/duties"),
  documents: () => queryDef<DocumentRecord[]>("/staff/documents"),

  requestLeave: (body: LeaveInput) => http.post<Leave>("/staff/leave", body),
  cancelLeave: (id: string) => http.post<{ ok: boolean }>(`/staff/leave/${id}/cancel`),
  completeDuty: (id: string) => http.post<{ ok: boolean }>(`/staff/duties/${id}/done`),
};
