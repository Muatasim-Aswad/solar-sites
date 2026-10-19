import { Component, type ReactNode } from "react";
import { Button } from "../../shared/ui/buttons";

export class AppErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    if (this.state.failed)
      return (
        <main className="mx-auto my-[15vh] max-w-150 p-8">
          <h1>The workspace could not be displayed.</h1>
          <p>Reload to restore your session and try again.</p>
          <Button onClick={() => window.location.reload()}>Reload workspace</Button>
        </main>
      );
    return this.props.children;
  }
}
