import type { Metadata } from "next";
import { TeacherClassesPage } from "@/features/teacher/classes-page";

export const metadata: Metadata = { title: "Classes & Subjects" };

export default function Page() {
  return <TeacherClassesPage />;
}
