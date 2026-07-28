import datetime
import pathlib
import zoneinfo
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette_admin.logging import get_logger
from starlette_admin.utils.countries import countries_codes

_log = get_logger(__name__)

DEFAULT_LOCALE = "en"
DEFAULT_TIMEZONE = "UTC"
DEFAULT_DB_TIMEZONE = "UTC"
SUPPORTED_LOCALES = [
    "de",  # German
    "en",  # English
    "fr",  # French
    "pt",  # Portuguese
    "ru",  # Russian
    "tr",  # Turkish
    "zh",  # Chinese (Simplified)
    "zh_Hant",  # Traditional Chinese
]

_current_timezone: ContextVar[str] = ContextVar(
    "current_timezone", default=DEFAULT_TIMEZONE
)
_current_database_timezone: ContextVar[str] = ContextVar(
    "current_database_timezone", default=DEFAULT_DB_TIMEZONE
)
_timezone_conversion_enabled: ContextVar[bool] = ContextVar(
    "timezone_conversion_enabled", default=False
)


@lru_cache(maxsize=512)
def _validate_timezone(timezone: str, default: str = DEFAULT_TIMEZONE) -> str:
    try:
        zoneinfo.ZoneInfo(timezone)
        return timezone
    except zoneinfo.ZoneInfoNotFoundError:
        return default


def set_timezone(timezone: str) -> None:
    validated = _validate_timezone(timezone, DEFAULT_TIMEZONE)
    _current_timezone.set(validated)
    _timezone_conversion_enabled.set(True)


def get_timezone() -> str:
    return _current_timezone.get()


def get_tzinfo() -> datetime.tzinfo:
    return zoneinfo.ZoneInfo(get_timezone())


def set_database_timezone(timezone: str) -> None:
    validated = _validate_timezone(timezone, DEFAULT_DB_TIMEZONE)
    _current_database_timezone.set(validated)
    _timezone_conversion_enabled.set(True)


def get_database_timezone() -> str:
    return _current_database_timezone.get()


def get_database_tzinfo() -> datetime.tzinfo:
    return zoneinfo.ZoneInfo(get_database_timezone())


def is_timezone_conversion_enabled() -> bool:
    """Check if timezone conversion is enabled."""
    return _timezone_conversion_enabled.get()


try:
    from babel import Locale, dates
    from babel.dates import get_timezone_name
    from babel.support import LazyProxy, NullTranslations, Translations

    def get_timezone_display_name(timezone: str, show_offset: bool = False) -> str:
        tz = zoneinfo.ZoneInfo(timezone)
        tz_name = get_timezone_name(tz, locale=get_locale())

        if not show_offset:
            return tz_name

        # Get UTC offset.
        now = datetime.datetime.now(tz)
        offset = now.strftime("%z")
        formatted_offset = f"UTC{offset[:3]}:{offset[3:]}"

        return f"{tz_name} ({formatted_offset})"

    translations: dict[str, NullTranslations] = {
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

    def register_translation_catalog(package: str, domain: str = "admin") -> None:
        """Merge the compiled catalogs shipped under ``<package>/translations``
        into the active catalogs.

        For each supported locale whose MO file is present, the catalog is
        loaded and merged into ``translations[locale]``; later calls win for
        shared message ids. Used at ``Admin`` construction to fold plugin and
        theme catalogs on top of the core ones. No-op when ``package`` ships no
        ``translations/`` folder.
        """
        import importlib.resources

        try:
            folder = importlib.resources.files(package) / "translations"
        except TypeError:
            # `package` is a module, not a package (no translations/ to ship).
            return
        if not folder.is_dir():
            return
        for locale in SUPPORTED_LOCALES:
            mo = folder / locale / "LC_MESSAGES" / f"{domain}.mo"
            if not mo.is_file():
                continue
            with mo.open("rb") as fp:
                extra = Translations(fp=fp, domain=domain)
            target = translations[locale]
            if isinstance(target, Translations):
                target.merge(extra)
            elif isinstance(extra, Translations):
                translations[locale] = extra

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
        # Returns a `LazyProxy`, which behaves like a `str` but defers
        # translation until the value is used, so the locale in effect at
        # render time is applied rather than the one active at call time.
        return LazyProxy(  # ty: ignore[invalid-return-type]
            gettext, message, enable_cache=False
        )

    def format_datetime(
        datetime: datetime.datetime,
        format: str | None = None,
        tzinfo: Any = None,
    ) -> str:
        return dates.format_datetime(datetime, format or "medium", tzinfo, get_locale())

    def format_date(date: datetime.date, format: str | None = None) -> str:
        return dates.format_date(date, format or "medium", get_locale())

    def format_time(
        time: datetime.time,
        format: str | None = None,
        tzinfo: Any = None,
    ) -> str:
        return dates.format_time(time, format or "medium", tzinfo, get_locale())

    def get_countries_list() -> list[tuple[str, str]]:
        locale = Locale.parse(get_locale())
        return [(x, locale.territories[x]) for x in countries_codes]

    def get_currencies_list() -> list[tuple[str, str]]:
        locale = Locale.parse(get_locale())
        return [(str(x), f"{x} - {locale.currencies[x]}") for x in locale.currencies]

    def get_locale_display_name(locale: str) -> str:
        return (Locale(locale).display_name or locale).capitalize()

except ImportError:
    # Provide i18n support even if Babel is not installed.

    def register_translation_catalog(package: str, domain: str = "admin") -> None:
        return None

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
        datetime: datetime.datetime,
        format: str | None = None,
        tzinfo: Any = None,
    ) -> str:
        if tzinfo is not None:
            datetime = datetime.astimezone(tzinfo)

        return datetime.strftime(format or "%B %d, %Y %H:%M:%S")

    def format_date(date: datetime.date, format: str | None = None) -> str:
        return date.strftime(format or "%B %d, %Y")

    def format_time(
        time: datetime.time, format: str | None = None, tzinfo: Any = None
    ) -> str:
        return time.strftime(format or "%H:%M:%S")

    def get_countries_list() -> list[tuple[str, str]]:
        raise NotImplementedError()

    def get_currencies_list() -> list[tuple[str, str]]:
        raise NotImplementedError()

    def get_locale_display_name(locale: str) -> str:
        raise NotImplementedError()

    def get_timezone_display_name(timezone: str, show_offset: bool = False) -> str:
        raise NotImplementedError()


