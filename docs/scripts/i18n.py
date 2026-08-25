"""Shared helpers for the localized docs pipeline."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import textwrap
import tomllib
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
LOCALES_DIR = DOCS_DIR / "locales"
SHARED_DIR = DOCS_DIR / "shared"
#: Files and directories synced from `shared/` into every locale content dir.
SHARED_ITEMS = ["assets", "javascripts", "stylesheets", "changelog.md"]
CONTENT_SUBDIR = "content"
SOURCE_LOCALE = "en"
EN_CONTENT_DIR = LOCALES_DIR / "en" / CONTENT_SUBDIR
REGISTRY_PATH = LOCALES_DIR / "locales.json"
#: Shared system prompt; `{name}` / `{code}` are filled in per locale at runtime.
TRANSLATIONS_PROMPT_PATH = LOCALES_DIR / "translations_prompt.md"
ROOT_CONFIG_PATH = PROJECT_ROOT / "zensical.toml"

NOTICE_TITLE = "Supervised Machine Translation"
#: Label of the per-page link pointing at the English original.
NOTICE_LINK_LABEL = "Read the original English version"
NOTICE_BODY = (
    "This content is translated using machine generation guided by "
    "human-curated glossaries and style guides. Because the text is not "
    "manually reviewed line by line, occasional errors or awkward phrasing "
    "may occur. In case of any discrepancies, the original English version "
    "is the authoritative source."
)
#: Delimit the disclosure notice block for replacement without re-parsing.
NOTICE_START_MARKER = "<!-- translation-notice:start -->"
NOTICE_END_MARKER = "<!-- translation-notice:end -->"
#: Heading line of the disclosure notice (`??? info "Title"` / warning).
NOTICE_HEADING_RE = re.compile(r'\?\?\? (?P<variant>info|warning) "[^"]*"')

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class I18nError(Exception):
    """A configuration or validation error in the docs i18n pipeline."""


# --------------------------------------------------------------------------
# Minimal TOML writer (stdlib-only, no tomli_w dependency)
# --------------------------------------------------------------------------

_TOML_BARE_KEY_RE = re.compile(r"[A-Za-z0-9_-]+")


def _toml_key(key: str) -> str:
    return (
        key if _TOML_BARE_KEY_RE.fullmatch(key) else json.dumps(key, ensure_ascii=False)
    )


def _toml_value(value: Any, indent: int = 0) -> str:
    """Serialize a value as inline TOML (arrays may span multiple lines)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        if not value:
            return "[]"
        if any(isinstance(item, dict) for item in value):
            pad = "    " * (indent + 1)
            close = "    " * indent
            items = ",\n".join(
                f"{pad}{_toml_value(item, indent + 1)}" for item in value
            )
            return f"[\n{items},\n{close}]"
        return "[" + ", ".join(_toml_value(item, indent) for item in value) + "]"
    if isinstance(value, dict):
        body = ", ".join(
            f"{_toml_key(key)} = {_toml_value(item, indent)}"
            for key, item in value.items()
        )
        return "{ " + body + " }"
    raise I18nError(f"cannot serialize {type(value).__name__} as TOML")


def _emit_toml_nav(lines: list[str], nav: list[Any], prefix: str) -> None:
    for item in nav:
        label, value = next(iter(item.items()))
        lines.append(f"\n[[{prefix}]]")
        lines.append(f"{_toml_key(label)} = {_toml_value(value, indent=1)}")


