import type { Metadata } from "next";
import { StudentFeedbackPage } from "@/features/student/feedback-page";

export const metadata: Metadata = { title: "Feedback" };

export default function Page() {
  return <StudentFeedbackPage />;
}
