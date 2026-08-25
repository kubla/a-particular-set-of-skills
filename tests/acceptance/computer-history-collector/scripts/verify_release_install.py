#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Verify a live Computer History Collector installation without changing it."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path
from typing import Any


LABEL = "com.fulcradynamics.computer-history-collector"
STATE_DIR = (
    Path.home()
    / "Library"
    / "Application Support"
    / "Fulcra"
    / "computer-history-collector"
)
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
INSTALLED_SKILL = Path.home() / ".agents" / "skills" / "computer-history-collector"


class VerificationError(RuntimeError):
    pass


def run(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        arguments,
        text=True,
        capture_output=True,
        check=False,
        timeout=300,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown error").strip()
        raise VerificationError(f"{' '.join(arguments)} failed: {detail}")
    return result


def fulcra(*arguments: str) -> str:
    return run("uvx", "--from", "fulcra-api@latest", "fulcra", *arguments).stdout


def documents(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        return [parsed]
    result: list[dict[str, Any]] = []
    for line in text.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise VerificationError(f"Fulcra returned invalid JSONL: {exc}") from exc
        if isinstance(item, dict):
            result.append(item)
        elif isinstance(item, list):
            result.extend(value for value in item if isinstance(value, dict))
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"Expected a JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instant(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_runtime(path: Path):
    spec = importlib.util.spec_from_file_location("installed_computer_history_collector", path)
    if spec is None or spec.loader is None:
        raise VerificationError(f"Cannot import installed runtime at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def select_samples(summaries: list[Any]) -> list[Any]:
    samples: list[Any] = []
    for kind in ("10min", "6h"):
        matches = sorted(
            (summary for summary in summaries if summary.kind == kind),
            key=lambda summary: summary.start,
        )
        if matches:
            samples.extend([matches[0], matches[-1]] if len(matches) > 1 else matches)
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify an installed collector, scheduler, and Fulcra projection."
    )
    parser.add_argument("--expected-owner-id", required=True)
    parser.add_argument("--skill-dir", type=Path, default=INSTALLED_SKILL)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    skill_dir = args.skill_dir.expanduser().resolve()
    installed_script = skill_dir / "scripts" / "computer_history_collector.py"
    runtime_script = STATE_DIR / "lib" / "computer_history_collector.py"
    config_path = STATE_DIR / "config.json"
    map_path = STATE_DIR / "projection-map.json"
    status_path = STATE_DIR / "status.json"
    for path in (
        skill_dir / "SKILL.md",
        installed_script,
        runtime_script,
        config_path,
        map_path,
        status_path,
        PLIST_PATH,
    ):
        require(path.is_file(), f"Missing expected file: {path}")
    if failures:
        raise VerificationError("; ".join(failures))

    runtime = load_runtime(runtime_script)
    config = load_json(config_path)
    projection_map = load_json(map_path)
    status = load_json(status_path)
    source_folder = Path(str(config.get("source_folder", "")))
    require(source_folder.is_dir(), f"Configured source folder is unavailable: {source_folder}")
    require(
        config.get("fulcra_user_id") == args.expected_owner_id,
        "Configured owner ID does not match the expected owner",
    )
    require(
        sha256(installed_script) == sha256(runtime_script),
        "Managed runtime does not match the installed skill runtime",
    )
    require(status.get("state") == "ok", f"Projection Status is {status.get('state')!r}")

    with PLIST_PATH.open("rb") as stream:
        plist = plistlib.load(stream)
    require(plist.get("Label") == LABEL, "LaunchAgent label is incorrect")
    require(plist.get("StartInterval") == 600, "LaunchAgent interval is not 600 seconds")
    require(plist.get("RunAtLoad") is True, "LaunchAgent is not configured for RunAtLoad")
    arguments = plist.get("ProgramArguments", [])
    require(arguments[-1:] == ["sweep"], "LaunchAgent does not invoke sweep")
    launchctl = run(
        "launchctl",
        "print",
        f"gui/{os.getuid()}/{LABEL}",
        check=False,
    )
    require(launchctl.returncode == 0, "LaunchAgent is not loaded")

    user_info = json.loads(fulcra("user-info"))
    require(user_info.get("userid") == args.expected_owner_id, "Authenticated Fulcra owner changed")
    tag_rows = documents(fulcra("tag", "list"))
    tag_names_by_id = {
        str(row.get("id")): str(row.get("name"))
        for row in tag_rows
        if row.get("id") and row.get("name")
    }

    now = dt.datetime.now(dt.UTC).timestamp()
    paths = sorted(
        path
        for path in source_folder.iterdir()
        if path.is_file()
        and runtime.FILENAME_RE.match(path.name)
        and now - path.stat().st_mtime >= 30
    )
    summaries = [runtime.parse_summary(path) for path in paths]
    entries = projection_map.get("files", {})
    require(isinstance(entries, dict), "Projection Map files value is not an object")
    expected_by_kind: dict[str, list[Any]] = {"10min": [], "6h": []}
    for summary in summaries:
        expected_by_kind[summary.kind].append(summary)
        entry = entries.get(summary.filename) if isinstance(entries, dict) else None
        if not isinstance(entry, dict):
            failures.append(f"Projection Map is missing {summary.filename}")
            continue
        require(
            entry.get("content_hash") == summary.content_hash,
            f"Projection Map hash is stale for {summary.filename}",
        )
        expected_id = runtime.stable_record_id(
            args.expected_owner_id,
            str(config.get("computer_name")),
            summary.filename,
            summary.content_hash,
        )
        require(
            entry.get("record_id") == expected_id,
            f"Projection Map record ID is incorrect for {summary.filename}",
        )

    remote_records: dict[str, dict[str, Any]] = {}
    for kind, kind_summaries in expected_by_kind.items():
        if not kind_summaries:
            continue
        data_type = str(config.get("data_types", {}).get(kind, ""))
        require(bool(data_type), f"Configuration has no data type for {kind}")
        start = min(summary.start for summary in kind_summaries) - dt.timedelta(minutes=1)
        end = max(summary.end for summary in kind_summaries) + dt.timedelta(minutes=1)
        rows = documents(
            fulcra(
                "get-records",
                data_type,
                runtime.isoformat(start),
                runtime.isoformat(end),
            )
        )
        record_ids = [str(row.get("id")) for row in rows if row.get("id")]
        expected_ids = {
            str(entries.get(summary.filename, {}).get("record_id"))
            for summary in kind_summaries
        }
        require(
            len(record_ids) == len(set(record_ids)),
            f"Fulcra returned duplicate {kind} record IDs",
        )
        require(
            set(record_ids) == expected_ids,
            f"Fulcra {kind} record IDs differ from the Projection Map",
        )
        remote_records.update(
            {str(row.get("id")): row for row in rows if row.get("id")}
        )
        for summary in kind_summaries:
            entry = entries.get(summary.filename, {})
            record = remote_records.get(str(entry.get("record_id")))
            if record is None:
                failures.append(f"Fulcra record is missing for {summary.filename}")
                continue
            note = str(record.get("note", ""))
            recorded_at = record.get("recorded_at", {})
            if not isinstance(recorded_at, dict):
                recorded_at = {}
            require(
                instant(recorded_at.get("start_time")) == summary.start,
                f"Start time differs for {summary.filename}",
            )
            require(
                instant(recorded_at.get("end_time")) == summary.end,
                f"End time differs for {summary.filename}",
            )
            require(
                hashlib.sha256(note.encode()).hexdigest()
                == hashlib.sha256(summary.projected_note.encode()).hexdigest(),
                f"Projected note differs for {summary.filename}",
            )
            expected_sources = set(runtime.source_names(str(config.get("computer_name"))))
            require(
                expected_sources.issubset(set(record.get("sources", []))),
                f"Producer sources differ for {summary.filename}",
            )
            expected_tags = {str(config.get("computer_name"))}
            application_tag_names = config.get(
                "application_tag_names", config.get("application_names", {})
            )
            for bundle_id in summary.applications:
                expected_tags.add(
                    str(
                        application_tag_names.get(bundle_id)
                        or runtime.application_tag_name(bundle_id)
                    )
                )
            actual_tags = {
                tag_names_by_id.get(str(tag_id), f"unknown:{tag_id}")
                for tag_id in record.get("tags", [])
            }
            require(actual_tags == expected_tags, f"Tags differ for {summary.filename}")
            require(
                not {"10-minute", "6-hour"}.intersection(actual_tags),
                f"Cadence tag is still present for {summary.filename}",
            )

    sampled_files = []
    for summary in select_samples(summaries):
        entry = entries.get(summary.filename, {})
        remote_path = str(entry.get("remote_file", ""))
        result = run(
            "uvx",
            "--from",
            "fulcra-api@latest",
            "fulcra",
            "file",
            "stat",
            remote_path,
            check=False,
        )
        require(result.returncode == 0, f"Fulcra source file is missing: {remote_path}")
        sampled_files.append(remote_path)

    manifest_path = str(config.get("manifest_path", ""))
    manifest_stat = run(
        "uvx",
        "--from",
        "fulcra-api@latest",
        "fulcra",
        "file",
        "stat",
        manifest_path,
        check=False,
    )
    require(manifest_stat.returncode == 0, f"Collector Manifest is missing: {manifest_path}")

    receipt = {
        "verified_at": runtime.isoformat(dt.datetime.now(dt.UTC)),
        "result": "failed" if failures else "passed",
        "owner_id": args.expected_owner_id,
        "computer_name": config.get("computer_name"),
        "source_folder": str(source_folder),
        "stable_source_files": len(summaries),
        "projection_map_entries": len(entries) if isinstance(entries, dict) else None,
        "remote_records_verified": len(remote_records),
        "catalog_tags_resolved": len(tag_names_by_id),
        "sampled_source_files": sampled_files,
        "collector_manifest": manifest_path,
        "skill_dir": str(skill_dir),
        "projection_status": status.get("state"),
        "launchd_loaded": launchctl.returncode == 0,
        "runtime_sha256": sha256(runtime_script),
        "failures": failures,
    }
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"verification error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
