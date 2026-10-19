import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string | undefined;
  hint?: string;
}

export const Field = forwardRef<HTMLInputElement, FieldProps>(function Field(
  { label, error, hint, id, name, className = "", ...props },
  ref,
) {
  const fieldId = id ?? name;
  const description = error ? `${fieldId}-error` : hint ? `${fieldId}-hint` : undefined;
  return (
    <div className="mb-[1.2rem] flex min-w-0 flex-col gap-[0.4rem]">
      <label className="text-[0.9rem] font-[650]" htmlFor={fieldId}>
        {label}
      </label>
      <input
        {...props}
        className={`min-h-11.5 w-full rounded-[5px] border border-input bg-white px-3 py-[0.6rem] text-ink aria-invalid:border-danger ${className}`}
        id={fieldId}
        name={name}
        ref={ref}
        aria-invalid={error ? true : undefined}
        aria-describedby={description}
      />
      {error ? (
        <span className="text-[0.85rem] text-danger" id={description}>
          {error}
        </span>
      ) : hint ? (
        <span className="text-[0.82rem] text-muted" id={description}>
          {hint}
        </span>
      ) : null}
    </div>
  );
});

export function FormActions({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap items-center gap-3">{children}</div>;
}
