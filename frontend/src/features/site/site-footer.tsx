import { Mail, MapPin, Phone } from "lucide-react";
import Link from "next/link";
import { school } from "@/config/school";
import { siteNav } from "./nav";

export function SiteFooter() {
  return (
    <footer className="mt-20 border-t-4 border-brand bg-night text-white/90">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 md:grid-cols-3">
        <div>
          <p className="font-display text-xl font-extrabold text-white">{school.name}</p>
          <p className="mt-2 text-sm text-white/75">{school.affiliation}</p>
          <p className="mt-1 text-sm text-white/75">Established {school.established}</p>
        </div>
        <div>
          <p className="text-sm font-bold uppercase tracking-wider text-brand-light">Explore</p>
          <ul className="mt-3 grid grid-cols-2 gap-2 text-sm">
            {siteNav.map((n) => (
              <li key={n.href}>
                <Link href={n.href} className="text-white/80 hover:text-white hover:underline">
                  {n.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/erp" className="text-white/80 hover:text-white hover:underline">
                {school.terminology.portal}
              </Link>
            </li>
          </ul>
        </div>
        <address className="space-y-2 text-sm not-italic">
          <p className="text-sm font-bold uppercase tracking-wider text-brand-light">Contact</p>
          <p className="flex gap-2">
            <MapPin className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>{school.contact.addressLines.join(", ")}</span>
          </p>
          <p className="flex gap-2">
            <Phone className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>{school.contact.phone}</span>
          </p>
          <p className="flex gap-2">
            <Mail className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>{school.contact.email}</span>
          </p>
        </address>
      </div>
      <div className="border-t border-white/15">
        <p className="mx-auto max-w-7xl px-4 py-4 text-xs text-white/70 sm:px-6">
          © {school.name}. {school.isFictional && "This is a fictional demonstration school; all names and content are illustrative."}
        </p>
      </div>
    </footer>
  );
}
