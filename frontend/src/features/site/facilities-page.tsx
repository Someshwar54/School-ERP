import { iconMap } from "@/features/site/icons";
import { PageHero, Section } from "@/features/site/section";
import { school } from "@/config/school";

export function FacilitiesPage() {
  return (
    <>
      <PageHero eyebrow="Campus" title="Facilities" intro="Spaces designed for learning, play and wellbeing." />
      <Section>
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {school.content.facilities.map((f) => {
            const Icon = iconMap[f.icon];
            return (
              <li key={f.title} className="rounded-brand border border-line p-5">
                <span className="inline-flex size-10 items-center justify-center rounded-brand bg-accent-soft text-accent-strong">
                  <Icon className="size-5" aria-hidden />
                </span>
                <h2 className="mt-4 font-semibold">{f.title}</h2>
                <p className="mt-1 text-sm text-muted">{f.text}</p>
              </li>
            );
          })}
        </ul>
      </Section>
    </>
  );
}