def _emit_toml_table(lines: list[str], table: dict[str, Any], prefix: str) -> None:
    scalars: list[tuple[str, Any]] = []
    subtables: list[tuple[str, Any]] = []
    arrays: list[tuple[str, Any]] = []
    for key, value in table.items():
        if isinstance(value, dict):
            subtables.append((key, value))
        elif (
            isinstance(value, list)
            and value
            and all(isinstance(item, dict) for item in value)
        ):
            arrays.append((key, value))
        else:
            scalars.append((key, value))
    for key, value in scalars:
        lines.append(f"{_toml_key(key)} = {_toml_value(value)}")
    if isinstance(table.get("nav"), list):
        _emit_toml_nav(lines, table["nav"], f"{prefix}.nav")
    for key, value in subtables:
        lines.append(f"\n[{prefix}.{_toml_key(key)}]")
        _emit_toml_table(lines, value, f"{prefix}.{_toml_key(key)}")
    for key, items in arrays:
        if key == "nav":
            continue
        for item in items:
            lines.append(f"\n[[{prefix}.{_toml_key(key)}]]")
            _emit_toml_table(lines, item, f"{prefix}.{_toml_key(key)}")


def dump_toml(data: dict[str, Any]) -> str:
    lines: list[str] = ["[project]"]
    _emit_toml_table(lines, data, "project")
    return "\n".join(lines) + "\n"


def locale_config_path(code: str) -> Path:
    return PROJECT_ROOT / f"zensical.{code}.toml"


def locale_dir(code: str) -> Path:
    return LOCALES_DIR / code


def locale_content_dir(code: str) -> Path:
    return locale_dir(code) / CONTENT_SUBDIR


def load_registry() -> list[dict[str, str]]:
    if not REGISTRY_PATH.exists():
        return []
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    entries = data.get("locales", [])
    seen: set[str] = set()
    for entry in entries:
        code = entry.get("code")
        if not isinstance(code, str) or not code:
            raise I18nError(f"{REGISTRY_PATH}: entry missing a valid 'code'")
        if code == SOURCE_LOCALE:
            raise I18nError(f"{REGISTRY_PATH}: '{SOURCE_LOCALE}' must not be listed")
        if code in seen:
            raise I18nError(f"{REGISTRY_PATH}: duplicate locale '{code}'")
        seen.add(code)
    return entries


def save_registry(entries: list[dict[str, str]]) -> None:
    payload = json.dumps({"locales": entries}, ensure_ascii=False, indent=2)
    REGISTRY_PATH.write_text(payload + "\n", encoding="utf-8")


def registry_codes() -> list[str]:
    return [entry["code"] for entry in load_registry()]


def require_locale_files(code: str) -> None:
    base = locale_dir(code)
    if not (base / "nav.json").is_file():
        raise I18nError(f"locale '{code}' is incomplete, missing nav.json in {base}")


def resolve_locales(selection: list[str]) -> list[str]:
    codes = registry_codes()
    if any(item == "all" for item in selection):
        selected = codes
    else:
        known = set(codes)
        unknown = [item for item in selection if item not in known]
        if unknown:
            raise I18nError(
                f"unknown locale(s) {unknown}, supported: {codes or 'none'} "
                f"(edit {REGISTRY_PATH})"
            )
        selected = selection
    for code in selected:
        require_locale_files(code)
    return selected


def load_en_nav() -> list[Any]:
    config = tomllib.loads(ROOT_CONFIG_PATH.read_text(encoding="utf-8"))
    project = config.get("project", {})
    nav = project.get("nav", [])
    if not isinstance(nav, list):
        raise I18nError(f"{ROOT_CONFIG_PATH}: 'project.nav' must be an array")
    return nav


def load_nav_json(code: str) -> dict[str, Any]:
    path = locale_dir(code) / "nav.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise I18nError(f"{path}: expected a JSON object")
    if not isinstance(data.get("nav", []), list):
        raise I18nError(f"{path}: 'nav' must be an array")
    if not isinstance(data.get("skip", []), list):
        raise I18nError(f"{path}: 'skip' must be an array")
    return data


