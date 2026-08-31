#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "certifi",
#   "mcp>=1.9.3",
# ]
# ///
"""Compare exact custom-type writes through Fulcra CLI and MCP interfaces."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import tempfile
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import certifi
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_CONFIG_PATH = "Agent Skills/Image Upgrade/config.json"
SOURCE = "com.fulcradynamics.acceptance.interface-parity"


class ParityTestError(RuntimeError):
    """An interface failed before or during the behavior under test."""


@dataclass
class InterfaceResult:
    interface: str
    passed: bool
    exact_type: str
    record_observed: bool
    cleanup_complete: bool
    detail: str


@dataclass
class RecordFixture:
    cli_record: dict[str, Any]
    mcp_fields: dict[str, Any]


def run_cli(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uvx", "--from", "fulcra-api@latest", "fulcra", *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def require_cli(*args: str, input_text: str | None = None) -> str:
    completed = run_cli(*args, input_text=input_text)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise ParityTestError(f"Fulcra CLI failed: {message}")
    return completed.stdout


def parse_prefixed_json(text: str, prefix: str) -> dict[str, Any]:
    for line in text.splitlines():
        if line.startswith(prefix):
            value = json.loads(line.removeprefix(prefix))
            if isinstance(value, dict):
                return value
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ParityTestError("Expected a JSON object")
    return value


def load_configuration(path: str) -> dict[str, Any]:
    value = json.loads(require_cli("file", "download", path, "-"))
    if not isinstance(value, dict):
        raise ParityTestError("Image Upgrade configuration is not a JSON object")
    request_type = value.get("request_data_type")
    contribution_type = value.get("contribution_data_type")
    if not all(
        isinstance(item, str) and item.startswith("MomentAnnotation/")
        for item in (request_type, contribution_type)
    ):
        raise ParityTestError("Configuration does not contain two MomentAnnotation IDs")
    if request_type == contribution_type:
        raise ParityTestError("Parity test requires two distinct custom types")
    return value


def load_custom_annotation_types() -> list[str]:
    entries = []
    for line in require_cli("catalog", "--recordable-only").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        data_type = value.get("id") if isinstance(value, dict) else None
        if isinstance(data_type, str) and "/" in data_type:
            entries.append(data_type)
    return sorted(set(entries))


def fixture_for(data_type: str, marker: str) -> RecordFixture:
    base_type = data_type.partition("/")[0]
    cli_record: dict[str, Any] = {"note": marker}
    mcp_fields: dict[str, Any] = {"note": marker}
    if base_type == "DurationAnnotation":
        start = datetime.now(timezone.utc).replace(microsecond=0)
        end = start + timedelta(seconds=1)
        cli_record["recorded_at"] = {
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }
        mcp_fields.update(
            {"start_time": start.isoformat(), "end_time": end.isoformat()}
        )
    elif base_type in {"BooleanAnnotation", "NumericAnnotation"}:
        cli_record["value"] = 1
        mcp_fields["value"] = "1"
    elif base_type == "ScaleAnnotation":
        cli_record["value"] = 3
        mcp_fields["value"] = "3"
    elif base_type != "MomentAnnotation":
        raise ParityTestError(f"Unsupported custom annotation base: {base_type}")
    return RecordFixture(cli_record=cli_record, mcp_fields=mcp_fields)


def cli_owner_id() -> str:
    value = json.loads(require_cli("user-info"))
    owner_id = value.get("userid")
    if not isinstance(owner_id, str) or not owner_id:
        raise ParityTestError("CLI user-info did not return an owner ID")
    return owner_id


def records_with_marker(data_type: str, marker: str) -> list[dict[str, Any]]:
    output = require_cli("get-records", data_type, "10 minutes")
    records = []
    for line in output.splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict) and value.get("note") == marker:
            records.append(value)
    by_id = {
        value["id"]: value
        for value in records
        if isinstance(value.get("id"), str) and value["id"]
    }
    return list(by_id.values())


def wait_for_records(data_type: str, marker: str, timeout: float = 12.0) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while True:
        records = records_with_marker(data_type, marker)
        if records or time.monotonic() >= deadline:
            return records
        time.sleep(1)


def cleanup_records(data_type: str, marker: str) -> bool:
    records = records_with_marker(data_type, marker)
    for record in records:
        require_cli("delete", data_type, record["id"])
    return not records_with_marker(data_type, marker)


def exercise_cli(
    data_type: str, marker: str, fixture: RecordFixture
) -> InterfaceResult:
    cleanup_complete = False
    passed = False
    records: list[dict[str, Any]] = []
    detail = "exact composite type write did not complete"
    try:
        payload = json.dumps(fixture.cli_record, separators=(",", ":"))
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as file:
            file.write(payload)
            file.flush()
            completed = run_cli("record", data_type, "-f", file.name, "--source", SOURCE)
        records = wait_for_records(data_type, marker)
        passed = completed.returncode == 0 and len(records) == 1
        detail = (
            "exact composite type accepted and one record observed"
            if passed
            else "exact composite type was not accepted or record was not observed"
        )
    finally:
        cleanup_complete = cleanup_records(data_type, marker)
    return InterfaceResult(
        interface="CLI",
        passed=passed,
        exact_type=data_type,
        record_observed=bool(records),
        cleanup_complete=cleanup_complete,
        detail=detail,
    )


def tool_text(result: Any) -> str:
    return "\n".join(
        block.text for block in result.content if hasattr(block, "text")
    )


@asynccontextmanager
async def mcp_session() -> AsyncIterator[ClientSession]:
    env = dict(os.environ)
    env["SSL_CERT_FILE"] = certifi.where()
    parameters = StdioServerParameters(
        command="uvx",
        args=["fulcra-context-mcp@latest"],
        env=env,
    )
    async with (
        stdio_client(parameters) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        yield session


async def mcp_owner_id(session: ClientSession) -> str:
    result = await session.call_tool("get_user_info", {})
    if result.is_error:
        raise ParityTestError("MCP get_user_info failed")
    value = parse_prefixed_json(tool_text(result), "User information: ")
    owner_id = value.get("userid")
    if not isinstance(owner_id, str) or not owner_id:
        raise ParityTestError("MCP get_user_info did not return an owner ID")
    return owner_id


async def mcp_catalog_resolves_exact_type(
    session: ClientSession, data_type: str
) -> bool:
    result = await session.call_tool("get_data_catalog", {"data_type": data_type})
    return not result.is_error and data_type in tool_text(result)


async def exercise_mcp(
    session: ClientSession,
    data_type: str,
    marker: str,
    fixture: RecordFixture,
) -> InterfaceResult:
    cleanup_complete = False
    passed = False
    records: list[dict[str, Any]] = []
    detail = "exact composite type write did not complete"
    try:
        arguments = {"data_type": data_type, **fixture.mcp_fields}
        result = await session.call_tool("record_data", arguments)
        response = tool_text(result)
        logical_failure = bool(
            re.search(r"matches \d+ catalog entries", response)
            or "No data type found" in response
            or "Could not" in response
            or "not valid" in response
        )
        records = (
            wait_for_records(data_type, marker)
            if not result.is_error and not logical_failure
            else []
        )
        passed = not result.is_error and not logical_failure and len(records) == 1
        if passed:
            detail = "exact composite type accepted and one record observed"
        elif re.search(r"matches \d+ catalog entries", response):
            detail = "exact composite type was reduced to ambiguous base type"
        else:
            detail = "exact composite type write failed"
    finally:
        cleanup_complete = cleanup_records(data_type, marker)
    return InterfaceResult(
        interface="MCP",
        passed=passed,
        exact_type=data_type,
        record_observed=bool(records),
        cleanup_complete=cleanup_complete,
        detail=detail,
    )


async def run_one_configured_type(args: argparse.Namespace) -> int:
    configuration = load_configuration(args.configuration_path)
    data_type = configuration[args.role]
    marker_root = f"fulcra-interface-parity/{uuid.uuid4()}"
    cli_marker = f"{marker_root}/cli"
    mcp_marker = f"{marker_root}/mcp"
    cli_fixture = fixture_for(data_type, cli_marker)
    mcp_fixture = fixture_for(data_type, mcp_marker)

    expected_owner = cli_owner_id()
    async with mcp_session() as session:
        if await mcp_owner_id(session) != expected_owner:
            raise ParityTestError("CLI and MCP are authenticated as different owners")
        mcp_exact_catalog_resolved = await mcp_catalog_resolves_exact_type(
            session, data_type
        )
        if not mcp_exact_catalog_resolved:
            raise ParityTestError("MCP catalog did not resolve the exact custom type")
        cli_result = exercise_cli(data_type, cli_marker, cli_fixture)
        mcp_result = await exercise_mcp(
            session, data_type, mcp_marker, mcp_fixture
        )

    results = [cli_result, mcp_result]
    report = {
        "scenario": "exact-custom-type-write-parity",
        "same_authenticated_owner": True,
        "two_distinct_types_share_base": True,
        "mcp_exact_catalog_resolved": mcp_exact_catalog_resolved,
        "results": [
            {
                **asdict(result),
                "exact_type": "MomentAnnotation/<UUID>",
            }
            for result in results
        ],
        "mcp_specific_failure": cli_result.passed and not mcp_result.passed,
        "cleanup_complete": all(result.cleanup_complete for result in results),
    }
    print(json.dumps(report, indent=2))
    return 0 if all(result.passed for result in results) else 1


async def audit_all_annotations() -> int:
    data_types = load_custom_annotation_types()
    if not data_types:
        raise ParityTestError("No user-defined annotation types were found")
    counts_by_base: dict[str, int] = {}
    for data_type in data_types:
        base_type = data_type.partition("/")[0]
        counts_by_base[base_type] = counts_by_base.get(base_type, 0) + 1

    expected_owner = cli_owner_id()
    type_results = []
    async with mcp_session() as session:
        if await mcp_owner_id(session) != expected_owner:
            raise ParityTestError("CLI and MCP are authenticated as different owners")
        for index, data_type in enumerate(data_types, start=1):
            base_type = data_type.partition("/")[0]
            marker_root = f"fulcra-interface-parity/{uuid.uuid4()}"
            cli_marker = f"{marker_root}/cli"
            mcp_marker = f"{marker_root}/mcp"
            catalog_resolved = await mcp_catalog_resolves_exact_type(
                session, data_type
            )
            cli_result = exercise_cli(
                data_type, cli_marker, fixture_for(data_type, cli_marker)
            )
            mcp_result = await exercise_mcp(
                session,
                data_type,
                mcp_marker,
                fixture_for(data_type, mcp_marker),
            )
            type_results.append(
                {
                    "type": f"{base_type}/<UUID>",
                    "ordinal": index,
                    "base_peer_count": counts_by_base[base_type],
                    "mcp_exact_catalog_resolved": catalog_resolved,
                    "cli": asdict(cli_result),
                    "mcp": asdict(mcp_result),
                }
            )

    for result in type_results:
        result["cli"]["exact_type"] = result["type"]
        result["mcp"]["exact_type"] = result["type"]
    cli_passed = sum(result["cli"]["passed"] for result in type_results)
    mcp_passed = sum(result["mcp"]["passed"] for result in type_results)
    mcp_ambiguous = sum(
        result["mcp"]["detail"]
        == "exact composite type was reduced to ambiguous base type"
        for result in type_results
    )
    cleanup_complete = all(
        result[interface]["cleanup_complete"]
        for result in type_results
        for interface in ("cli", "mcp")
    )
    report = {
        "scenario": "all-custom-annotation-write-parity",
        "same_authenticated_owner": True,
        "custom_type_count": len(type_results),
        "counts_by_base": counts_by_base,
        "cli_passed": cli_passed,
        "mcp_passed": mcp_passed,
        "mcp_ambiguous": mcp_ambiguous,
        "mcp_specific_failure_count": sum(
            result["cli"]["passed"] and not result["mcp"]["passed"]
            for result in type_results
        ),
        "cleanup_complete": cleanup_complete,
        "results": type_results,
    }
    print(json.dumps(report, indent=2))
    return 0 if cli_passed == mcp_passed == len(type_results) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--configuration-path",
        default=DEFAULT_CONFIG_PATH,
        help="Owner-scoped Image Upgrade configuration file.",
    )
    parser.add_argument(
        "--role",
        choices=("request_data_type", "contribution_data_type"),
        default="request_data_type",
        help="Configured custom type to exercise.",
    )
    parser.add_argument(
        "--all-annotations",
        action="store_true",
        help="Exercise every recordable user-defined annotation type.",
    )
    args = parser.parse_args()
    try:
        operation = (
            audit_all_annotations()
            if args.all_annotations
            else run_one_configured_type(args)
        )
        return asyncio.run(operation)
    except ParityTestError as error:
        print(json.dumps({"valid": False, "error": str(error)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
