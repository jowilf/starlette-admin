"""Translate the documentation into supported locales using LLMs (OpenRouter)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from i18n import (
    EN_CONTENT_DIR,
    LOCALES_DIR,
    NOTICE_BODY,
    NOTICE_LINK_LABEL,
    NOTICE_TITLE,
    REGISTRY_PATH,
    TRANSLATIONS_PROMPT_PATH,
    I18nError,
    dump_document,
    en_page_url,
    insert_notice,
    iter_markdown,
    load_en_nav,
    load_nav_json,
    load_registry,
    locale_content_dir,
    page_state,
    prompt_hash,
    require_locale_files,
    require_registered,
    save_registry,
    select_targets,
    split_front_matter,
    validate_nav,
    validate_nav_structure,
)

DEFAULT_MODEL = "google/gemini-2.5-flash"
MAX_TOKENS_TIMEOUT_MS = 300_000
BACKOFF_SECONDS = (2, 8)
MAX_JOBS = 8

_print_lock = threading.Lock()


def _read_prompt(code: str, name: str | None = None) -> str:
    """Load the shared translation prompt with the target locale filled in."""
    if not TRANSLATIONS_PROMPT_PATH.is_file():
        raise I18nError(f"{TRANSLATIONS_PROMPT_PATH} is missing")
    template = TRANSLATIONS_PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not template:
        raise I18nError(f"{TRANSLATIONS_PROMPT_PATH} is empty")
    return template.replace("{name}", name or _locale_name(code)).replace(
        "{code}", code
    )


def _locale_name(code: str) -> str:
    for entry in load_registry():
        if entry["code"] == code:
            return entry.get("name") or code
    return code


def _get_client() -> Any:
    client = getattr(_get_client, "_instance", None)
    if client is None:
        try:
            from openrouter import OpenRouter
        except ImportError as error:
            raise I18nError(
                "the 'openrouter' package is not installed; run: uv sync --group docs"
            ) from error
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise I18nError("OPENROUTER_API_KEY is not set")
        client = OpenRouter(api_key=api_key, timeout_ms=MAX_TOKENS_TIMEOUT_MS)
        _get_client._instance = client
    return client


def _chat(system: str, user: str, model: str, reasoning: str | None = None) -> Any:
    kwargs: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "model": model,
        "stream": False,
    }
    if reasoning:
        kwargs["reasoning_effort"] = reasoning
    return _get_client().chat.send(**kwargs)


def _extract_content(response: Any) -> str:
    try:
        content = response.choices[0].message.content
    except (IndexError, AttributeError) as error:
        raise ValueError("malformed API response") from error
    if not isinstance(content, str) or not content.strip():
        raise ValueError("empty completion")
    return content


def _extract_usage(response: Any) -> tuple[int, int]:
    usage = getattr(response, "usage", None)
    prompt = getattr(usage, "prompt_tokens", None)
    completion = getattr(usage, "completion_tokens", None)
    prompt = prompt if isinstance(prompt, int) else 0
    completion = completion if isinstance(completion, int) else 0
    return prompt, completion


def _clean_output(text: str) -> str:
    text = text.strip()
    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        text = "\n".join(lines[1:-1]).strip()
    fences = sum(1 for line in text.splitlines() if line.lstrip().startswith("```"))
    if not text:
        raise ValueError("completion has no content")
    if fences % 2:
        raise ValueError("unbalanced code fences in completion")
    return text.rstrip() + "\n"


def _with_retries(action: Any, label: str) -> Any:
    last_error: Exception | None = None
    for attempt in range(len(BACKOFF_SECONDS) + 1):
        try:
            return action()
        except Exception as error:
            last_error = error
            if attempt < len(BACKOFF_SECONDS):
                time.sleep(BACKOFF_SECONDS[attempt])
    raise RuntimeError(
        f"{label} failed after {len(BACKOFF_SECONDS) + 1} attempts: {last_error}"
    ) from last_error


def _compose_document(
    translated: str,
    source_hash: str,
    prompt_hash_value: str,
    code: str,
    rel: str,
) -> str:
    meta, body = split_front_matter(translated)
    meta = meta or {}
    meta["source_hash"] = source_hash
    meta["prompt_hash"] = prompt_hash_value
    meta["machine_translated"] = True
    return dump_document(
        meta, insert_notice(body, "info", code, en_url=en_page_url(rel))
    )


def _translate_one(
    rel: str,
    code: str,
    system_prompt: str,
    model: str,
    force: bool,
    reasoning: str | None = None,
) -> tuple[str, int, int]:
    en_path = EN_CONTENT_DIR / rel
    loc_path = locale_content_dir(code) / rel
    if not en_path.exists():
        return ("skipped-orphan", 0, 0)
    if loc_path.exists() and not force:
        state = page_state(rel, code)
        if state == "fresh":
            return ("skipped", 0, 0)
        if state == "orphan":
            return ("skipped-orphan", 0, 0)
    source_bytes = en_path.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    prompt_digest = prompt_hash()

    def attempt() -> tuple[str, int, int]:
        response = _chat(system_prompt, source_bytes.decode("utf-8"), model, reasoning)
        content = _clean_output(_extract_content(response))
        prompt, completion = _extract_usage(response)
        return content, prompt, completion

    translated, prompt, completion = _with_retries(attempt, rel)
    document = _compose_document(translated, digest, prompt_digest, code, rel)
    loc_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = loc_path.with_name(loc_path.name + ".tmp")
    tmp_path.write_text(document, encoding="utf-8")
    os.replace(tmp_path, loc_path)
    return ("translated", prompt, completion)


def _print_dry_run(
    pending: list[str], states: dict[str, str], fresh: int, orphans: list[str]
) -> None:
    for rel in pending:
        if states[rel] == "missing":
            print(f"[dry-run] translate {rel} (missing)")
        elif states[rel] == "stale":
            print(f"[dry-run] retranslate {rel} (stale)")
        else:
            print(f"[dry-run] retranslate {rel} (forced)")
    print(
        f"[dry-run] {len(pending)} file(s) would be requested, "
        f"{fresh} fresh skipped, {len(orphans)} orphan(s)"
    )


def _cmd_translate(args: argparse.Namespace) -> int:
    require_registered(args.locale)
    require_locale_files(args.locale)
    nav_data = load_nav_json(args.locale)
    skip = nav_data.get("skip", [])
    targets = select_targets(args.paths, skip)
    if not targets:
        print("nothing to do: no English pages matched")
        return 0
    states = {rel: page_state(rel, args.locale) for rel in targets}
    pending = [
        rel for rel in targets if args.force or states[rel] in ("missing", "stale")
    ]
    fresh = sum(1 for rel in targets if states[rel] == "fresh" and rel not in pending)
    orphans = [rel for rel in targets if states[rel] == "orphan"]

    if args.dry_run:
        _print_dry_run(pending, states, fresh, orphans)
        return 0

    if not pending:
        print(f"already up to date ({fresh} fresh, {len(orphans)} orphan(s))")
        return 0

    model = args.model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
    reasoning = args.reasoning or os.environ.get("OPENROUTER_REASONING") or None
    system_prompt = _read_prompt(args.locale)

    results: list[tuple[str, str, int, int]] = []

    def worker(rel: str) -> None:
        try:
            outcome, prompt, completion = _translate_one(
                rel,
                args.locale,
                system_prompt,
                model,
                args.force,
                reasoning,
            )
            with _print_lock:
                results.append((rel, outcome, prompt, completion))
                if outcome == "translated":
                    print(
                        f"✓ {args.locale} {rel} in={prompt} out={completion}",
                        flush=True,
                    )
        except Exception as error:
            with _print_lock:
                results.append((rel, f"failed: {error}", 0, 0))
                print(f"✗ {args.locale} {rel}: {error}", flush=True)

    if args.jobs > 1:
        with ThreadPoolExecutor(max_workers=min(args.jobs, MAX_JOBS)) as pool:
            list(pool.map(worker, pending))
    else:
        for rel in pending:
            worker(rel)

    done = sum(1 for r in results if r[1] == "translated")
    failed = sum(1 for r in results if r[1].startswith("failed"))
    tokens_in = sum(r[2] for r in results)
    tokens_out = sum(r[3] for r in results)
    skipped_now = len(results) - done - failed
    print(
        f"done: model={model}, translated={done}, skipped={skipped_now}, "
        f"failed={failed}, fresh_skipped={fresh}, "
        f"tokens in={tokens_in} out={tokens_out}"
    )
    return 2 if failed else 0


def _cmd_status(args: argparse.Namespace) -> int:
    require_registered(args.locale)
    require_locale_files(args.locale)
    nav_data = load_nav_json(args.locale)
    en_rels = select_targets([], nav_data.get("skip", []))
    buckets: dict[str, list[str]] = {
        "fresh": [],
        "stale": [],
        "missing": [],
        "orphan": [],
    }
    for rel in en_rels:
        buckets[page_state(rel, args.locale)].append(rel)
    en_set = set(en_rels)
    for path in iter_markdown(locale_content_dir(args.locale)):
        rel = path.relative_to(locale_content_dir(args.locale)).as_posix()
        if rel not in en_set:
            buckets["orphan"].append(rel)

    counts = {key: len(value) for key, value in buckets.items()}
    total = sum(counts.values())
    summary = ", ".join(
        f"{counts[key]} {key}" for key in ("fresh", "stale", "missing", "orphan")
    )
    print(f"{args.locale}: {summary} ({total} tracked)")

    stale_or_missing = buckets["stale"] + buckets["missing"]
    for key in ("stale", "missing", "orphan"):
        for rel in sorted(buckets[key]):
            marker = {"stale": "~", "missing": "+", "orphan": "?"}[key]
            print(f"  {marker} {rel}")

    if args.fail_on_stale and stale_or_missing:
        print(
            f"error: {args.locale} has {len(stale_or_missing)} "
            "untranslated or outdated page(s)"
        )
        return 2
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    code = args.locale
    if code == "en":
        raise I18nError("'en' is the source language and cannot be initialized")
    if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", code):
        raise I18nError(
            f"invalid locale code '{code}' (expected lowercase BCP-47 like 'fr' or 'pt-br')"
        )
    entries = load_registry()
    if any(entry["code"] == code for entry in entries):
        raise I18nError(f"locale '{code}' is already listed in {REGISTRY_PATH}")
    base = LOCALES_DIR / code
    if base.exists():
        raise I18nError(f"{base} already exists")
    name = args.name or code
    system_prompt = _read_prompt(code, name)
    model = args.model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
    reasoning = args.reasoning or os.environ.get("OPENROUTER_REASONING") or None

    # Translate the AI notice first: it needs one LLM round-trip, and doing
    # it before anything is written keeps a failed init free of side effects.
    # Notices must always be translated, so there is no English fallback here.
    notice = _translate_notice(code, name, system_prompt, model, reasoning)

    base.mkdir(parents=True)
    notice_data = {
        "skip": [],
        "nav": load_en_nav(),
        "notice_title": notice["title"],
        "notice_body": notice["body"],
    }
    if "link_label" in notice:
        notice_data["notice_link_label"] = notice["link_label"]
    (base / "nav.json").write_text(
        json.dumps(
            notice_data,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    entries.append({"code": code, "name": name})
    save_registry(entries)
    print(f"initialized locale '{code}' in {base} (model={model})")
    print(f"wrote localized notice into {base / 'nav.json'}")
    print("next steps:")
    print(f"  1. review {base / 'nav.json'} labels and notice (or run --nav later)")
    print(f"  2. OPENROUTER_API_KEY=... python docs/scripts/translate.py {code}")
    return 0


NAV_PROMPT = """\
Translate the navigation labels in the following JSON array into {name}.

