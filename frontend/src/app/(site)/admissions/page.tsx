import type { Metadata } from "next";
import { AdmissionsPage } from "@/features/site/admissions-page";

export const metadata: Metadata = { title: "Admissions" };

export default function Page() {
  return <AdmissionsPage />;
}
