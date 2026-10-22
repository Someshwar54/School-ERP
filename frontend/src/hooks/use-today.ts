"use client";

import { useSyncExternalStore } from "react";
import { todayISO } from "@/lib/format";

const noop = () => () => {};

/** Today's date in the school timezone, read only in the browser (null during prerender). */
export function useTodayISO(): string | null {
  return useSyncExternalStore(noop, todayISO, () => null);
}
