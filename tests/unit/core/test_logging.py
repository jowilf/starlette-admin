"""Unit tests for `starlette_admin.logging`."""

from __future__ import annotations

import logging

from starlette_admin.logging import configure_logging, get_logger, logger

# ── get_logger ────────────────────────────────────────────────────────────────


def test_get_logger_with_package_prefix_passthrough():
    child = get_logger("starlette_admin.base")
    assert child.name == "starlette_admin.base"


def test_get_logger_exact_package_name_returns_root_logger():
    child = get_logger("starlette_admin")
    assert child is logger


def test_get_logger_unprefixed_name_adds_namespace():
    child = get_logger("mymodule")
    assert child.name == "starlette_admin.mymodule"


# ── configure_logging ─────────────────────────────────────────────────────────


def test_configure_logging_attaches_handler():
    # Removes any previously attached handlers to ensure a clean test start.
    original_handlers = logger.handlers[:]
    original_propagate = logger.propagate
    logger.handlers.clear()
    logger.propagate = True
    configure_logging()
    assert len(logger.handlers) == 1
    assert not isinstance(logger.handlers[0], logging.NullHandler)
    assert logger.level == logging.DEBUG
    # Restores state for other tests.
    logger.handlers[:] = original_handlers
    logger.setLevel(logging.WARNING)
    logger.propagate = original_propagate


def test_configure_logging_idempotent():
    """A second call, when handlers already exist, must be a no-op."""
    original_handlers = logger.handlers[:]
    original_propagate = logger.propagate
    logger.handlers.clear()
    logger.propagate = True
    configure_logging()
    handler_before = logger.handlers[0]
    configure_logging()  # Second call: must not add another handler.
    assert len(logger.handlers) == 1
    assert logger.handlers[0] is handler_before
    # Restore.
    logger.handlers[:] = original_handlers
    logger.setLevel(logging.WARNING)
    logger.propagate = original_propagate


def test_default_state_has_null_handler_and_no_stderr_leak():
    """Before `configure_logging()` or when `debug=True`, records must not leak to `stderr` via logging's last-resort handler."""
    assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)


# ── _ColorFormatter ───────────────────────────────────────────────────────────


def test_color_formatter_outputs_colored_log_line():
    from starlette_admin.logging import _ColorFormatter

    formatter = _ColorFormatter()
    record = logging.LogRecord(
        name="starlette_admin.test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "INFO:" in formatted
    assert "hello world" in formatted
