import type { Metadata } from "next";
import { RecoveryPage } from "@/features/auth/recovery-page";

export const metadata: Metadata = { title: "Account recovery" };

export default function Page() {
  return <RecoveryPage />;
}
