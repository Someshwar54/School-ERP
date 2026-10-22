import type { Metadata } from "next";
import { StudentTimetablePage } from "@/features/student/timetable-page";

export const metadata: Metadata = { title: "Timetable" };

export default function Page() {
  return <StudentTimetablePage />;
}
