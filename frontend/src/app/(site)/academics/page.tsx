import type { Metadata } from "next";
import { AcademicsPage } from "@/features/site/academics-page";

export const metadata: Metadata = { title: "Academics" };

export default function Page() {
  return <AcademicsPage />;
}
