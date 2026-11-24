import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  /** Rendered instead of the children after a render error. */
  fallback: (reset: () => void) => ReactNode;
  children: ReactNode;
};

type State = { hasError: boolean };

/** Catches render errors so one broken screen does not blank the whole Mini App. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Render error", error, info.componentStack);
  }

  private reset = (): void => this.setState({ hasError: false });

  render(): ReactNode {
    return this.state.hasError ? this.props.fallback(this.reset) : this.props.children;
  }
}
