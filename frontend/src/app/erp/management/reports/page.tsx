import type { Metadata } from "next";
import { ManagementReportsPage } from "@/features/management/reports-page";

export const metadata: Metadata = { title: "Reports & Analytics" };

export default function Page() {
  return <ManagementReportsPage />;
}
