import datetime
import pathlib
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette_admin.utils.countries import countries_codes

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = [
    "de",  # German
    "en",  # English
    "fr",  # French
    "ru",  # Russian
    "tr",  # Turkish
]


try:
    from babel import Locale, dates
    from babel.support import LazyProxy, NullTranslations, Translations

    translations: Dict[str, NullTranslations] = {
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
    _current_translation: ContextVar[NullTranslations] = ContextVar(
        "current_translation", default=translations[DEFAULT_LOCALE]
    )

    def set_locale(locale: str) -> None:
        _current_locale.set(locale if locale in translations else DEFAULT_LOCALE)
        _current_translation.set(translations[get_locale()])

    def get_locale() -> str:
        return _current_locale.get()

    def gettext(message: str) -> str:
        return _current_translation.get().ugettext(message)

    def ngettext(msgid1: str, msgid2: str, n: int) -> str:
        return _current_translation.get().ngettext(msgid1, msgid2, n)

    def lazy_gettext(message: str) -> str:
        return LazyProxy(gettext, message)  # type: ignore[return-value]

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

    def get_countries_list() -> List[Tuple[str, str]]:
        locale = Locale.parse(get_locale())
        return [(x, locale.territories[x]) for x in countries_codes]

    def get_currencies_list() -> List[Tuple[str, str]]:
        locale = Locale.parse(get_locale())
        return [(str(x), f"{x} - {locale.currencies[x]}") for x in locale.currencies]

    def get_locale_display_name(locale: str) -> str:
        return Locale(locale).display_name.capitalize()

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

    def get_countries_list() -> List[Tuple[str, str]]:
        raise NotImplementedError()

    def get_currencies_list() -> List[Tuple[str, str]]:
        raise NotImplementedError()

    def get_locale_display_name(locale: str) -> str:
        raise NotImplementedError()


@dataclass
class I18nConfig:
    """
    i18n config for your admin interface
    """

    default_locale: str = DEFAULT_LOCALE
    language_cookie_name: Optional[str] = "language"
    language_header_name: Optional[str] = "Accept-Language"
    language_switcher: Optional[List[str]] = None


class LocaleMiddleware:
    def __init__(self, app: ASGIApp, i18n_config: I18nConfig) -> None:
        self.app = app
        self.i18n_config = i18n_config

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        conn = HTTPConnection(scope)
        locale: Optional[str] = self.i18n_config.default_locale
        if (
            self.i18n_config.language_cookie_name
            and conn.cookies.get(self.i18n_config.language_cookie_name, None)
            in SUPPORTED_LOCALES
        ):
            """detect locale in cookies"""
            locale = conn.cookies.get(self.i18n_config.language_cookie_name)
        elif (
            self.i18n_config.language_header_name
            and conn.headers.get(self.i18n_config.language_header_name, None)
            in SUPPORTED_LOCALES
        ):
            """detect locale in headers"""
            locale = conn.headers.get(self.i18n_config.language_header_name)
        set_locale(locale or DEFAULT_LOCALE)
        await self.app(scope, receive, send)
