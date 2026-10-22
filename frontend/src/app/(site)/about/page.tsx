import type { Metadata } from "next";
import { AboutPage } from "@/features/site/about-page";

export const metadata: Metadata = { title: "About" };

export default function Page() {
  return <AboutPage />;
}
