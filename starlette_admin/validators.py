"""Reusable field validators.

Design and API are inspired by wtforms.validators:
https://wtforms.readthedocs.io/en/3.1.x/validators/#built-in-validators

A validator is a callable ``(request, field, value, form_values)`` that raises
`ValueError` to reject the value and returns ``None`` to accept it. Validators
may be sync or async. They are attached to a field through
``BaseField.validators`` and run by
[BaseField.validate][starlette_admin.fields.BaseField.validate] after the
built-in ``required`` check, in order, stopping at the first error.

For [FileField][starlette_admin.fields.FileField] and its subclasses, ``value``
is a single Starlette `UploadFile`; validators run once per uploaded file.
Every other field receives its parsed form value (relation fields receive
primary keys, multi-value fields receive the whole list).

``form_values`` is the full submitted data, keyed by field name, parsed from
the form (or import row) before validation started; use it for validators
that depend on another field's value.

Each factory below builds a configured validator, e.g.
``StringField("title", validators=[length(min=3)])``.
"""

import inspect
import ipaddress
import re
import uuid as _uuid
from collections.abc import Awaitable, Callable, Collection
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from starlette.requests import Request
from starlette_admin.i18n import lazy_gettext as _
from starlette_admin.logging import get_logger

if TYPE_CHECKING:
    from starlette_admin.fields import BaseField

_log = get_logger(__name__)

Validator = Callable[
    [Request, "BaseField", Any, "dict[str, Any]"], "None | Awaitable[None]"
]


def length(
    min: int = -1,
    max: int = -1,
    message: str | None = None,
) -> Validator:
    """Requires ``min <= len(value) <= max``. Unset bounds are not checked."""
    assert min != -1 or max != -1, "At least one of `min` or `max` must be set"

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        size = len(value)
        if size < min or (max != -1 and size > max):
            _log.debug(
                "length: field %r has %d characters (min=%d, max=%d)",
                field.name,
                size,
                min,
                max,
            )
            if message is not None:
                raise ValueError(message)
            if max == -1:
                raise ValueError(
                    _("Ensure this value has at least %(min)d characters")
                    % {"min": min}
                )
            if min == -1:
                raise ValueError(
                    _("Ensure this value has at most %(max)d characters") % {"max": max}
                )
            raise ValueError(
                _("Ensure this value has between %(min)d and %(max)d characters")
                % {"min": min, "max": max}
            )

    return validate


def number_range(
    min: float | None = None,
    max: float | None = None,
    message: str | None = None,
) -> Validator:
    """Requires ``min <= value <= max``. Unset bounds are not checked."""
    assert min is not None or max is not None, (
        "At least one of `min` or `max` must be set"
    )

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if (min is not None and value < min) or (max is not None and value > max):
            _log.debug(
                "number_range: field %r value %r out of range (min=%s, max=%s)",
                field.name,
                value,
                min,
                max,
            )
            if message is not None:
                raise ValueError(message)
            if max is None:
                raise ValueError(
                    _("Ensure this value is at least %(min)s") % {"min": min}
                )
            if min is None:
                raise ValueError(
                    _("Ensure this value is at most %(max)s") % {"max": max}
                )
            raise ValueError(
                _("Ensure this value is between %(min)s and %(max)s")
                % {"min": min, "max": max}
            )

    return validate


def number_gt(min: float, message: str | None = None) -> Validator:
    """Requires ``value > min`` (strict). For an inclusive bound, use
    [number_range][starlette_admin.validators.number_range]."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if value <= min:
            _log.debug(
                "number_gt: field %r value %r is not greater than %s",
                field.name,
                value,
                min,
            )
            raise ValueError(
                message or _("Ensure this value is greater than %(min)s") % {"min": min}
            )

    return validate


def number_lt(max: float, message: str | None = None) -> Validator:
    """Requires ``value < max`` (strict). For an inclusive bound, use
    [number_range][starlette_admin.validators.number_range]."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if value >= max:
            _log.debug(
                "number_lt: field %r value %r is not less than %s",
                field.name,
                value,
                max,
            )
            raise ValueError(
                message or _("Ensure this value is less than %(max)s") % {"max": max}
            )

    return validate


