import { Landmark } from "lucide-react";
import type { Metadata } from "next";
import { LoginPage } from "@/features/auth/login-page";

export const metadata: Metadata = { title: "Director Login" };

export default function DirectorLoginPage() {
  return (
    <LoginPage
      portal="director"
      icon={Landmark}
      title="Director Login"
      description="For directors and school management. What you can see depends on your management role."
      note="Multi-factor authentication for management accounts is planned before production use."
    />
  );
}
