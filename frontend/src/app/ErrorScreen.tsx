import { Ban, Smartphone, TriangleAlert, Wrench } from "lucide-react";

import { errorCode } from "@/api";
import { errorText, useI18n } from "@/shared/i18n";
import { StatusScreen } from "@/shared/ui/StatusScreen";

const ICONS = { banned: Ban, maintenance: Wrench } as const;

/** Full-screen state for errors that block the whole app (ban, maintenance, auth, network). */
export function ErrorScreen({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { t } = useI18n();
  const code = errorCode(error);

  if (code === "banned" || code === "maintenance") {
    return (
      <StatusScreen
        icon={ICONS[code]}
        title={t(`error.title.${code}`)}
        text={errorText(t, code)}
        action={code === "maintenance" ? { label: t("error.retry"), onPress: onRetry } : undefined}
      />
    );
  }

  return (
    <StatusScreen
      icon={TriangleAlert}
      title={t("error.title")}
      text={errorText(t, code)}
      action={{ label: t("error.retry"), onPress: onRetry }}
    />
  );
}

/** Shown when the page is opened in a regular browser. */
export function OutsideTelegramScreen() {
  const { t } = useI18n();
  return <StatusScreen icon={Smartphone} title={t("outside.title")} text={t("outside.text")} />;
}
