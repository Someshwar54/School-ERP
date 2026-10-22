import type { Metadata } from "next";
import { school } from "@/config/school";
import { PortalEntryPage } from "@/features/auth/portal-entry-page";

export const metadata: Metadata = { title: school.terminology.portal };

export default function Page() {
  return <PortalEntryPage />;
}
