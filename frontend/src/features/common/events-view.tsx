"use client";

import { CalendarDays, MapPin } from "lucide-react";
import { Badge, DataState, EmptyState, PageHeader } from "@/components/ui";
import { useApiQuery } from "@/lib/api/query";
import { formatDateTime } from "@/lib/format";
import { sharedApi } from "@/services/shared";

export function EventsView() {
  const state = useApiQuery(sharedApi.events());
  return (
    <>
      <PageHeader title="Events" description="Upcoming and recent school events." />
      <DataState state={state}>
        {(events) =>
          events.length === 0 ? (
            <EmptyState title="No events scheduled" />
          ) : (
            <ul className="grid gap-4 md:grid-cols-2">
              {events.map((e) => (
                <li key={e.id} className="rounded-brand border border-line bg-white p-4">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold">{e.title}</p>
                    <Badge tone={e.is_past ? "neutral" : "success"}>{e.is_past ? "Completed" : "Upcoming"}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-muted">{e.description}</p>
                  <p className="mt-2 flex items-center gap-1.5 text-xs text-muted">
                    <CalendarDays className="size-3.5" aria-hidden /> {formatDateTime(e.starts_at)}
                  </p>
                  <p className="mt-1 flex items-center gap-1.5 text-xs text-muted">
                    <MapPin className="size-3.5" aria-hidden /> {e.location}
                  </p>
                </li>
              ))}
            </ul>
          )
        }
      </DataState>
    </>
  );
}
