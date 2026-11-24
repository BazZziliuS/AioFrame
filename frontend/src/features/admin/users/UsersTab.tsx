import { Alert, Button, Card, SearchField, Separator, Spinner } from "@heroui/react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { Fragment, useState } from "react";

import { api, errorCode, queryKeys } from "@/api";
import { useDebounced } from "@/shared/hooks/useDebounced";
import { errorText, useI18n } from "@/shared/i18n";

import { UserRow } from "./UserRow";

const PAGE_SIZE = 20;

export function UsersTab({ adminId }: { adminId: number }) {
  const { t } = useI18n();
  const [search, setSearch] = useState("");
  const query = useDebounced(search.trim());

  const users = useInfiniteQuery({
    queryKey: queryKeys.admin.users(query),
    queryFn: ({ pageParam }) => api.admin.users(query, pageParam, PAGE_SIZE),
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
              <Alert.Description>{errorText(t, errorCode(users.error))}</Alert.Description>
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