def date_range(
    min: Any = None,
    max: Any = None,
    message: str | None = None,
) -> Validator:
    """Requires ``min <= value <= max``. Unset bounds are not checked.

    Bounds must be comparable with the field's parsed value (`date`, `datetime`,
    `time`, or Arrow, matching the field type). A bound may also be a zero-argument
    callable returning the bound, evaluated on each validation, e.g.
    ``date_range(min=datetime.date.today)`` to reject past dates.
    """
    assert min is not None or max is not None, (
        "At least one of `min` or `max` must be set"
    )

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        min_value = min() if callable(min) else min
        max_value = max() if callable(max) else max
        if (min_value is not None and value < min_value) or (
            max_value is not None and value > max_value
        ):
            _log.debug(
                "date_range: field %r value %r out of range (min=%s, max=%s)",
                field.name,
                value,
                min_value,
                max_value,
            )
            if message is not None:
                raise ValueError(message)
            if max_value is None:
                raise ValueError(
                    _("Ensure this value is not before %(min)s") % {"min": min_value}
                )
            if min_value is None:
                raise ValueError(
                    _("Ensure this value is not after %(max)s") % {"max": max_value}
                )
            raise ValueError(
                _("Ensure this value is between %(min)s and %(max)s")
                % {"min": min_value, "max": max_value}
            )

    return validate


def regexp(
    pattern: str | re.Pattern[str],
    flags: int = 0,
    message: str | None = None,
) -> Validator:
    """Requires the value to match `pattern` (via `re.match`)."""
    compiled = re.compile(pattern, flags) if isinstance(pattern, str) else pattern

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if compiled.match(str(value)) is None:
            _log.debug(
                "regexp: field %r value %r does not match %r",
                field.name,
                value,
                compiled.pattern,
            )
            raise ValueError(message or _("Invalid input"))

    return validate


def disallow(
    pattern: str | re.Pattern[str],
    flags: int = 0,
    message: str | None = None,
) -> Validator:
    """Rejects values containing a match for `pattern` (via `re.search`), the
    inverse of [regexp][starlette_admin.validators.regexp]. Useful to block
    unwanted content, e.g. ``disallow(r"<[^>]+>")`` to reject HTML tags."""
    compiled = re.compile(pattern, flags) if isinstance(pattern, str) else pattern

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if compiled.search(str(value)) is not None:
            _log.debug(
                "disallow: field %r value %r matches disallowed pattern %r",
                field.name,
                value,
                compiled.pattern,
            )
            raise ValueError(message or _("Invalid input"))

    return validate


_MAC_ADDRESS_RE = re.compile(
    r"^[0-9a-f]{2}([:-])(?:[0-9a-f]{2}\1){4}[0-9a-f]{2}$", re.IGNORECASE
)


