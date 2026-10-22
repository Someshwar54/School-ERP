import type { Metadata } from "next";
import { FacilitiesPage } from "@/features/site/facilities-page";

export const metadata: Metadata = { title: "Facilities" };

export default function Page() {
  return <FacilitiesPage />;
}
