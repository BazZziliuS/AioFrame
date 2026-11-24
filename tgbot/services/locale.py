import json
from functools import cache
from pathlib import Path
from typing import Any

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LOCALE = "en_us"

_cache: dict[str, dict[str, Any]] = {}


def _load_locale(locale: str) -> dict[str, Any]:
    if locale in _cache:
        return _cache[locale]

    path = LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        path = LOCALES_DIR / f"{DEFAULT_LOCALE}.json"

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    _cache[locale] = data
    return data


@cache
def get_available_locales() -> tuple[str, ...]:
    return tuple(sorted(p.stem for p in LOCALES_DIR.glob("*.json")))


def _lookup(data: dict[str, Any], key: str) -> str | None:
    value: Any = data
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value if isinstance(value, str) else None


class Locale:
    def __init__(self, lang: str = DEFAULT_LOCALE):
        self._lang = lang
        self._data = _load_locale(lang)
        self._fallback = _load_locale(DEFAULT_LOCALE) if lang != DEFAULT_LOCALE else self._data

    @property
    def lang(self) -> str:
        return self._lang

    @property
    def language_code(self) -> str:
        """Two-letter code used by Telegram (`ru_ru` -> `ru`)."""
        return self._lang.split("_", 1)[0]

    def get(self, key: str, **kwargs: Any) -> str:
        value = _lookup(self._data, key)
        if value is None:
            value = _lookup(self._fallback, key)  # Fallback to default locale
        if value is None:
            return key
        return value.format(**kwargs) if kwargs else value

    def __call__(self, key: str, **kwargs: Any) -> str:
        return self.get(key, **kwargs)


@cache
def get_translations(key: str) -> frozenset[str]:
    """All translations of a key: used to match reply-keyboard buttons in any language."""
    return frozenset(Locale(lang)(key) for lang in get_available_locales())


def language_code_to_locale(language_code: str | None) -> str:
    """Map Telegram language code (`ru`, `pt-br`) to an available locale file."""
    if not language_code:
        return DEFAULT_LOCALE

    code = language_code.lower().replace("-", "_")
    locales = get_available_locales()
    if code in locales:
        return code

    prefix = code.split("_", 1)[0]
    for locale in locales:
        if locale.split("_", 1)[0] == prefix:
            return locale
    return DEFAULT_LOCALE