def mac_address(message: str | None = None) -> Validator:
    """Requires the value to be a valid MAC address, six pairs of hex digits
    separated consistently by ``:`` or ``-``."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if _MAC_ADDRESS_RE.match(str(value)) is None:
            _log.debug("mac_address: field %r cannot parse %r", field.name, value)
            raise ValueError(message or _("Invalid MAC address"))

    return validate


_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SLUG_UNDERSCORE_RE = re.compile(r"^[a-z0-9_]+(?:-[a-z0-9_]+)*$")


def slug(allow_underscores: bool = False, message: str | None = None) -> Validator:
    """Requires the value to be a URL-safe slug: lowercase letters, digits, and
    single hyphens between segments. `allow_underscores` also permits ``_``."""
    pattern = _SLUG_UNDERSCORE_RE if allow_underscores else _SLUG_RE

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if pattern.match(str(value)) is None:
            _log.debug("slug: field %r rejected %r", field.name, value)
            raise ValueError(message or _("Invalid slug"))

    return validate


_COLOR_RES = {
    "hex": re.compile(
        r"^#(?:[0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$", re.IGNORECASE
    ),
    "rgb": re.compile(
        r"^rgba?\(\s*(?:25[0-5]|2[0-4]\d|1\d\d|\d\d?)\s*"
        r"(?:,\s*(?:25[0-5]|2[0-4]\d|1\d\d|\d\d?)\s*){2}"
        r"(?:,\s*(?:0|1|0?\.\d+)\s*)?\)$",
        re.IGNORECASE,
    ),
    "hsl": re.compile(
        r"^hsla?\(\s*\d{1,3}(?:\.\d+)?\s*"
        r"(?:,\s*\d{1,3}(?:\.\d+)?%\s*){2}"
        r"(?:,\s*(?:0|1|0?\.\d+)\s*)?\)$",
        re.IGNORECASE,
    ),
}


def color(formats: Collection[str] = ("hex",), message: str | None = None) -> Validator:
    """Requires the value to be a CSS color in one of `formats`: ``"hex"``
    (``#rgb``, ``#rgba``, ``#rrggbb``, or ``#rrggbbaa``), ``"rgb"`` (``rgb()``
    or ``rgba()``), and ``"hsl"`` (``hsl()`` or ``hsla()``)."""
    unknown = set(formats) - _COLOR_RES.keys()
    assert formats and not unknown, "`formats` must be a subset of: hex, rgb, hsl"
    patterns = [_COLOR_RES[fmt] for fmt in formats]

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        raw = str(value)
        if not any(pattern.match(raw) for pattern in patterns):
            _log.debug(
                "color: field %r value %r matches none of formats %r",
                field.name,
                value,
                formats,
            )
            raise ValueError(message or _("Invalid color"))

    return validate


def email(message: str | None = None, **options: Any) -> Validator:
    """Requires the value to be a valid email address, checked with the
    `email-validator` package (``pip install starlette-admin[email]``).

    `options` are forwarded to ``email_validator.validate_email``. Deliverability
    (DNS/MX) checks are disabled by default; pass ``check_deliverability=True``
    to enable them.
    """
    options.setdefault("check_deliverability", False)

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        try:
            from email_validator import EmailNotValidError, validate_email
        except ImportError as exc:
            raise ImportError(
                "The 'email-validator' package is required to use the 'email' "
                "validator. Install it with: pip install starlette-admin[email]"
            ) from exc

        try:
            validate_email(str(value), **options)
        except EmailNotValidError as exc:
            _log.debug("email: field %r rejected %r: %s", field.name, value, exc)
            raise ValueError(message or _("Invalid email address")) from None

    return validate


_URL_UNSAFE_CHARS = ("\t", "\r", "\n")
_URL_DOMAIN_LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
_URL_TLD_RE = re.compile(
    r"^(?!-)(?:[a-z-]{2,63}|xn--[a-z0-9]{1,59})(?<!-)$", re.IGNORECASE
)


def _url_host_is_domain(hostname: str) -> bool:
    labels = hostname.rstrip(".").split(".")
    if len(labels) < 2:
        return False
    *subdomains, tld = labels
    return bool(_URL_TLD_RE.match(tld)) and all(
        _URL_DOMAIN_LABEL_RE.match(label) for label in subdomains
    )


def _is_domain_name(name: str) -> bool:
    if _url_host_is_domain(name):
        return True
    try:
        ascii_name = name.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    return _url_host_is_domain(ascii_name)


def _url_host_is_valid(hostname: str) -> bool:
    if hostname == "localhost":
        return True
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    return _is_domain_name(hostname)


def url(
    schemes: Collection[str] | None = ("http", "https", "ftp", "ftps"),
    max_length: int = 2048,
    message: str | None = None,
) -> Validator:
    """Requires the value to be an absolute URL with a valid scheme and host.

    `schemes` restricts the accepted schemes (default ``http``/``https``/``ftp``/
    ``ftps``); pass `None` to accept any scheme. The host must be `localhost`, a
    valid IPv4/IPv6 address, or a domain name with a valid TLD (internationalized
    domains are accepted via IDNA encoding). `max_length` rejects overly long
    values before parsing, to avoid pathological input.
    """
    allowed = {s.lower() for s in schemes} if schemes is not None else None

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        raw = str(value)
        if len(raw) > max_length or any(c in raw for c in _URL_UNSAFE_CHARS):
            _log.debug(
                "url: field %r value exceeds max_length or contains unsafe characters",
                field.name,
            )
            raise ValueError(message or _("Invalid URL"))

        try:
            parts = urlsplit(raw)
            hostname = parts.hostname
        except ValueError:
            _log.debug("url: field %r value %r failed to parse", field.name, raw)
            raise ValueError(message or _("Invalid URL")) from None

        if (
            not parts.scheme
            or not hostname
            or (allowed is not None and parts.scheme.lower() not in allowed)
            or not _url_host_is_valid(hostname)
        ):
            _log.debug(
                "url: field %r rejected %r (scheme=%r, host=%r)",
                field.name,
                raw,
                parts.scheme,
                hostname,
            )
            raise ValueError(message or _("Invalid URL"))

    return validate


def uuid(version: int | None = None, message: str | None = None) -> Validator:
    """Requires the value to be a valid UUID. If `version` is set (1, 3, 4, or 5),
    also requires the UUID to be of that version."""
    assert version in (None, 1, 3, 4, 5), "`version` must be 1, 3, 4, 5 or None"

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        try:
            parsed = _uuid.UUID(str(value))
        except (ValueError, AttributeError, TypeError):
            _log.debug("uuid: field %r cannot parse %r", field.name, value)
            raise ValueError(message or _("Invalid UUID")) from None
        if version is not None and parsed.version != version:
            _log.debug(
                "uuid: field %r expected version %d, got %s",
                field.name,
                version,
                parsed.version,
            )
            raise ValueError(
                message
                or _("Invalid UUID, expected version %(version)d")
                % {"version": version}
            )

    return validate


def ip_address(
    ipv4: bool = True, ipv6: bool = False, message: str | None = None
) -> Validator:
    """Requires the value to be a valid IP address. `ipv4` and `ipv6` control
    which address families are accepted; at least one must be `True`."""
    assert ipv4 or ipv6, "At least one of `ipv4` or `ipv6` must be True"

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        try:
            parsed = ipaddress.ip_address(str(value))
        except ValueError:
            _log.debug("ip_address: field %r cannot parse %r", field.name, value)
            raise ValueError(message or _("Invalid IP address")) from None
        if (parsed.version == 4 and not ipv4) or (parsed.version == 6 and not ipv6):
            _log.debug(
                "ip_address: field %r rejected IPv%d address (ipv4=%s, ipv6=%s)",
                field.name,
                parsed.version,
                ipv4,
                ipv6,
            )
            raise ValueError(
                message
                or _("Invalid IPv%(version)d address") % {"version": parsed.version}
            )

    return validate


def any_of(values: Collection[Any], message: str | None = None) -> Validator:
    """Requires the value to be one of `values`."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if value not in values:
            _log.debug(
                "any_of: field %r value %r not in allowed values",
                field.name,
                value,
            )
            raise ValueError(
                message
                or _("Invalid value, must be one of: %(values)s")
                % {"values": ", ".join(map(str, values))}
            )

    return validate


