import { backButton, miniApp, themeParams, useSignal } from "@tma.js/sdk-react";
import { useEffect } from "react";

/** Any CSS color (oklch, var(), ...) -> #rrggbb, the format Telegram accepts. */
function cssColorToHex(color: string): `#${string}` | null {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 1;
  const context = canvas.getContext("2d");
  if (!context) return null;

  context.fillStyle = color;
  context.fillRect(0, 0, 1, 1);
  const [r, g, b] = context.getImageData(0, 0, 1, 1).data;
  return `#${[r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

/**
 * Follows the Telegram light/dark mode with the HeroUI theme and paints
 * the Telegram header and background with the HeroUI background color.
 */
export function useTelegramTheme(enabled: boolean): void {
  const isDark = useSignal(themeParams.isDark);

  useEffect(() => {
    if (!enabled) return;

    const root = document.documentElement;
    const theme = isDark ? "dark" : "light";
    root.classList.toggle("dark", isDark);
    root.classList.toggle("light", !isDark);
    root.dataset.theme = theme;
    root.style.colorScheme = theme;

    const background = cssColorToHex(getComputedStyle(document.body).backgroundColor);
    if (background) {
      miniApp.setHeaderColor.ifAvailable(background);
      miniApp.setBgColor.ifAvailable(background);
      miniApp.setBottomBarColor.ifAvailable(background);
    }
  }, [enabled, isDark]);
}

/** Shows Telegram's native back button while `visible`, calling `onBack` on press. */
export function useBackButton(visible: boolean, onBack: () => void): void {
  useEffect(() => {
    if (!visible || !backButton.isMounted()) return;

    backButton.show();
    const off = backButton.onClick(onBack);
    return () => {
      off();
      backButton.hide();
    };
  }, [visible, onBack]);
}
