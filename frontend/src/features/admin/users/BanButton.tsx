import { AlertDialog, Button, Chip } from "@heroui/react";

import type { User } from "@/api";
import { useI18n } from "@/shared/i18n";
import { displayName } from "@/shared/lib/user";

import { useSetBanned } from "./useSetBanned";

/** Ban (with confirmation) or unban; admins cannot be banned. */
export function BanButton({ user, isAdmin }: { user: User; isAdmin: boolean }) {
  const { t } = useI18n();
  const setBanned = useSetBanned();
  const isPending = setBanned.isPending && setBanned.variables?.user.user_id === user.user_id;

  if (isAdmin) {
    return (
      <Chip color="accent" variant="soft" size="sm">
        {t("profile.admin")}
      </Chip>
    );
  }

  if (user.is_banned) {
    return (
      <Button
        size="sm"
        variant="secondary"
        isPending={isPending}
        onPress={() => setBanned.mutate({ user, banned: false })}
      >
        {t("users.unban")}
      </Button>
    );
  }

  // Banning is destructive: ask for confirmation
  return (
    <AlertDialog>
      <Button size="sm" variant="outline" isPending={isPending}>
        {t("users.ban")}
      </Button>
      <AlertDialog.Backdrop>
        <AlertDialog.Container placement="center" size="sm">
          <AlertDialog.Dialog>
            <AlertDialog.Header>
              <AlertDialog.Icon status="danger" />
              <AlertDialog.Heading>
                {t("users.banTitle", { name: displayName(user) })}
              </AlertDialog.Heading>
            </AlertDialog.Header>
            <AlertDialog.Body>
              <p className="text-sm text-muted">{t("users.banText")}</p>
            </AlertDialog.Body>
            <AlertDialog.Footer>
              <Button slot="close" variant="tertiary">
                {t("users.cancel")}
              </Button>
              <Button
                slot="close"
                variant="danger"
                onPress={() => setBanned.mutate({ user, banned: true })}
              >
                {t("users.ban")}
              </Button>
            </AlertDialog.Footer>
          </AlertDialog.Dialog>
        </AlertDialog.Container>
      </AlertDialog.Backdrop>
    </AlertDialog>
  );
}
