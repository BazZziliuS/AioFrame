import { toast } from "@heroui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, errorCode, queryKeys, type User } from "@/api";
import { errorText, useI18n } from "@/shared/i18n";
import { displayName } from "@/shared/lib/user";
import { haptic } from "@/shared/telegram/sdk";

/** Ban or unban a user, with a toast, haptic feedback and refreshed admin data. */
export function useSetBanned() {
  const { t } = useI18n();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ user, banned }: { user: User; banned: boolean }) =>
      api.admin.setBanned(user.user_id, banned),
    onSuccess: (updated) => {
      haptic.success();
      toast.success(
        t(updated.is_banned ? "users.banned.toast" : "users.unbanned.toast", {
          name: displayName(updated),
        }),
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.admin.all });
    },
    onError: (error) => {
      haptic.error();
      toast.danger(errorText(t, errorCode(error)));
    },
  });
}
