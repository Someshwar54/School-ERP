import type { Metadata } from "next";
import { StudentComplaintsPage } from "@/features/student/complaints-page";

export const metadata: Metadata = { title: "Complaints & Requests" };

export default function Page() {
  return <StudentComplaintsPage />;
}
