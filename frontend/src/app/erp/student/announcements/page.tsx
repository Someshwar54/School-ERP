import type { Metadata } from "next";
import { AnnouncementsView } from "@/features/common/announcements";

export const metadata: Metadata = { title: "Announcements" };

export default function Page() {
  return <AnnouncementsView />;
}
