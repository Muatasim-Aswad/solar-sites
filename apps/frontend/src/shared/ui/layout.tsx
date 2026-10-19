import type { ComponentPropsWithoutRef } from "react";

const panelPadding = {
  normal: "p-[1.8rem] max-compact:p-[1.2rem]",
  auth: "p-8 max-compact:p-[1.2rem]",
  empty: "px-8 py-16 max-compact:p-[1.2rem]",
  none: "p-0",
};

export function Panel({
  padding = "normal",
  className = "",
  ...props
}: ComponentPropsWithoutRef<"section"> & { padding?: keyof typeof panelPadding }) {
  return (
    <section
      {...props}
      className={`rounded-[10px] border border-line bg-white ${panelPadding[padding]} ${className}`}
    />
  );
}

export function PageHeading({ className = "", ...props }: ComponentPropsWithoutRef<"div">) {
  return (
    <div
      {...props}
      className={`mt-4 mb-8 flex items-center justify-between gap-4 max-compact:mb-6 max-compact:flex-col max-compact:items-start [&_h1]:wrap-anywhere [&_p]:m-0 [&_p]:text-muted [&_p]:wrap-anywhere ${className}`}
    />
  );
}
