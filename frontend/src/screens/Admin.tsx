import { Tabs } from "@heroui/react";

import { useI18n } from "../lib/i18n";
import { haptic } from "../lib/telegram";
import { Overview } from "./admin/Overview";
import { Settings } from "./admin/Settings";
import { Users } from "./admin/Users";

const TABS = [
  { id: "overview", label: "admin.tab.overview" },
  { id: "users", label: "admin.tab.users" },
  { id: "settings", label: "admin.tab.settings" },
] as const;

export function Admin({ adminId }: { adminId: number }) {
  const { t } = useI18n();

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">{t("admin.title")}</h1>
        <p className="text-sm text-muted">{t("admin.subtitle")}</p>
      </header>

      <Tabs defaultSelectedKey="overview" onSelectionChange={() => haptic.selection()}>
        <Tabs.ListContainer>
          <Tabs.List aria-label={t("admin.title")} className="w-full">
            {TABS.map((tab) => (
              <Tabs.Tab key={tab.id} id={tab.id} className="flex-1">
                {t(tab.label)}
                <Tabs.Indicator />
              </Tabs.Tab>
            ))}
          </Tabs.List>
        </Tabs.ListContainer>

        <Tabs.Panel id="overview" className="px-0 pt-4">
          <Overview />
        </Tabs.Panel>
        <Tabs.Panel id="users" className="px-0 pt-4">
          <Users adminId={adminId} />
        </Tabs.Panel>
        <Tabs.Panel id="settings" className="px-0 pt-4">
          <Settings />
        </Tabs.Panel>
      </Tabs>
    </div>
  );
}
