import type { Metadata } from "next";
import { HrView } from "@/features/common/hr-view";

export const metadata: Metadata = { title: "Payroll & HR" };

export default function Page() {
  return <HrView />;
}
