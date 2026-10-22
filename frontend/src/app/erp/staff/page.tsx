import type { Metadata } from "next";
import { StaffHomePage } from "@/features/staff/home-page";

export const metadata: Metadata = { title: "Dashboard" };

export default function Page() {
  return <StaffHomePage />;
}
