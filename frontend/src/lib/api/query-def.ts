/** A typed description of a GET endpoint. Plain data, so it is usable from server and client code. */
export interface QueryDef<T> {
  readonly path: string;
  /** Phantom field carrying the response type; never set at runtime. */
  readonly __response?: T;
}

export function queryDef<T>(path: string): QueryDef<T> {
  return { path };
}
