import { getRawInitData } from "@/shared/telegram/sdk";

/** Error returned by the backend: `detail` is a machine-readable code (see webapp/api/deps.py). */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

/** Error code of any thrown value, for messages shown to the user. */
export function errorCode(error: unknown): string {
  return error instanceof ApiError ? error.detail : "server_error";
}

type RequestOptions = {
  body?: unknown;
  headers?: Record<string, string>;
};

/**
 * JSON request to the Mini App API. Every request is authorized with Telegram initData,
 * failures are thrown as ApiError (status 0 for network errors).
 */
export async function request<T>(
  method: string,
  path: string,
  { body, headers }: RequestOptions = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        Authorization: `tma ${getRawInitData()}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "network_error");
  }

  if (!response.ok) {
    let detail = "server_error";
    try {
      const data = (await response.json()) as { detail?: unknown };
      if (typeof data.detail === "string") detail = data.detail;
    } catch {
      // Not a JSON error body
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}
