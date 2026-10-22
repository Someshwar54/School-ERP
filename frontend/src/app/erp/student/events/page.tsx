import type { Metadata } from "next";
import { EventsView } from "@/features/common/events-view";

export const metadata: Metadata = { title: "Events" };

export default function Page() {
  return <EventsView />;
}
