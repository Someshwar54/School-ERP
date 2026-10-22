import { PageHero, Section } from "@/features/site/section";
import { school } from "@/config/school";

export function AboutPage() {
  const { about } = school.content;
  return (
    <>
      <PageHero eyebrow="About us" title={`About ${school.name}`} intro={about.intro} />
      <Section>
        <div className="grid gap-10 lg:grid-cols-2">
          <div>
            <h2 className="font-display text-2xl font-semibold">Our vision</h2>
            <p className="mt-3 text-lg leading-relaxed text-muted">{about.vision}</p>
            <h2 className="mt-10 font-display text-2xl font-semibold">Our mission</h2>
            <ul className="mt-3 space-y-3">
              {about.mission.map((m) => (
                <li key={m} className="flex gap-3 text-muted">
                  <span aria-hidden className="mt-2 size-2 shrink-0 rounded-full bg-accent" />
                  {m}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h2 className="font-display text-2xl font-semibold">Milestones</h2>
            <ol className="mt-4 space-y-4 border-l-2 border-brand-soft pl-6">
              {about.milestones.map((m) => (
                <li key={m.year} className="relative">
                  <span aria-hidden className="absolute -left-[1.95rem] top-1 size-3 rounded-full bg-brand" />
                  <p className="font-semibold text-brand">{m.year}</p>
                  <p className="text-muted">{m.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </Section>
      <Section title="A message from the Principal">
        <blockquote className="rounded-brand border-l-4 border-accent bg-surface p-6">
          <p className="text-lg leading-relaxed text-ink">“{about.principalMessage.message}”</p>
          <footer className="mt-3 text-sm text-muted">
            {about.principalMessage.name}, {about.principalMessage.role}
          </footer>
        </blockquote>
      </Section>
    </>
  );
}
