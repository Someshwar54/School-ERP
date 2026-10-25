import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { school } from "@/config/school";

/** Thin promotional strip above the header, driven by the school's hero eyebrow text. */
export function AnnouncementBar() {
  return (
    <div className="bg-night text-white">
      <p className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-3 gap-y-1 px-4 py-2 text-center text-sm sm:px-6">
        <span className="font-semibold">{school.content.hero.eyebrow}</span>
        <Link href="/admissions" className="inline-flex items-center gap-1 font-bold text-brand-light hover:text-white">
          Apply now <ArrowRight className="size-3.5" aria-hidden />
        </Link>
      </p>
    </div>
  );
}
