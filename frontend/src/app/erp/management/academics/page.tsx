import type { Metadata } from "next";
import { ManagementAcademicsPage } from "@/features/management/academics-page";

export const metadata: Metadata = { title: "Academic Performance" };

export default function Page() {
  return <ManagementAcademicsPage />;
}
