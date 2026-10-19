import type { components } from "./schema";

export type ApiErrorBody = components["schemas"]["ErrorBody"];
export type ApiIssue = components["schemas"]["ValidationIssue"];

export class ApiError extends Error {
  readonly status: number;
  readonly requestId: string | undefined;
  readonly issues: ApiIssue[];

  constructor(status: number, body?: ApiErrorBody) {
    super(body?.message ?? "The request failed. Please try again.");
    this.name = "ApiError";
    this.status = status;
    this.requestId = body?.request_id;
    this.issues = Array.isArray(body?.issues)
      ? body.issues.filter(
          (issue) => issue && typeof issue.field === "string" && typeof issue.message === "string",
        )
      : [];
  }
}

export function readErrorBody(value: unknown): ApiErrorBody | undefined {
  if (!value || typeof value !== "object" || !("error" in value)) return undefined;

  const body = value.error;
  if (!body || typeof body !== "object") return undefined;
  if (
    !("message" in body) ||
    typeof body.message !== "string" ||
    !("status" in body) ||
    typeof body.status !== "number" ||
    !("request_id" in body) ||
    typeof body.request_id !== "string"
  )
    return undefined;

  return body as ApiErrorBody;
}
