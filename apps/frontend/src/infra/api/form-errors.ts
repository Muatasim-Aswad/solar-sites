import type { FieldValues, Path, UseFormSetError } from "react-hook-form";
import { ApiError } from "./errors";

export function setApiFieldErrors<T extends FieldValues>(
  error: unknown,
  fields: readonly Path<T>[],
  setError: UseFormSetError<T>,
) {
  if (!(error instanceof ApiError)) return;
  for (const issue of error.issues) {
    const field = fields.find((name) => name === issue.field);
    if (field) setError(field, { type: "server", message: issue.message }, { shouldFocus: true });
  }
}
