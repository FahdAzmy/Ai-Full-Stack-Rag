'use client';

import React, { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional fallback UI. If not provided, a default error card is shown. */
  fallback?: ReactNode;
  /** Optional callback when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          className="flex items-center justify-center min-h-[200px] p-8"
        >
          <div className="max-w-md w-full bg-white dark:bg-gray-900 border border-red-200 dark:border-red-800/50 rounded-2xl p-8 shadow-lg text-center">
            {/* Error icon */}
            <div className="w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-4">
              <span className="material-symbols-outlined text-3xl text-red-500 dark:text-red-400" aria-hidden="true">
                error
              </span>
            </div>

            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
              An unexpected error occurred. Please try again or refresh the page.
            </p>

            {/* Error details (dev mode) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-6 text-start">
                <summary className="text-xs font-semibold text-slate-400 cursor-pointer hover:text-slate-600 dark:hover:text-slate-300 transition-colors">
                  Error details
                </summary>
                <pre className="mt-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-800 text-xs text-red-600 dark:text-red-400 overflow-auto max-h-32 border border-slate-200 dark:border-slate-700">
                  {this.state.error.message}
                  {'\n'}
                  {this.state.error.stack}
                </pre>
              </details>
            )}

            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="px-5 py-2.5 bg-primary hover:bg-primary-light text-white font-semibold rounded-xl text-sm transition-colors shadow-sm"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-5 py-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold rounded-xl text-sm transition-colors"
              >
                Refresh Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Lightweight error boundary for individual sections/components.
 * Renders a compact inline error instead of a full-page card.
 */
export class SectionErrorBoundary extends Component<
  { children: ReactNode; section?: string },
  ErrorBoundaryState
> {
  constructor(props: { children: ReactNode; section?: string }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`[SectionErrorBoundary${this.props.section ? `: ${this.props.section}` : ''}]`, error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          className="flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/40 text-sm"
        >
          <span className="material-symbols-outlined text-red-500 dark:text-red-400 text-lg" aria-hidden="true">
            warning
          </span>
          <div className="flex-1">
            <p className="font-medium text-red-700 dark:text-red-300">
              {this.props.section ? `${this.props.section} failed to load` : 'This section encountered an error'}
            </p>
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="text-xs font-semibold text-red-600 dark:text-red-400 hover:underline"
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
