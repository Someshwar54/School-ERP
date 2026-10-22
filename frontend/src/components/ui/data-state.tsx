import type { ReactNode } from "react";
import type { ApiQueryState } from "@/lib/api/query";
import { ErrorState, Spinner } from "./feedback";

/** Renders loading / error / data states consistently. */
export function DataState<T>({
  state,
  children,
  loadingLabel,
}: {
  state: ApiQueryState<T>;
  children: (data: T) => ReactNode;
  loadingLabel?: string;
}) {
  if (state.error) return <ErrorState error={state.error} onRetry={state.reload} />;
  if (state.data === null) return <Spinner label={loadingLabel} />;
  return <>{children(state.data)}</>;
}
