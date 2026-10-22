import type { Metadata } from "next";
import { SchoolConfigPage } from "@/features/management/config-page";

export const metadata: Metadata = { title: "School Configuration" };

export default function Page() {
  return <SchoolConfigPage />;
}
