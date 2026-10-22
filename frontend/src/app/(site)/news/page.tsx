import type { Metadata } from "next";
import { NewsPage } from "@/features/site/news-page";

export const metadata: Metadata = { title: "News & Events" };

export default function Page() {
  return <NewsPage />;
}
