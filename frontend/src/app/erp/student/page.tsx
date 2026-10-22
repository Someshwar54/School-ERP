import type { Metadata } from "next";
import { StudentDashboardPage } from "@/features/student/dashboard-page";

export const metadata: Metadata = { title: "Dashboard" };

export default function Page() {
  return <StudentDashboardPage />;
}