def validate_nav_structure(
    en_nav: list[Any], loc_nav: list[Any], where: str = "nav"
) -> None:
    if len(en_nav) != len(loc_nav):
        raise I18nError(
            f"nav mismatch at {where}: {len(en_nav)} entries in English nav, "
            f"{len(loc_nav)} in translation"
        )
    for index, (en_item, loc_item) in enumerate(zip(en_nav, loc_nav)):
        spot = f"{where}[{index}]"
        if not isinstance(en_item, dict) or not isinstance(loc_item, dict):
            raise I18nError(f"nav mismatch at {spot}: expected objects")
        if len(en_item) != 1 or len(loc_item) != 1:
            raise I18nError(
                f"nav mismatch at {spot}: each entry needs exactly one label"
            )
        en_value = next(iter(en_item.values()))
        loc_value = next(iter(loc_item.values()))
        en_is_str = isinstance(en_value, str)
        if en_is_str != isinstance(loc_value, str):
            raise I18nError(f"nav mismatch at {spot}: page vs section")
        if en_is_str:
            if en_value != loc_value:
                raise I18nError(
                    f"nav mismatch at {spot}: path {loc_value!r} != {en_value!r}"
                )
        else:
            validate_nav_structure(en_value, loc_value, spot)


def validate_nav(code: str) -> None:
    validate_nav_structure(load_en_nav(), load_nav_json(code)["nav"], f"{code}.nav")


def require_registered(code: str) -> None:
    if code == SOURCE_LOCALE:
        raise I18nError(f"'{SOURCE_LOCALE}' is the source language")
    if code not in registry_codes():
        raise I18nError(
            f"locale '{code}' is not in {REGISTRY_PATH} "
            f"(run: python docs/scripts/translate.py {code} --init)"
        )


def iter_markdown(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("*.md"))


def is_skipped(rel: str, skip: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) for pattern in skip)


def is_shared(rel: str) -> bool:
    """True when a relative path comes from the shared directory."""
    return rel in SHARED_ITEMS or any(
        rel.startswith(f"{item}/") for item in SHARED_ITEMS
    )


def select_targets(paths: list[str], skip: list[str]) -> list[str]:
    targets: list[str] = []
    if paths:
        for raw in paths:
            candidate = (EN_CONTENT_DIR / raw).resolve()
            try:
                candidate.relative_to(EN_CONTENT_DIR.resolve())
            except ValueError as error:
                raise I18nError(f"path outside content root: {raw}") from error
            if candidate.is_dir():
                targets.extend(
                    p.relative_to(EN_CONTENT_DIR).as_posix()
                    for p in iter_markdown(candidate)
                    if not is_skipped(p.relative_to(EN_CONTENT_DIR).as_posix(), skip)
                )
            elif candidate.is_file():
                rel = candidate.relative_to(EN_CONTENT_DIR).as_posix()
                if not is_skipped(rel, skip):
                    targets.append(rel)
            else:
                raise I18nError(f"no such file or directory: {raw}")
    else:
        targets = [
            p.relative_to(EN_CONTENT_DIR).as_posix()
            for p in iter_markdown(EN_CONTENT_DIR)
            if not is_skipped(p.relative_to(EN_CONTENT_DIR).as_posix(), skip)
        ]
    seen: set[str] = set()
    unique = [t for t in targets if not (t in seen or seen.add(t))]
    return sorted(unique)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_front_matter(text: str) -> tuple[dict[str, Any] | None, str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return None, text
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None, text
    if not isinstance(meta, dict):
        return None, text
    return meta, text[match.end() :]


def dump_document(meta: dict[str, Any], body: str) -> str:
    front = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True).rstrip("\n")
    body = body.lstrip("\n")
    return f"---\n{front}\n---\n\n{body}"


