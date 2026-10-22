import type { Metadata } from "next";
import { StaffDocumentsPage } from "@/features/staff/documents-page";

export const metadata: Metadata = { title: "Documents" };

export default function Page() {
  return <StaffDocumentsPage />;
}
