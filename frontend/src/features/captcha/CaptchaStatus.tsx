import { Button, Spinner } from "@heroui/react";
import { ShieldCheck, TriangleAlert } from "lucide-react";

import type { CaptchaStatus as Status } from "@/features/captcha/useCaptcha";
import { useI18n } from "@/shared/i18n";

/** Compact verification state shown inside a protected form. */
export function CaptchaStatus({ status, onRetry }: { status: Status; onRetry: () => void }) {
  const { t } = useI18n();

  if (status === "disabled") return null;

  return (
    <div
      className="flex min-h-10 items-center gap-2.5 rounded-xl bg-surface-secondary px-3 py-2 text-sm"
      role="status"
      aria-live="polite"
    >
      {status === "solving" && (
        <>
          <Spinner size="sm" color="current" className="text-muted" />
          <span className="text-muted">{t("captcha.solving")}</span>
        </>
      )}
      {status === "ready" && (
        <>
          <ShieldCheck className="size-4 text-success" strokeWidth={2} />
          <span>{t("captcha.ready")}</span>
        </>
      )}
      {status === "error" && (
        <>
          <TriangleAlert className="size-4 text-danger" strokeWidth={2} />
          <span className="flex-1">{t("captcha.error")}</span>
          <Button size="sm" variant="ghost" onPress={onRetry}>
            {t("error.retry")}
          </Button>
        </>
      )}
    </div>
  );
}
