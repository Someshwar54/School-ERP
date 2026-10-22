import type { Metadata } from "next";
import { PlannedModule } from "@/features/common/planned-module";

export const metadata: Metadata = { title: "Transport" };

export default function Page() {
  return (
    <PlannedModule
      title="Transport"
      items={[
        "Routes, stops and vehicle assignments",
        "Student route allocation linked to transport fees",
        "Live GPS tracking (requires an external provider)",
      ]}
    />
  );
}
