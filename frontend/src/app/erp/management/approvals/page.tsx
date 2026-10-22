import type { Metadata } from "next";
import { ApprovalsAuditPage } from "@/features/management/approvals-page";

export const metadata: Metadata = { title: "Approvals & Audit" };

export default function Page() {
  return <ApprovalsAuditPage />;
}
