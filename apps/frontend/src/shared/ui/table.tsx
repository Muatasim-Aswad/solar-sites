import type { ComponentPropsWithoutRef } from "react";

export function Table({
  variant,
  ...props
}: Omit<ComponentPropsWithoutRef<"table">, "className"> & {
  variant: "sites" | "production";
}) {
  const cells =
    variant === "sites"
      ? "[&_tr>*]:px-6 [&_tr>*]:py-[1.1rem] max-compact:[&_tr>*]:p-4 [&_td]:whitespace-nowrap"
      : "[&_tr>*]:px-[0.9rem] [&_tr>*]:py-[0.65rem] [&_tr>td]:text-right [&_thead_th:last-child]:text-right [&_tbody_th]:pl-0";
  return (
    <table
      {...props}
      className={`w-full border-collapse tabular-nums [&_tr>*]:border-b [&_tr>*]:border-line-soft [&_tr>*]:text-left [&_thead_th]:bg-surface-subtle [&_thead_th]:text-[0.85rem] [&_thead_th]:font-[650] [&_thead_th]:text-muted [&_tbody_th]:font-medium [&_tbody_tr:last-child>*]:border-b-0 ${cells}`}
    />
  );
}
