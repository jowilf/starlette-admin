"""Every `cls('...')` and `icon('...')` literal used in `templates/` must
resolve in `CoreClasses`/`CoreIcons`, so a theme that only maps roles it
restyles never renders an unresolved semantic name by accident.
"""

import re
from pathlib import Path

import pytest
from starlette_admin.theme import CoreClasses, CoreIcons

TEMPLATES_DIR = Path(__file__).parents[3] / "starlette_admin" / "templates"

CLS_CALL_RE = re.compile(r"""cls\(\s*(["'])([a-zA-Z0-9_.]+)\1\s*\)""")
ICON_CALL_RE = re.compile(r"""icon\(\s*(["'])([a-zA-Z0-9_.]+)\1\s*\)""")


def _literals(pattern: re.Pattern) -> set[str]:
    found: set[str] = set()
    for path in TEMPLATES_DIR.rglob("*.html"):
        content = path.read_text()
        for match in pattern.finditer(content):
            found.add(match.group(2))
    return found


def test_every_cls_literal_resolves_in_core_classes():
    missing = _literals(CLS_CALL_RE) - set(CoreClasses.classes)
    assert not missing, (
        f"cls() literal(s) {sorted(missing)} used in templates/ have no "
        "entry in CoreClasses; add a default so unmapped themes still "
        "render something."
    )


def test_every_icon_literal_resolves_in_core_icons():
    missing = _literals(ICON_CALL_RE) - set(CoreIcons.icons)
    assert not missing, (
        f"icon() literal(s) {sorted(missing)} used in templates/ have no "
        "entry in CoreIcons; add a default so unmapped themes still render "
        "something."
    )


@pytest.mark.parametrize("role", sorted(CoreClasses.classes))
def test_core_class_role_value_is_nonempty_string(role: str):
    assert isinstance(CoreClasses.classes[role], str)
