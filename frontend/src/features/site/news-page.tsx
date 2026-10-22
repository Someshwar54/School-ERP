import { PageHero, Section } from "@/features/site/section";
import { Badge } from "@/components/ui";
import { school } from "@/config/school";
import { formatDate } from "@/lib/format";

const tone = { news: "info", notice: "warning", event: "success" } as const;

export function NewsPage() {
  return (
    <>
      <PageHero
        eyebrow="Stay informed"
        title="News, notices and events"
        intro="Public updates from the school. Class-specific notices are shared in the ERP."
      />
      <Section>
        <ul className="divide-y divide-line rounded-brand border border-line">
          {school.content.news.map((n) => (
            <li key={n.title} className="flex flex-col gap-1 p-5 sm:flex-row sm:items-start sm:gap-6">
              <time dateTime={n.date} className="w-32 shrink-0 text-sm font-medium text-muted">
                {formatDate(n.date)}
              </time>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold">{n.title}</h2>
                  <Badge tone={tone[n.kind]}>{n.kind}</Badge>
                </div>
                <p className="mt-1 text-sm text-muted">{n.summary}</p>
              </div>
            </li>
          ))}
        </ul>
      </Section>
    </>
  );
}
