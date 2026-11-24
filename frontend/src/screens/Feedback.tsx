import { Button, Card, Description, Label, TextArea, TextField, toast } from "@heroui/react";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { CaptchaStatus } from "../components/CaptchaStatus";
import { api, ApiError } from "../lib/api";
import { useCaptcha } from "../lib/captcha";
import { errorText, useI18n } from "../lib/i18n";
import { haptic } from "../lib/telegram";

const MAX_LENGTH = 2000;

/** Captcha-protected form: an example for any action that should not be automated. */
export function Feedback() {
  const { t } = useI18n();
  const [text, setText] = useState("");
  const captcha = useCaptcha();

  const send = useMutation({
    mutationFn: () => api.sendFeedback(text.trim(), captcha.payload),
    onSuccess: () => {
      haptic.success();
      toast.success(t("feedback.sent"));
      setText("");
    },
    onError: (error) => {
      haptic.error();
      toast.danger(errorText(t, error instanceof ApiError ? error.detail : "server_error"));
    },
    // A solution is single-use: prepare the next one in any case
    onSettled: () => captcha.refresh(),
  });

  const canSend = text.trim().length > 0 && captcha.isReady;

  return (
    <Card>
      <Card.Header>
        <Card.Title>{t("feedback.title")}</Card.Title>
        <Card.Description>{t("feedback.description")}</Card.Description>
      </Card.Header>

      <Card.Content className="gap-3">
        <TextField value={text} onChange={setText} maxLength={MAX_LENGTH} variant="secondary">
          <Label className="sr-only">{t("feedback.title")}</Label>
          <TextArea placeholder={t("feedback.placeholder")} rows={4} />
          <Description className="text-right tabular-nums">
            {text.length}/{MAX_LENGTH}
          </Description>
        </TextField>
        <CaptchaStatus status={captcha.status} onRetry={captcha.refresh} />
      </Card.Content>

      <Card.Footer>
        <Button
          fullWidth
          isDisabled={!canSend}
          isPending={send.isPending}
          onPress={() => send.mutate()}
        >
          {t("feedback.send")}
        </Button>
      </Card.Footer>
    </Card>
  );
}
