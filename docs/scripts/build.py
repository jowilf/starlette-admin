"""Sync shared files into the content directory and build the docs."""

import shutil
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent
SHARED_DIR = DOCS_DIR / "shared"
CONTENT_DIR = DOCS_DIR / "locales" / "en" / "content"
SHARED_ITEMS = ["assets", "javascripts", "stylesheets"]


def sync_shared() -> None:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    for item in SHARED_ITEMS:
        src = SHARED_DIR / item
        if not src.is_dir():
            print(f"warning: {src} does not exist, skipping", file=sys.stderr)
            continue
        dest = CONTENT_DIR / item
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print(f"synced shared/{item} -> locales/en/content/{item}", flush=True)


def main() -> int:
    sync_shared()
    result = subprocess.run(["zensical", "build", *sys.argv[1:]], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
