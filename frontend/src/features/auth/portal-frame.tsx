import { ArrowLeft } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import type { ReactNode } from "react";
import { school } from "@/config/school";

/** Frame for the ERP entry and sign-in pages: clearly separate from the public site, with a way back. */
export function PortalFrame({
  children,
  back = { href: "/", label: "Back to school website" },
}: {
  children: ReactNode;
  back?: { href: string; label: string };
}) {
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <header className="border-b-4 border-brand bg-night text-white">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-3 px-4">
          <Link href="/erp" className="flex min-w-0 items-center gap-2.5">
            <Image src={school.logo.src} alt="" width={36} height={36} className="size-9 shrink-0" />
            <span className="min-w-0 leading-tight">
              <span className="block truncate text-sm font-extrabold text-white">{school.name}</span>
              <span className="block text-xs text-white/70">{school.terminology.portal}</span>
            </span>
          </Link>
          <Link
            href={back.href}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-white/30 px-4 py-1.5 text-sm font-semibold text-white hover:bg-white hover:text-ink"
          >
            <ArrowLeft className="size-4" aria-hidden /> <span className="hidden sm:inline">{back.label}</span>
            <span className="sm:hidden">Back</span>
          </Link>
        </div>
      </header>
      <main id="main" className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:py-16">
        {children}
      </main>
    </div>
  );
}
