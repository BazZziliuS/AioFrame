import { Button, Card, Chip, Separator, Skeleton } from "@heroui/react";
import { ArrowRight } from "lucide-react";

import { UserAvatar } from "../components/UserAvatar";
import type { Me } from "../lib/api";
import { useI18n } from "../lib/i18n";
import { Feedback } from "./Feedback";

const LANGUAGE_NAMES: Record<string, string> = { ru: "Русский", en: "English" };

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 text-sm">
      <span className="text-muted">{label}</span>
      <span className="truncate font-medium tabular-nums">{value}</span>
    </div>
  );
}

export function Profile({ me, onOpenAdmin }: { me: Me; onOpenAdmin: () => void }) {
  const { t, lang } = useI18n();
  const { user } = me;
  const name = user.user_fullname || String(user.user_id);
  const languageCode = user.user_locale.slice(0, 2);
  const joined = new Intl.DateTimeFormat(lang, { dateStyle: "long" }).format(
    new Date(user.created_at),
  );

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">{t("profile.title")}</h1>

      <Card>
        <Card.Header className="flex-row items-center gap-3">
          <UserAvatar name={name} photoUrl={me.photo_url} size="lg" />
          <div className="min-w-0 flex-1">
            <Card.Title className="truncate">{name}</Card.Title>
            {user.user_login && <Card.Description>@{user.user_login}</Card.Description>}
          </div>
          {me.is_admin && (
            <Chip color="accent" variant="soft" size="sm">
              {t("profile.admin")}
            </Chip>
          )}
        </Card.Header>

        <Card.Content>
          <Separator />
          <InfoRow label={t("profile.telegramId")} value={String(user.user_id)} />
          <Separator />
          <InfoRow
            label={t("profile.language")}
            value={LANGUAGE_NAMES[languageCode] ?? languageCode}
          />
          <Separator />
          <InfoRow label={t("profile.joined")} value={joined} />
        </Card.Content>

        {me.is_admin && (
          <Card.Footer>
            <Button fullWidth onPress={onOpenAdmin}>
              {t("profile.openAdmin")}
              <ArrowRight className="size-4" />
            </Button>
          </Card.Footer>
        )}
      </Card>

      <Feedback />
    </div>
  );
}

export function ProfileSkeleton() {
  return (
    <div className="flex flex-col gap-4" aria-busy="true">
      <Skeleton className="h-8 w-32 rounded-lg" />
      <Card>
        <Card.Header className="flex-row items-center gap-3">
          <Skeleton className="size-12 rounded-full" />
          <div className="flex flex-1 flex-col gap-2">
            <Skeleton className="h-4 w-2/5 rounded-md" />
            <Skeleton className="h-3 w-1/4 rounded-md" />
          </div>
        </Card.Header>
        <Card.Content className="gap-4 py-2">
          <Skeleton className="h-4 w-full rounded-md" />
          <Skeleton className="h-4 w-full rounded-md" />
          <Skeleton className="h-4 w-full rounded-md" />
        </Card.Content>
      </Card>
    </div>
  );
}
