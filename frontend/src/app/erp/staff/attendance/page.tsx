import type { Metadata } from "next";
import { TeacherAttendancePage } from "@/features/teacher/attendance-page";

export const metadata: Metadata = { title: "Student Attendance" };

export default function Page() {
  return <TeacherAttendancePage />;
}
