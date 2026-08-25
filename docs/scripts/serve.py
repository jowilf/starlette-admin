"""Serve the built site folder, rebuilding on changes.

With `--alternate-prefix`, the site is served under the same base path as
the deployment (e.g. /starlette-admin), so root-relative language switcher
links behave exactly like in production; unprefixed URLs are redirected.
"""

import argparse
import contextlib
import functools
import http.server
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from i18n import normalize_prefix

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


def build(locales: list[str] | None = None, prefix: str = "/") -> None:
    command = [sys.executable, str(BUILD_SCRIPT), "--alternate-prefix", prefix]
    if locales:
        command.extend(["--locales", *locales])
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode == 0:
        print("build ok", flush=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, prefix: str = "", **kwargs):
        self.prefix = prefix
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:
        print(format % args, flush=True)

    def handle(self) -> None:
        with contextlib.suppress(BrokenPipeError, ConnectionResetError):
            super().handle()

    def _redirect(self, location: str) -> None:
        self.send_response(301)
        self.send_header("Location", location)
        self.end_headers()

    def _unprefixed_location(self) -> str | None:
        """Location to redirect to when the URL lacks the prefix, else None."""
        if not self.prefix:
            return None
        target = urlparse(self.path).path
        if target == self.prefix or target.startswith(f"{self.prefix}/"):
            return None
        return f"{self.prefix}{self.path}"

    def do_GET(self) -> None:
        location = self._unprefixed_location()
        if location:
            self._redirect(location)
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        location = self._unprefixed_location()
        if location:
            self._redirect(location)
            return
        super().do_HEAD()

    def translate_path(self, path: str) -> str:
        clean = urlparse(path).path
        if self.prefix and (
            clean == self.prefix or clean.startswith(f"{self.prefix}/")
        ):
            clean = clean[len(self.prefix) :] or "/"
        return super().translate_path(clean)


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
    parser.add_argument(
        "--alternate-prefix",
        default="/",
        metavar="PATH",
        help="serve the site under this base path and build matching "
        'language switcher links (default: "/")',
    )
    args = parser.parse_args()
    prefix = normalize_prefix(args.alternate_prefix)

    build(args.locales, prefix=args.alternate_prefix)
    handler = functools.partial(Handler, prefix=prefix)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    location = f"http://127.0.0.1:{args.port}{prefix}/"
    print(f"serving {SITE_DIR} at {location}", flush=True)

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
                build(args.locales, prefix=args.alternate_prefix)
                last = snapshot()  # Re-baseline: the build touches watched paths.
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
