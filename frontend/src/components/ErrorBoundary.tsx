import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { motion } from 'framer-motion';

/**
 * Error Boundary Component
 * Catches errors in child components and displays graceful fallback UI
 */

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Update state
    this.setState((prev) => ({
      errorInfo,
      errorCount: prev.errorCount + 1,
    }));

    // Call custom error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Optional: Send to error tracking service
    // this.sendToErrorTracking(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default premium error UI
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-2xl w-full"
          >
            <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-red-500 to-orange-500 p-8">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring' }}
                  className="flex justify-center mb-4"
                >
                  <div className="bg-white dark:bg-slate-900 rounded-full p-4">
                    <AlertTriangle className="w-12 h-12 text-red-500" />
                  </div>
                </motion.div>
                <h1 className="text-3xl font-bold text-white text-center mb-2">
                  Oops! Something went wrong
                </h1>
                <p className="text-red-100 text-center">
                  We're sorry for the inconvenience. An unexpected error occurred.
                </p>
              </div>

              {/* Body */}
              <div className="p-8">
                {/* Error Message */}
                <div className="mb-6">
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                    Error Details:
                  </h2>
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <p className="text-red-800 dark:text-red-200 font-mono text-sm break-all">
                      {this.state.error?.toString()}
                    </p>
                  </div>
                </div>

                {/* Show Stack Trace in Development */}
                {this.props.showDetails && this.state.errorInfo && (
                  <details className="mb-6">
                    <summary className="cursor-pointer text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white mb-2">
                      Show Technical Details
                    </summary>
                    <div className="bg-slate-100 dark:bg-slate-800 rounded-lg p-4 overflow-auto max-h-64">
                      <pre className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </div>
                  </details>
                )}

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={this.handleReset}
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-700 hover:to-primary-600 text-white rounded-lg font-medium transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    <RefreshCw className="w-5 h-5" />
                    Try Again
                  </button>
                  <button
                    onClick={this.handleReload}
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-all duration-200"
                  >
                    <RefreshCw className="w-5 h-5" />
                    Reload Page
                  </button>
                  <button
                    onClick={this.handleGoHome}
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg font-medium transition-all duration-200"
                  >
                    <Home className="w-5 h-5" />
                    Go Home
                  </button>
                </div>

                {/* Error Count Warning */}
                {this.state.errorCount > 2 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
                  >
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      <strong>Multiple errors detected.</strong> This might indicate a persistent issue.
                      Please contact support if the problem continues.
                    </p>
                  </motion.div>
                )}

                {/* Help Text */}
                <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800">
                  <p className="text-sm text-slate-600 dark:text-slate-400 text-center">
                    Need help? Contact our support team at{' '}
                    <a
                      href="mailto:support@platform.com"
                      className="text-primary-600 dark:text-primary-400 hover:underline"
                    >
                      support@platform.com
                    </a>
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Async Error Boundary for handling async errors
 */
export const AsyncErrorBoundary: React.FC<Props> = ({ children, ...props }) => {
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      setError(new Error(event.reason));
      event.preventDefault();
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  if (error) {
    throw error;
  }

  return <ErrorBoundary {...props}>{children}</ErrorBoundary>;
};

/**
 * Compact Error Boundary for smaller components
 */
export const CompactErrorBoundary: React.FC<Props> = ({ children, ...props }) => {
  return (
    <ErrorBoundary
      {...props}
      fallback={
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-red-900 dark:text-red-100 mb-1">
                Component Error
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300">
                This component encountered an error. Please try refreshing the page.
              </p>
            </div>
          </div>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  );
};

export default ErrorBoundary;
