import { GraduationCap } from "lucide-react";
import type { Metadata } from "next";
import { LoginPage } from "@/features/auth/login-page";

export const metadata: Metadata = { title: "Student Login" };

export default function StudentLoginPage() {
  return (
    <LoginPage
      portal="student"
      icon={GraduationCap}
      title="Student Login"
      description="Sign in with your Student ID to view your attendance, results, timetable and fees."
      note="First time signing in? Use the initial password given by the school office, then change it in Account Settings."
    />
  );
}
