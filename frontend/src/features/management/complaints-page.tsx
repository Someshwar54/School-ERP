"use client";

import { useState } from "react";
import { ComplaintList } from "@/features/common/complaint-list";
import { useSession } from "@/features/auth/use-session";
import { Alert, Card, DataState, PageHeader, Select, Stat, Table, Td } from "@/components/ui";
import { titleCase } from "@/lib/format";
import { useApiMutation, useApiQuery } from "@/lib/api/query";
import { managementApi } from "@/services/management";

export function ManagementComplaintsPage() {
  const { can } = useSession();
  const [status, setStatus] = useState("");
  const complaints = useApiQuery(
    can("complaints.view_summary") || can("complaints.view_all") || can("complaints.view_confidential")
      ? managementApi.complaints(status)
      : null,
  );
  const updateComplaint = useApiMutation(managementApi.updateComplaint, { invalidates: ["/management/complaints"] });
  const feedback = useApiQuery(can("feedback.view_aggregate") ? managementApi.feedback() : null);
  return (
    <>
      <PageHeader
        title="Complaints and feedback"
        description="What you see depends on your role: summary counts, non-confidential cases, or confidential cases."
      />
      <div className="space-y-6">
        {complaints.data || complaints.error || complaints.loading ? (
          <DataState state={complaints}>
            {(d) => (
              <>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {["open", "in_review", "resolved", "closed"].map((s) => (
                    <Stat key={s} label={titleCase(s)} value={d.summary.by_status[s] ?? 0} />
                  ))}
                </div>
                <p className="text-sm text-muted">
                  Confidential cases open: {d.summary.confidential_open}. By category:{" "}
                  {Object.entries(d.summary.by_category)
                    .map(([k, v]) => `${titleCase(k)} ${v}`)
                    .join(", ")}
                  .
                </p>
                {d.items === null ? (
                  <Alert tone="info">Your role can see summary figures only. Individual complaints are restricted.</Alert>
                ) : (
                  <Card
                    title="Complaints"
                    action={
                      <Select aria-label="Filter by status" className="w-40" value={status} onChange={(e) => setStatus(e.target.value)}>
                        <option value="">All statuses</option>
                        {["open", "in_review", "resolved", "closed"].map((s) => (
                          <option key={s} value={s}>
                            {titleCase(s)}
                          </option>
                        ))}
                      </Select>
                    }
                  >
                    {!d.can_view_confidential && (
                      <Alert tone="info" className="mb-4">
                        Confidential complaints are hidden for your role.
                      </Alert>
                    )}
                    <ComplaintList items={d.items} update={d.can_manage ? updateComplaint : undefined} />
                  </Card>
                )}
              </>
            )}
          </DataState>
        ) : null}
        {can("feedback.view_aggregate") && (
          <Card title="Feedback summary" padded={false}>
            <DataState state={feedback}>
              {(f) => (
                <>
                  <Table headers={["Category", "Responses", "Average rating"]} caption="Feedback by category">
                    {f.categories.map((c) => (
                      <tr key={c.category}>
                        <Td className="font-medium">{titleCase(c.category)}</Td>
                        <Td>{c.responses}</Td>
                        <Td>
                          {c.suppressed ? (
                            <span className="text-xs text-muted">Hidden (fewer than {f.minimum_group_size})</span>
                          ) : (
                            `${c.average_rating} / 5`
                          )}
                        </Td>
                      </tr>
                    ))}
                  </Table>
                  <div className="p-4">
                    <p className="text-xs text-muted">{f.note}</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                      {f.recent_comments.slice(0, 8).map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </DataState>
          </Card>
        )}
      </div>
    </>
  );
}
