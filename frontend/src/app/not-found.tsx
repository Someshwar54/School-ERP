import type { Metadata } from "next";
import { ButtonLink } from "@/components/ui";
import { school } from "@/config/school";

export const metadata: Metadata = { title: "Page not found" };

export default function NotFound() {
  return (
    <main id="main" className="mx-auto max-w-lg px-4 py-20 text-center">
      <p className="text-sm font-semibold uppercase tracking-wider text-accent-strong">404</p>
      <h1 className="mt-2 font-display text-3xl font-semibold">Page not found</h1>
      <p className="mt-2 text-muted">The page you are looking for does not exist or has moved.</p>
      <div className="mt-6 flex justify-center gap-3">
        <ButtonLink href="/">Go to {school.shortName} home</ButtonLink>
        <ButtonLink href="/erp" variant="secondary">
          {school.terminology.portal}
        </ButtonLink>
      </div>
    </main>
  );
}
