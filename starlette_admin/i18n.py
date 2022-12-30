import datetime
import pathlib
from contextvars import ContextVar
from typing import Any, Dict, Optional, Union

from starlette.types import ASGIApp, Receive, Scope, Send

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ["en", "fr"]

try:
    from babel import dates
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
        return LazyProxy(gettext, message)

    def lazy_ngettext(msgid1: str, msgid2: str, n: int) -> str:
        return LazyProxy(ngettext, msgid1, msgid2, n)

    def format_datetime(
        datetime: Union[datetime.date, datetime.time],
        format: Optional[str] = None,
        tzinfo: Any = None,
    ) -> str:
        return dates.format_datetime(datetime, format or "medium", tzinfo, get_locale())

    def format_date(date: datetime.date, format: Optional[str] = None) -> str:
        return dates.format_date(date, format or "medium", get_locale())

    def format_time(
        time: datetime.time,
        format: Optional[str] = None,
        tzinfo: Any = None,
    ) -> str:
        return dates.format_time(time, format or "medium", tzinfo, get_locale())

except ImportError:
    # Provide i18n support even if babel is not installed

    def set_locale(locale: str) -> None:
        pass

    def get_locale() -> str:
        return DEFAULT_LOCALE

    def gettext(message: str) -> str:
        return message

    def ngettext(msgid1: str, msgid2: str, n: int) -> str:
        return msgid1 if (n == 1) else msgid2

    def lazy_gettext(message: str) -> str:
        return gettext(message)

    def lazy_ngettext(msgid1: str, msgid2: str, n: int) -> str:
        return ngettext(msgid1, msgid2, n)

    def format_datetime(
        datetime: Union[datetime.date, datetime.time],
        format: Optional[str] = None,
        tzinfo: Any = None,
    ) -> str:
        return datetime.strftime(format or "%B %d, %Y %H:%M:%S")

    def format_date(date: datetime.date, format: Optional[str] = None) -> str:
        return date.strftime(format or "%B %d, %Y")

    def format_time(
        time: datetime.time, format: Optional[str] = None, tzinfo: Any = None
    ) -> str:
        return time.strftime(format or "%H:%M:%S")


class LocaleMiddleware:
    def __init__(self, app: ASGIApp, locale: str = DEFAULT_LOCALE) -> None:
        self.app = app
        self.locale = locale

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        set_locale(self.locale)
        await self.app(scope, receive, send)
