#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Validate and construct Image Upgrade protocol envelopes."""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlparse

PROTOCOL = "image-upgrade/v1"


class ProtocolError(ValueError):
    """The supplied value is not valid for the supported protocol."""


def _canonical_request_id(value: str) -> str:
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as error:
        raise ProtocolError("request_id must be a UUID") from error
    canonical = str(parsed)
    if value != canonical:
        raise ProtocolError("request_id must use canonical lowercase UUID form")
    return canonical


def _moment_annotation_id(value: str) -> str:
    if not isinstance(value, str) or not value.startswith("MomentAnnotation/"):
        raise ProtocolError("data type must be a MomentAnnotation identifier")
    _, identifier = value.split("/", 1)
    return f"MomentAnnotation/{_canonical_request_id(identifier)}"


def configuration(
    *,
    request_data_type: str,
    contribution_data_type: str,
    trusted_artifact_hosts: list[str],
) -> dict[str, Any]:
    """Return a canonical Image Upgrade Configuration."""

    if not isinstance(trusted_artifact_hosts, list):
        raise ProtocolError("trusted_artifact_hosts must be an array")
    hosts: list[str] = []
    for value in trusted_artifact_hosts:
        if not isinstance(value, str) or not value.strip():
            raise ProtocolError("trusted artifact host must be a nonempty string")
        host = value.strip().lower().rstrip(".")
        if "://" in host or "/" in host:
            raise ProtocolError("trusted artifact host must be a hostname")
        if host not in hosts:
            hosts.append(host)
    request_type = _moment_annotation_id(request_data_type)
    contribution_type = _moment_annotation_id(contribution_data_type)
    if request_type == contribution_type:
        raise ProtocolError("request and contribution data types must be separate")
    return {
        "protocol": PROTOCOL,
        "request_data_type": request_type,
        "contribution_data_type": contribution_type,
        "trusted_artifact_hosts": hosts,
    }


def request_envelope(
    *, brief: str, request_id: str, inputs: list[Mapping[str, Any]] | None = None
) -> dict[str, Any]:
    """Return a canonical v1 Image Upgrade Request envelope."""

    if not isinstance(brief, str) or not brief.strip():
        raise ProtocolError("brief must be a nonempty string")

    envelope: dict[str, Any] = {
        "protocol": PROTOCOL,
        "request_id": _canonical_request_id(request_id),
        "brief": brief.strip(),
    }
    if inputs is not None:
        envelope["inputs"] = [_representation(value) for value in inputs]
    return envelope


def validate_request_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("protocol") != PROTOCOL:
        raise ProtocolError(f"request must use protocol {PROTOCOL}")
    unknown = set(value) - {"protocol", "request_id", "brief", "inputs"}
    if unknown:
        raise ProtocolError(f"request contains unsupported fields: {', '.join(sorted(unknown))}")
    inputs = value.get("inputs")
    if inputs is not None and not isinstance(inputs, list):
        raise ProtocolError("inputs must be an array when present")
    return request_envelope(
        brief=value.get("brief"),
        request_id=value.get("request_id"),
        inputs=inputs,
    )


def parse_request_note(note: str) -> dict[str, Any]:
    try:
        value = json.loads(note)
    except (TypeError, json.JSONDecodeError) as error:
        raise ProtocolError("request note must be valid JSON") from error
    return validate_request_envelope(value)


def _representation(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtocolError("representation must be an object")
    url = value.get("url")
    parsed = urlparse(url) if isinstance(url, str) else None
    if not parsed or parsed.scheme != "https" or not parsed.hostname:
        raise ProtocolError("representation url must be an absolute HTTPS URL")
    media_type = value.get("media_type")
    if not isinstance(media_type, str) or not media_type.strip():
        raise ProtocolError("representation media_type must be a nonempty string")
    digest = value.get("sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdefABCDEF" for character in digest)
    ):
        raise ProtocolError("representation sha256 must be 64 hexadecimal characters")

    representation = {
        "url": url,
        "media_type": media_type.strip(),
        "sha256": digest.lower(),
    }
    for dimension in ("width", "height"):
        if dimension in value:
            size = value[dimension]
            if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
                raise ProtocolError(f"representation {dimension} must be a positive integer")
            representation[dimension] = size
    return representation


def contribution_envelope(
    *,
    request_id: str,
    representations: list[Mapping[str, Any]],
    summary: str | None = None,
) -> dict[str, Any]:
    """Return a canonical v1 Image Upgrade Contribution envelope."""

    if not isinstance(representations, list) or not representations:
        raise ProtocolError("representations must be a nonempty array")
    envelope: dict[str, Any] = {
        "protocol": PROTOCOL,
        "request_id": _canonical_request_id(request_id),
        "representations": [_representation(value) for value in representations],
    }
    if summary is not None:
        if not isinstance(summary, str) or not summary.strip():
            raise ProtocolError("summary must be a nonempty string when present")
        envelope["summary"] = summary.strip()
    return envelope


def validate_contribution_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("protocol") != PROTOCOL:
        raise ProtocolError(f"contribution must use protocol {PROTOCOL}")
    unknown = set(value) - {
        "protocol",
        "request_id",
        "representations",
        "summary",
    }
    if unknown:
        raise ProtocolError(
            f"contribution contains unsupported fields: {', '.join(sorted(unknown))}"
        )
    return contribution_envelope(
        request_id=value.get("request_id"),
        representations=value.get("representations"),
        summary=value.get("summary"),
    )


def matching_contributions(
    records: Iterable[Mapping[str, Any]], request_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return exact matching records in input order plus parse errors."""

    wanted = _canonical_request_id(request_id)
    matches: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        try:
            note = record.get("note")
            if not isinstance(note, str):
                raise ProtocolError("record note must be a JSON string")
            envelope = validate_contribution_envelope(json.loads(note))
        except (json.JSONDecodeError, ProtocolError) as error:
            errors.append(
                {
                    "index": index,
                    "record_id": record.get("id"),
                    "error": str(error),
                }
            )
            continue
        if envelope["request_id"] == wanted:
            match = dict(record)
            match["envelope"] = envelope
            matches.append(match)
    return matches, errors


def request_receipt(
    *, request_id: str, created_at: str, brief_summary: str
) -> dict[str, str]:
    """Return the receipt preserved between Request creation and later checking."""

    if not isinstance(created_at, str) or not created_at.strip():
        raise ProtocolError("created_at must be a nonempty timestamp string")
    if not isinstance(brief_summary, str) or not brief_summary.strip():
        raise ProtocolError("brief_summary must be a nonempty string")
    return {
        "request_id": _canonical_request_id(request_id),
        "created_at": created_at.strip(),
        "brief_summary": brief_summary.strip(),
    }
