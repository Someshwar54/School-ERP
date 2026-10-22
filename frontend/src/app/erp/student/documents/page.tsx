import type { Metadata } from "next";
import { StudentDocumentsPage } from "@/features/student/documents-page";

export const metadata: Metadata = { title: "Documents & Report Cards" };

export default function Page() {
  return <StudentDocumentsPage />;
}
