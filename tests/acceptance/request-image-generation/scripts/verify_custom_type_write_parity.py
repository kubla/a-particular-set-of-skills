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
import subprocess
import tempfile
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
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


def exercise_cli(data_type: str, marker: str) -> InterfaceResult:
    cleanup_complete = False
    passed = False
    records: list[dict[str, Any]] = []
    detail = "exact composite type write did not complete"
    try:
        payload = json.dumps({"note": marker}, separators=(",", ":"))
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
    session: ClientSession, data_type: str, marker: str
) -> InterfaceResult:
    cleanup_complete = False
    passed = False
    records: list[dict[str, Any]] = []
    detail = "exact composite type write did not complete"
    try:
        result = await session.call_tool(
            "record_data", {"data_type": data_type, "note": marker}
        )
        records = wait_for_records(data_type, marker) if not result.is_error else []
        passed = not result.is_error and len(records) == 1
        response = tool_text(result)
        if passed:
            detail = "exact composite type accepted and one record observed"
        elif "matches 2 catalog entries" in response:
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


async def run(args: argparse.Namespace) -> int:
    configuration = load_configuration(args.configuration_path)
    data_type = configuration[args.role]
    marker_root = f"fulcra-interface-parity/{uuid.uuid4()}"
    cli_marker = f"{marker_root}/cli"
    mcp_marker = f"{marker_root}/mcp"

    expected_owner = cli_owner_id()
    async with mcp_session() as session:
        if await mcp_owner_id(session) != expected_owner:
            raise ParityTestError("CLI and MCP are authenticated as different owners")
        mcp_exact_catalog_resolved = await mcp_catalog_resolves_exact_type(
            session, data_type
        )
        if not mcp_exact_catalog_resolved:
            raise ParityTestError("MCP catalog did not resolve the exact custom type")
        cli_result = exercise_cli(data_type, cli_marker)
        mcp_result = await exercise_mcp(session, data_type, mcp_marker)

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
    args = parser.parse_args()
    try:
        return asyncio.run(run(args))
    except ParityTestError as error:
        print(json.dumps({"valid": False, "error": str(error)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