def none_of(values: Collection[Any], message: str | None = None) -> Validator:
    """Requires the value to not be any of `values`."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        if value in values:
            _log.debug(
                "none_of: field %r value %r is a disallowed value",
                field.name,
                value,
            )
            raise ValueError(
                message
                or _("Invalid value, can't be any of: %(values)s")
                % {"values": ", ".join(map(str, values))}
            )

    return validate


def items(*validators: Validator) -> Validator:
    """Applies `validators` to each element of a multi-value field's list
    (e.g. [TagsField][starlette_admin.fields.TagsField]), stopping at the first
    error. Example: ``TagsField("tags", validators=[items(length(min=3))])``."""
    assert validators, "At least one validator must be provided"

    async def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        for item in value:
            for validator in validators:
                result = validator(request, field, item, form_values)
                if inspect.isawaitable(result):
                    await result

    return validate


def file_size(max_size: int, message: str | None = None) -> Validator:
    """Rejects uploads larger than `max_size` bytes."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        size = value.size
        assert size is not None, "UploadFile size should be set by Starlette"
        if size > max_size:
            _log.debug(
                "file_size: field %r upload is %d bytes, maximum is %d",
                field.name,
                size,
                max_size,
            )
            raise ValueError(
                message
                or _("File is too large (%(size)d bytes; maximum is %(max)d bytes)")
                % {"size": size, "max": max_size}
            )

    return validate


