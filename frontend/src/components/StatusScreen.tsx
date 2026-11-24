import { Button } from "@heroui/react";
import type { LucideIcon } from "lucide-react";

type Props = {
  icon: LucideIcon;
  title: string;
  text: string;
  action?: { label: string; onPress: () => void };
};

/** Full-screen message: errors, maintenance, opened outside Telegram. */
export function StatusScreen({ icon: Icon, title, text, action }: Props) {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center gap-3 px-6 text-center">
      <div className="flex size-14 items-center justify-center rounded-full bg-default">
        <Icon className="size-7 text-muted" strokeWidth={1.75} />
      </div>
      <h1 className="text-lg font-semibold">{title}</h1>
      <p className="max-w-xs text-sm text-muted">{text}</p>
      {action && (
        <Button className="mt-2" variant="secondary" onPress={action.onPress}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
