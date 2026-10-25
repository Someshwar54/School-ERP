import { ArrowRight, Briefcase, CalendarDays, GraduationCap, Landmark } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { ButtonLink } from "@/components/ui";
import { school } from "@/config/school";
import { iconMap } from "@/features/site/icons";
import { Section } from "@/features/site/section";
import { formatDate } from "@/lib/format";

const signIn = [
  { href: "/erp/login/student", icon: GraduationCap, title: "Students", text: "Attendance, results, timetable and fees." },
  { href: "/erp/login/staff", icon: Briefcase, title: "Staff", text: "Registers, marks, leave and duties." },
  { href: "/erp/login/director", icon: Landmark, title: "Management", text: "School-wide insight and approvals." },
];

export function HomePage() {
  const { hero, stats, highlights, about, news } = school.content;
  return (
    <>
      <section className="relative overflow-hidden bg-night text-white">
        <div aria-hidden className="absolute -left-40 -top-40 size-[34rem] rounded-full bg-brand/35 blur-3xl" />
        <div aria-hidden className="absolute -bottom-48 right-0 size-[30rem] rounded-full bg-brand/20 blur-3xl" />
        <Image
          src={school.logo.src}
          alt=""
          width={480}
          height={480}
          aria-hidden
          className="pointer-events-none absolute -right-20 top-1/2 hidden size-[30rem] -translate-y-1/2 opacity-[0.07] lg:block"
        />
        <div className="relative mx-auto grid max-w-7xl gap-12 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-[1.25fr_1fr] lg:items-center">
          <div>
            <p className="inline-flex rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-sm font-semibold text-white">
              {hero.eyebrow}
            </p>
            <h1 className="mt-6 font-display text-4xl font-extrabold leading-[1.1] sm:text-5xl lg:text-6xl">{hero.title}</h1>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-white/75">{hero.subtitle}</p>
            <div className="mt-9 flex flex-wrap gap-3">
              <ButtonLink href="/admissions" size="lg">
                Admissions <ArrowRight className="size-4" aria-hidden />
              </ButtonLink>
              <ButtonLink href="/about" size="lg" variant="outline-inverse">
                About the school
              </ButtonLink>
            </div>
          </div>
          <dl className="grid grid-cols-2 gap-4">
            {stats.map((s) => (
              <div key={s.label} className="rounded-2xl border border-white/10 bg-white/[0.07] p-6 backdrop-blur-sm">
                <dd className="font-display text-4xl font-extrabold text-white">{s.value}</dd>
                <dt className="mt-1 text-sm font-medium text-white/70">{s.label}</dt>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <Section eyebrow="Why families choose us" title="Everything a growing learner needs" intro={about.vision}>
        <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {highlights.map((h) => {
            const Icon = iconMap[h.icon];
            return (
              <li
                key={h.title}
                className="group rounded-2xl border border-line bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:border-brand/40 hover:shadow-xl"
              >
                <span className="inline-flex size-14 items-center justify-center rounded-full bg-brand text-brand-contrast shadow-md">
                  <Icon className="size-7" aria-hidden />
                </span>
                <h3 className="mt-6 text-lg font-bold text-ink">{h.title}</h3>
                <p className="mt-2 leading-relaxed text-muted">{h.text}</p>
              </li>
            );
          })}
        </ul>
      </Section>

      <section className="bg-surface">
        <Section
          eyebrow={school.terminology.portal}
          title="One sign-in for the whole school"
          intro="Choose your account type to open your workspace."
        >
          <ul className="grid gap-6 md:grid-cols-3">
            {signIn.map(({ href, icon: Icon, title, text }) => (
              <li key={href}>
                <Link
                  href={href}
                  className="group flex h-full items-center gap-5 rounded-2xl border border-line bg-white p-6 shadow-sm transition hover:border-brand hover:shadow-lg"
                >
                  <span className="inline-flex size-14 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand transition group-hover:bg-brand group-hover:text-brand-contrast">
                    <Icon className="size-7" aria-hidden />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-lg font-bold text-ink">{title}</span>
                    <span className="mt-0.5 block text-sm text-muted">{text}</span>
                  </span>
                  <ArrowRight className="size-5 shrink-0 text-brand transition group-hover:translate-x-1" aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        </Section>
      </section>

      <section className="bg-brand text-brand-contrast">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-14 sm:px-6 lg:grid-cols-[2fr_1fr] lg:items-center">
          <blockquote>
            <p className="font-display text-2xl font-bold leading-relaxed sm:text-3xl">“{about.principalMessage.message}”</p>
            <footer className="mt-5 text-base font-medium text-white/85">
              {about.principalMessage.name}, {about.principalMessage.role}
            </footer>
          </blockquote>
          <div className="space-y-4 lg:justify-self-end">
            <p className="text-base text-white/90">Students, staff and management sign in to the school ERP.</p>
            <ButtonLink href="/erp" variant="inverse" size="lg">
              Go to {school.terminology.portal}
            </ButtonLink>
          </div>
        </div>
      </section>

      <Section eyebrow="Stay informed" title="Latest news and notices">
        <ul className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {news.slice(0, 4).map((n) => (
            <li
              key={n.title}
              className="flex flex-col rounded-2xl border border-line border-t-4 border-t-brand bg-white p-6 shadow-sm transition hover:shadow-lg"
            >
              <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-brand">
                <CalendarDays className="size-3.5" aria-hidden /> {formatDate(n.date)}
              </p>
              <h3 className="mt-3 text-lg font-bold leading-snug text-ink">{n.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{n.summary}</p>
            </li>
          ))}
        </ul>
        <Link href="/news" className="mt-8 inline-flex items-center gap-1 font-bold text-brand hover:underline">
          All news and events <ArrowRight className="size-4" aria-hidden />
        </Link>
      </Section>
    </>
  );
}
