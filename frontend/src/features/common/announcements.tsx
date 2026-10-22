"use client";

import { Pin } from "lucide-react";
import { useState } from "react";
import { Badge, Card, DataState, EmptyState, PageHeader, Pager } from "@/components/ui";
import { useApiQuery } from "@/lib/api/query";
import { formatDateTime } from "@/lib/format";
import { sharedApi, type Announcement } from "@/services/shared";

export function AnnouncementList({ items }: { items: Announcement[] }) {
  if (!items.length) return <EmptyState title="No announcements" text="New notices from the school will appear here." />;
  return (
    <ul className="divide-y divide-line">
      {items.map((a) => (
        <li key={a.id} className="py-3 first:pt-0 last:pb-0">
          <div className="flex flex-wrap items-center gap-2">
            {a.is_pinned && <Pin className="size-3.5 text-accent" aria-label="Pinned" />}
            <p className="font-medium">{a.title}</p>
            {a.section_specific && <Badge tone="info">Your class</Badge>}
          </div>
          <p className="mt-0.5 text-sm text-muted">{a.body}</p>
          <p className="mt-1 text-xs text-muted">{formatDateTime(a.published_at)}</p>
        </li>
      ))}
    </ul>
  );
}

export function AnnouncementsView() {
  const [page, setPage] = useState(1);
  const state = useApiQuery(sharedApi.announcements(page));
  return (
    <>
      <PageHeader title="Announcements" description="Notices published for your account type and class." />
      <Card>
        <DataState state={state}>
          {(d) => (
            <>
              <AnnouncementList items={d.items} />
              {d.total > d.page_size && <Pager page={d.page} pageSize={d.page_size} total={d.total} onPage={setPage} />}
            </>
          )}
        </DataState>
      </Card>
    </>
  );
}
