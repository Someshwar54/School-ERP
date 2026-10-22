import { KeyRound } from "lucide-react";
import Link from "next/link";
import { PortalFrame } from "@/features/auth/portal-frame";
import { Alert } from "@/components/ui";
import { school } from "@/config/school";

export function RecoveryPage() {
  return (
    <PortalFrame back={{ href: "/erp", label: "All sign-in options" }}>
      <div className="mx-auto max-w-lg rounded-brand border border-line bg-white p-6 shadow-sm sm:p-8">
        <span className="inline-flex size-12 items-center justify-center rounded-brand bg-brand-soft text-brand">
          <KeyRound className="size-6" aria-hidden />
        </span>
        <h1 className="mt-4 font-display text-2xl font-semibold">Forgot your password?</h1>
        <Alert tone="warning" title="Self-service recovery is not connected yet" className="mt-4">
          This prototype does not send reset links by email or SMS. No reset request has been made.
        </Alert>
        <div className="mt-5 space-y-3 text-sm text-muted">
          <p>To regain access, contact the school office. Staff will verify your identity before issuing a temporary password.</p>
          <p>
            <span className="font-medium text-ink">Office:</span> {school.contact.phone} · {school.contact.email}
          </p>
          <p>
            Management accounts are reset only after identity verification by the school&apos;s administrator, and will require multi-factor
            authentication in production.
          </p>
        </div>
        <Link href="/erp" className="mt-6 inline-block text-sm font-medium text-brand hover:underline">
          Return to sign-in options
        </Link>
      </div>
    </PortalFrame>
  );
}
