import { request } from "./client";
import type { BotSettings, CaptchaChallenge, Me, Stats, User, UsersPage } from "./types";

export { ApiError, errorCode } from "./client";
export { queryKeys } from "./queryKeys";
export type * from "./types";

/** Mini App API endpoints (webapp/api/routes). */
export const api = {
  me: () => request<Me>("GET", "/api/me"),

  captcha: () => request<CaptchaChallenge>("GET", "/api/captcha"),

  sendFeedback: (text: string, captcha: string | null) =>
    request<{ ok: boolean }>("POST", "/api/feedback", {
      body: { text },
      headers: captcha ? { "X-Captcha": captcha } : undefined,
    }),

  admin: {
    stats: () => request<Stats>("GET", "/api/admin/stats"),

    users: (q: string, offset: number, limit = 20) =>
      request<UsersPage>(
        "GET",
        `/api/admin/users?${new URLSearchParams({ q, offset: String(offset), limit: String(limit) })}`,
      ),

    setBanned: (userId: number, isBanned: boolean) =>
      request<User>("PATCH", `/api/admin/users/${userId}`, { body: { is_banned: isBanned } }),

    settings: () => request<BotSettings>("GET", "/api/admin/settings"),

    setMaintenance: (isMaintenance: boolean) =>
      request<BotSettings>("PATCH", "/api/admin/settings", {
        body: { is_maintenance: isMaintenance },
      }),
  },
};
