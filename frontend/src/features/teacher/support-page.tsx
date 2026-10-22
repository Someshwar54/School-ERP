"use client";

import { useCallback, useState } from "react";
import { AssignmentPicker } from "@/features/teacher/assignment-picker";
import { MessagesView } from "@/features/common/messages-view";
import { Badge, Card, DataState, EmptyState, PageHeader } from "@/components/ui";
import { titleCase } from "@/lib/format";
import { useApiQuery } from "@/lib/api/query";
import { teacherApi, type Assignment } from "@/services/teacher";

export function TeacherSupportPage() {
  const [a, setA] = useState<Assignment | null>(null);
  const onChange = useCallback((x: Assignment) => setA(x), []);
  const fb = useApiQuery(a ? teacherApi.topicFeedback(a) : null);
  return (
    <>
      <PageHeader
        title="Student support and topic feedback"
        description="Students' self-reported understanding of topics, to help you plan revision and support. Not an assessment."
      />
      <div className="space-y-5">
        <AssignmentPicker value={a} onChange={onChange} />
        {a && (
          <Card title={`Topic feedback · Class ${a.section} · ${a.subject}`}>
            <DataState state={fb}>
              {(rows) =>
                rows.length === 0 ? (
                  <EmptyState title="No topic feedback yet" />
                ) : (
                  <ul className="space-y-4">
                    {rows.map((r) => (
                      <li key={r.topic_id} className="rounded-brand border border-line p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="font-medium">
                            {r.title} <Badge tone="neutral">{titleCase(r.status)}</Badge>
                          </p>
                          <p className="text-sm text-muted">
                            Average understanding <strong className="text-ink">{r.average_understanding.toFixed(1)}</strong> / 5 ·{" "}
                            {r.responses} responses
                          </p>
                        </div>
                        {r.needs_support.length > 0 && (
                          <p className="mt-2 text-sm">
                            <span className="font-medium text-amber-800">May need support:</span> {r.needs_support.join(", ")}
                          </p>
                        )}
                        {r.comments.length > 0 && (
                          <ul className="mt-2 space-y-1 text-sm text-muted">
                            {r.comments.map((c, i) => (
                              <li key={i}>
                                “{c.comment}” — {c.student ?? "Name withheld"} ({c.understanding}/5)
                              </li>
                            ))}
                          </ul>
                        )}
                      </li>
                    ))}
                  </ul>
                )
              }
            </DataState>
          </Card>
        )}
        <MessagesView audience="teacher" />
      </div>
    </>
  );
}
