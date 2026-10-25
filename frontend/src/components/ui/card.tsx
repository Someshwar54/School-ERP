/** Bordered surface with an optional header row (title + action). */
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Card({
  title,
  action,
  children,
  className,
  padded = true,
}: {
  title?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <section className={cn("rounded-2xl border border-line bg-white shadow-sm", className)}>
      {(title || action) && (
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-4 py-3">
          {title && <h2 className="text-sm font-bold text-ink">{title}</h2>}
          {action}
        </header>
      )}
      <div className={padded ? "p-4" : undefined}>{children}</div>
    </section>
  );
}
