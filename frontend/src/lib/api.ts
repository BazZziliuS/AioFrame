import { getRawInitData } from "./telegram";

export type User = {
  user_id: number;
  user_login: string;
  user_fullname: string;
  user_locale: string;
  is_banned: boolean;
  is_blocked: boolean;
  created_at: string;
};

export type Me = {
  user: User;
  is_admin: boolean;
  photo_url: string | null;
};

export type Stats = {
  total: number;
  new_day: number;
  new_week: number;
  active: number;
  banned: number;
  blocked: number;
};

export type UsersPage = {
  items: User[];
  total: number;
  offset: number;
  limit: number;
};

export type BotSettings = {
  is_maintenance: boolean;
};

/** Error returned by the backend: `detail` is a machine-readable code (see webapp/auth.py). */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      headers: {
        Authorization: `tma ${getRawInitData()}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
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

export const api = {
  me: () => request<Me>("GET", "/api/me"),
  stats: () => request<Stats>("GET", "/api/admin/stats"),
  users: (q: string, offset: number, limit = 20) =>
    request<UsersPage>(
      "GET",
      `/api/admin/users?${new URLSearchParams({ q, offset: String(offset), limit: String(limit) })}`,
    ),
  setBanned: (userId: number, isBanned: boolean) =>
    request<User>("PATCH", `/api/admin/users/${userId}`, { is_banned: isBanned }),
  settings: () => request<BotSettings>("GET", "/api/admin/settings"),
  setMaintenance: (isMaintenance: boolean) =>
    request<BotSettings>("PATCH", "/api/admin/settings", { is_maintenance: isMaintenance }),
};
