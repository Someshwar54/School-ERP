import type { Metadata } from "next";
import { TeacherComplaintsPage } from "@/features/teacher/complaints-page";

export const metadata: Metadata = { title: "Assigned Complaints" };

export default function Page() {
  return <TeacherComplaintsPage />;
}
