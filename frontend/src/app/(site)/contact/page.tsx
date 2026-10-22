import type { Metadata } from "next";
import { ContactPage } from "@/features/site/contact-page";

export const metadata: Metadata = { title: "Contact" };

export default function Page() {
  return <ContactPage />;
}
