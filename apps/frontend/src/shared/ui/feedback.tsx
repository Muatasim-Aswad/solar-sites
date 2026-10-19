import type { ComponentPropsWithoutRef } from "react";
import { Button } from "./buttons";

export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  if (!error) return null;
  const message =
    error instanceof Error ? error.message : "Something went wrong. Please try again.";
  return (
    <Notice tone="error" role="alert">
      <p>{message}</p>
      {error instanceof Error && "requestId" in error && typeof error.requestId === "string" ? (
        <small>Reference: {error.requestId}</small>
      ) : null}
      {retry ? (
        <Button variant="secondary" onClick={retry}>
          Try again
        </Button>
      ) : null}
    </Notice>
  );
}

export function Loading({ children = "Loading…" }: { children?: string }) {
  return <output className="block py-6 text-muted">{children}</output>;
}
export function Notice({
  as: Tag = "div",
  tone = "info",
  ...props
}: Pick<ComponentPropsWithoutRef<"div">, "children" | "role"> & {
  as?: "div" | "output";
  tone?: "info" | "error";
}) {
  const colors =
    tone === "error" ? "border-danger bg-danger-soft text-danger-strong" : "border-muted bg-notice";
  return (
    <Tag
      {...props}
      className={`my-4 block rounded-md border-l-[3px] p-4 wrap-anywhere [&_p:last-child]:mb-0 [&_small]:block [&_button]:mt-3 ${colors}`}
    />
  );
}