def load_notice(code: str) -> tuple[str, str]:
    """Return the localized (title, body, link label) for the disclosure notice.

    Values come from nav.json (`notice_title` / `notice_body` /
    `notice_link_label`); falls back to English when incomplete.
    """
    if code == SOURCE_LOCALE:
        return NOTICE_TITLE, NOTICE_BODY, NOTICE_LINK_LABEL
    try:
        data = load_nav_json(code)
    except (OSError, ValueError):
        return NOTICE_TITLE, NOTICE_BODY, NOTICE_LINK_LABEL
    title = data.get("notice_title")
    body = data.get("notice_body")
    if (
        isinstance(title, str)
        and title.strip()
        and isinstance(body, str)
        and body.strip()
    ):
        label = data.get("notice_link_label")
        if not isinstance(label, str) or not label.strip():
            label = NOTICE_LINK_LABEL
        return title, body, label.strip()
    return NOTICE_TITLE, NOTICE_BODY, NOTICE_LINK_LABEL


def site_url() -> str:
    """Base URL of the English site, from the root zensical config."""
    try:
        config = tomllib.loads(ROOT_CONFIG_PATH.read_text(encoding="utf-8"))
        url = config["project"]["site_url"]
        if isinstance(url, str) and url.strip():
            return url.rstrip("/") + "/"
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        pass
    return "https://jowilf.github.io/starlette-admin/"


def en_page_url(rel: str) -> str:
    """URL of the English counterpart of a translated page (`dir/page.md`)."""
    base = site_url()
    if rel == "index.md":
        return base
    path = rel.removesuffix(".md")
    if path.endswith("/index"):
        path = path[: -len("/index")]
    return f"{base}{path}/"


def notice_text(
    variant: str, code: str = SOURCE_LOCALE, en_url: str | None = None
) -> str:
    title, notice_body, link_label = load_notice(code)
    paragraphs = []
    for para in notice_body.split("\n" * 2):
        if "](" in para:
            # Keep linked paragraphs unwrapped so link syntax stays intact.
            paragraphs.append("    " + para)
        else:
            paragraphs.append(
                textwrap.fill(
                    para,
                    width=76,
                    initial_indent="    ",
                    subsequent_indent="    ",
                    break_long_words=False,
                    break_on_hyphens=False,
                )
            )
    if en_url:
        paragraphs.append(f"    [{link_label}]({en_url})")
    body = ("\n" * 2).join(paragraphs)
    return f'??? {variant} "{title}"\n\n{body}\n'


def insert_notice(
    body: str, variant: str, code: str = SOURCE_LOCALE, en_url: str | None = None
) -> str:
    """Prepend a marker-wrapped notice block followed by the page body."""
    return (
        f"{NOTICE_START_MARKER}\n"
        f"{notice_text(variant, code, en_url)}"
        f"{NOTICE_END_MARKER}\n\n{body.strip(chr(10))}\n"
    )


def set_notice(
    text: str, variant: str, code: str, en_url: str | None = None
) -> tuple[str, bool]:
    """Rewrite the notice block; migrates legacy unmarked notices.

    Idempotent: returns the text unchanged when the block already matches.
    """
    meta, body = split_front_matter(text)
    if meta is None:
        return text, False
    start = body.find(NOTICE_START_MARKER)
    if start != -1:
        end = body.find(NOTICE_END_MARKER, start)
        if end == -1:
            return text, False
        rest = body[end + len(NOTICE_END_MARKER) :]
        updated = dump_document(meta, insert_notice(rest, variant, code, en_url))
        return updated, updated != text
    # Legacy unmarked notice: the admonition is the first line of the body.
    lines = body.lstrip("\n").split("\n")
    heading = NOTICE_HEADING_RE.match(lines[0]) if lines else None
    if not heading:
        return text, False
    index = 1
    while index < len(lines):
        line = lines[index]
        # A blank line ends the block unless another indented line follows.
        if line.startswith("    ") or (
            line == ""
            and index + 1 < len(lines)
            and lines[index + 1].startswith("    ")
        ):
            index += 1
            continue
        break
    rest = "\n".join(lines[index:])
    updated = dump_document(meta, insert_notice(rest, variant, code, en_url))
    return updated, updated != text


