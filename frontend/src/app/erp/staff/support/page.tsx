import type { Metadata } from "next";
import { TeacherSupportPage } from "@/features/teacher/support-page";

export const metadata: Metadata = { title: "Student Support" };

export default function Page() {
  return <TeacherSupportPage />;
}
