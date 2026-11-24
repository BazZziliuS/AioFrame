import {
  Alert,
  AlertDialog,
  Button,
  Card,
  Chip,
  SearchField,
  Separator,
  Spinner,
  toast,
} from "@heroui/react";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Fragment, useState } from "react";

import { UserAvatar } from "../../components/UserAvatar";
import { api, ApiError, type User } from "../../lib/api";
import { useDebounced } from "../../lib/hooks";
import { errorText, useI18n } from "../../lib/i18n";
import { haptic } from "../../lib/telegram";

const PAGE_SIZE = 20;

function displayName(user: User): string {
  return user.user_fullname || (user.user_login ? `@${user.user_login}` : String(user.user_id));
}

function useSetBanned() {
  const { t } = useI18n();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ user, banned }: { user: User; banned: boolean }) =>
      api.setBanned(user.user_id, banned),
    onSuccess: (updated) => {
      haptic.success();
      toast.success(
        t(updated.is_banned ? "users.banned.toast" : "users.unbanned.toast", {
          name: displayName(updated),
        }),
      );
      void queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
    onError: (error) => {
      haptic.error();
      toast.danger(errorText(t, error instanceof ApiError ? error.detail : "server_error"));
    },
  });
}

function BanButton({ user, isAdmin }: { user: User; isAdmin: boolean }) {
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
              <AlertDialog.Heading>{t("users.banTitle", { name: displayName(user) })}</AlertDialog.Heading>
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

function UserRow({ user, adminId }: { user: User; adminId: number }) {
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

export function Users({ adminId }: { adminId: number }) {
  const { t } = useI18n();
  const [search, setSearch] = useState("");
  const query = useDebounced(search.trim());

  const users = useInfiniteQuery({
    queryKey: ["admin", "users", query],
    queryFn: ({ pageParam }) => api.users(query, pageParam, PAGE_SIZE),
    initialPageParam: 0,
    getNextPageParam: (last) =>
      last.offset + last.items.length < last.total ? last.offset + last.limit : undefined,
  });

  const items = users.data?.pages.flatMap((page) => page.items) ?? [];
  const total = users.data?.pages[0]?.total ?? 0;

  return (
    <Card>
      <Card.Header>
        <Card.Title>{t("users.title")}</Card.Title>
        <Card.Description>
          {users.data ? t("users.shown", { shown: items.length, total }) : " "}
        </Card.Description>
      </Card.Header>

      <Card.Content className="gap-1">
        <SearchField
          aria-label={t("users.search")}
          value={search}
          onChange={setSearch}
          variant="secondary"
          className="mb-2"
        >
          <SearchField.Group>
            <SearchField.SearchIcon />
            <SearchField.Input placeholder={t("users.search")} />
            <SearchField.ClearButton />
          </SearchField.Group>
        </SearchField>

        {users.isPending ? (
          <div className="flex justify-center py-10">
            <Spinner />
          </div>
        ) : users.error ? (
          <Alert status="danger">
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Description>
                {errorText(t, users.error instanceof ApiError ? users.error.detail : "server_error")}
              </Alert.Description>
            </Alert.Content>
          </Alert>
        ) : items.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted">{t("users.empty")}</p>
        ) : (
          items.map((user, index) => (
            <Fragment key={user.user_id}>
              {index > 0 && <Separator />}
              <UserRow user={user} adminId={adminId} />
            </Fragment>
          ))
        )}
      </Card.Content>

      {users.hasNextPage && (
        <Card.Footer>
          <Button
            variant="secondary"
            fullWidth
            isPending={users.isFetchingNextPage}
            onPress={() => void users.fetchNextPage()}
          >
            {t("users.loadMore")}
          </Button>
        </Card.Footer>
      )}
    </Card>
  );
}
