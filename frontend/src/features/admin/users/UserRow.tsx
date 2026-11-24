import { Chip } from "@heroui/react";

import type { User } from "@/api";
import { useI18n } from "@/shared/i18n";
import { displayName } from "@/shared/lib/user";
import { UserAvatar } from "@/shared/ui/UserAvatar";

import { BanButton } from "./BanButton";

export function UserRow({ user, adminId }: { user: User; adminId: number }) {
  const { t } = useI18n();
  const name = displayName(user);
  const meta = [user.user_login && `@${user.user_login}`, user.user_id].filter(Boolean).join(" · ");

  return (
    <div className="flex items-center gap-3 py-3">
      <UserAvatar name={name} size="sm" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{name}</p>
        <p className="truncate text-xs text-muted tabular-nums">{meta}</p>
        {(user.is_banned || user.is_blocked) && (
          <div className="mt-1 flex gap-1">
            {user.is_banned && (
              <Chip color="danger" variant="soft" size="sm">
                {t("users.banned")}
              </Chip>
            )}
            {user.is_blocked && (
              <Chip color="warning" variant="soft" size="sm">
                {t("users.blocked")}
              </Chip>
            )}
          </div>
        )}
      </div>
      <BanButton user={user} isAdmin={user.user_id === adminId} />
    </div>
  );
}
