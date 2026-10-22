import type { Metadata } from "next";
import { StaffAttendancePage } from "@/features/staff/my-attendance-page";

export const metadata: Metadata = { title: "My Attendance" };

export default function Page() {
  return <StaffAttendancePage />;
}
