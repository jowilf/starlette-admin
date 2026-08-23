"""Serve the built site folder, rebuilding on changes."""

import argparse
import contextlib
import functools
import http.server
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
BUILD_SCRIPT = DOCS_DIR / "scripts" / "build.py"
SITE_DIR = PROJECT_ROOT / "site"
WATCH_FILES = [PROJECT_ROOT / "zensical.toml"]
WATCH_DIRS = [DOCS_DIR / "shared", DOCS_DIR / "locales"]
WATCH_SUFFIXES = [".md", ".yml", ".yaml", ".html", ".css", ".js"]
IGNORED_DIRS = {"site"}
POLL_INTERVAL = 1.0
DEFAULT_PORT = 8080


def snapshot() -> dict[str, float]:
    state: dict[str, float] = {}
    paths = list(WATCH_FILES)
    for root in WATCH_DIRS:
        if root.is_dir():
            paths.extend(root.rglob("*"))
    for path in paths:
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and (path.suffix in WATCH_SUFFIXES or path in WATCH_FILES):
            with contextlib.suppress(OSError):
                state[str(path)] = path.stat().st_mtime
    return state


def build(locales: list[str] | None = None) -> None:
    command = [sys.executable, str(BUILD_SCRIPT)]
    if locales:
        command.extend(["--locales", *locales])
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode == 0:
        print("build ok", flush=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        print(format % args, flush=True)

    def handle(self) -> None:
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            super().handle()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"port to serve on (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--locales",
        nargs="+",
        metavar="LOC",
        help="locale codes to build on each rebuild ('all' for every supported locale)",
    )
    args = parser.parse_args()

    build(args.locales)
    handler = functools.partial(Handler)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"serving {SITE_DIR} at http://127.0.0.1:{args.port}", flush=True)

    try:
        last = snapshot()
        while True:
            time.sleep(POLL_INTERVAL)
            current = snapshot()
            if current != last:
                changed = {
                    k
                    for k in current.keys() | last.keys()
                    if current.get(k) != last.get(k)
                }
                print(f"change detected: {len(changed)} file(s), rebuilding...")
                build(args.locales)
                last = current
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
