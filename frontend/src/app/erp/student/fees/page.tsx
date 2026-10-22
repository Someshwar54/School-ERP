import type { Metadata } from "next";
import { StudentFeesPage } from "@/features/student/fees-page";

export const metadata: Metadata = { title: "Fees & Payments" };

export default function Page() {
  return <StudentFeesPage />;
}
