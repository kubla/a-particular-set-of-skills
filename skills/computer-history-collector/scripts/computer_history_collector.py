#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Project completed Codex Computer History summaries into Fulcra."""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import fcntl
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import uuid
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

COLLECTOR_NAME = "Computer History Collector"
COLLECTOR_VERSION = "0.2.1"
RUNTIME_SLUG = "computer-history-collector"
LAUNCHD_LABEL = "com.fulcradynamics.computer-history-collector"
MANIFEST_DIRECTORY = "Collector Manifests/Computer History Collector"
DATA_TYPES = {
    "10min": {
        "name": "Computer History (10-minute)",
        "description": "Ten-minute Computer History summaries projected by owner-authorized Computer History Collectors.",
        "duration": dt.timedelta(minutes=10),
    },
    "6h": {
        "name": "Computer History (6-hour)",
        "description": "Six-hour Computer History summaries projected by owner-authorized Computer History Collectors.",
        "duration": dt.timedelta(hours=6),
    },
}
FILENAME_RE = re.compile(
    r"^(?P<stamp>\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})-"
    r"(?P<nonce>[A-Za-z]{4})-(?P<kind>10min|6h)-(?P<slug>.+)\.md$"
)
FRONTMATTER_RE = re.compile(r"\A---\r?\n(?P<header>.*?)\r?\n---\r?\n", re.DOTALL)
END_SUBJECT = r"(?:summary window|captured segment|segment metadata|the segment|the window|event stream|observed activity|visible activity|further activity)"
END_VERB = r"(?:[^\n]{0,100}?\b(?:ended|ending|through|until|endedAt)\b[^\n]{0,30}?)"
FULL_END_RE = re.compile(
    END_SUBJECT
    + END_VERB
    + r"(?P<value>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z)",
    re.IGNORECASE,
)
TIME_END_RE = re.compile(
    END_SUBJECT + END_VERB + r"(?P<value>\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z)",
    re.IGNORECASE,
)
REVERSED_ACTIVITY_END_RE = re.compile(
    r"(?:ended|ending)\s+(?:the\s+)?(?:visible|observed|captured)\s+activity[^\n]{0,80}?"
    r"(?P<value>(?:\d{4}-\d{2}-\d{2}T)?\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z)",
    re.IGNORECASE,
)
KNOWN_APPS = {
    "com.openai.codex": "Codex",
    "com.apple.Safari": "Safari",
    "com.apple.finder": "Finder",
    "com.apple.Terminal": "Terminal",
    "com.apple.systempreferences": "System Settings",
    "com.apple.ActivityMonitor": "Activity Monitor",
    "com.apple.LocalAuthentication.UIAgent": "Local Authentication",
    "com.apple.MobileSMS": "Messages",
    "com.apple.Passwords.MenuBarExtra": "Passwords",
    "com.apple.UserNotificationCenter": "Notification Center",
    "com.apple.appkit.xpc.openAndSavePanelService": "Open and Save Panel",
    "com.apple.dock": "Dock",
    "com.apple.dock.helper": "Dock Helper",
    "com.apple.loginwindow": "Login Window",
    "com.apple.notificationcenterui": "Notification Center",
    "com.anthropic.claudefordesktop": "Claude",
    "us.zoom.xos": "Zoom",
    "com.superhuman.electron": "Superhuman",
    "com.tinyspeck.slackmacgap": "Slack",
    "com.github.GitHubClient": "GitHub Desktop",
    "com.1password.1password": "1Password",
    "com.todesktop.230313mzl4w4u92": "Cursor",
    "com.mitchellh.ghostty": "Ghostty",
}


class CollectorError(RuntimeError):
    """A failure that should be presented without a traceback."""

    def __init__(
        self,
        message: str,
        *,
        condition: str = "collector-error",
        action_required: bool = False,
    ):
        super().__init__(message)
        self.condition = condition
        self.action_required = action_required


@dataclasses.dataclass(frozen=True)
class Summary:
    path: Path
    filename: str
    kind: str
    start: dt.datetime
    end: dt.datetime
    applications: tuple[str, ...]
    content: str
    projected_note: str
    content_hash: str


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def isoformat(value: dt.datetime) -> str:
    return value.astimezone(dt.UTC).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temporary)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectorError(
            f"Cannot read {path}: {exc}",
            condition="local-state-unreadable",
            action_required=True,
        ) from exc


