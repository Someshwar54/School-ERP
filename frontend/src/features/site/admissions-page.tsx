import { PageHero, Section } from "@/features/site/section";
import { ButtonLink } from "@/components/ui";
import { school } from "@/config/school";

export function AdmissionsPage() {
  const { admissions } = school.content;
  return (
    <>
      <PageHero eyebrow="Admissions" title="Joining our school" intro={admissions.intro} />
      <Section title="How admission works">
        <ol className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {admissions.steps.map((s, i) => (
            <li key={s.title} className="rounded-brand border border-line p-5">
              <span className="inline-flex size-8 items-center justify-center rounded-full bg-brand text-sm font-semibold text-brand-contrast">
                {i + 1}
              </span>
              <h3 className="mt-3 font-semibold">{s.title}</h3>
              <p className="mt-1 text-sm text-muted">{s.text}</p>
            </li>
          ))}
        </ol>
      </Section>
      <Section className="pt-0">
        <div className="grid gap-8 lg:grid-cols-2">
          <div className="rounded-brand bg-surface p-6">
            <h2 className="font-display text-xl font-semibold">Key dates</h2>
            <dl className="mt-4 divide-y divide-line">
              {admissions.dates.map((d) => (
                <div key={d.label} className="flex justify-between gap-4 py-2.5 text-sm">
                  <dt className="text-muted">{d.label}</dt>
                  <dd className="font-medium">{d.value}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="rounded-brand bg-surface p-6">
            <h2 className="font-display text-xl font-semibold">Documents required</h2>
            <ul className="mt-4 list-disc space-y-1.5 pl-5 text-sm text-muted">
              {admissions.documents.map((d) => (
                <li key={d}>{d}</li>
              ))}
            </ul>
            <p className="mt-4 text-sm text-muted">{admissions.feeNote}</p>
          </div>
        </div>
        <div className="mt-8">
          <ButtonLink href="/contact" size="lg">
            Send an admission enquiry
          </ButtonLink>
        </div>
      </Section>
    </>
  );
}
