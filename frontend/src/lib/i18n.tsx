import { createContext, useContext, type ReactNode } from "react";

const en = {
  "profile.admin": "Admin",
  "profile.telegramId": "Telegram ID",
  "profile.language": "Language",
  "profile.joined": "Joined",
  "profile.openAdmin": "Open admin panel",
  "profile.title": "Profile",

  "admin.title": "Admin panel",
  "admin.subtitle": "Bot users and settings",
  "admin.tab.overview": "Overview",
  "admin.tab.users": "Users",
  "admin.tab.settings": "Settings",

  "stats.total": "Total users",
  "stats.active": "Reachable",
  "stats.newDay": "New today",
  "stats.newWeek": "New this week",
  "stats.banned": "Banned",
  "stats.blocked": "Blocked the bot",
  "stats.audience": "Audience",
  "stats.growth": "New users",
  "stats.reachableOf": "{count} can receive messages",

  "users.title": "Users",
  "users.search": "Search by name, @username or ID",
  "users.empty": "No users found",
  "users.shown": "Shown {shown} of {total}",
  "users.loadMore": "Load more",
  "users.banned": "Banned",
  "users.blocked": "Blocked bot",
  "users.ban": "Ban",
  "users.unban": "Unban",
  "users.banTitle": "Ban {name}?",
  "users.banText": "The bot and this app will ignore the user until you unban them.",
  "users.cancel": "Cancel",
  "users.banned.toast": "{name} is banned",
  "users.unbanned.toast": "{name} is unbanned",

  "settings.title": "Bot mode",
  "settings.description": "Applies to the bot and this app at once",
  "settings.activeAlert": "Maintenance is on: users see a maintenance message.",
  "feedback.title": "Message to the admins",
  "feedback.description": "The admins will receive it in the bot",
  "feedback.placeholder": "Your question or suggestion",
  "feedback.send": "Send",
  "feedback.sent": "Message sent",

  "captcha.solving": "Checking that you are not a robot…",
  "captcha.ready": "Verification passed",
  "captcha.error": "Verification failed",

  "settings.maintenance": "Maintenance mode",
  "settings.maintenanceText":
    "Only admins can use the bot and this app. Users see a maintenance message.",
  "settings.saved": "Saved",

  "error.title": "Something went wrong",
  "error.title.maintenance": "Maintenance",
  "error.title.banned": "Access restricted",
  "error.retry": "Try again",
  "error.network_error": "No connection to the server. Check your network and try again.",
  "error.server_error": "The server returned an error. Try again later.",
  "error.banned": "Your access to this app is restricted.",
  "error.maintenance": "The bot is under maintenance. Please come back later.",
  "error.init_data_expired": "The session has expired. Close the app and open it again.",
  "error.invalid_init_data": "Could not verify your Telegram account. Reopen the app.",
  "error.missing_init_data": "Could not verify your Telegram account. Reopen the app.",
  "error.admin_only": "This section is available to admins only.",
  "error.cannot_ban_admin": "Admins cannot be banned.",
  "error.user_not_found": "User not found.",
  "error.captcha_required": "Please wait for the verification to finish.",
  "error.captcha_invalid": "Verification failed. Try again.",
  "error.captcha_expired": "Verification expired. Try again.",
  "error.captcha_used": "Verification expired. Try again.",

  "outside.title": "Open in Telegram",
  "outside.text": "This app works inside Telegram. Open it from the bot menu.",
};

type Key = keyof typeof en;