def stored_source_hash(text: str) -> str | None:
    meta, _ = split_front_matter(text)
    if not meta:
        return None
    value = meta.get("source_hash")
    return value if isinstance(value, str) else None


def stored_prompt_hash(text: str) -> str | None:
    meta, _ = split_front_matter(text)
    if not meta:
        return None
    value = meta.get("prompt_hash")
    return value if isinstance(value, str) else None


def prompt_hash() -> str:
    return sha256_file(TRANSLATIONS_PROMPT_PATH)


def hashes_current(text: str, en_path: Path, code: str) -> bool:
    """True when the English source and the shared prompt are unchanged."""
    return (
        en_path.exists()
        and stored_source_hash(text) == sha256_file(en_path)
        and stored_prompt_hash(text) == prompt_hash()
    )


def is_machine_translated(text: str) -> bool:
    meta, _ = split_front_matter(text)
    return bool(meta and meta.get("machine_translated"))


def page_state(rel: str, code: str) -> str:
    en_path = EN_CONTENT_DIR / rel
    loc_path = locale_content_dir(code) / rel
    if not loc_path.exists():
        return "missing"
    if not en_path.exists():
        return "orphan"
    text = loc_path.read_text(encoding="utf-8")
    if not is_machine_translated(text):
        return "fresh"
    return "fresh" if hashes_current(text, en_path, code) else "stale"


def staleness_pass(content_dir: Path) -> int:
    code = content_dir.parent.name
    flipped = 0
    for path in iter_markdown(content_dir):
        rel = path.relative_to(content_dir).as_posix()
        text = path.read_text(encoding="utf-8")
        if not is_machine_translated(text):
            continue
        fresh = hashes_current(text, EN_CONTENT_DIR / rel, code)
        # Refresh variant, wording and English link; migrates legacy notices.
        text, did = set_notice(
            text, "info" if fresh else "warning", code, en_url=en_page_url(rel)
        )
        if did:
            path.write_text(text, encoding="utf-8")
            flipped += 1
    return flipped


def _prune_nav(nav: list[Any], content_dir: Path) -> list[Any]:
    pruned: list[Any] = []
    for item in nav:
        if not isinstance(item, dict) or len(item) != 1:
            pruned.append(item)
            continue
        label, value = next(iter(item.items()))
        if isinstance(value, str):
            if (content_dir / value).is_file():
                pruned.append(item)
        else:
            sub = _prune_nav(value, content_dir)
            if sub:
                pruned.append({label: sub})
    return pruned


def _nav_translation_stats(
    nav: list[Any], content_dir: Path, skip: list[str]
) -> tuple[int, int]:
    """Return (translated, expected) nav leaf counts, excluding skipped pages."""
    translated = expected = 0
    for item in nav:
        if not isinstance(item, dict) or len(item) != 1:
            continue
        value = next(iter(item.values()))
        if isinstance(value, str):
            if is_skipped(value, skip):
                continue
            expected += 1
            if (content_dir / value).is_file():
                translated += 1
        else:
            sub_translated, sub_expected = _nav_translation_stats(
                value, content_dir, skip
            )
            translated += sub_translated
            expected += sub_expected
    return translated, expected


def generate_locale_config(code: str, prefix: str = "/") -> Path:
    validate_nav(code)
    config = tomllib.loads(ROOT_CONFIG_PATH.read_text(encoding="utf-8"))["project"]
    config["docs_dir"] = f"docs/locales/{code}/{CONTENT_SUBDIR}"
    config["site_dir"] = f"site/{code}"
    # Absolute URL of this locale (canonical tags, sitemap); `site_url`
    # already carries the deployment base path.
    config["site_url"] = f"{site_url()}{code}"
    config.setdefault("extra", {})["alternate"] = alternate_entries(prefix)
    theme = config.setdefault("theme", {})
    theme["language"] = code
    nav_data = load_nav_json(code)
    nav = nav_data["nav"]
    content_dir = locale_content_dir(code)
    translated, total = _nav_translation_stats(
        nav, content_dir, nav_data.get("skip", [])
    )
    config["nav"] = _prune_nav(nav, content_dir)
    if translated < total:
        print(
            f"note ({code}): {total - translated}/{total} nav pages are not "
            "translated yet and were left out of this build",
            flush=True,
        )
    out_path = locale_config_path(code)
    out_path.write_text(dump_toml(config), encoding="utf-8")
    return out_path


