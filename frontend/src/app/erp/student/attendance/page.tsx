import type { Metadata } from "next";
import { StudentAttendancePage } from "@/features/student/attendance-page";

export const metadata: Metadata = { title: "Attendance" };

export default function Page() {
  return <StudentAttendancePage />;
}
