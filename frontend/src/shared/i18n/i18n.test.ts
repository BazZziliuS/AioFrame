import { describe, expect, it } from "vitest";

import { createTranslate, errorText, toLang } from "./index";
import { en } from "./locales/en";
import { ru } from "./locales/ru";

describe("toLang", () => {
  it.each([
    ["ru", "ru"],
    ["ru_ru", "ru"],
    ["RU-ru", "ru"],
    ["en_us", "en"],
    ["de", "en"],
    [undefined, "en"],
    [null, "en"],
  ])("%s -> %s", (code, expected) => {
    expect(toLang(code)).toBe(expected);
  });
});

describe("createTranslate", () => {
  it("translates and substitutes parameters", () => {
    expect(createTranslate("ru")("users.shown", { shown: 20, total: 25 })).toBe(
      "Показано 20 из 25",
    );
  });

  it("replaces every occurrence of a parameter", () => {
    expect(createTranslate("en")("users.banTitle", { name: "Ann" })).toBe("Ban Ann?");
  });
});

describe("errorText", () => {
  const t = createTranslate("en");

  it("translates known API error codes", () => {
    expect(errorText(t, "banned")).toBe(en["error.banned"]);
  });

  it("falls back to a generic message for unknown codes", () => {
    expect(errorText(t, "something_new")).toBe(en["error.server_error"]);
  });
});

describe("dictionaries", () => {
  it("have no empty translations", () => {
    for (const dictionary of [en, ru]) {
      for (const [key, value] of Object.entries(dictionary)) {
        expect(value.trim(), key).not.toBe("");
      }
    }
  });

  it("keep the same placeholders in every language", () => {
    const placeholders = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const key of Object.keys(en) as (keyof typeof en)[]) {
      expect(placeholders(ru[key]), key).toEqual(placeholders(en[key]));
    }
  });
});
