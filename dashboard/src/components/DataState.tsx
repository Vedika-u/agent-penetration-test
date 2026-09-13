import type { ReactNode } from "react";
import type { FetchState } from "../lib/useJson";

interface DataStateProps<T> {
  state: FetchState<T>;
  path: string;
  children: (data: T) => ReactNode;
}

/** Renders loading/error/ok branches consistently for every view. */
export function DataState<T>({ state, path, children }: DataStateProps<T>) {
  if (state.status === "loading") {
    return <div className="panel panel--muted">Loading {path}…</div>;
  }
  if (state.status === "error") {
    return (
      <div className="panel panel--error">
        <strong>Couldn't load {path}.</strong>
        <div>{state.error}</div>
        <div className="panel__note">
          Expected a JSON file at <code>{path}</code> matching the Phase 5 data
          contract.
        </div>
      </div>
    );
  }
  return <>{children(state.data)}</>;
}
