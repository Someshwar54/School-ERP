"use client";

import { AlertTriangle, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useSession } from "@/features/auth/use-session";
import { barTrace, ChartPanel, lineTrace } from "@/components/charts/chart";
import { Badge, Card, DataState, EmptyState, PageHeader, Stat } from "@/components/ui";
import { formatDate, formatDateTime, formatMoney, formatPercent } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { SEVERITY_TONE } from "@/domain/status";
import { managementApi } from "@/services/management";

export function ManagementOverviewPage() {
  const { me } = useSession();
  const router = useRouter();
  const allowed = me ? me.workspace.modules.includes("overview") : null;
  useEffect(() => {
    // Roles without the overview (e.g. technical administrator) go to their first permitted module.
    if (me && allowed === false) router.replace(me.workspace.home);
  }, [me, allowed, router]);
  const state = useApiQuery(allowed ? managementApi.overview() : null);
  return (
    <DataState state={state} loadingLabel="Loading the executive overview…">
      {(d) => {
        const k = d.kpis;
        const trendX = d.charts.attendance_trend.map((t) => formatDate(t.day, { day: "numeric", month: "short" }));
        return (
          <>
            <PageHeader
              title="Executive overview"
              description={
                <>
                  Figures as of {d.as_of ? formatDate(d.as_of) : "—"}. <Badge tone="warning">{d.data_label}</Badge>
                </>
              }
            />
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <Stat label="Enrolled students" value={k.enrolled_students} hint={`${k.active_staff} active staff`} />
              <Stat label="Student attendance" value={formatPercent(k.student_attendance_percent)} hint="Latest school day" />
              <Stat label="Staff attendance" value={formatPercent(k.staff_attendance_percent)} hint="Latest school day" />
              <Stat label="Average published score" value={formatPercent(k.average_score_percent)} />
              {d.finance && (
                <>
                  <Stat
                    label="Fees collected"
                    value={formatMoney(d.finance.collected)}
                    hint={d.finance.collection_rate_percent !== null ? `${d.finance.collection_rate_percent}% of billed` : undefined}
                  />
                  <Stat
                    label="Outstanding fees"
                    value={formatMoney(d.finance.outstanding)}
                    tone="warning"
                    hint={`${formatMoney(d.finance.overdue_amount)} overdue`}
                  />
                </>
              )}
              <Stat
                label="Pending approvals"
                value={k.pending_leave_requests + k.assessments_ready_to_publish}
                hint={`${k.pending_leave_requests} leave · ${k.assessments_ready_to_publish} results`}
              />
              <Stat
                label="Open complaints"
                value={k.open_complaints}
                hint={k.average_feedback_rating ? `Feedback avg ${k.average_feedback_rating}/5` : undefined}
              />
            </div>

            <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_24rem]">
              <Card title="Student attendance trend (last 30 school days)">
                <ChartPanel
                  label="Daily student attendance percentage"
                  data={[
                    lineTrace(
                      trendX,
                      d.charts.attendance_trend.map((t) => t.percent),
                      "Attendance",
                      "%",
                    ),
                  ]}
                  layout={{ yaxis: { range: [80, 100], ticksuffix: "%", gridcolor: "#eef0f3" } }}
                  headers={["Day", "Attendance"]}
                  rows={d.charts.attendance_trend.map((t) => [t.day, formatPercent(t.percent)])}
                />
              </Card>
              <Card title="Management action items">
                {d.action_items.length === 0 ? (
                  <EmptyState title="No action items" />
                ) : (
                  <ul className="space-y-3">
                    {d.action_items.map((a) => (
                      <li key={a.text}>
                        <Link href={a.href} className="group flex items-start gap-2 text-sm">
                          <AlertTriangle
                            className={`mt-0.5 size-4 shrink-0 ${a.severity === "high" ? "text-red-700" : a.severity === "medium" ? "text-amber-700" : "text-sky-700"}`}
                            aria-hidden
                          />
                          <span className="flex-1 group-hover:underline">{a.text}</span>
                          <Badge tone={SEVERITY_TONE[a.severity]}>{a.severity}</Badge>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <Card title="Average score by subject (published results)">
                <ChartPanel
                  label="Average score by subject"
                  data={[
                    barTrace(
                      d.charts.subject_performance.map((s) => s.subject),
                      d.charts.subject_performance.map((s) => s.average_percent),
                      "Average %",
                    ),
                  ]}
                  layout={{ yaxis: { range: [0, 100], ticksuffix: "%", gridcolor: "#eef0f3" } }}
                  headers={["Subject", "Average", "Marks counted"]}
                  rows={d.charts.subject_performance.map((s) => [s.subject, formatPercent(s.average_percent), s.marks])}
                />
              </Card>
              <Card title="Score distribution (published marks)">
                <ChartPanel
                  label="Distribution of published scores"
                  data={[
                    barTrace(
                      d.charts.score_distribution.map((b) => `${b.range}%`),
                      d.charts.score_distribution.map((b) => b.count),
                      "Marks",
                    ),
                  ]}
                  layout={{ bargap: 0.15 }}
                  headers={["Score range", "Count"]}
                  rows={d.charts.score_distribution.map((b) => [`${b.range}%`, b.count])}
                />
              </Card>
              {d.charts.fee_collection && (
                <Card title="Fee collection by month">
                  <ChartPanel
                    label="Fee collection by month"
                    data={[
                      barTrace(
                        d.charts.fee_collection.map((m) => formatDate(`${m.month}-01`, { month: "short", year: "2-digit" })),
                        d.charts.fee_collection.map((m) => Number(m.amount)),
                        "Collected",
                        { hovertemplate: "%{x}<br>Collected: ₹%{y:,.0f}<extra></extra>" },
                      ),
                    ]}
                    layout={{ yaxis: { tickprefix: "₹", tickformat: ",.0f", gridcolor: "#eef0f3" } }}
                    headers={["Month", "Collected"]}
                    rows={d.charts.fee_collection.map((m) => [m.month, formatMoney(m.amount)])}
                  />
                </Card>
              )}
              <Card title="Operational exceptions">
                <ChartPanel
                  label="Open operational exceptions"
                  data={[
                    barTrace(
                      d.charts.exceptions.map((e) => e.count),
                      d.charts.exceptions.map((e) => e.label),
                      "Count",
                      { orientation: "h", hovertemplate: "%{y}: %{x}<extra></extra>" },
                    ),
                  ]}
                  layout={{ margin: { l: 130, r: 16, t: 8, b: 40 }, xaxis: { gridcolor: "#eef0f3", dtick: 5 } }}
                  height={220}
                  headers={["Exception", "Count"]}
                  rows={d.charts.exceptions.map((e) => [e.label, e.count])}
                />
              </Card>
            </div>

            {d.recent_activity && (
              <Card
                title="Recent activity (audit log)"
                className="mt-6"
                action={
                  <Link href="/erp/management/approvals" className="inline-flex items-center gap-1 text-sm text-brand hover:underline">
                    Approvals & audit <ArrowRight className="size-4" aria-hidden />
                  </Link>
                }
              >
                <ul className="divide-y divide-line text-sm">
                  {d.recent_activity.map((a, i) => (
                    <li key={i} className="flex flex-wrap justify-between gap-2 py-2">
                      <span>
                        <code className="text-xs">{a.action}</code> · {a.actor ?? "System"}
                      </span>
                      <span className="text-muted">{formatDateTime(a.created_at)}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}
          </>
        );
      }}
    </DataState>
  );
}
