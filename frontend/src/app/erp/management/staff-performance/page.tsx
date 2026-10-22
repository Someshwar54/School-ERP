import type { Metadata } from "next";
import { StaffPerformancePage } from "@/features/management/staff-performance-page";

export const metadata: Metadata = { title: "Teacher & Staff Performance" };

export default function Page() {
  return <StaffPerformancePage />;
}