@dataclass
class I18nConfig:
    """i18n configuration for your admin interface."""

    default_locale: str = DEFAULT_LOCALE
    language_cookie_name: str | None = "language"
    language_header_name: str | None = "Accept-Language"
    language_switcher: list[str] | None = None


@dataclass
class TimezoneConfig:
    """Timezone configuration for your admin interface."""

    default_timezone: str = DEFAULT_TIMEZONE
    timezone_cookie_name: str | None = "timezone"
    database_timezone: str = DEFAULT_DB_TIMEZONE
    timezone_switcher: list[str] | None = None

    # If True, the user's locale-based timezone will be used
    # instead of the `default_timezone` (when available).
    use_user_locale_timezone: bool = True


class LocaleMiddleware:
    def __init__(self, app: ASGIApp, i18n_config: I18nConfig) -> None:
        self.app = app
        self.i18n_config = i18n_config

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        conn = HTTPConnection(scope)
        locale: str | None = self.i18n_config.default_locale
        if (
            self.i18n_config.language_cookie_name
            and conn.cookies.get(self.i18n_config.language_cookie_name, None)
            in SUPPORTED_LOCALES
        ):
            """Detect locale in cookies."""
            locale = conn.cookies.get(self.i18n_config.language_cookie_name)
        elif (
            self.i18n_config.language_header_name
            and conn.headers.get(self.i18n_config.language_header_name, None)
            in SUPPORTED_LOCALES
        ):
            """Detect locale in headers."""
            locale = conn.headers.get(self.i18n_config.language_header_name)
        set_locale(locale or DEFAULT_LOCALE)
        _log.debug(
            "LocaleMiddleware: resolved locale=%r for %s %s",
            get_locale(),
            scope.get("method"),
            scope.get("path"),
        )
        await self.app(scope, receive, send)


class TimezoneMiddleware:
    def __init__(self, app: ASGIApp, timezone_config: TimezoneConfig) -> None:
        self.app = app
        self.timezone_config = timezone_config

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        conn = HTTPConnection(scope)

        timezone = self.timezone_config.default_timezone

        if self.timezone_config.timezone_cookie_name:
            cookie_timezone = conn.cookies.get(
                self.timezone_config.timezone_cookie_name
            )
            if cookie_timezone:
                timezone = cookie_timezone

        set_timezone(timezone)
        set_database_timezone(self.timezone_config.database_timezone)
        _log.debug(
            "TimezoneMiddleware: resolved timezone=%r db_timezone=%r for %s %s",
            timezone,
            self.timezone_config.database_timezone,
            scope.get("method"),
            scope.get("path"),
        )

        await self.app(scope, receive, send)