def parse_json_documents(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass
    documents: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CollectorError(
                f"Fulcra returned unrecognized JSON: {exc}",
                condition="fulcra-response-invalid",
            ) from exc
        if isinstance(value, dict):
            documents.append(value)
        elif isinstance(value, list):
            documents.extend(item for item in value if isinstance(item, dict))
    return documents


class FulcraCLI:
    def __init__(self, uvx_path: str):
        self.uvx_path = uvx_path

    @property
    def prefix(self) -> list[str]:
        return [self.uvx_path, "--from", "fulcra-api@latest", "fulcra"]

    def run(
        self,
        *arguments: str,
        input_text: str | None = None,
        check: bool = True,
        interactive: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                [*self.prefix, *arguments],
                input=input_text,
                text=True,
                capture_output=not interactive,
                check=False,
                timeout=None if interactive else 180,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise CollectorError(
                f"Could not run Fulcra CLI: {exc}",
                condition="fulcra-cli-unavailable",
                action_required=True,
            ) from exc
        if check and result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown error").strip()
            raise CollectorError(
                f"Fulcra CLI failed: {detail}", condition="fulcra-cli-failed"
            )
        return result

    def authenticated_user_id(self) -> str:
        result = self.run("user-info", check=False)
        if result.returncode != 0:
            raise CollectorError(
                "Fulcra authentication is unavailable. Run computer-history-collector setup to sign in again.",
                condition="fulcra-authentication-required",
                action_required=True,
            )
        try:
            payload = json.loads(result.stdout)
            user_id = payload["userid"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CollectorError(
                "Fulcra authentication response did not contain a user ID.",
                condition="fulcra-response-invalid",
            ) from exc
        if not isinstance(user_id, str) or not user_id:
            raise CollectorError(
                "Fulcra authentication response did not contain a user ID.",
                condition="fulcra-response-invalid",
            )
        return user_id

    def login(self) -> None:
        result = self.run("auth", "login", interactive=True, check=False)
        if result.returncode != 0:
            raise CollectorError(
                "Fulcra sign-in did not complete.",
                condition="fulcra-authentication-required",
                action_required=True,
            )

    def ensure_data_type(self, kind: str) -> str:
        specification = DATA_TYPES[kind]
        response = self.run("catalog", "--recordable-only", "-n", specification["name"])
        matches = [
            item
            for item in parse_json_documents(response.stdout)
            if item.get("name") == specification["name"]
        ]
        if len(matches) > 1:
            raise CollectorError(
                f"More than one data type is named {specification['name']!r}; choose unique names before setup.",
                condition="ambiguous-data-type",
                action_required=True,
            )
        if matches:
            identifier = str(matches[0].get("id", ""))
            if "/" in identifier:
                return identifier
            if identifier:
                return f"DurationAnnotation/{identifier}"
        created = self.run(
            "data-type",
            "create",
            "DurationAnnotation",
            specification["name"],
            "-d",
            specification["description"],
            "--add-to-timeline",
        )
        objects = parse_json_documents(created.stdout)
        if len(objects) != 1 or not objects[0].get("id"):
            raise CollectorError(
                f"Fulcra did not return the created {specification['name']} ID.",
                condition="fulcra-response-invalid",
            )
        return f"DurationAnnotation/{objects[0]['id']}"

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        self.run("file", "upload", str(local_path), remote_path)

    def stat_file(self, remote_path: str) -> bool:
        return self.run("file", "stat", remote_path, check=False).returncode == 0

    def record(
        self,
        data_type: str,
        record: dict[str, Any],
        tags: Iterable[str],
        sources: Iterable[str],
    ) -> None:
        arguments = ["record", data_type]
        for tag in tags:
            arguments.extend(("--tag", tag))
        for source in sources:
            arguments.extend(("--source", source))
        self.run(*arguments, input_text=json.dumps(record, separators=(",", ":")))

    def delete_record(self, data_type: str, record_id: str) -> None:
        result = self.run("delete", data_type, record_id, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "unknown error").strip()
            if "not found" not in detail.lower():
                raise CollectorError(
                    f"Could not retire the prior Timeline revision: {detail}",
                    condition="revision-cleanup-failed",
                )


def default_state_dir() -> Path:
    override = os.environ.get("COMPUTER_HISTORY_COLLECTOR_HOME")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / "Library" / "Application Support" / "Fulcra" / RUNTIME_SLUG


def default_source_folder() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return codex_home / "memories" / "extensions" / "skysight" / "resources"


def computer_name() -> str:
    result = subprocess.run(
        ["/usr/sbin/scutil", "--get", "ComputerName"],
        text=True,
        capture_output=True,
        check=False,
    )
    name = result.stdout.strip()
    if not name:
        name = subprocess.run(
            ["/bin/hostname", "-s"], text=True, capture_output=True, check=False
        ).stdout.strip()
    if not name:
        raise CollectorError(
            "Could not determine this Mac's computer name.",
            condition="computer-name-unavailable",
            action_required=True,
        )
    return name


def remote_component(value: str) -> str:
    return urllib.parse.quote(value, safe=" -_.()")


def parse_applications(header: str) -> tuple[str, ...]:
    match = re.search(r"(?m)^applications:\s*\[(?P<items>.*)\]\s*$", header)
    if not match or not match.group("items").strip():
        return ()
    applications = []
    for raw in match.group("items").split(","):
        value = raw.strip().strip("'\"")
        if value and value not in applications:
            applications.append(value)
    return tuple(applications)


def explicit_end(
    content: str, start: dt.datetime, nominal_end: dt.datetime
) -> dt.datetime | None:
    candidates: list[dt.datetime] = []
    for match in FULL_END_RE.finditer(content):
        with contextlib.suppress(ValueError):
            candidates.append(
                dt.datetime.fromisoformat(match.group("value").replace("Z", "+00:00"))
            )
    for match in TIME_END_RE.finditer(content):
        value = match.group("value")
        with contextlib.suppress(ValueError):
            parsed_time = dt.time.fromisoformat(value.removesuffix("Z")).replace(
                tzinfo=dt.UTC
            )
            candidate = dt.datetime.combine(start.date(), parsed_time)
            if candidate < start - dt.timedelta(hours=12):
                candidate += dt.timedelta(days=1)
            candidates.append(candidate)
    for match in REVERSED_ACTIVITY_END_RE.finditer(content):
        value = match.group("value")
        with contextlib.suppress(ValueError):
            if "T" in value:
                candidates.append(
                    dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                )
            else:
                parsed_time = dt.time.fromisoformat(value.removesuffix("Z")).replace(
                    tzinfo=dt.UTC
                )
                candidates.append(dt.datetime.combine(start.date(), parsed_time))
    plausible = [
        candidate
        for candidate in candidates
        if start <= candidate <= nominal_end + dt.timedelta(minutes=2)
    ]
    return max(plausible) if plausible else None


def project_note(content: str) -> str:
    matches = list(re.finditer(r"(?m)^## Citations[ \t]*\r?$", content))
    if not matches:
        return content
    match = matches[-1]
    if re.search(r"(?m)^#{1,2}[ \t]+", content[match.end() :]):
        return content
    return content[: match.start()].rstrip() + "\n"


def parse_summary(path: Path) -> Summary:
    match = FILENAME_RE.match(path.name)
    if not match:
        raise CollectorError(
            f"Unsupported Computer History filename: {path.name}",
            condition="source-format-changed",
            action_required=True,
        )
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CollectorError(
            f"Cannot read {path}: {exc}", condition="source-unreadable"
        ) from exc
    frontmatter = FRONTMATTER_RE.match(content)
    if not frontmatter:
        raise CollectorError(
            f"Computer History file has no expected YAML frontmatter: {path.name}",
            condition="source-format-changed",
            action_required=True,
        )
    kind = match.group("kind")
    start = dt.datetime.strptime(match.group("stamp"), "%Y-%m-%dT%H-%M-%S").replace(
        tzinfo=dt.UTC
    )
    nominal_end = start + DATA_TYPES[kind]["duration"]
    end = explicit_end(content, start, nominal_end) or nominal_end
    return Summary(
        path=path,
        filename=path.name,
        kind=kind,
        start=start,
        end=end,
        applications=parse_applications(frontmatter.group("header")),
        content=content,
        projected_note=project_note(content),
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def split_words(value: str) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    value = re.sub(r"[-_]+", " ", value)
    return " ".join(
        part.upper() if len(part) <= 2 else part.capitalize() for part in value.split()
    )


def application_tag_name(bundle_id: str) -> str:
    if bundle_id in KNOWN_APPS:
        return KNOWN_APPS[bundle_id]
    query = f"kMDItemCFBundleIdentifier == '{bundle_id.replace(chr(39), chr(92) + chr(39))}'"
    found = subprocess.run(
        ["/usr/bin/mdfind", query], text=True, capture_output=True, check=False
    ).stdout.splitlines()
    for candidate in found:
        display = (
            subprocess.run(
                ["/usr/bin/mdls", "-raw", "-name", "kMDItemDisplayName", candidate],
                text=True,
                capture_output=True,
                check=False,
            )
            .stdout.strip()
            .strip('"')
        )
        if display and display != "(null)":
            return display.removesuffix(".app")
    tail = bundle_id.rsplit(".", 1)[-1]
    if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{1,40}", tail) and not any(
        character.isdigit() for character in tail
    ):
        return split_words(tail)
    return bundle_id


def record_tag_names(
    computer: str,
    applications: Iterable[str],
    cached_application_tag_names: Mapping[str, str] | None = None,
) -> list[str]:
    tags = [computer]
    for bundle_id in applications:
        if (
            cached_application_tag_names is not None
            and bundle_id in cached_application_tag_names
        ):
            tag = cached_application_tag_names[bundle_id]
        else:
            tag = application_tag_name(bundle_id)
        if tag not in tags:
            tags.append(tag)
    return tags


def stable_record_id(
    user_id: str, computer: str, filename: str, content_hash: str
) -> str:
    namespace = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"fulcra://context-collector/computer-history/{user_id}/{urllib.parse.quote(computer, safe='')}",
    )
    return str(uuid.uuid5(namespace, f"{filename}:{content_hash}"))


def source_names(computer: str) -> tuple[str, str, str]:
    return ("Codex", "Codex Computer History", f"Codex Computer History on {computer}")


def projection_preview(summary: Summary, computer: str) -> dict[str, Any]:
    return {
        "source_file": str(summary.path),
        "remote_file": (
            f"Codex/{remote_component(computer)}/memories/extensions/skysight/resources/"
            f"{summary.filename}"
        ),
        "data_type": DATA_TYPES[summary.kind]["name"],
        "annotation": {
            "recorded_at": {
                "start_time": isoformat(summary.start),
                "end_time": isoformat(summary.end),
            },
            "note": summary.projected_note,
        },
        "tag_names": record_tag_names(computer, summary.applications),
        "collector_sources": list(source_names(computer)),
    }


def preview_summary_path(
    requested_file: Path | None,
    source_folder: Path,
    *,
    minimum_age_seconds: int,
) -> Path:
    if requested_file is not None:
        path = requested_file.expanduser().resolve()
        candidates = [path]
    else:
        if not source_folder.is_dir():
            raise CollectorError(
                f"Computer History folder does not exist: {source_folder}",
                condition="source-folder-unavailable",
                action_required=True,
            )
        candidates = sorted(
            (
                path
                for path in source_folder.iterdir()
                if path.is_file() and FILENAME_RE.match(path.name)
            ),
            reverse=True,
        )
    now_timestamp = utc_now().timestamp()
    for path in candidates:
        if not path.is_file() or not FILENAME_RE.match(path.name):
            continue
        if now_timestamp - path.stat().st_mtime >= minimum_age_seconds:
            return path
    if requested_file is not None:
        raise CollectorError(
            f"The requested file is not a completed, stable Computer History summary: {requested_file}",
            condition="source-not-ready",
        )
    raise CollectorError(
        "No completed, stable Computer History summaries are available to preview.",
        condition="source-not-ready",
    )


def manifest_markdown(config: dict[str, Any], ended_at: str | None = None) -> str:
    state = (
        "Collection has ended. Existing projected context and source-file snapshots are retained."
        if ended_at
        else "Collection is active."
    )
    ended = f"\n- Ended: {ended_at}" if ended_at else ""
    return f"""# Collector

- Name: {COLLECTOR_NAME}
- Version: {config.get("collector_version", COLLECTOR_VERSION)}
- Instance: {config["computer_name"]}
- State: {state}{ended}

# Sources

- Completed derived Markdown summaries from Codex Computer History on `{config["computer_name"]}`.
- Local source folder at setup: `{config["source_folder"]}`.
- Raw Computer History events and actively growing files are outside this collector's boundary.

# Intended outputs

- Fulcra Files beneath `Codex/{remote_component(config["computer_name"])}/memories/extensions/skysight/resources/`.
- Duration annotations in `Computer History (10-minute)` and `Computer History (6-hour)`.
- Files preserve each completed Markdown summary unchanged; annotation notes omit its terminal Citations section.
- Tags identify the computer and applications listed in the summary metadata.
- Timeline records and source files are independently permissionable and are not directly linked.

# Collection behavior

- A per-user macOS LaunchAgent sweeps about every ten minutes.
- Existing local files whose contents change are revisions: Fulcra retains a new file snapshot and the collector replaces the prior Timeline projection.
- Missing local files do not cause remote deletion.
- The collector's local Projection Map provides idempotency and can be rebuilt from owner context if necessary.
"""


class Collector:
    def __init__(self, state_dir: Path, cli: FulcraCLI):
        self.state_dir = state_dir
        self.cli = cli
        self.config_path = state_dir / "config.json"
        self.map_path = state_dir / "projection-map.json"
        self.status_path = state_dir / "status.json"
        self.lock_path = state_dir / "collector.lock"

    def config(self) -> dict[str, Any]:
        config = read_json(self.config_path, None)
        if not isinstance(config, dict):
            raise CollectorError(
                "Collector setup has not completed. Run computer-history-collector setup.",
                condition="setup-required",
                action_required=True,
            )
        return config

    @contextlib.contextmanager
    def lock(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+") as stream:
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise CollectorError(
                    "Another collector operation is already running.",
                    condition="collector-busy",
                ) from exc
            yield

    def update_status(
        self,
        state: str,
        message: str,
        *,
        condition: str | None = None,
        notify: bool = False,
        counts: dict[str, int] | None = None,
    ) -> None:
        previous = read_json(self.status_path, {})
        previous_condition = (
            previous.get("condition") if isinstance(previous, dict) else None
        )
        status = {
            "collector_version": COLLECTOR_VERSION,
            "state": state,
            "message": message,
            "condition": condition,
            "checked_at": isoformat(utc_now()),
            "counts": counts or {},
        }
        atomic_json(self.status_path, status)
        if notify and state == "action_required" and condition != previous_condition:
            script = "on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run"
            subprocess.run(
                ["/usr/bin/osascript", "-e", script, COLLECTOR_NAME, message],
                text=True,
                capture_output=True,
                check=False,
            )

    def write_manifest(
        self, config: dict[str, Any], *, ended_at: str | None = None
    ) -> None:
        content = manifest_markdown(config, ended_at=ended_at)
        digest = hashlib.sha256(content.encode()).hexdigest()
        if not ended_at and config.get("manifest_hash") == digest:
            return
        local_manifest = self.state_dir / "collector-manifest.md"
        local_manifest.write_text(content, encoding="utf-8")
        self.cli.upload_file(local_manifest, config["manifest_path"])
        config["manifest_hash"] = digest
        atomic_json(self.config_path, config)

    def sweep(
        self, *, notify: bool = True, minimum_age_seconds: int = 30
    ) -> dict[str, int]:
        with self.lock():
            try:
                counts = self._sweep(minimum_age_seconds=minimum_age_seconds)
                self.update_status(
                    "ok", "The most recent sweep completed.", counts=counts
                )
                return counts
            except CollectorError as exc:
                state = "action_required" if exc.action_required else "error"
                self.update_status(
                    state, str(exc), condition=exc.condition, notify=notify
                )
                raise

    def _sweep(self, *, minimum_age_seconds: int) -> dict[str, int]:
        config = self.config()
        user_id = self.cli.authenticated_user_id()
        if user_id != config.get("fulcra_user_id"):
            raise CollectorError(
                "Fulcra is signed in as a different owner. Run setup to confirm the intended account.",
                condition="fulcra-owner-changed",
                action_required=True,
            )
        source_folder = Path(config["source_folder"])
        if not source_folder.is_dir():
            raise CollectorError(
                f"Computer History folder is unavailable: {source_folder}",
                condition="source-folder-unavailable",
                action_required=True,
            )
        projection_map = read_json(self.map_path, {"version": 1, "files": {}})
        if not isinstance(projection_map, dict) or not isinstance(
            projection_map.get("files"), dict
        ):
            raise CollectorError(
                "Projection Map has an unsupported format.",
                condition="projection-map-invalid",
                action_required=True,
            )
        entries = projection_map["files"]
        now_timestamp = utc_now().timestamp()
        candidates = sorted(
            path
            for path in source_folder.iterdir()
            if path.is_file() and FILENAME_RE.match(path.name)
        )
        counts = {
            "discovered": len(candidates),
            "created": 0,
            "revised": 0,
            "unchanged": 0,
            "deferred": 0,
        }
        config_changed = False
        legacy_application_names = config.pop("application_names", None)
        application_tag_names = config.get("application_tag_names")
        if application_tag_names is None:
            application_tag_names = {}
            config["application_tag_names"] = application_tag_names
            config_changed = True
        if not isinstance(application_tag_names, dict):
            raise CollectorError(
                "Application tag name cache has an unsupported format.",
                condition="collector-config-invalid",
                action_required=True,
            )
        if legacy_application_names is not None:
            if not isinstance(legacy_application_names, dict):
                raise CollectorError(
                    "Legacy application name cache has an unsupported format.",
                    condition="collector-config-invalid",
                    action_required=True,
                )
            for bundle_id, tag_name in legacy_application_names.items():
                application_tag_names.setdefault(bundle_id, tag_name)
            config_changed = True
        for path in candidates:
            before = path.stat()
            if now_timestamp - before.st_mtime < minimum_age_seconds:
                counts["deferred"] += 1
                continue
            summary = parse_summary(path)
            after = path.stat()
            if (
                before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
            ):
                counts["deferred"] += 1
                continue
            prior = entries.get(summary.filename)
            if prior and prior.get("content_hash") == summary.content_hash:
                counts["unchanged"] += 1
                continue
            for bundle_id in summary.applications:
                if bundle_id not in application_tag_names:
                    application_tag_names[bundle_id] = application_tag_name(bundle_id)
                    config_changed = True
            remote_path = (
                f"Codex/{remote_component(config['computer_name'])}/memories/extensions/skysight/resources/"
                f"{summary.filename}"
            )
            record_id = stable_record_id(
                user_id, config["computer_name"], summary.filename, summary.content_hash
            )
            record = {
                "id": record_id,
                "recorded_at": {
                    "start_time": isoformat(summary.start),
                    "end_time": isoformat(summary.end),
                },
                "note": summary.projected_note,
            }
            tags = record_tag_names(
                config["computer_name"],
                summary.applications,
                application_tag_names,
            )
            self.cli.upload_file(path, remote_path)
            self.cli.record(
                config["data_types"][summary.kind],
                record,
                tags,
                source_names(config["computer_name"]),
            )
            if prior and prior.get("record_id") and prior["record_id"] != record_id:
                self.cli.delete_record(
                    config["data_types"][summary.kind], prior["record_id"]
                )
                counts["revised"] += 1
            else:
                counts["created"] += 1
            entries[summary.filename] = {
                "content_hash": summary.content_hash,
                "record_id": record_id,
                "remote_file": remote_path,
                "kind": summary.kind,
                "projected_at": isoformat(utc_now()),
            }
            projection_map["updated_at"] = isoformat(utc_now())
            atomic_json(self.map_path, projection_map)
        if config_changed:
            atomic_json(self.config_path, config)
        return counts


def uv_tool_path(executable: str) -> str:
    found = shutil.which(executable)
    if not found:
        raise CollectorError(
            f"{executable} is required. Install uv, then run setup again.",
            condition="uv-required",
            action_required=True,
        )
    # Preserve a stable PATH entry such as /opt/homebrew/bin/uv instead of
    # resolving it to a versioned Homebrew Cellar target.
    return str(Path(found).expanduser().absolute())


def install_runtime(state_dir: Path, source_script: Path, resolved_uv: str) -> None:
    library = state_dir / "lib"
    binary = state_dir / "bin"
    logs = state_dir / "logs"
    for directory in (library, binary, logs):
        directory.mkdir(parents=True, exist_ok=True)
    installed_script = library / "computer_history_collector.py"
    shutil.copy2(source_script, installed_script)
    launcher = binary / RUNTIME_SLUG
    launcher.write_text(
        "#!/bin/sh\n"
        + f'exec "{resolved_uv}" run --script "{installed_script}" "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)


def launch_agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


def install_launch_agent(state_dir: Path, resolved_uv: str) -> None:
    plist_path = launch_agent_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "Label": LAUNCHD_LABEL,
        "ProgramArguments": [
            resolved_uv,
            "run",
            "--script",
            str(state_dir / "lib" / "computer_history_collector.py"),
            "sweep",
        ],
        "RunAtLoad": True,
        "StartInterval": 600,
        "ProcessType": "Background",
        "StandardOutPath": str(state_dir / "logs" / "collector.log"),
        "StandardErrorPath": str(state_dir / "logs" / "collector-error.log"),
    }
    if override := os.environ.get("COMPUTER_HISTORY_COLLECTOR_HOME"):
        payload["EnvironmentVariables"] = {"COMPUTER_HISTORY_COLLECTOR_HOME": override}
    with plist_path.open("wb") as stream:
        plistlib.dump(payload, stream)
    domain = f"gui/{os.getuid()}"
    subprocess.run(
        ["/bin/launchctl", "bootout", f"{domain}/{LAUNCHD_LABEL}"],
        capture_output=True,
        check=False,
    )
    result = subprocess.run(
        ["/bin/launchctl", "bootstrap", domain, str(plist_path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise CollectorError(
            f"Could not install the LaunchAgent: {result.stderr.strip()}",
            condition="launch-agent-install-failed",
            action_required=True,
        )


def setup(args: argparse.Namespace) -> int:
    state_dir = default_state_dir()
    resolved_uv = uv_tool_path("uv")
    resolved_uvx = uv_tool_path("uvx")
    cli = FulcraCLI(resolved_uvx)
    try:
        user_id = cli.authenticated_user_id()
    except CollectorError as exc:
        if args.non_interactive or not exc.action_required:
            raise
        cli.login()
        user_id = cli.authenticated_user_id()
    source_folder = (
        Path(args.source_folder or default_source_folder()).expanduser().resolve()
    )
    if not source_folder.is_dir():
        raise CollectorError(
            f"Computer History folder does not exist: {source_folder}",
            condition="source-folder-unavailable",
            action_required=True,
        )
    machine = args.computer_name or computer_name()
    if not machine.strip():
        raise CollectorError(
            "Computer name cannot be empty.",
            condition="computer-name-unavailable",
            action_required=True,
        )
    install_runtime(state_dir, Path(__file__).resolve(), resolved_uv)
    collector = Collector(state_dir, cli)
    prior = read_json(collector.config_path, {})
    config = {
        **(prior if isinstance(prior, dict) else {}),
        "version": 1,
        "collector": COLLECTOR_NAME,
        "collector_version": COLLECTOR_VERSION,
        "computer_name": machine,
        "source_folder": str(source_folder),
        "fulcra_user_id": user_id,
        "uv_path": resolved_uv,
        "uvx_path": resolved_uvx,
        "manifest_path": f"{MANIFEST_DIRECTORY}/{remote_component(machine)}.md",
        "data_types": {kind: cli.ensure_data_type(kind) for kind in DATA_TYPES},
        "configured_at": isoformat(utc_now()),
    }
    atomic_json(collector.config_path, config)
    collector.write_manifest(config)
    counts = collector.sweep(notify=False, minimum_age_seconds=args.minimum_age_seconds)
    if not args.no_launchd:
        install_launch_agent(state_dir, resolved_uv)
    print(f"Computer History Collector {COLLECTOR_VERSION} is configured for {machine}.")
    print(f"Fulcra owner: {user_id}")
    print(
        f"Initial sweep: {counts['created']} created, {counts['revised']} revised, {counts['unchanged']} unchanged, {counts['deferred']} deferred."
    )
    print(f"Runtime: {state_dir / 'bin' / RUNTIME_SLUG}")
    return 0


def command_preview(args: argparse.Namespace) -> int:
    source_folder = (
        Path(args.source_folder or default_source_folder()).expanduser().resolve()
    )
    path = preview_summary_path(
        args.file,
        source_folder,
        minimum_age_seconds=args.minimum_age_seconds,
    )
    before = path.stat()
    summary = parse_summary(path)
    after = path.stat()
    if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise CollectorError(
            f"Computer History file changed while being previewed: {path}",
            condition="source-not-ready",
        )
    preview = projection_preview(summary, args.computer_name or computer_name())
    if args.json:
        print(json.dumps(preview, indent=2))
        return 0
    print(f"Source file: {preview['source_file']}")
    print(f"Remote file: {preview['remote_file']}")
    print(f"Data type: {preview['data_type']}")
    print(
        "Interval: "
        f"{preview['annotation']['recorded_at']['start_time']} -> "
        f"{preview['annotation']['recorded_at']['end_time']}"
    )
    print("Tag names:")
    for tag in preview["tag_names"]:
        print(f"- {tag}")
    print("Collector sources:")
    for source in preview["collector_sources"]:
        print(f"- {source}")
    print("Fulcra also adds its CLI and annotation-type provenance sources.")
    print("Note (projected Markdown; terminal Citations section omitted):")
    print("--- BEGIN NOTE ---")
    print(preview["annotation"]["note"], end="")
    if not preview["annotation"]["note"].endswith("\n"):
        print()
    print("--- END NOTE ---")
    return 0


def command_sweep(args: argparse.Namespace) -> int:
    state_dir = default_state_dir()
    config = read_json(state_dir / "config.json", {})
    cli = FulcraCLI(str(config.get("uvx_path") or uv_tool_path("uvx")))
    counts = Collector(state_dir, cli).sweep(
        notify=not args.no_notify, minimum_age_seconds=args.minimum_age_seconds
    )
    print(
        f"Sweep complete: {counts['created']} created, {counts['revised']} revised, {counts['unchanged']} unchanged, {counts['deferred']} deferred."
    )
    return 0


def command_status(_args: argparse.Namespace) -> int:
    state_dir = default_state_dir()
    status = read_json(state_dir / "status.json", None)
    if not isinstance(status, dict):
        print("Computer History Collector has no Projection Status. Run setup.")
        return 1
    print(f"Version: {status.get('collector_version', COLLECTOR_VERSION)}")
    print(f"State: {status.get('state', 'unknown')}")
    print(f"Checked: {status.get('checked_at', 'unknown')}")
    print(f"Message: {status.get('message', '')}")
    counts = status.get("counts") or {}
    if counts:
        print(
            "Last sweep: "
            + ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        )
    return 0 if status.get("state") == "ok" else 1


def command_diagnose(_args: argparse.Namespace) -> int:
    state_dir = default_state_dir()
    problems: list[str] = []
    try:
        config = read_json(state_dir / "config.json", None)
        if not isinstance(config, dict):
            raise CollectorError("setup is incomplete")
        source = Path(config["source_folder"])
        if not source.is_dir():
            problems.append(f"source folder is unavailable: {source}")
        if not Path(config["uvx_path"]).exists():
            problems.append(f"configured uvx is unavailable: {config['uvx_path']}")
        cli = FulcraCLI(config["uvx_path"])
        cli.authenticated_user_id()
        if not cli.stat_file(config["manifest_path"]):
            problems.append(
                f"collector manifest is unavailable: {config['manifest_path']}"
            )
        if launch_agent_path().exists():
            target = f"gui/{os.getuid()}/{LAUNCHD_LABEL}"
            result = subprocess.run(
                ["/bin/launchctl", "print", target], capture_output=True, check=False
            )
            if result.returncode != 0:
                problems.append("LaunchAgent plist exists but the job is not loaded")
        else:
            problems.append("LaunchAgent plist is not installed")
    except (CollectorError, KeyError) as exc:
        problems.append(str(exc))
    if problems:
        print("Diagnosis found:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("Diagnosis found no problems.")
    return 0


def validate_removal_target(state_dir: Path, config: dict[str, Any]) -> None:
    if config.get("collector") != COLLECTOR_NAME:
        raise CollectorError(
            f"Refusing to remove a runtime without {COLLECTOR_NAME} identity: {state_dir}",
            condition="unsafe-runtime-path",
            action_required=True,
        )
    expected_parent = Path.home() / "Library" / "Application Support" / "Fulcra"
    if "COMPUTER_HISTORY_COLLECTOR_HOME" not in os.environ:
        safe = state_dir.name == RUNTIME_SLUG and state_dir.parent == expected_parent
    else:
        safe = all(
            candidate.exists()
            for candidate in (
                state_dir / "config.json",
                state_dir / "bin" / RUNTIME_SLUG,
                state_dir / "lib" / "computer_history_collector.py",
            )
        )
    if not safe:
        raise CollectorError(
            f"Refusing to remove unexpected runtime path: {state_dir}",
            condition="unsafe-runtime-path",
            action_required=True,
        )


def command_uninstall(_args: argparse.Namespace) -> int:
    state_dir = default_state_dir()
    config = read_json(state_dir / "config.json", None)
    if not isinstance(config, dict):
        raise CollectorError(
            "Collector setup was not found.", condition="setup-required"
        )
    validate_removal_target(state_dir, config)
    cli = FulcraCLI(str(config.get("uvx_path") or uv_tool_path("uvx")))
    collector = Collector(state_dir, cli)
    collector.write_manifest(config, ended_at=isoformat(utc_now()))
    domain = f"gui/{os.getuid()}"
    subprocess.run(
        ["/bin/launchctl", "bootout", f"{domain}/{LAUNCHD_LABEL}"],
        capture_output=True,
        check=False,
    )
    plist_path = launch_agent_path()
    with contextlib.suppress(FileNotFoundError):
        plist_path.unlink()
    shutil.rmtree(state_dir)
    print(
        "Computer History Collector was removed from this Mac. Fulcra context and file snapshots were retained."
    )
    return 0


def parser() -> argparse.ArgumentParser:
    command_parser = argparse.ArgumentParser(prog=RUNTIME_SLUG, description=__doc__)
    subcommands = command_parser.add_subparsers(dest="command", required=True)
    setup_parser = subcommands.add_parser(
        "setup", help="Configure, backfill, and schedule collection"
    )
    setup_parser.add_argument("--source-folder", type=Path)
    setup_parser.add_argument("--computer-name")
    setup_parser.add_argument("--non-interactive", action="store_true")
    setup_parser.add_argument(
        "--no-launchd", action="store_true", help=argparse.SUPPRESS
    )
    setup_parser.add_argument(
        "--minimum-age-seconds", type=int, default=30, help=argparse.SUPPRESS
    )
    setup_parser.set_defaults(handler=setup)
    preview_parser = subcommands.add_parser(
        "preview", help="Show one projected annotation without writing to Fulcra"
    )
    preview_parser.add_argument("file", nargs="?", type=Path)
    preview_parser.add_argument("--source-folder", type=Path)
    preview_parser.add_argument("--computer-name")
    preview_parser.add_argument("--json", action="store_true")
    preview_parser.add_argument(
        "--minimum-age-seconds", type=int, default=30, help=argparse.SUPPRESS
    )
    preview_parser.set_defaults(handler=command_preview)
    sweep_parser = subcommands.add_parser(
        "sweep", help="Project new and revised summaries now"
    )
    sweep_parser.add_argument(
        "--no-notify", action="store_true", help=argparse.SUPPRESS
    )
    sweep_parser.add_argument(
        "--minimum-age-seconds", type=int, default=30, help=argparse.SUPPRESS
    )
    sweep_parser.set_defaults(handler=command_sweep)
    status_parser = subcommands.add_parser(
        "status", help="Show passive Projection Status"
    )
    status_parser.set_defaults(handler=command_status)
    diagnose_parser = subcommands.add_parser(
        "diagnose",
        help="Check configuration, authentication, source, manifest, and scheduler",
    )
    diagnose_parser.set_defaults(handler=command_diagnose)
    uninstall_parser = subcommands.add_parser(
        "uninstall", help="Stop collection without deleting owner context"
    )
    uninstall_parser.set_defaults(handler=command_uninstall)
    return command_parser


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except CollectorError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
