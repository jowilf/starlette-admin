import gettext
import pathlib
from contextvars import ContextVar

DEFAULT_LOCALE = "en_US"
_current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)

translations_dir = pathlib.Path(__file__).parent.joinpath("translations/")

translations = {
    "fr_FR": gettext.translation("admin", translations_dir, ["fr_FR"]),
}


def set_locale(locale: str) -> None:
    _current_locale.set(locale if locale in translations.keys() else DEFAULT_LOCALE)


def get_locale() -> str:
    return _current_locale.get()


def _(message: str) -> str:
    translator = translations.get(get_locale(), None)
    if translator is None:
        return message
    return translator.gettext(message)


if __name__ == "__main__":
    set_locale("fr_FR")
    print(_("This is a translatable string."))
