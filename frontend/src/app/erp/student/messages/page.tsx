import type { Metadata } from "next";
import { MessagesView } from "@/features/common/messages-view";

export const metadata: Metadata = { title: "Teacher Communication" };

export default function Page() {
  return <MessagesView audience="student" />;
}
