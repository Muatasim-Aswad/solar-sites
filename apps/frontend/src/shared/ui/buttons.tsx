import type { ComponentPropsWithoutRef } from "react";
import { Link, type LinkProps } from "react-router";

type ButtonVariant = "primary" | "secondary" | "danger" | "danger-link";

const base =
  "inline-flex min-h-11 cursor-pointer items-center justify-center font-[650] leading-[1.3] disabled:cursor-wait disabled:opacity-65";

const shape = "rounded-md border px-[1.1rem] py-[0.62rem] no-underline";

const variants: Record<ButtonVariant, string> = {
  primary: `${shape} border-transparent bg-teal text-white hover:bg-teal-hover hover:text-white`,
  secondary: `${shape} border-control bg-white text-ink hover:bg-surface-hover hover:text-ink`,
  danger: `${shape} border-transparent bg-danger text-white hover:bg-danger-strong hover:text-white`,
  "danger-link":
    "rounded-md border border-transparent bg-transparent px-0 py-2 text-danger underline hover:text-danger",
};

export function Button({
  variant = "primary",
  type = "button",
  ...props
}: Omit<ComponentPropsWithoutRef<"button">, "className"> & { variant?: ButtonVariant }) {
  return <button {...props} type={type} className={`${base} ${variants[variant]}`} />;
}

export function ButtonLink({
  variant = "primary",
  ...props
}: Omit<LinkProps, "className"> & { variant?: "primary" | "secondary" }) {
  return <Link {...props} className={`${base} ${variants[variant]}`} />;
}
