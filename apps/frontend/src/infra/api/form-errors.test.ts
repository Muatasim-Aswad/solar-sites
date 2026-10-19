import type { UseFormSetError } from "react-hook-form";
import { expect, test, vi } from "vite-plus/test";
import { ApiError, type ApiIssue } from "./errors";
import { setApiFieldErrors } from "./form-errors";

type FormValues = { latitude: number; peakKwp: number };
const fields = ["latitude", "peakKwp"] as const;

function validationError(issues: ApiIssue[]) {
  return new ApiError(422, {
    status: 422,
    code: "VALIDATION_ERROR",
    message: "Check the entered values.",
    request_id: "test-request",
    issues,
  });
}

test("maps each server validation issue onto its form field", () => {
  const setError = vi.fn<UseFormSetError<FormValues>>();
  const error = validationError([
    { field: "latitude", message: "Enter a valid latitude.", type: "value_error" },
    { field: "peakKwp", message: "Enter a positive capacity.", type: "value_error" },
  ]);

  setApiFieldErrors<FormValues>(error, fields, setError);

  expect(setError.mock.calls).toEqual([
    ["latitude", { type: "server", message: "Enter a valid latitude." }, { shouldFocus: true }],
    ["peakKwp", { type: "server", message: "Enter a positive capacity." }, { shouldFocus: true }],
  ]);
});

test("ignores unknown fields while still mapping known fields", () => {
  const setError = vi.fn<UseFormSetError<FormValues>>();
  const error = validationError([
    { field: "unrecognized", message: "Unknown field.", type: "value_error" },
    { field: "latitude", message: "Enter a valid latitude.", type: "value_error" },
  ]);

  setApiFieldErrors<FormValues>(error, fields, setError);

  expect(setError.mock.calls).toEqual([
    ["latitude", { type: "server", message: "Enter a valid latitude." }, { shouldFocus: true }],
  ]);
});

test.each([new Error("Network unavailable"), new ApiError(500), null, "Unexpected failure"])(
  "does not turn unrelated errors into field errors: %s",
  (error) => {
    const setError = vi.fn<UseFormSetError<FormValues>>();

    setApiFieldErrors<FormValues>(error, fields, setError);

    expect(setError).not.toHaveBeenCalled();
  },
);
