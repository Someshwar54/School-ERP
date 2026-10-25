import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/** Hero band for inner pages: dark, with a red accent rule. */
export function PageHero({ eyebrow, title, intro }: { eyebrow?: string; title: string; intro?: string }) {
  return (
    <div className="relative overflow-hidden bg-night text-white">
      <div aria-hidden className="absolute -right-32 -top-32 size-96 rounded-full bg-brand/30 blur-3xl" />
      <div className="relative mx-auto max-w-7xl px-4 py-14 sm:px-6 sm:py-20">
        {eyebrow && <p className="text-sm font-bold uppercase tracking-widest text-brand-light">{eyebrow}</p>}
        <h1 className="mt-3 max-w-3xl font-display text-4xl font-extrabold leading-tight sm:text-5xl">{title}</h1>
        <span aria-hidden className="mt-5 block h-1 w-16 rounded-full bg-brand" />
        {intro && <p className="mt-5 max-w-3xl text-lg leading-relaxed text-white/75">{intro}</p>}
      </div>
    </div>
  );
}

export function Section({
  title,
  intro,
  eyebrow,
  children,
  className,
}: {
  title?: string;
  intro?: string;
  eyebrow?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("mx-auto max-w-7xl px-4 py-14 sm:px-6 sm:py-16", className)}>
      {eyebrow && <p className="text-sm font-bold uppercase tracking-widest text-brand">{eyebrow}</p>}
      {title && <h2 className="mt-1 font-display text-3xl font-extrabold text-ink sm:text-4xl">{title}</h2>}
      {intro && <p className="mt-3 max-w-3xl text-lg text-muted">{intro}</p>}
      <div className={title || intro ? "mt-10" : undefined}>{children}</div>
    </section>
  );
}
