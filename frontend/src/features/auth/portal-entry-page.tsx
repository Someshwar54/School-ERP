import { Briefcase, ChevronRight, GraduationCap, Landmark } from "lucide-react";
import Link from "next/link";
import { PortalFrame } from "@/features/auth/portal-frame";
import { school } from "@/config/school";

const options = [
  {
    href: "/erp/login/student",
    icon: GraduationCap,
    title: "Student Login",
    text: "Attendance, results, timetable, fees, announcements and messages to your teachers.",
    testId: "portal-student",
  },
  {
    href: "/erp/login/staff",
    icon: Briefcase,
    title: "Staff Login",
    text: "For teachers and non-teaching staff. Your workspace matches your role and assignments.",
    testId: "portal-staff",
  },
  {
    href: "/erp/login/director",
    icon: Landmark,
    title: "Director Login",
    text: "For directors and school management. Access depends on your management role.",
    testId: "portal-director",
  },
];

export function PortalEntryPage() {
  return (
    <PortalFrame>
      <div className="text-center">
        <h1 className="font-display text-3xl font-semibold text-ink">Welcome to the {school.terminology.portal}</h1>
        <p className="mt-2 text-muted">Choose how you would like to sign in.</p>
      </div>
      <ul className="mt-10 grid gap-5 md:grid-cols-3">
        {options.map(({ href, icon: Icon, title, text, testId }) => (
          <li key={href}>
            <Link
              href={href}
              data-testid={testId}
              className="group flex h-full flex-col rounded-brand border border-line bg-white p-6 shadow-sm transition hover:border-brand hover:shadow-md"
            >
              <span className="inline-flex size-12 items-center justify-center rounded-brand bg-brand-soft text-brand">
                <Icon className="size-6" aria-hidden />
              </span>
              <span className="mt-4 text-lg font-semibold text-ink">{title}</span>
              <span className="mt-1 flex-1 text-sm leading-relaxed text-muted">{text}</span>
              <span className="mt-5 inline-flex items-center gap-1 text-sm font-medium text-brand">
                Continue <ChevronRight className="size-4 transition group-hover:translate-x-0.5" aria-hidden />
              </span>
            </Link>
          </li>
        ))}
      </ul>
      <p className="mt-10 text-center text-xs text-muted">
        Use only the ID issued to you by the school. Do not share your password with anyone.
      </p>
    </PortalFrame>
  );
}
