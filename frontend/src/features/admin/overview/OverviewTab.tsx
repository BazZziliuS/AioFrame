import { Alert, Card, Skeleton } from "@heroui/react";
import { useQuery } from "@tanstack/react-query";

import { api, errorCode, type Stats, queryKeys } from "@/api";
import { errorText, useI18n } from "@/shared/i18n";

/** Share of reachable / banned / blocked users as one segmented bar with a legend. */
function AudienceBar({ stats }: { stats: Stats }) {
  const { t, lang } = useI18n();
  const format = new Intl.NumberFormat(lang);
  const segments = [
    { label: t("stats.active"), value: stats.active, color: "bg-success" },
    { label: t("stats.blocked"), value: stats.blocked, color: "bg-warning" },
    { label: t("stats.banned"), value: stats.banned, color: "bg-danger" },
  ];
  const total = Math.max(stats.total, 1);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex h-2 w-full gap-0.5 overflow-hidden rounded-full bg-default">
        {segments.map(
          (segment) =>
            segment.value > 0 && (
              <div
                key={segment.label}
                className={segment.color}
                style={{ width: `${(segment.value / total) * 100}%` }}
              />
            ),
        )}
      </div>
      <ul className="flex flex-col gap-2 text-sm">
        {segments.map((segment) => (
          <li key={segment.label} className="flex items-center gap-2">
            <span className={`size-2 rounded-full ${segment.color}`} />
            <span className="text-muted">{segment.label}</span>
            <span className="ml-auto font-medium tabular-nums">{format.format(segment.value)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number | undefined }) {
  const { lang } = useI18n();

  return (
    <Card>
      <Card.Header>
        <Card.Description>{label}</Card.Description>
      </Card.Header>
      <Card.Content>
        {value === undefined ? (
          <Skeleton className="h-8 w-16 rounded-md" />
        ) : (
          <span className="text-3xl font-semibold tabular-nums tracking-tight">
            {new Intl.NumberFormat(lang).format(value)}
          </span>
        )}
      </Card.Content>
    </Card>
  );
}

export function OverviewTab() {
  const { t, lang } = useI18n();
  const stats = useQuery({ queryKey: queryKeys.admin.stats, queryFn: api.admin.stats });

  if (stats.error) {
    const detail = errorCode(stats.error);
    return (
      <Alert status="danger">
        <Alert.Indicator />
        <Alert.Content>
          <Alert.Title>{t("error.title")}</Alert.Title>
          <Alert.Description>{errorText(t, detail)}</Alert.Description>
        </Alert.Content>
      </Alert>
    );
  }

  const data = stats.data;

  return (
    <div className="flex flex-col gap-3">
      <Card>
        <Card.Header>
          <Card.Description>{t("stats.audience")}</Card.Description>
          {data ? (
            <Card.Title className="text-3xl font-semibold tabular-nums tracking-tight">
              {new Intl.NumberFormat(lang).format(data.total)}
            </Card.Title>
          ) : (
            <Skeleton className="h-8 w-20 rounded-md" />
          )}
          {data && (
            <Card.Description>
              {t("stats.reachableOf", { count: new Intl.NumberFormat(lang).format(data.active) })}
            </Card.Description>
          )}
        </Card.Header>
        <Card.Content>
          {data ? <AudienceBar stats={data} /> : <Skeleton className="h-20 rounded-lg" />}
        </Card.Content>
      </Card>

      <div className="grid grid-cols-2 gap-3">
        <Metric label={t("stats.newDay")} value={data?.new_day} />
        <Metric label={t("stats.newWeek")} value={data?.new_week} />
      </div>
    </div>
  );
}
