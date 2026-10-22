"use client";

/**
 * The signed-in user, read from the shared query cache (GET /auth/me). Any component may call this;
 * the request is made once and shared. Permissions decide what the UI shows, but the backend is the
 * security boundary: hiding a button never grants or removes access.
 */
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { useApiQuery } from "@/lib/api/query";
import { authApi, LOGIN_PATH, type WorkspaceKind } from "@/services/auth";

export function useSession() {
  const state = useApiQuery(authApi.me());
  const permissions = state.data?.workspace.permissions;
  const can = useCallback((permission: string) => Boolean(permissions?.includes(permission)), [permissions]);
  return { ...state, me: state.data, can };
}

/** Sign out, drop every cached response (so the next user never sees this user's data) and go to sign-in. */
export function useSignOut(kind: WorkspaceKind) {
  const client = useQueryClient();
  const router = useRouter();
  return useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      client.clear();
      router.replace(LOGIN_PATH[kind]);
    }
  }, [client, router, kind]);
}
