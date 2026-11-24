import { Toast } from "@heroui/react";
import { useQuery } from "@tanstack/react-query";
import { Ban, Smartphone, TriangleAlert, Wrench } from "lucide-react";
import { lazy, Suspense, useCallback, useState } from "react";

import { StatusScreen } from "./components/StatusScreen";
import { api, ApiError } from "./lib/api";
import { useBackButton, useTelegramTheme } from "./lib/hooks";
import { errorText, I18nProvider, toLang, useI18n } from "./lib/i18n";
import { getInitDataLanguage } from "./lib/telegram";
import { Profile, ProfileSkeleton } from "./screens/Profile";

type Screen = "profile" | "admin";

// Admin code is loaded only by admins
const Admin = lazy(() => import("./screens/Admin").then((m) => ({ default: m.Admin })));

const ERROR_ICONS = { banned: Ban, maintenance: Wrench } as const;

function ErrorScreen({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const { t } = useI18n();
  const detail = error instanceof ApiError ? error.detail : "server_error";
  const icon = ERROR_ICONS[detail as keyof typeof ERROR_ICONS] ?? TriangleAlert;
  const canRetry = detail !== "banned";

  return (
    <StatusScreen
      icon={icon}
      title={
        detail === "maintenance" || detail === "banned" ? t(`error.title.${detail}`) : t("error.title")
      }
      text={errorText(t, detail)}
      action={canRetry ? { label: t("error.retry"), onPress: onRetry } : undefined}
    />
  );
}

function MiniApp() {
  const [screen, setScreen] = useState<Screen>("profile");
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });

  const goBack = useCallback(() => setScreen("profile"), []);
  useBackButton(screen === "admin", goBack);

  const lang = toLang(me.data?.user.user_locale ?? getInitDataLanguage());

  let content;
  if (me.isPending) {
    content = <ProfileSkeleton />;
  } else if (me.error) {
    content = <ErrorScreen error={me.error} onRetry={() => void me.refetch()} />;
  } else if (screen === "admin" && me.data.is_admin) {
    content = (
      <Suspense fallback={<ProfileSkeleton />}>
        <Admin adminId={me.data.user.user_id} />
      </Suspense>
    );
  } else {
    content = <Profile me={me.data} onOpenAdmin={() => setScreen("admin")} />;
  }

  return (
    <I18nProvider lang={lang}>
      <main className="app-shell mx-auto w-full max-w-lg">{content}</main>
    </I18nProvider>
  );
}

export function App({ insideTelegram }: { insideTelegram: boolean }) {
  useTelegramTheme(insideTelegram);

  return (
    <>
      <Toast.Provider placement="top" />
      {insideTelegram ? (
        <MiniApp />
      ) : (
        <I18nProvider lang={toLang(navigator.language)}>
          <OutsideTelegram />
        </I18nProvider>
      )}
    </>
  );
}

function OutsideTelegram() {
  const { t } = useI18n();
  return <StatusScreen icon={Smartphone} title={t("outside.title")} text={t("outside.text")} />;
}
