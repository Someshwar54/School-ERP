import type { Metadata } from "next";
import { ManagementOverviewPage } from "@/features/management/overview-page";

export const metadata: Metadata = { title: "Executive Overview" };

export default function Page() {
  return <ManagementOverviewPage />;
}
