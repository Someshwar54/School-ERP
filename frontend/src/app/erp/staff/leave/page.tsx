import type { Metadata } from "next";
import { StaffLeavePage } from "@/features/staff/leave-page";

export const metadata: Metadata = { title: "Leave Requests" };

export default function Page() {
  return <StaffLeavePage />;
}
