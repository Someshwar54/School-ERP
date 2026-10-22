import type { Metadata } from "next";
import { StaffDutiesPage } from "@/features/staff/duties-page";

export const metadata: Metadata = { title: "Assigned Duties" };

export default function Page() {
  return <StaffDutiesPage />;
}
