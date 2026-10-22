import type { Metadata } from "next";
import { ManagementAttendancePage } from "@/features/management/attendance-page";

export const metadata: Metadata = { title: "Student & Staff Attendance" };

export default function Page() {
  return <ManagementAttendancePage />;
}
