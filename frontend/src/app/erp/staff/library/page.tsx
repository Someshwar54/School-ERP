import type { Metadata } from "next";
import { PlannedModule } from "@/features/common/planned-module";

export const metadata: Metadata = { title: "Library" };

export default function Page() {
  return (
    <PlannedModule
      title="Library"
      items={["Catalogue and accession register", "Issue and return with due dates", "Overdue reminders (requires notification service)"]}
    />
  );
}
