import { ArrowRight, CalendarDays } from "lucide-react";
import Link from "next/link";
import { iconMap } from "@/features/site/icons";
import { Section } from "@/features/site/section";
import { ButtonLink } from "@/components/ui";
import { school } from "@/config/school";
import { formatDate } from "@/lib/format";

export function HomePage() {
  const { hero, stats, highlights, about, news } = school.content;
  return (
    <>
      <section className="relative overflow-hidden border-b border-line bg-surface">
        <div aria-hidden className="absolute -right-24 -top-24 size-96 rounded-full bg-accent-soft" />
        <div aria-hidden className="absolute -bottom-32 right-48 size-72 rounded-full bg-brand-soft" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-16 sm:px-6 sm:py-24 lg:grid-cols-[1.3fr_1fr] lg:items-center">
          <div>
            <p className="inline-flex rounded-full bg-white px-3 py-1 text-sm font-medium text-accent-strong shadow-sm">{hero.eyebrow}</p>
            <h1 className="mt-5 font-display text-4xl font-semibold leading-tight text-ink sm:text-5xl">{hero.title}</h1>
            <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted">{hero.subtitle}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <ButtonLink href="/admissions" size="lg">
                Admissions <ArrowRight className="size-4" aria-hidden />
              </ButtonLink>
              <ButtonLink href="/about" size="lg" variant="secondary">
                About the school
              </ButtonLink>
            </div>
          </div>
          <dl className="grid grid-cols-2 gap-4">
            {stats.map((s) => (
              <div key={s.label} className="rounded-brand border border-line bg-white p-5 shadow-sm">
                <dt className="text-sm text-muted">{s.label}</dt>
                <dd className="mt-1 font-display text-3xl font-semibold text-brand">{s.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <Section title="Why families choose us" intro={about.vision}>
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {highlights.map((h) => {
            const Icon = iconMap[h.icon];
            return (
              <li key={h.title} className="rounded-brand border border-line p-5">
                <span className="inline-flex size-10 items-center justify-center rounded-brand bg-brand-soft text-brand">
                  <Icon className="size-5" aria-hidden />
                </span>
                <h3 className="mt-4 font-semibold text-ink">{h.title}</h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">{h.text}</p>
              </li>
            );
          })}
        </ul>
      </Section>

      <Section className="pt-0">
        <div className="grid gap-8 rounded-brand bg-brand px-6 py-10 text-brand-contrast sm:px-10 lg:grid-cols-[2fr_1fr] lg:items-center">
          <blockquote>
            <p className="font-display text-xl leading-relaxed sm:text-2xl">“{about.principalMessage.message}”</p>
            <footer className="mt-4 text-sm text-white/80">
              {about.principalMessage.name}, {about.principalMessage.role}
            </footer>
          </blockquote>
          <div className="space-y-3 lg:justify-self-end">
            <p className="text-sm text-white/85">Students, staff and management sign in to the school ERP.</p>
            <ButtonLink href="/erp" variant="accent" size="lg">
              Go to {school.terminology.portal}
            </ButtonLink>
          </div>
        </div>
      </Section>

      <Section title="Latest news and notices">
        <ul className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {news.slice(0, 4).map((n) => (
            <li key={n.title} className="flex flex-col rounded-brand border border-line p-5">
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-accent-strong">
                <CalendarDays className="size-3.5" aria-hidden /> {formatDate(n.date)}
              </p>
              <h3 className="mt-2 font-semibold text-ink">{n.title}</h3>
              <p className="mt-1 text-sm text-muted">{n.summary}</p>
            </li>
          ))}
        </ul>
        <Link href="/news" className="mt-6 inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline">
          All news and events <ArrowRight className="size-4" aria-hidden />
        </Link>
      </Section>
    </>
  );
}
