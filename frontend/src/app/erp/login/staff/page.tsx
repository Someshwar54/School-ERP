import { Briefcase } from "lucide-react";
import type { Metadata } from "next";
import { LoginPage } from "@/features/auth/login-page";

export const metadata: Metadata = { title: "Staff Login" };

export default function StaffLoginPage() {
  return (
    <LoginPage
      portal="staff"
      icon={Briefcase}
      title="Staff Login"
      description="For teachers and non-teaching staff. Your workspace is set by your role and assignments."
    />
  );
}
