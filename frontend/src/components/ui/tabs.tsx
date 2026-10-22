"use client";

import { cn } from "@/lib/cn";

/** Simple accessible tab list. The parent owns which tab is active. */
export function Tabs<K extends string>({
  tabs,
  active,
  onChange,
  label,
}: {
  tabs: { key: K; label: string }[];
  active: K | null;
  onChange: (key: K) => void;
  label: string;
}) {
  return (
    <div role="tablist" aria-label={label} className="mb-5 flex flex-wrap gap-2">
      {tabs.map((t) => (
        <button
          key={t.key}
          role="tab"
          type="button"
          aria-selected={active === t.key}
          onClick={() => onChange(t.key)}
          className={cn(
            "rounded-brand border px-3 py-1.5 text-sm",
            active === t.key ? "border-brand bg-brand text-brand-contrast" : "border-line bg-white hover:bg-surface",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
