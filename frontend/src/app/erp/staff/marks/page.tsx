import type { Metadata } from "next";
import { TeacherMarksPage } from "@/features/teacher/marks-page";

export const metadata: Metadata = { title: "Assessments & Marks" };

export default function Page() {
  return <TeacherMarksPage />;
}
