import { PageHero, Section } from "@/features/site/section";
import { school } from "@/config/school";

function initials(name: string) {
  return name
    .replace(/^Dr\.\s*/, "")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("");
}

export function FacultyPage() {
  return (
    <>
      <PageHero
        eyebrow="Our people"
        title="Faculty and leadership"
        intro="Our teachers bring subject expertise and care to every classroom. Only information approved for publication is shown here."
      />
      <Section>
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {school.content.faculty.map((f) => (
            <li key={f.name} className="rounded-brand border border-line p-5">
              <span
                aria-hidden
                className="inline-flex size-12 items-center justify-center rounded-full bg-brand-soft font-semibold text-brand"
              >
                {initials(f.name)}
              </span>
              <h2 className="mt-3 font-semibold">{f.name}</h2>
              <p className="text-sm text-accent-strong">{f.role}</p>
              <p className="mt-1 text-sm text-muted">
                {f.department} · {f.qualification}
              </p>
            </li>
          ))}
        </ul>
      </Section>
    </>
  );
}
