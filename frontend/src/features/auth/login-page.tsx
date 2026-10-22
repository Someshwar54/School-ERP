import type { LucideIcon } from "lucide-react";
import { env } from "@/config/env";
import type { Portal } from "@/services/auth";
import { LoginForm } from "./login-form";
import { PortalFrame } from "./portal-frame";

export function LoginPage({
  portal,
  title,
  description,
  icon: Icon,
  note,
}: {
  portal: Portal;
  title: string;
  description: string;
  icon: LucideIcon;
  note?: string;
}) {
  return (
    <PortalFrame back={{ href: "/erp", label: "All sign-in options" }}>
      <div className="mx-auto max-w-md rounded-brand border border-line bg-white p-6 shadow-sm sm:p-8">
        <span className="inline-flex size-12 items-center justify-center rounded-brand bg-brand-soft text-brand">
          <Icon className="size-6" aria-hidden />
        </span>
        <h1 className="mt-4 font-display text-2xl font-semibold text-ink">{title}</h1>
        <p className="mt-1 text-sm text-muted">{description}</p>
        {note && <p className="mt-3 text-xs text-muted">{note}</p>}
        <div className="mt-6">
          <LoginForm
            portal={portal}
            demoNote={
              env.demoMode
                ? "Prototype / demo mode: use the fictional demo accounts listed in the project README. No real data is used."
                : undefined
            }
          />
        </div>
      </div>
    </PortalFrame>
  );
}
