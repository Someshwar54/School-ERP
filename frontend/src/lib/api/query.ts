"use client";

/**
 * Server-state management on top of TanStack Query.
 *
 * - A query is described by a typed `QueryDef` from src/services (its key is the API path).
 * - `useApiQuery` caches and de-duplicates reads; `useApiMutation` runs a write and then invalidates
 *   every cached query whose path starts with one of the given prefixes, so all screens refresh.
 * - A 401 anywhere triggers one global "unauthenticated" event (handled by the workspace shell).
 */
import { MutationCache, QueryCache, QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { ApiError, http } from "./client";
import type { QueryDef } from "./query-def";

export type { QueryDef } from "./query-def";

export interface ApiQueryState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
}

export const UNAUTHENTICATED_EVENT = "erp:unauthenticated";

function toApiError(e: unknown): ApiError {
  return e instanceof ApiError ? e : new ApiError(0, "error", "Something went wrong.");
}

function onError(e: unknown) {
  if (e instanceof ApiError && e.status === 401 && typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(UNAUTHENTICATED_EVENT));
  }
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    queryCache: new QueryCache({ onError }),
    mutationCache: new MutationCache({ onError }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        // Retry transient failures once; never retry 4xx (permission, validation, not found).
        retry: (count, e) => !(e instanceof ApiError && e.isClientError) && count < 1,
      },
      mutations: { retry: false },
    },
  });
}

/** Read server data. Pass `null` to wait (e.g. until a filter is chosen). */
export function useApiQuery<T>(def: QueryDef<T> | null): ApiQueryState<T> {
  const q = useQuery({
    queryKey: [def?.path ?? "__disabled__"],
    queryFn: ({ signal }) => http.get<T>(def!.path, signal),
    enabled: def !== null,
  });
  const { refetch } = q;
  const reload = useCallback(() => void refetch(), [refetch]);
  return {
    data: (q.data as T | undefined) ?? null,
    error: q.error ? toApiError(q.error) : null,
    loading: def !== null && q.isPending,
    reload,
  };
}

/** Invalidate cached queries by API-path prefix (e.g. "/teacher/attendance"). */
export function useInvalidate() {
  const client = useQueryClient();
  return useCallback(
    (prefixes: string[]) =>
      client.invalidateQueries({
        predicate: (q) => typeof q.queryKey[0] === "string" && prefixes.some((p) => (q.queryKey[0] as string).startsWith(p)),
      }),
    [client],
  );
}

export interface ApiMutation<TArgs, TResult> {
  run: (args: TArgs) => Promise<TResult>;
  pending: boolean;
  error: ApiError | null;
  reset: () => void;
}

/** Perform a write, then refresh every cached read under the `invalidates` path prefixes. */
export function useApiMutation<TArgs, TResult>(
  fn: (args: TArgs) => Promise<TResult>,
  options: { invalidates?: string[] } = {},
): ApiMutation<TArgs, TResult> {
  const invalidate = useInvalidate();
  const m = useMutation({
    mutationFn: fn,
    onSuccess: async () => {
      if (options.invalidates?.length) await invalidate(options.invalidates);
    },
  });
  return { run: m.mutateAsync, pending: m.isPending, error: m.error ? toApiError(m.error) : null, reset: m.reset };
}
