/** Response shapes of the Mini App API (see webapp/schemas). */
import type { Challenge } from "altcha-lib";

export type User = {
  user_id: number;
  user_login: string;
  user_fullname: string;
  user_locale: string;
  is_banned: boolean;
  is_blocked: boolean;
  /** ISO 8601 in UTC, e.g. "2026-11-24T10:00:00Z" */
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

export type CaptchaChallenge = {
  enabled: boolean;
  challenge: Challenge | null;
};
