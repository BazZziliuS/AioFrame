import { useQuery } from "@tanstack/react-query";
import { lazy, Suspense, useCallback, useState } from "react";

import { api, queryKeys } from "@/api";
import { ProfilePage } from "@/features/profile/ProfilePage";
import { ProfileSkeleton } from "@/features/profile/ProfileSkeleton";
import { I18nProvider, toLang } from "@/shared/i18n";
import { useBackButton, useTelegramTheme } from "@/shared/telegram/hooks";
import { getInitDataLanguage } from "@/shared/telegram/sdk";
import { ErrorBoundary } from "@/shared/ui/ErrorBoundary";

import { ErrorScreen, OutsideTelegramScreen } from "./ErrorScreen";

// Admin code is downloaded only by admins
const AdminPage = lazy(() =>
  import("@/features/admin/AdminPage").then((module) => ({ default: module.AdminPage })),
);

type Screen = "profile" | "admin";

function MiniApp() {
  const [screen, setScreen] = useState<Screen>("profile");
  const me = useQuery({ queryKey: queryKeys.me, queryFn: api.me });

  const openProfile = useCallback(() => setScreen("profile"), []);
  useBackButton(screen === "admin", openProfile);

  const lang = toLang(me.data?.user.user_locale ?? getInitDataLanguage());

  let content;
  if (me.isPending) {
    content = <ProfileSkeleton />;
  } else if (me.isError) {
    content = <ErrorScreen error={me.error} onRetry={() => void me.refetch()} />;
  } else if (screen === "admin" && me.data.is_admin) {
    content = (
      <Suspense fallback={<ProfileSkeleton />}>
        <AdminPage adminId={me.data.user.user_id} />
      </Suspense>
    );
  } else {
    content = <ProfilePage me={me.data} onOpenAdmin={() => setScreen("admin")} />;
  }

  return (
    <I18nProvider lang={lang}>
      <main className="app-shell mx-auto w-full max-w-lg">
        <ErrorBoundary fallback={(reset) => <ErrorScreen error={null} onRetry={reset} />}>
          {content}
        </ErrorBoundary>
      </main>
    </I18nProvider>
  );
}

export function App({ insideTelegram }: { insideTelegram: boolean }) {
  useTelegramTheme(insideTelegram);

  if (!insideTelegram) {
    return (
      <I18nProvider lang={toLang(navigator.language)}>
        <OutsideTelegramScreen />
      </I18nProvider>
    );
  }
  return <MiniApp />;
}
