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
SHARED_ITEMS = ["assets", "javascripts", "stylesheets"]
CONTENT_SUBDIR = "content"
SOURCE_LOCALE = "en"
EN_CONTENT_DIR = LOCALES_DIR / "en" / CONTENT_SUBDIR
REGISTRY_PATH = LOCALES_DIR / "locales.json"
ROOT_CONFIG_PATH = PROJECT_ROOT / "zensical.toml"

#: Pages never translated, regardless of per-locale `skip` lists.
DEFAULT_SKIP = ["changelog.md"]

NOTICE_TITLE = "Supervised Machine Translation"
NOTICE_BODY = (
    "This content is translated using machine generation guided by "
    "human-curated glossaries and style guides. Because the text is not "
    "manually reviewed line by line, occasional errors or awkward phrasing "
    "may occur. In case of any discrepancies, the original English version "
    "is the authoritative source."
)
#: Localized notices for machine translated pages, keyed by locale code.
#: Falls back to the English notice for locales without an entry.
NOTICES: dict[str, tuple[str, str]] = {
    "fr": (
        "Traduction automatique supervisée",
        "Ce contenu est généré par traduction automatique, guidée par des "
        "glossaires et des guides de style validés par des humains. Comme le "
        "texte n'est pas relu ligne par ligne, des erreurs ou des formulations "
        "maladroites peuvent parfois apparaître."
        "\n\n"
        "En cas de divergence, la [version originale en anglais]"
        "(https://jowilf.github.io/starlette-admin/) fait foi.",
    ),
}
NOTICE_RE = re.compile(
    r"\A---\n.*?\n---\n\n"
    r"\?\?\? (?P<variant>info|warning) \"[^\"]*\"\n\n"
    r"(?:    .*(?:\n|\Z))+",
    re.DOTALL,
)
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class I18nError(Exception):
    """A configuration or validation error in the docs i18n pipeline."""


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
    missing = [
        name for name in ("llm_prompt.md", "nav.json") if not (base / name).is_file()
    ]
    if missing:
        raise I18nError(f"locale '{code}' is incomplete, missing {missing} in {base}")


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
    return any(fnmatch.fnmatch(rel, pattern) for pattern in [*DEFAULT_SKIP, *skip])


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


def notice_text(variant: str, code: str = SOURCE_LOCALE) -> str:
    title, notice_body = NOTICES.get(code, (NOTICE_TITLE, NOTICE_BODY))
    paragraphs = []
    for para in notice_body.split("\n" * 2):
        if "](" in para:
            # Keep paragraphs with markdown links on a single unwrapped
            # line so the link syntax is never split across lines.
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
    body = ("\n" * 2).join(paragraphs)
    return f'??? {variant} "{title}"\n\n{body}\n'


def insert_notice(body: str, variant: str, code: str = SOURCE_LOCALE) -> str:
    return f"{notice_text(variant, code)}\n{body.strip(chr(10))}\n"


def flip_notice(text: str, desired: str) -> tuple[str, bool]:
    match = NOTICE_RE.search(text)
    if not match:
        return text, False
    current = match.group("variant")
    if current == desired:
        return text, False
    start = match.start("variant")
    return text[:start] + desired + text[start + len(current) :], True


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


def prompt_hash(code: str) -> str:
    return sha256_file(locale_dir(code) / "llm_prompt.md")


def hashes_current(text: str, en_path: Path, code: str) -> bool:
    """True when the English source and the locale llm_prompt are unchanged."""
    return (
        en_path.exists()
        and stored_source_hash(text) == sha256_file(en_path)
        and stored_prompt_hash(text) == prompt_hash(code)
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
        text, did = flip_notice(text, "info" if fresh else "warning")
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


def _count_leaves(nav: list[Any]) -> int:
    total = 0
    for item in nav:
        if isinstance(item, dict) and len(item) == 1:
            value = next(iter(item.values()))
            total += 1 if isinstance(value, str) else _count_leaves(value)
    return total


def generate_locale_config(code: str) -> Path:
    validate_nav(code)
    config = tomllib.loads(ROOT_CONFIG_PATH.read_text(encoding="utf-8"))["project"]
    config["docs_dir"] = f"docs/locales/{code}/{CONTENT_SUBDIR}"
    config["site_dir"] = f"site/{code}"
    theme = config.setdefault("theme", {})
    theme["language"] = code
    nav = load_nav_json(code)["nav"]
    content_dir = locale_content_dir(code)
    available, total = _count_leaves(_prune_nav(nav, content_dir)), _count_leaves(nav)
    config["nav"] = _prune_nav(nav, content_dir)
    if available < total:
        print(
            f"note ({code}): {total - available}/{total} nav pages are not "
            "translated yet and were left out of this build",
            flush=True,
        )
    out_path = PROJECT_ROOT / f"zensical.{code}.json"
    out_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out_path