Rules:
- Return ONLY the translated JSON document, no code fences, no commentary.
- Keep the exact same structure, nesting, order and every file path unchanged.
- Translate only the human-readable labels (the object keys).

{payload}
"""

NOTICE_PROMPT = """\
Translate the AI-disclosure notice below into {name} ({code}). It is shown
at the top of every machine-translated documentation page.

Rules:
- Return ONLY a JSON object with three string keys, no code fences, no
  commentary: {{"title": "...", "body": "...", "link_label": "..."}}
- "title" is a short noun phrase equivalent to the English title.
- "body" keeps the meaning, tone and paragraph breaks of the English body.
  It has exactly two paragraphs separated by one blank line ("\\n\\n").
  Do NOT include any markdown links or URLs in "body": the per-page link
  to the English original is added automatically by the build.
- "link_label" is a short phrase equivalent to the English label; it is
  used as the visible text of that automatic link.

English title:
{title}

English body:
{body}

English link label:
{label}
"""


def _extract_notice(raw: str) -> dict[str, str]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise I18nError("model did not return JSON for the notice") from None
        data = json.loads(match.group(0))
    title = data.get("title") if isinstance(data, dict) else None
    body = data.get("body") if isinstance(data, dict) else None
    if (
        not isinstance(title, str)
        or not title.strip()
        or not isinstance(body, str)
        or not body.strip()
    ):
        raise I18nError("model returned an incomplete notice translation")
    notice = {"title": title.strip(), "body": body.strip()}
    label = data.get("link_label") if isinstance(data, dict) else None
    if isinstance(label, str) and label.strip():
        notice["link_label"] = label.strip()
    return notice


def _translate_notice(
    code: str,
    name: str,
    system_prompt: str,
    model: str,
    reasoning: str | None = None,
) -> dict[str, str]:
    """One LLM round-trip: localized disclosure notice (title/body/label)."""
    user = NOTICE_PROMPT.format(
        name=name,
        code=code,
        title=NOTICE_TITLE,
        body=NOTICE_BODY,
        label=NOTICE_LINK_LABEL,
    )
    raw = _with_retries(
        lambda: _clean_output(
            _extract_content(_chat(system_prompt, user, model, reasoning))
        ),
        f"notice translation ({code})",
    )
    return _extract_notice(raw)


def _cmd_nav(args: argparse.Namespace) -> int:
    require_registered(args.locale)
    require_locale_files(args.locale)
    validate_nav(args.locale)
    name = _locale_name(args.locale)
    en_nav = load_en_nav()
    model = args.model or os.environ.get("OPENROUTER_MODEL") or DEFAULT_MODEL
    reasoning = args.reasoning or os.environ.get("OPENROUTER_REASONING") or None
    system_prompt = _read_prompt(args.locale)
    user = NAV_PROMPT.format(name=name, payload=json.dumps(en_nav, indent=2))

    def attempt() -> str:
        return _clean_output(
            _extract_content(_chat(system_prompt, user, model, reasoning))
        )

    raw = _with_retries(attempt, f"nav translation ({args.locale})")
    try:
        translated = json.loads(raw)
    except json.JSONDecodeError as error:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            raise I18nError("model did not return JSON") from error
        translated = json.loads(match.group(0))
    validate_nav_structure(en_nav, translated)

    nav_path = LOCALES_DIR / args.locale / "nav.json"
    existing = json.loads(nav_path.read_text(encoding="utf-8"))
    existing["nav"] = translated

    has_notice = (
        isinstance(existing.get("notice_title"), str)
        and bool(existing["notice_title"].strip())
        and isinstance(existing.get("notice_body"), str)
        and bool(existing["notice_body"].strip())
    )
    if args.force or not has_notice:
        # Same command translates the disclosure notice; an existing one is
        # only redone with --force so wording is never duplicated per run.
        notice = _translate_notice(args.locale, name, system_prompt, model, reasoning)
        existing["notice_title"] = notice["title"]
        existing["notice_body"] = notice["body"]
        if "link_label" in notice:
            existing["notice_link_label"] = notice["link_label"]
        print("translated disclosure notice")

    nav_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {nav_path} (model={model})")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("locale", help="target locale code, e.g. fr")
    parser.add_argument(
        "paths",
        nargs="*",
        help="optional English pages/dirs relative to the content root",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--status", action="store_true", help="report freshness; no network"
    )
    mode.add_argument(
        "--nav",
        action="store_true",
        help="(re)translate nav.json labels and the AI-disclosure notice",
    )
    mode.add_argument("--init", action="store_true", help="scaffold a new locale")
    parser.add_argument(
        "--force", action="store_true", help="retranslate even when fresh"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="list planned work; no network"
    )
    parser.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="with --status: exit 2 if stale/missing",
    )
    parser.add_argument(
        "--model", help=f"OpenRouter model id (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--reasoning",
        help="reasoning effort passed to the model, e.g. high (env: OPENROUTER_REASONING)",
    )
    parser.add_argument(
        "--jobs", type=int, default=1, help="parallel requests (default: 1)"
    )
    parser.add_argument(
        "--name", help="with --init: display name stored in locales.json"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.init:
            _get_client()
            return _cmd_init(args)
        if not args.dry_run and not args.status:
            _get_client()
        if args.status:
            return _cmd_status(args)
        if args.nav:
            return _cmd_nav(args)
        return _cmd_translate(args)
    except I18nError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
