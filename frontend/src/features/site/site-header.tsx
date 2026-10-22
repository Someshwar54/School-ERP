"use client";

import { LogIn, Menu, X } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { buttonClasses } from "@/components/ui";
import { school } from "@/config/school";
import { cn } from "@/lib/cn";
import { siteNav } from "./nav";

export function SiteHeader() {
  const pathname = usePathname();
  // The menu is open only for the path it was opened on, so navigating closes it.
  const [openOn, setOpenOn] = useState<string | null>(null);
  const open = openOn === pathname;
  const setOpen = (next: boolean | ((o: boolean) => boolean)) =>
    setOpenOn((typeof next === "function" ? next(open) : next) ? pathname : null);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <Link href="/" className="flex min-w-0 items-center gap-2.5" aria-label={`${school.name} home`}>
          <Image src={school.logo.src} alt="" width={40} height={40} priority className="size-10 shrink-0" />
          <span className="min-w-0 leading-tight">
            <span className="block truncate font-display text-base font-semibold text-brand sm:text-lg">{school.name}</span>
            <span className="hidden truncate text-xs text-muted sm:block">{school.tagline}</span>
          </span>
        </Link>

        <nav aria-label="Main" className="ml-auto hidden xl:block">
          <ul className="flex items-center gap-1">
            {siteNav.map((item) => {
              const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "rounded-brand px-3 py-2 text-sm font-medium transition-colors",
                      active ? "bg-brand-soft text-brand" : "text-ink hover:bg-surface",
                    )}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <Link href="/erp" className={buttonClasses("accent", "md", "ml-auto shrink-0 xl:ml-2")} data-testid="erp-portal-button">
          <LogIn className="size-4" aria-hidden />
          <span>{school.terminology.portal}</span>
        </Link>

        <button
          type="button"
          className="rounded-brand p-2 text-ink hover:bg-surface xl:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((o) => !o)}
        >
          {open ? <X className="size-5" aria-hidden /> : <Menu className="size-5" aria-hidden />}
        </button>
      </div>

      {open && (
        <nav id="mobile-nav" aria-label="Mobile" className="border-t border-line bg-white xl:hidden">
          <ul className="mx-auto max-w-7xl space-y-1 px-4 py-3">
            {siteNav.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="block rounded-brand px-3 py-2 text-sm font-medium text-ink hover:bg-surface">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  );
}