const ru: Record<Key, string> = {
  "profile.admin": "Админ",
  "profile.telegramId": "Telegram ID",
  "profile.language": "Язык",
  "profile.joined": "С нами с",
  "profile.openAdmin": "Открыть админ-панель",
  "profile.title": "Профиль",

  "admin.title": "Админ-панель",
  "admin.subtitle": "Пользователи и настройки бота",
  "admin.tab.overview": "Обзор",
  "admin.tab.users": "Пользователи",
  "admin.tab.settings": "Настройки",

  "stats.total": "Всего",
  "stats.active": "Доступны",
  "stats.newDay": "Новых за сутки",
  "stats.newWeek": "Новых за неделю",
  "stats.banned": "Забанены",
  "stats.blocked": "Заблокировали бота",
  "stats.audience": "Аудитория",
  "stats.growth": "Новые пользователи",
  "stats.reachableOf": "{count} могут получать сообщения",

  "users.title": "Пользователи",
  "users.search": "Поиск по имени, @username или ID",
  "users.empty": "Никого не нашлось",
  "users.shown": "Показано {shown} из {total}",
  "users.loadMore": "Показать ещё",
  "users.banned": "Забанен",
  "users.blocked": "Заблокировал бота",
  "users.ban": "Забанить",
  "users.unban": "Разбанить",
  "users.banTitle": "Забанить {name}?",
  "users.banText": "Бот и приложение будут игнорировать пользователя, пока вы его не разбаните.",
  "users.cancel": "Отмена",
  "users.banned.toast": "{name} забанен",
  "users.unbanned.toast": "{name} разбанен",

  "settings.title": "Режим работы",
  "settings.description": "Действует сразу на бота и приложение",
  "settings.activeAlert": "Техобслуживание включено: пользователи видят сообщение о работах.",
  "feedback.title": "Написать администрации",
  "feedback.description": "Сообщение придёт админам в боте",
  "feedback.placeholder": "Ваш вопрос или предложение",
  "feedback.send": "Отправить",
  "feedback.sent": "Сообщение отправлено",

  "captcha.solving": "Проверяем, что вы не робот…",
  "captcha.ready": "Проверка пройдена",
  "captcha.error": "Не удалось пройти проверку",

  "settings.maintenance": "Техобслуживание",
  "settings.maintenanceText":
    "Ботом и приложением могут пользоваться только админы. Остальные видят сообщение о работах.",
  "settings.saved": "Сохранено",

  "error.title": "Что-то пошло не так",
  "error.title.maintenance": "Технические работы",
  "error.title.banned": "Доступ ограничен",
  "error.retry": "Повторить",
  "error.network_error": "Нет связи с сервером. Проверьте интернет и попробуйте снова.",
  "error.server_error": "Сервер вернул ошибку. Попробуйте позже.",
  "error.banned": "Доступ к приложению ограничен.",
  "error.maintenance": "Бот на техническом обслуживании. Загляните позже.",
  "error.init_data_expired": "Сессия устарела. Закройте приложение и откройте снова.",
  "error.invalid_init_data": "Не удалось проверить аккаунт Telegram. Откройте приложение заново.",
  "error.missing_init_data": "Не удалось проверить аккаунт Telegram. Откройте приложение заново.",
  "error.admin_only": "Раздел доступен только админам.",
  "error.cannot_ban_admin": "Админа забанить нельзя.",
  "error.user_not_found": "Пользователь не найден.",
  "error.captcha_required": "Дождитесь окончания проверки.",
  "error.captcha_invalid": "Проверка не пройдена. Попробуйте ещё раз.",
  "error.captcha_expired": "Проверка устарела. Попробуйте ещё раз.",
  "error.captcha_used": "Проверка устарела. Попробуйте ещё раз.",

  "outside.title": "Откройте в Telegram",
  "outside.text": "Приложение работает внутри Telegram. Откройте его из меню бота.",
};

const dictionaries = { en, ru } as const;
export type Lang = keyof typeof dictionaries;

/** `ru_ru`, `ru`, `ru-RU` -> `ru`; unknown languages fall back to English. */
export function toLang(code: string | undefined | null): Lang {
  const prefix = (code ?? "").slice(0, 2).toLowerCase();
  return prefix in dictionaries ? (prefix as Lang) : "en";
}

export type Translate = (key: Key, params?: Record<string, string | number>) => string;

function makeTranslate(lang: Lang): Translate {
  return (key, params) => {
    let text: string = dictionaries[lang][key] ?? en[key];
    for (const [name, value] of Object.entries(params ?? {})) {
      text = text.replaceAll(`{${name}}`, String(value));
    }
    return text;
  };
}

const I18nContext = createContext<{ lang: Lang; t: Translate }>({
  lang: "en",
  t: makeTranslate("en"),
});

export function I18nProvider({ lang, children }: { lang: Lang; children: ReactNode }) {
  return (
    <I18nContext.Provider value={{ lang, t: makeTranslate(lang) }}>{children}</I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}

/** Translation for an API error code, with a generic fallback. */
export function errorText(t: Translate, detail: string): string {
  const key = `error.${detail}` as Key;
  return key in en ? t(key) : t("error.server_error");
}
