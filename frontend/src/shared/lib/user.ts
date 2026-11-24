import type { User } from "@/api";

/** Name to show for a user: full name, @login or the Telegram ID. */
export function displayName(user: User): string {
  return user.user_fullname || (user.user_login ? `@${user.user_login}` : String(user.user_id));
}
