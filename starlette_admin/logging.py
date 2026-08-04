"""
Package-level logging for starlette_admin.

All loggers in this package live under the "starlette_admin" namespace so they
inherit from a single root logger, which callers can configure like any stdlib
logger:

    logging.getLogger("starlette_admin").setLevel(logging.DEBUG)

By default a ``NullHandler`` is attached so nothing is printed until you opt in.
Without it, Python's logging module would fall back to its "handler of last
resort" and print WARNING+ records (and exception tracebacks) to stderr even
though nobody asked for them.

To quickly enable coloured console output during development, call
``configure_logging()`` before starting your server::

    from starlette_admin.logging import configure_logging
    configure_logging()          # defaults to DEBUG
    configure_logging(level=logging.INFO)  # or any stdlib level
"""

import logging
import sys

logger = logging.getLogger("starlette_admin")
# Prevent Python's logging module from falling back to its "handler of last
# resort" (a stderr StreamHandler at WARNING level) for records that reach
# this logger before the caller opts in via configure_logging() or debug=True.
# See https://docs.python.org/3/howto/logging.html#library-config
logger.addHandler(logging.NullHandler())


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the starlette_admin namespace.

    Usage in any module::

        from starlette_admin.logging import get_logger
        _log = get_logger(__name__)  # → "starlette_admin.<module>"
    """
    # Strip the package prefix if the caller passes __name__ directly so we
    # don't end up with "starlette_admin.starlette_admin.base".
    if name.startswith("starlette_admin."):
        return logging.getLogger(name)
    if name == "starlette_admin":
        return logger
    return logging.getLogger(f"starlette_admin.{name}")


_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[32m",  # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[1;31m",  # bold red
}
_RESET = "\033[0m"


class _ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, "")
        level_tag = f"{record.levelname}:"
        # Pad visible level tag to 10 chars so all levels align
        padding = " " * (10 - len(level_tag))
        colored = f"{color}{level_tag}{_RESET}{padding}"
        return f"{colored}{record.name} -  {record.getMessage()}"


def _make_dev_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_ColorFormatter())
    return handler


def configure_logging(*, level: int = logging.DEBUG) -> None:
    """Enable coloured console logging for the starlette_admin package.

    Call this once before starting your server to see admin logs in the
    terminal. Safe to call multiple times: a second call is a no-op if a
    handler is already attached.

    Args:
        level: Log level to set on the package logger (e.g. ``logging.DEBUG``,
            ``logging.INFO``). Defaults to ``logging.DEBUG``.
    """
    if any(not isinstance(h, logging.NullHandler) for h in logger.handlers):
        return
    logger.setLevel(level)
    logger.addHandler(_make_dev_handler())
    # Don't propagate to the root logger; let the user's own root config coexist
    # without double-printing starlette_admin messages.
    logger.propagate = False
