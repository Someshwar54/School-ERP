"use client";

import { useQueryClient } from "@tanstack/react-query";
import { LogOut, Menu, X } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { Alert, ErrorBoundary, ErrorState, Spinner } from "@/components/ui";
import { school } from "@/config/school";
import { useSession, useSignOut } from "@/features/auth/use-session";
import { cn } from "@/lib/cn";
import { UNAUTHENTICATED_EVENT } from "@/lib/api/query";
import { LOGIN_PATH, type WorkspaceKind } from "@/services/auth";
import { navFor } from "./nav";

const TITLES: Record<WorkspaceKind, string> = { student: "Student Portal", staff: "Staff Workspace", management: "Management Portal" };

/** Signs the user out locally when any request returns 401 (expired or revoked session). */
function useRedirectWhenUnauthenticated(kind: WorkspaceKind) {
  const router = useRouter();
  const client = useQueryClient();
  useEffect(() => {
    const onUnauthenticated = () => {
      client.clear();
      router.replace(LOGIN_PATH[kind]);
    };
    window.addEventListener(UNAUTHENTICATED_EVENT, onUnauthenticated);
    return () => window.removeEventListener(UNAUTHENTICATED_EVENT, onUnauthenticated);
  }, [kind, router, client]);
}

/**
 * Layout for every ERP workspace: header, server-driven navigation and the page body.
 * The page always renders (it fetches its own data and the backend authorises every call);
 * only the navigation chrome waits for the session.
 */
export function WorkspaceShell({ kind, children }: { kind: WorkspaceKind; children: ReactNode }) {
  useRedirectWhenUnauthenticated(kind);
  const { me, error, reload } = useSession();
  const signOut = useSignOut(kind);
  const pathname = usePathname();
  // The menu is open only for the path it was opened on, so navigating closes it.
  const [openOn, setOpenOn] = useState<string | null>(null);
  const open = openOn === pathname;

  let body: ReactNode = children;
  if (error && error.status !== 401) {
    body = <ErrorState error={error} onRetry={reload} />;
  } else if (me && me.workspace.kind !== kind) {
    // UX only: the backend independently rejects API calls from the wrong account type.
    body = (
      <div className="max-w-lg space-y-4">
        <Alert tone="warning" title="This workspace is not available for your account">
          You are signed in as {me.user.display_name}. Continue to the workspace assigned to your account.
        </Alert>
        <Link href={me.workspace.home} className="font-medium text-brand underline">
          Go to my workspace
        </Link>
      </div>
    );
  }

  const nav = me && me.workspace.kind === kind ? navFor(kind, me.workspace.modules) : [];
  const isActive = (href: string) => (href === nav[0]?.href ? pathname === href : pathname.startsWith(href));
  const sidebar = (
    <nav aria-label="Workspace" className="space-y-0.5 p-3">
      {!me && <Spinner label="Loading menu…" />}
      {nav.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          aria-current={isActive(item.href) ? "page" : undefined}
          className={cn(
            "flex items-center gap-2.5 rounded-brand px-3 py-2 text-sm transition-colors",
            isActive(item.href) ? "bg-brand text-brand-contrast" : "text-ink hover:bg-surface",
          )}
        >
          <item.icon className="size-4 shrink-0" aria-hidden />
          {item.label}
        </Link>
      ))}
    </nav>
  );

  return (
    <div className="min-h-screen bg-surface">
      <header className="no-print sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-line bg-white px-3 sm:px-5">
        <button
          type="button"
          className="rounded-brand p-2 hover:bg-surface lg:hidden"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          onClick={() => setOpenOn(open ? null : pathname)}
        >
          {open ? <X className="size-5" aria-hidden /> : <Menu className="size-5" aria-hidden />}
        </button>
        <Link href={me?.workspace.home ?? "/erp"} className="flex min-w-0 items-center gap-2">
          <Image src={school.logo.src} alt="" width={28} height={28} className="size-7 shrink-0" />
          <span className="truncate text-sm font-semibold text-brand">{school.shortName}</span>
          <span className="hidden text-sm text-muted sm:inline">· {TITLES[kind]}</span>
        </Link>
        <div className="ml-auto flex items-center gap-3">
          {me && (
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium leading-tight" data-testid="signed-in-name">
                {me.user.display_name}
              </p>
              <p className="text-xs text-muted">
                {me.user.login_id}
                {me.workspace.roles.length > 0 && ` · ${me.workspace.roles.join(", ")}`}
              </p>
            </div>
          )}
          <button
            type="button"
            onClick={() => void signOut()}
            className="inline-flex items-center gap-1.5 rounded-brand border border-line px-3 py-1.5 text-sm hover:bg-surface"
          >
            <LogOut className="size-4" aria-hidden /> Sign out
          </button>
        </div>
      </header>

      <div className="flex">
        <aside className="no-print sticky top-14 hidden h-[calc(100vh-3.5rem)] w-64 shrink-0 overflow-y-auto border-r border-line bg-white lg:block">
          {sidebar}
        </aside>
        {open && (
          <div className="fixed inset-0 top-14 z-20 lg:hidden">
            <div className="absolute inset-0 bg-black/30" onClick={() => setOpenOn(null)} aria-hidden />
            <aside className="relative h-full w-72 max-w-[85vw] overflow-y-auto border-r border-line bg-white">{sidebar}</aside>
          </div>
        )}
        <main id="main" className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
          {me?.user.must_change_password && (
            <Alert tone="warning" title="You are using an initial password" className="mb-5">
              Please change it in account settings.{" "}
              {me.demo_mode &&
                "(Prototype: demo accounts start with initial passwords; production will require a change before continuing.)"}
            </Alert>
          )}
          <ErrorBoundary resetKey={pathname}>{body}</ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
