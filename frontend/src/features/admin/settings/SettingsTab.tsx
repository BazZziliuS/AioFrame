import { Alert, Card, Skeleton, Switch, toast } from "@heroui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type BotSettings, errorCode, queryKeys } from "@/api";
import { errorText, useI18n } from "@/shared/i18n";
import { haptic } from "@/shared/telegram/sdk";

const SETTINGS_KEY = queryKeys.admin.settings;

export function SettingsTab() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const settings = useQuery({ queryKey: SETTINGS_KEY, queryFn: api.admin.settings });

  const setMaintenance = useMutation({
    mutationFn: api.admin.setMaintenance,
    // Optimistic update: the switch reacts instantly, rolls back on error
    onMutate: async (value) => {
      await queryClient.cancelQueries({ queryKey: SETTINGS_KEY });
      const previous = queryClient.getQueryData<BotSettings>(SETTINGS_KEY);
      queryClient.setQueryData<BotSettings>(SETTINGS_KEY, { is_maintenance: value });
      return { previous };
    },
    onSuccess: () => {
      haptic.success();
      toast.success(t("settings.saved"));
    },
    onError: (error, _value, context) => {
      queryClient.setQueryData(SETTINGS_KEY, context?.previous);
      haptic.error();
      toast.danger(errorText(t, errorCode(error)));
    },
  });

  const isMaintenance = settings.data?.is_maintenance ?? false;

  return (
    <div className="flex flex-col gap-3">
      {isMaintenance && (
        <Alert status="warning">
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Description>{t("settings.activeAlert")}</Alert.Description>
          </Alert.Content>
        </Alert>
      )}

      <Card>
        <Card.Header>
          <Card.Title>{t("settings.title")}</Card.Title>
          <Card.Description>{t("settings.description")}</Card.Description>
        </Card.Header>
        <Card.Content>
          {settings.data ? (
            <Switch
              isSelected={isMaintenance}
              onChange={(value) => setMaintenance.mutate(value)}
              isDisabled={setMaintenance.isPending}
            >
              <Switch.Content className="w-full justify-between gap-4">
                <span className="flex flex-col gap-0.5">
                  <span className="text-sm font-medium">{t("settings.maintenance")}</span>
                  <span className="text-xs text-muted">{t("settings.maintenanceText")}</span>
                </span>
                <Switch.Control>
                  <Switch.Thumb />
                </Switch.Control>
              </Switch.Content>
            </Switch>
          ) : (
            <Skeleton className="h-12 rounded-lg" />
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
