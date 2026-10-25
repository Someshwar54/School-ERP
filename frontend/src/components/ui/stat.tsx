/** KPI tile: label, value and optional hint. */
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Stat({ label, value, hint, tone }: { label: string; value: ReactNode; hint?: ReactNode; tone?: "warning" | "good" }) {
  return (
    <div className="rounded-2xl border border-line border-l-4 border-l-brand bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-muted">{label}</p>
      <p
        className={cn(
          "mt-1 text-2xl font-extrabold",
          tone === "warning" ? "text-amber-700" : tone === "good" ? "text-emerald-700" : "text-ink",
        )}
      >
        {value}
      </p>
      {hint && <p className="mt-0.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}
