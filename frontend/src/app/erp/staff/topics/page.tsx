import type { Metadata } from "next";
import { TeacherTopicsPage } from "@/features/teacher/topics-page";

export const metadata: Metadata = { title: "Lesson Progression" };

export default function Page() {
  return <TeacherTopicsPage />;
}
