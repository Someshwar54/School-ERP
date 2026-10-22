import { PageHero, Section } from "@/features/site/section";
import { school } from "@/config/school";

export function AcademicsPage() {
  const { academics } = school.content;
  return (
    <>
      <PageHero eyebrow="Academics" title="Curriculum and learning" intro={academics.intro} />
      <Section title="Stages of learning">
        <div className="grid gap-5 md:grid-cols-2">
          {academics.stages.map((s) => (
            <article key={s.name} className="rounded-brand border border-line p-6">
              <p className="text-sm font-semibold text-accent-strong">{s.grades}</p>
              <h3 className="mt-1 font-display text-xl font-semibold">{s.name}</h3>
              <p className="mt-2 text-muted">{s.focus}</p>
            </article>
          ))}
        </div>
      </Section>
      <Section title="Subjects offered">
        <ul className="flex flex-wrap gap-2">
          {academics.subjects.map((s) => (
            <li key={s} className="rounded-full bg-brand-soft px-4 py-1.5 text-sm font-medium text-brand">
              {s}
            </li>
          ))}
        </ul>
      </Section>
      <Section title="Assessment and reporting">
        <p className="max-w-3xl leading-relaxed text-muted">{academics.assessment}</p>
      </Section>
    </>
  );
}
