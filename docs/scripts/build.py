"""Sync shared files and build the docs site (English plus optional locales)."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from i18n import (
    CONTENT_SUBDIR,
    DOCS_DIR,
    LOCALES_DIR,
    SHARED_DIR,
    SHARED_ITEMS,
    I18nError,
    generate_locale_config,
    iter_markdown,
    locale_content_dir,
    resolve_locales,
    staleness_pass,
    sync_alternates,
)


def sync_shared(content_dir: Path) -> None:
    content_dir.mkdir(parents=True, exist_ok=True)
    for item in SHARED_ITEMS:
        src = SHARED_DIR / item
        if not src.is_dir():
            print(f"warning: {src} does not exist, skipping", file=sys.stderr)
            continue
        dest = content_dir / item
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        rel = content_dir.relative_to(DOCS_DIR)
        print(f"synced shared/{item} -> {rel}/{item}", flush=True)


def sync_all_shared() -> None:
    """Sync shared files into every locale content dir (EN included)."""
    for content_dir in sorted(LOCALES_DIR.glob(f"*/{CONTENT_SUBDIR}")):
        if content_dir.is_dir():
            sync_shared(content_dir)


def run_zensical(args: list[str]) -> int:
    return subprocess.run(["zensical", "build", *args], check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--locales",
        nargs="+",
        metavar="LOC",
        help="locale codes to build after English ('all' for every supported locale)",
    )
    args, extras = parser.parse_known_args()

    try:
        sync_alternates()
    except I18nError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    sync_all_shared()
    code = run_zensical(extras)
    if code != 0 or not args.locales:
        return code

    try:
        codes = resolve_locales(args.locales)
    except I18nError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    for loc in codes:
        content = locale_content_dir(loc)
        if not iter_markdown(content):
            print(f"skipping locale '{loc}': no translated pages yet", flush=True)
            continue
        flipped = staleness_pass(content)
        if flipped:
            print(f"staleness pass ({loc}): {flipped} notice(s) updated", flush=True)
        config_path = generate_locale_config(loc)
        print(f"building locale '{loc}' with {config_path.name}", flush=True)
        code = run_zensical(["--config-file", str(config_path), *extras])
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