def generate_english_config(prefix: str) -> Path:
    """Root config copy whose switcher links use the given base path.

    Used for builds with a non-default `--alternate-prefix` so the tracked
    root config always keeps its default "/" entries.
    """
    config = tomllib.loads(ROOT_CONFIG_PATH.read_text(encoding="utf-8"))["project"]
    config.setdefault("extra", {})["alternate"] = alternate_entries(prefix)
    out_path = PROJECT_ROOT / f"zensical.{SOURCE_LOCALE}.toml"
    out_path.write_text(dump_toml(config), encoding="utf-8")
    return out_path


# --------------------------------------------------------------------------
# Language switcher (`extra.alternate`) in the main zensical.toml
# --------------------------------------------------------------------------

ALTERNATE_HEADER = "[[project.extra.alternate]]"
ALTERNATE_MARKER = (
    "# Language switcher entries -- managed by docs/scripts/build.py, do not edit."
)


def alternate_entries(prefix: str = "/") -> list[dict[str, str]]:
    """Language switcher entries: English at the site root, locales in subdirs.

    Links are root-relative and must mirror the deployment base path
    (`prefix`, e.g. "/starlette-admin" for GitHub Pages project sites)
    because zensical renders them verbatim on every page.
    """
    base = normalize_prefix(prefix)
    entries = [
        {
            "name": f"{SOURCE_LOCALE} - English",
            "link": f"{base}/" if base else "/",
            "lang": SOURCE_LOCALE,
        }
    ]
    for entry in load_registry():
        code = entry["code"]
        entries.append(
            {
                "name": f"{code} - {entry.get('name') or code}",
                "link": f"{base}/{code}/",
                "lang": code,
            }
        )
    return entries


def normalize_prefix(prefix: str) -> str:
    """Normalize a base path to "" or "/starlette-admin" form."""
    stripped = prefix.strip().strip("/")
    return f"/{stripped}" if stripped else ""


def render_alternate_block() -> str:
    chunks = [ALTERNATE_MARKER]
    for entry in alternate_entries():
        chunks.extend(
            [
                ALTERNATE_HEADER,
                f'name = "{entry["name"]}"',
                f'link = "{entry["link"]}"',
                f'lang = "{entry["lang"]}"',
                "",
            ]
        )
    return "\n".join(chunks).rstrip("\n")


def strip_alternate_block(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]
        if line.strip() in (ALTERNATE_HEADER, ALTERNATE_MARKER):
            index += 1
            # Skip the managed block; stop at foreign tables or comments.
            while index < total:
                stripped = lines[index].strip()
                if stripped in (ALTERNATE_HEADER, ALTERNATE_MARKER):
                    index += 1
                elif stripped.startswith(("[", "#")):
                    break
                else:
                    index += 1
            continue
        kept.append(line)
        index += 1
    return "\n".join(kept).rstrip("\n")


def sync_alternates() -> None:
    """Regenerate the `[[project.extra.alternate]]` block in zensical.toml."""
    text = strip_alternate_block(ROOT_CONFIG_PATH.read_text(encoding="utf-8"))
    updated = text + "\n\n" + render_alternate_block() + "\n"
    if updated == ROOT_CONFIG_PATH.read_text(encoding="utf-8"):
        return
    ROOT_CONFIG_PATH.write_text(updated, encoding="utf-8")
    print(f"synced language switcher into {ROOT_CONFIG_PATH.name}", flush=True)
