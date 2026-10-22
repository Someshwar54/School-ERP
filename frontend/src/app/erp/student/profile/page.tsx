import type { Metadata } from "next";
import { StudentProfilePage } from "@/features/student/profile-page";

export const metadata: Metadata = { title: "My Profile" };

export default function Page() {
  return <StudentProfilePage />;
}
