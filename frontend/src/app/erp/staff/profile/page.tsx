import type { Metadata } from "next";
import { StaffProfilePage } from "@/features/staff/profile-page";

export const metadata: Metadata = { title: "Profile & Settings" };

export default function Page() {
  return <StaffProfilePage />;
}
