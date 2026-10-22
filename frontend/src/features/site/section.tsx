import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function PageHero({ eyebrow, title, intro }: { eyebrow?: string; title: string; intro?: string }) {
  return (
    <div className="border-b border-line bg-surface">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 sm:py-16">
        {eyebrow && <p className="text-sm font-semibold uppercase tracking-wider text-accent-strong">{eyebrow}</p>}
        <h1 className="mt-2 max-w-3xl font-display text-3xl font-semibold text-ink sm:text-4xl">{title}</h1>
        {intro && <p className="mt-4 max-w-3xl text-base leading-relaxed text-muted">{intro}</p>}
      </div>
    </div>
  );
}

export function Section({
  title,
  intro,
  children,
  className,
}: {
  title?: string;
  intro?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("mx-auto max-w-7xl px-4 py-12 sm:px-6", className)}>
      {title && <h2 className="font-display text-2xl font-semibold text-ink">{title}</h2>}
      {intro && <p className="mt-2 max-w-3xl text-muted">{intro}</p>}
      <div className={title || intro ? "mt-8" : undefined}>{children}</div>
    </section>
  );
}
