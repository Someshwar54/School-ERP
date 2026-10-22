import type { Metadata } from "next";
import { TeacherTimetablePage } from "@/features/teacher/timetable-page";

export const metadata: Metadata = { title: "Timetable" };

export default function Page() {
  return <TeacherTimetablePage />;
}
