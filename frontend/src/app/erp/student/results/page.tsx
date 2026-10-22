import type { Metadata } from "next";
import { StudentResultsPage } from "@/features/student/results-page";

export const metadata: Metadata = { title: "Examinations & Results" };

export default function Page() {
  return <StudentResultsPage />;
}
