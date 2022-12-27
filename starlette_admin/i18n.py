import pathlib
from contextvars import ContextVar
from typing import Dict, Optional

from starlette.types import ASGIApp, Receive, Scope, Send

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ["en", "fr"]

try:
    from babel.support import LazyProxy, Translations

    translations: Dict[str, Translations] = {
        locale: Translations.load(
            dirname=pathlib.Path(__file__).parent.joinpath("translations/"),
            locales=[locale],
            domain="admin",
        )
        for locale in SUPPORTED_LOCALES
    }

    _current_locale: ContextVar[str] = ContextVar(
        "current_locale", default=DEFAULT_LOCALE
    )
    _current_translation: ContextVar[Translations] = ContextVar(
        "current_translation", default=translations[DEFAULT_LOCALE]
    )

    def set_locale(locale: str) -> None:
        _current_locale.set(locale if locale in translations.keys() else DEFAULT_LOCALE)
        _current_translation.set(translations[get_locale()])

    def get_locale() -> str:
        return _current_locale.get()

    def gettext(message: str) -> str:
        return _current_translation.get().ugettext(message)

    def ngettext(msgid1: str, msgid2: str, n: int) -> str:
        return _current_translation.get().ngettext(msgid1, msgid2, n)

    def lazy_gettext(message: str) -> str:
        return LazyProxy(gettext, message)  # type: ignore

    def lazy_ngettext(msgid1: str, msgid2: str, n: int) -> str:
        return LazyProxy(ngettext, msgid1, msgid2, n)  # type: ignore

except ImportError:
    # Provide i18n support even if babel is not installed

    def set_locale(locale: str) -> None:
        pass

    def get_locale() -> str:
        return DEFAULT_LOCALE

    def gettext(message: str):
        return message

    def ngettext(msgid1: str, msgid2: str, n: int) -> str:
        return msgid1 if (n == 1) else msgid2

    def lazy_gettext(message: str):
        return gettext(message)

    def lazy_ngettext(msgid1: str, msgid2: str, n: int):
        return ngettext(msgid1, msgid2, n)


class LocaleMiddleware:
    def __init__(self, app: ASGIApp, locale: Optional[str] = DEFAULT_LOCALE) -> None:
        self.app = app
        self.locale = locale

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        set_locale(self.locale)
        await self.app(scope, receive, send)
