#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Audit the author's live Computer History corpus for source-format changes."""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys
from pathlib import Path


FILENAME_RE = re.compile(
    r"^(?P<stamp>\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})-"
    r"(?P<nonce>[A-Za-z]{4})-(?P<kind>10min|6h)-(?P<slug>.+)\.md$"
)
FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<header>.*?)\r?\n---\r?\n", re.DOTALL)
CITATIONS_HEADING_RE = re.compile(r"(?m)^## Citations[ \t]*\r?$")
LATER_SECTION_RE = re.compile(r"(?m)^#{1,2}[ \t]+")


def default_source_folder() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "memories" / "extensions" / "skysight" / "resources"


def citation_category(target: str) -> str | None:
    if FILENAME_RE.fullmatch(Path(target).name):
        return "computer-history-summary"
    if (
        target.startswith("/")
        and "/ComputerUse/Skysight/segments/" in target
        and target.endswith("/events.jsonl")
    ):
        return "computer-use-events-cache"
    if (
        target.startswith("/")
        and "/ComputerUse/Skysight/segments/" in target
        and target.endswith("/metadata.json")
    ):
        return "computer-use-segment-metadata"
    if target.startswith("/") and target.endswith(".md"):
        return "local-markdown"
    return None


def audit(source_folder: Path) -> tuple[collections.Counter[str], list[str], int]:
    categories: collections.Counter[str] = collections.Counter()
    errors: list[str] = []
    paths = sorted(path for path in source_folder.glob("*.md") if path.is_file())
    if not paths:
        return categories, [f"No Markdown files found in {source_folder}"], 0

    for path in paths:
        filename = FILENAME_RE.fullmatch(path.name)
        if not filename:
            errors.append(f"{path.name}: unexpected filename")
            continue
        categories[f"summary-kind:{filename.group('kind')}"] += 1
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{path.name}: unreadable: {exc}")
            continue

        frontmatter = FRONTMATTER_RE.match(content)
        if not frontmatter:
            errors.append(f"{path.name}: expected YAML frontmatter is missing")
        else:
            header = frontmatter.group("header")
            for field in ("title", "description", "applications"):
                if not re.search(rf"(?m)^{field}:", header):
                    errors.append(f"{path.name}: frontmatter field {field!r} is missing")

        headings = list(CITATIONS_HEADING_RE.finditer(content))
        if len(headings) != 1:
            errors.append(
                f"{path.name}: expected one Citations section, found {len(headings)}"
            )
            continue
        tail = content[headings[0].end() :]
        if LATER_SECTION_RE.search(tail):
            errors.append(f"{path.name}: Citations is no longer the terminal section")
            continue
        entries = [line.strip() for line in tail.splitlines() if line.strip()]
        if not entries:
            errors.append(f"{path.name}: Citations section is empty")
            continue
        for entry in entries:
            if not entry.startswith("- "):
                errors.append(f"{path.name}: non-bullet citation content: {entry!r}")
                continue
            target = entry.removeprefix("- ").strip()
            category = citation_category(target)
            if category is None:
                errors.append(f"{path.name}: new citation category: {target!r}")
            else:
                categories[f"citation:{category}"] += 1

    return categories, errors, len(paths)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect changes in the author's live Computer History Markdown format."
    )
    parser.add_argument(
        "source_folder",
        nargs="?",
        type=Path,
        default=default_source_folder(),
    )
    args = parser.parse_args()
    source_folder = args.source_folder.expanduser().resolve()
    categories, errors, file_count = audit(source_folder)

    print(f"Audited {file_count} Computer History Markdown files in {source_folder}")
    for category, count in sorted(categories.items()):
        print(f"{category}: {count}")
    if errors:
        print("Source-format changes detected:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("No source-format changes detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
