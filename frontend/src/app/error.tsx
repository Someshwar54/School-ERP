"use client";

import { useEffect } from "react";
import { Button, ButtonLink } from "@/components/ui";

/** Route-level error boundary: shown when a page throws while rendering. */
export default function RouteError({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    // Hook point for an error-tracking service.
    console.error("route_error", error);
  }, [error]);
  return (
    <main id="main" className="mx-auto max-w-lg px-4 py-20 text-center">
      <h1 className="font-display text-2xl font-semibold">Something went wrong</h1>
      <p className="mt-2 text-muted">This page could not be displayed. No data was changed. Please try again.</p>
      <div className="mt-6 flex justify-center gap-3">
        <Button onClick={() => retry()}>Try again</Button>
        <ButtonLink href="/" variant="secondary">
          School website
        </ButtonLink>
      </div>
    </main>
  );
}
