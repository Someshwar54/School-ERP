import type { Metadata } from "next";
import { ClassTeacherPage } from "@/features/teacher/class-page";

export const metadata: Metadata = { title: "My Class" };

export default function Page() {
  return <ClassTeacherPage />;
}
