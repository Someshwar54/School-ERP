import { AlertTriangle, CheckCircle2, Info, Inbox, Lock, XCircle } from "lucide-react";
import type { ReactNode } from "react";
import type { ApiError } from "@/lib/api/client";
import type { Tone } from "@/domain/status";
import { cn } from "@/lib/cn";

const alertTones: Record<Tone, string> = {
  info: "border-sky-200 bg-sky-50 text-sky-900",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  error: "border-red-200 bg-red-50 text-red-900",
  neutral: "border-line bg-surface text-ink",
};
const alertIcons = { info: Info, success: CheckCircle2, warning: AlertTriangle, error: XCircle, neutral: Info };

export function Alert({
  tone = "info",
  title,
  children,
  className,
}: {
  tone?: Tone;
  title?: string;
  children?: ReactNode;
  className?: string;
}) {
  const Icon = alertIcons[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn("flex gap-3 rounded-brand border p-3 text-sm", alertTones[tone], className)}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="space-y-0.5">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div>{children}</div>}
      </div>
    </div>
  );
}

const badgeTones: Record<Tone, string> = {
  info: "bg-sky-100 text-sky-800",
  success: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-900",
  error: "bg-red-100 text-red-800",
  neutral: "bg-slate-100 text-slate-700",
};

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", badgeTones[tone], className)}>
      {children}
    </span>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-muted" role="status" aria-live="polite">
      <span className="size-5 animate-spin rounded-full border-2 border-brand border-r-transparent" aria-hidden />
      {label}
    </div>
  );
}

export function EmptyState({ title, text, action }: { title: string; text?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-brand border border-dashed border-line px-6 py-10 text-center">
      <Inbox className="size-8 text-muted" aria-hidden />
      <p className="font-medium text-ink">{title}</p>
      {text && <p className="max-w-md text-sm text-muted">{text}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  if (error.status === 403) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-brand border border-line bg-surface px-6 py-10 text-center" role="alert">
        <Lock className="size-8 text-muted" aria-hidden />
        <p className="font-medium">Access restricted</p>
        <p className="max-w-md text-sm text-muted">{error.message}</p>
      </div>
    );
  }
  return (
    <Alert tone="error" title="Could not load this section">
      <p>{error.message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-2 font-medium underline">
          Try again
        </button>
      )}
    </Alert>
  );
}
