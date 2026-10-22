import type { Metadata } from "next";
import { StudentPerformancePage } from "@/features/student/performance-page";

export const metadata: Metadata = { title: "Academic Performance" };

export default function Page() {
  return <StudentPerformancePage />;
}
