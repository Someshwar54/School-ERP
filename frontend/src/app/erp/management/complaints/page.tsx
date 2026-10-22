import type { Metadata } from "next";
import { ManagementComplaintsPage } from "@/features/management/complaints-page";

export const metadata: Metadata = { title: "Complaints & Feedback" };

export default function Page() {
  return <ManagementComplaintsPage />;
}
