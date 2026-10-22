import { Card, DataState, PageHeader } from "@/components/ui";
import { cn } from "@/lib/cn";
import type { ApiQueryState } from "@/lib/api/query";
import { WEEKDAYS } from "@/lib/format";
import type { TimetableData } from "@/services/shared";

export function TimetableGrid({ data, show }: { data: TimetableData; show: "teacher" | "section" }) {
  const days = [0, 1, 2, 3, 4, 5];
  const cell = (d: number, p: number) => data.entries.find((e) => e.day_of_week === d && e.period_no === p);
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[48rem] border-collapse text-xs">
        <caption className="sr-only">Weekly timetable</caption>
        <thead>
          <tr>
            <th scope="col" className="w-28 border-b border-line p-2 text-left font-medium text-muted">
              Period
            </th>
            {days.map((d) => (
              <th
                key={d}
                scope="col"
                className={cn("border-b border-line p-2 text-left font-semibold", d === data.today_day_of_week ? "text-brand" : "text-ink")}
              >
                {WEEKDAYS[d]}
                {d === data.today_day_of_week && <span className="ml-1 font-normal text-muted">(today)</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.periods.map((p) => (
            <tr key={p.period_no}>
              <th scope="row" className="border-b border-line p-2 text-left font-normal text-muted">
                <span className="block font-medium text-ink">{p.label}</span>
                {p.starts_at}–{p.ends_at}
              </th>
              {days.map((d) => {
                const e = cell(d, p.period_no);
                return (
                  <td
                    key={d}
                    className={cn("border-b border-l border-line p-2 align-top", d === data.today_day_of_week && "bg-brand-soft/60")}
                  >
                    {e ? (
                      <>
                        <span className="block font-medium text-ink">{e.subject}</span>
                        <span className="block text-muted">{show === "teacher" ? (e.teacher ?? "—") : `Class ${e.section}`}</span>
                        {e.room && <span className="block text-muted">{e.room}</span>}
                      </>
                    ) : (
                      <span className="text-muted">Free</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Full timetable page used by both students (shows teacher) and teachers (shows class). */
export function TimetableView({
  state,
  show,
  title,
  description,
}: {
  state: ApiQueryState<TimetableData>;
  show: "teacher" | "section";
  title: string;
  description: string;
}) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <Card padded={false}>
        <div className="p-2">
          <DataState state={state}>{(d) => <TimetableGrid data={d} show={show} />}</DataState>
        </div>
      </Card>
    </>
  );
}
