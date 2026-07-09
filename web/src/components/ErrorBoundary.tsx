import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            backgroundColor: 'var(--bg-primary)',
            color: 'var(--text-primary)',
            padding: '32px',
            fontFamily: 'var(--font-sans)',
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: '520px',
              textAlign: 'center',
              padding: '32px',
            }}
          >
            <h1
              style={{
                fontSize: '20px',
                fontWeight: 700,
                color: 'var(--error)',
                marginBottom: '12px',
              }}
            >
              Something went wrong
            </h1>
            <p
              style={{
                color: 'var(--text-secondary)',
                marginBottom: '16px',
                fontSize: '14px',
              }}
            >
              An unexpected error occurred. Try refreshing the page.
            </p>
            {this.state.error && (
              <pre
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                  borderRadius: '6px',
                  padding: '12px',
                  fontSize: '12px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                  textAlign: 'left',
                  overflow: 'auto',
                  maxHeight: '160px',
                  marginBottom: '16px',
                }}
              >
                {this.state.error.message}
              </pre>
            )}
            <button
              className="btn btn-primary"
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
