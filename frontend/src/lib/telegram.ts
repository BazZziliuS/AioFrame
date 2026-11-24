import {
  backButton,
  hapticFeedback,
  init,
  isTMA,
  miniApp,
  mockTelegramEnv,
  retrieveRawInitData,
  themeParams,
  viewport,
} from "@tma.js/sdk-react";

/** Colors used when the app is opened in a regular browser during development. */
const DEV_THEME = {
  bg_color: "#17212b",
  secondary_bg_color: "#0e1621",
  section_bg_color: "#17212b",
  section_separator_color: "#0e1621",
  text_color: "#f5f5f5",
  hint_color: "#708499",
  link_color: "#6ab3f3",
  button_color: "#5288c1",
  button_text_color: "#ffffff",
  destructive_text_color: "#ec3942",
  header_bg_color: "#17212b",
  accent_text_color: "#6ab2f2",
  subtitle_text_color: "#708499",
  section_header_text_color: "#6ab3f3",
} as const;

const DEV_THEME_LIGHT = {
  bg_color: "#ffffff",
  secondary_bg_color: "#f0f0f0",
  section_bg_color: "#ffffff",
  section_separator_color: "#e7e7e7",
  text_color: "#000000",
  hint_color: "#999999",
  link_color: "#2481cc",
  button_color: "#2481cc",
  button_text_color: "#ffffff",
  destructive_text_color: "#ff3b30",
  header_bg_color: "#ffffff",
  accent_text_color: "#2481cc",
  subtitle_text_color: "#999999",
  section_header_text_color: "#2481cc",
} as const;

let mocked = false;

/** Dev only: emulate Telegram with initData signed by the backend (see frontend/.env.example). */
function mockOutsideTelegram(): void {
  const initData = import.meta.env.VITE_DEV_INIT_DATA;
  // A real client: native apps inject TelegramWebviewProxy, web clients open us in an iframe.
  // isTMA() is not enough here: it also trusts launch params saved by a previous mock.
  const realTelegram = "TelegramWebviewProxy" in window || window.parent !== window;
  if (!import.meta.env.DEV || !initData || realTelegram) return;

  mockTelegramEnv({
    launchParams: {
      tgWebAppPlatform: "tdesktop",
      tgWebAppVersion: "8.0",
      tgWebAppThemeParams: import.meta.env.VITE_DEV_THEME === "light" ? DEV_THEME_LIGHT : DEV_THEME,
      tgWebAppData: initData,
    },
  });
  mocked = true;
}

/**
 * Initializes the Telegram SDK. Returns false when the page is opened outside Telegram.
 */
export async function initTelegram(): Promise<boolean> {
  mockOutsideTelegram();
  if (!isTMA()) return false;

  try {
    init();
  } catch {
    return false; // Not a usable Telegram environment
  }

  backButton.mount.ifAvailable();
  themeParams.mount.ifAvailable();
  themeParams.bindCssVars.ifAvailable();
  miniApp.mount.ifAvailable();

  // Viewport waits for an answer from the Telegram client, which the mock does not send
  if (!mocked && viewport.mount.isAvailable()) {
    try {
      await viewport.mount();
      viewport.bindCssVars.ifAvailable();
      viewport.expand.ifAvailable();
    } catch {
      // Not critical: the app works with the default viewport
    }
  }

  miniApp.ready.ifAvailable();
  return true;
}

/** Raw initData string: sent to the backend in every request for authorization. */
export function getRawInitData(): string {
  return retrieveRawInitData() ?? "";
}

/** Telegram language of the current user (before the profile is loaded). */
export function getInitDataLanguage(): string | undefined {
  try {
    const user = new URLSearchParams(getRawInitData()).get("user");
    return user ? (JSON.parse(user) as { language_code?: string }).language_code : undefined;
  } catch {
    return undefined;
  }
}

export const haptic = {
  success: () => hapticFeedback.notificationOccurred.ifAvailable("success"),
  error: () => hapticFeedback.notificationOccurred.ifAvailable("error"),
  selection: () => hapticFeedback.selectionChanged.ifAvailable(),
};
