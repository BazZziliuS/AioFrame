import { createContext, useContext, useMemo, type ReactNode } from "react";

import { en, type TranslationKey } from "./locales/en";
import { ru } from "./locales/ru";

export type { TranslationKey };

const dictionaries = { en, ru } as const;
export type Lang = keyof typeof dictionaries;

/** `ru_ru`, `ru`, `ru-RU` -> `ru`; unknown languages fall back to English. */
export function toLang(code: string | undefined | null): Lang {
  const prefix = (code ?? "").slice(0, 2).toLowerCase();
  return prefix in dictionaries ? (prefix as Lang) : "en";
}

export type Translate = (key: TranslationKey, params?: Record<string, string | number>) => string;

export function createTranslate(lang: Lang): Translate {
  return (key, params) => {
    let text: string = dictionaries[lang][key] ?? en[key];
    for (const [name, value] of Object.entries(params ?? {})) {
      text = text.replaceAll(`{${name}}`, String(value));
    }
    return text;
  };
}

type I18nValue = { lang: Lang; t: Translate };

const I18nContext = createContext<I18nValue>({ lang: "en", t: createTranslate("en") });

export function I18nProvider({ lang, children }: { lang: Lang; children: ReactNode }) {
  const value = useMemo(() => ({ lang, t: createTranslate(lang) }), [lang]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  return useContext(I18nContext);
}

/** Translation for an API error code, with a generic fallback. */
export function errorText(t: Translate, code: string): string {
  const key = `error.${code}` as TranslationKey;
  return key in en ? t(key) : t("error.server_error");
}
