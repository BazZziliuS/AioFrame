import pytest

from tgbot.config import Settings
from tgbot.services.locale import Locale, get_translations, language_code_to_locale


################################### CONFIG ###################################
def make_settings(**env: str) -> Settings:
    return Settings(_env_file=None, **{"bot_token": "123:abc", **env})  # type: ignore[arg-type]


def test_locale_format_and_fallback():
    ru = Locale("ru_ru")
    assert ru("start.greeting", user_name="Иван").startswith("🔸 Привет, Иван")
    assert ru("no.such.key") == "no.such.key"
    assert Locale("xx_xx")("menu.user_button") == "User button"  # unknown locale -> default


def test_all_locales_have_the_same_keys():
    import json

    from tgbot.services.locale import LOCALES_DIR

    def keys(data, prefix=""):
        for key, value in data.items():
            if isinstance(value, dict):
                yield from keys(value, f"{prefix}{key}.")
            else:
                yield f"{prefix}{key}"

    files = sorted(LOCALES_DIR.glob("*.json"))
    reference = set(keys(json.loads(files[0].read_text(encoding="utf-8"))))
    for file in files[1:]:
        assert set(keys(json.loads(file.read_text(encoding="utf-8")))) == reference, file.name


def test_translations_cover_all_languages():
    assert get_translations("menu.admin_button") == {"Admin button", "Админ панель"}


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("ru", "ru_ru"),
        ("en", "en_us"),
        ("RU", "ru_ru"),
        ("en-GB", "en_us"),
        ("de", "en_us"),
        (None, "en_us"),
    ],
)
def test_language_code_to_locale(code, expected):
    assert language_code_to_locale(code) == expected
