"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { Alert } from "./feedback";

interface State {
  error: Error | null;
}

/**
 * Catches rendering errors in one part of the screen so the rest (navigation, header) keeps working.
 * `resetKey` (e.g. the current path) clears the error when the user navigates elsewhere.
 */
export class ErrorBoundary extends Component<{ children: ReactNode; resetKey?: string }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidUpdate(prev: { resetKey?: string }) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null });
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Hook for an error-tracking service; console output is the prototype's only sink.
    console.error("ui_error", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <Alert tone="error" title="This section could not be displayed">
          <p>Something went wrong while showing this page. Your data has not been changed.</p>
          <button type="button" className="mt-2 font-medium underline" onClick={() => this.setState({ error: null })}>
            Try again
          </button>
        </Alert>
      );
    }
    return this.props.children;
  }
}
