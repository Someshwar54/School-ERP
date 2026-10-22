import { Construction } from "lucide-react";
import { PageHeader } from "@/components/ui";

/** Honest placeholder for modules whose permissions exist but whose workflows are not built yet. */
export function PlannedModule({ title, items }: { title: string; items: string[] }) {
  return (
    <>
      <PageHeader title={title} />
      <div className="rounded-brand border border-dashed border-line bg-white p-8">
        <Construction className="size-8 text-accent" aria-hidden />
        <p className="mt-3 font-semibold">Planned module — not connected yet</p>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Your account has permission for this module, but its workflows are not implemented in this prototype. No data is stored or
          processed here.
        </p>
        <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-muted">
          {items.map((i) => (
            <li key={i}>{i}</li>
          ))}
        </ul>
      </div>
    </>
  );
}
