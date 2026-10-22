import type { Metadata } from "next";
import { FacultyPage } from "@/features/site/faculty-page";

export const metadata: Metadata = { title: "Faculty" };

export default function Page() {
  return <FacultyPage />;
}
