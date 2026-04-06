import json
from pathlib import Path
from typing import Optional

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LOCALE = "en_us"

_cache: dict[str, dict] = {}


def _load_locale(locale: str) -> dict:
    if locale in _cache:
        return _cache[locale]

    path = LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        path = LOCALES_DIR / f"{DEFAULT_LOCALE}.json"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _cache[locale] = data
    return data


def get_available_locales() -> list[str]:
    return [p.stem for p in LOCALES_DIR.glob("*.json")]


class Locale:
    def __init__(self, lang: str = DEFAULT_LOCALE):
        self._lang = lang
        self._data = _load_locale(lang)
        self._fallback = (
            _load_locale(DEFAULT_LOCALE) if lang != DEFAULT_LOCALE else self._data
        )

    @property
    def lang(self) -> str:
        return self._lang

    def get(self, key: str, **kwargs) -> str:
        parts = key.split(".")
        value = self._data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = None
                break

        # Fallback to default locale
        if value is None:
            value = self._fallback
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return key

        if isinstance(value, str) and kwargs:
            return value.format(**kwargs)

        return value if isinstance(value, str) else key

    def __call__(self, key: str, **kwargs) -> str:
        return self.get(key, **kwargs)


def language_code_to_locale(language_code: Optional[str]) -> str:
    if language_code == "ru":
        return "ru_ru"
    return DEFAULT_LOCALE