def file_type(accept: str, message: str | None = None) -> Validator:
    """Rejects uploads not matching `accept`, a comma-separated list of file
    specifiers as understood by the HTML file input (e.g., ``".pdf"``,
    ``"image/*"``, ``"image/png,.svg"``)."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        filename = (value.filename or "").lower()
        content_type = (value.content_type or "").lower()
        for token in (t.strip().lower() for t in accept.split(",")):
            if not token:
                continue
            if token.startswith("."):
                if filename.endswith(token):
                    return
            elif token.endswith("/*"):
                if content_type.startswith(token[:-1]):
                    return
            elif content_type == token:
                return
        _log.debug(
            "file_type: field %r rejected %r (content type %r, accept %r)",
            field.name,
            filename,
            content_type,
            accept,
        )
        raise ValueError(
            message
            or _("File type is not allowed (accepted: %(accept)s)") % {"accept": accept}
        )

    return validate


def valid_image(message: str | None = None) -> Validator:
    """Rejects uploads that Pillow cannot verify as images."""

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        from PIL import Image

        try:
            value.file.seek(0)
            with Image.open(value.file) as img:
                img.verify()
        except Exception as exc:
            _log.debug(
                "valid_image: field %r upload failed Pillow verification: %s",
                field.name,
                exc,
            )
            raise ValueError(message or _("Upload a valid image file.")) from None
        finally:
            value.file.seek(0)

    return validate


def image_size(
    min_width: int | None = None,
    min_height: int | None = None,
    max_width: int | None = None,
    max_height: int | None = None,
    message: str | None = None,
) -> Validator:
    """Rejects image uploads whose pixel dimensions fall outside the given
    bounds. Unset bounds are not checked. Requires Pillow; uploads Pillow
    cannot open are rejected."""
    assert any(
        bound is not None for bound in (min_width, min_height, max_width, max_height)
    ), "At least one bound must be set"

    def validate(
        request: Request, field: "BaseField", value: Any, form_values: dict[str, Any]
    ) -> None:
        from PIL import Image

        try:
            value.file.seek(0)
            with Image.open(value.file) as img:
                width, height = img.size
        except Exception as exc:
            _log.debug(
                "image_size: field %r upload could not be opened: %s",
                field.name,
                exc,
            )
            raise ValueError(message or _("Upload a valid image file.")) from None
        finally:
            value.file.seek(0)

        error: str | None = None
        if min_width is not None and width < min_width:
            error = _("Image width must be at least %(min)d pixels") % {
                "min": min_width
            }
        elif max_width is not None and width > max_width:
            error = _("Image width must be at most %(max)d pixels") % {"max": max_width}
        elif min_height is not None and height < min_height:
            error = _("Image height must be at least %(min)d pixels") % {
                "min": min_height
            }
        elif max_height is not None and height > max_height:
            error = _("Image height must be at most %(max)d pixels") % {
                "max": max_height
            }
        if error is not None:
            _log.debug(
                "image_size: field %r image is %dx%d pixels: %s",
                field.name,
                width,
                height,
                error,
            )
            raise ValueError(message or error)

    return validate
