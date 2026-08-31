#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Validate and construct Image Upgrade protocol envelopes."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sys
import uuid
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PROTOCOL = "image-upgrade/v1"
REQUEST_TYPE_NAME = "Image Upgrade Request"
CONTRIBUTION_TYPE_NAME = "Image Upgrade Contribution"


class ProtocolError(ValueError):
    """The supplied value is not valid for the supported protocol."""


@dataclasses.dataclass(frozen=True)
class SetupDecision:
    action: str
    configuration: dict[str, Any] | None
    observed: dict[str, Any]
    change: str


@dataclasses.dataclass(frozen=True)
class RepresentationVerification:
    allowed: bool
    accepted: bool
    status: str
    final_url: str
    final_host: str
    actual_sha256: str
    observed_media_type: str


@dataclasses.dataclass(frozen=True)
class RetrievalAuthorization:
    allowed: bool
    accepted: bool
    status: str
    url: str
    host: str


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


def validate_configuration(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or value.get("protocol") != PROTOCOL:
        raise ProtocolError(f"configuration must use protocol {PROTOCOL}")
    unknown = set(value) - {
        "protocol",
        "request_data_type",
        "contribution_data_type",
        "trusted_artifact_hosts",
    }
    if unknown:
        raise ProtocolError(
            f"configuration contains unsupported fields: {', '.join(sorted(unknown))}"
        )
    return configuration(
        request_data_type=value.get("request_data_type"),
        contribution_data_type=value.get("contribution_data_type"),
        trusted_artifact_hosts=value.get("trusted_artifact_hosts"),
    )


def reconcile_setup(
    *,
    configuration_value: Mapping[str, Any] | None,
    catalog: Iterable[Mapping[str, Any]],
) -> SetupDecision:
    """Choose the single safe setup action from observed owner state."""

    entries = list(catalog)
    requests = [entry for entry in entries if entry.get("name") == REQUEST_TYPE_NAME]
    contributions = [
        entry for entry in entries if entry.get("name") == CONTRIBUTION_TYPE_NAME
    ]
    observed = {
        "configuration_present": configuration_value is not None,
        "request_type_ids": [entry.get("id") for entry in requests],
        "contribution_type_ids": [entry.get("id") for entry in contributions],
    }
    if configuration_value is None and not requests and not contributions:
        return SetupDecision(
            action="create_pair",
            configuration=None,
            observed=observed,
            change="Create one Request type and one Contribution type, then write configuration.",
        )
    if configuration_value is None and len(requests) == len(contributions) == 1:
        adopted = configuration(
            request_data_type=requests[0].get("id"),
            contribution_data_type=contributions[0].get("id"),
            trusted_artifact_hosts=[],
        )
        return SetupDecision(
            action="adopt_pair",
            configuration=adopted,
            observed=observed,
            change="Write configuration adopting the observed compatible type pair.",
        )
    if configuration_value is None:
        observed = [str(entry.get("id")) for entry in [*requests, *contributions]]
        if len(requests) > 1 or len(contributions) > 1:
            raise ProtocolError(
                f"duplicate Image Upgrade types require explicit repair: {observed}"
            )
        raise ProtocolError(
            f"partial Image Upgrade type pair requires explicit repair: {observed}"
        )

    configured = validate_configuration(configuration_value)
    by_id = {entry.get("id"): entry for entry in entries}
    required = (
        (configured["request_data_type"], REQUEST_TYPE_NAME),
        (configured["contribution_data_type"], CONTRIBUTION_TYPE_NAME),
    )
    for identifier, expected_name in required:
        entry = by_id.get(identifier)
        if entry is None:
            raise ProtocolError(f"configured data type is missing: {identifier}")
        if entry.get("name") != expected_name:
            raise ProtocolError(
                f"configured {expected_name} has incompatible name: "
                f"{entry.get('name')!r} ({identifier})"
            )
        _moment_annotation_id(identifier)
    return SetupDecision(
        action="verified",
        configuration=configured,
        observed=observed,
        change="No setup mutation.",
    )


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
    unknown = set(value) - {"url", "media_type", "sha256", "width", "height"}
    if unknown:
        raise ProtocolError(
            f"representation contains unsupported fields: {', '.join(sorted(unknown))}"
        )
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


def verify_representation(
    *,
    representation: Mapping[str, Any],
    authorization: RetrievalAuthorization,
    observed_media_type: str,
    content: bytes,
) -> RepresentationVerification:
    """Decide whether retrieved representation bytes satisfy the v1 contract."""

    declared = _representation(representation)
    if not isinstance(authorization, RetrievalAuthorization) or not authorization.allowed:
        raise ProtocolError("representation bytes were retrieved without authorization")
    host = authorization.host
    actual_digest = hashlib.sha256(content).hexdigest()
    if observed_media_type != declared["media_type"]:
        status = "media_type_mismatch"
    elif actual_digest != declared["sha256"]:
        status = "digest_mismatch"
    else:
        status = "verified"
    return RepresentationVerification(
        allowed=True,
        accepted=status == "verified",
        status=status,
        final_url=authorization.url,
        final_host=host,
        actual_sha256=actual_digest,
        observed_media_type=observed_media_type,
    )


def authorize_retrieval(
    *,
    candidate_url: str,
    trusted_artifact_hosts: list[str],
    user_approved: bool = False,
) -> RetrievalAuthorization:
    """Authorize an observed final HTTPS host before its body is downloaded."""

    if not isinstance(user_approved, bool):
        raise ProtocolError("user_approved must be a boolean")
    if not isinstance(trusted_artifact_hosts, list) or any(
        not isinstance(value, str) for value in trusted_artifact_hosts
    ):
        raise ProtocolError("trusted_artifact_hosts must be an array of hostnames")
    parsed = urlparse(candidate_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ProtocolError("final representation URL must be absolute HTTPS")
    host = parsed.hostname.lower().rstrip(".")
    trusted = {value.lower().rstrip(".") for value in trusted_artifact_hosts}
    allowed = host in trusted or user_approved
    return RetrievalAuthorization(
        allowed=allowed,
        accepted=False,
        status="authorized" if allowed else "approval_required",
        url=candidate_url,
        host=host,
    )


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


def parse_contribution_note(note: str) -> dict[str, Any]:
    try:
        value = json.loads(note)
    except (TypeError, json.JSONDecodeError) as error:
        raise ProtocolError("contribution note must be valid JSON") from error
    return validate_contribution_envelope(value)


def _parse_record_envelope(
    *,
    record: Mapping[str, Any],
    index: int,
    record_kind: str,
    parser: Callable[[str], dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        note = record.get("note")
        if not isinstance(note, str):
            raise ProtocolError("record note must be a JSON string")
        return parser(note), None
    except ProtocolError as error:
        return None, {
            "record_kind": record_kind,
            "index": index,
            "record_id": record.get("id"),
            "error": str(error),
        }


def matching_contributions(
    records: Iterable[Mapping[str, Any]], request_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return exact matching records in input order plus parse errors."""

    wanted = _canonical_request_id(request_id)
    matches: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        envelope, error = _parse_record_envelope(
            record=record,
            index=index,
            record_kind="contribution",
            parser=parse_contribution_note,
        )
        if error is not None:
            errors.append(error)
            continue
        assert envelope is not None
        if envelope["request_id"] == wanted:
            match = dict(record)
            match["envelope"] = envelope
            matches.append(match)
    return matches, errors


def prioritize_requests(
    request_records: Iterable[Mapping[str, Any]],
    contribution_records: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return valid Requests with unanswered records first, preserving order."""

    counts: dict[str, int] = {}
    errors: list[dict[str, Any]] = []
    for index, record in enumerate(contribution_records):
        envelope, error = _parse_record_envelope(
            record=record,
            index=index,
            record_kind="contribution",
            parser=parse_contribution_note,
        )
        if error is not None:
            errors.append(error)
            continue
        assert envelope is not None
        request_id = envelope["request_id"]
        counts[request_id] = counts.get(request_id, 0) + 1

    requests: list[dict[str, Any]] = []
    for index, record in enumerate(request_records):
        envelope, error = _parse_record_envelope(
            record=record,
            index=index,
            record_kind="request",
            parser=parse_request_note,
        )
        if error is not None:
            errors.append(error)
            continue
        assert envelope is not None
        candidate = dict(record)
        candidate["envelope"] = envelope
        candidate["contribution_count"] = counts.get(envelope["request_id"], 0)
        requests.append(candidate)

    requests.sort(key=lambda record: record["contribution_count"] > 0)
    return requests, errors


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=(
            "setup-decision",
            "catalog-json",
            "jsonl-array",
            "owner-id",
            "prioritize-requests",
            "matching-contributions",
            "contribution-note",
            "contribution-record",
            "authorize-url",
            "verify-artifact",
            "file-representation",
        ),
        help="Deterministic protocol operation to perform from JSON stdin.",
    )
    args = parser.parse_args(argv)
    try:
        if args.operation == "setup-decision":
            value = json.load(sys.stdin)
            if not isinstance(value, Mapping):
                raise ProtocolError("stdin must contain a JSON object")
            missing = {"configuration", "catalog"} - set(value)
            if missing:
                raise ProtocolError(
                    f"setup observation is missing: {', '.join(sorted(missing))}"
                )
            if not isinstance(value["catalog"], list):
                raise ProtocolError("catalog observation must be an array")
            decision = reconcile_setup(
                configuration_value=value["configuration"],
                catalog=value["catalog"],
            )
            json.dump(dataclasses.asdict(decision), sys.stdout, separators=(",", ":"))
            sys.stdout.write("\n")
            return 0
        if args.operation in {"catalog-json", "jsonl-array"}:
            entries: list[Mapping[str, Any]] = []
            for line in sys.stdin:
                if not line.strip():
                    continue
                parsed = json.loads(line)
                values = parsed if isinstance(parsed, list) else [parsed]
                if any(not isinstance(item, Mapping) for item in values):
                    raise ProtocolError("JSON stream entries must be objects")
                entries.extend(values)
            json.dump(entries, sys.stdout, separators=(",", ":"))
            sys.stdout.write("\n")
            return 0
        if args.operation == "owner-id":
            value = json.load(sys.stdin)
            if not isinstance(value, Mapping) or not isinstance(
                value.get("userid"), str
            ):
                raise ProtocolError("user information does not contain userid")
            json.dump({"userid": value["userid"]}, sys.stdout, separators=(",", ":"))
            sys.stdout.write("\n")
            return 0
        value = json.load(sys.stdin)
        if not isinstance(value, Mapping):
            raise ProtocolError("stdin must contain a JSON object")
        if args.operation == "prioritize-requests":
            records, errors = prioritize_requests(
                value.get("requests", []), value.get("contributions", [])
            )
            json.dump(
                {"requests": records, "errors": errors},
                sys.stdout,
                separators=(",", ":"),
            )
        elif args.operation == "matching-contributions":
            records, errors = matching_contributions(
                value.get("records", []), value.get("request_id")
            )
            json.dump(
                {"contributions": records, "errors": errors},
                sys.stdout,
                separators=(",", ":"),
            )
        elif args.operation in {"contribution-note", "contribution-record"}:
            envelope = contribution_envelope(
                request_id=value.get("request_id"),
                representations=value.get("representations"),
                summary=value.get("summary"),
            )
            value_to_write: Mapping[str, Any]
            if args.operation == "contribution-record":
                value_to_write = {
                    "note": json.dumps(envelope, separators=(",", ":"))
                }
            else:
                value_to_write = envelope
            json.dump(value_to_write, sys.stdout, separators=(",", ":"))
        elif args.operation == "authorize-url":
            result = authorize_retrieval(
                candidate_url=value.get("url"),
                trusted_artifact_hosts=value.get("trusted_artifact_hosts", []),
                user_approved=value.get("user_approved", False),
            )
            json.dump(dataclasses.asdict(result), sys.stdout, separators=(",", ":"))
        elif args.operation == "verify-artifact":
            content_path = value.get("content_path")
            if not isinstance(content_path, str) or not content_path:
                raise ProtocolError("content_path must be a nonempty string")
            declared_representation = _representation(value.get("representation"))
            authorization = authorize_retrieval(
                candidate_url=value.get("final_url"),
                trusted_artifact_hosts=value.get("trusted_artifact_hosts", []),
                user_approved=value.get("user_approved", False),
            )
            if not authorization.allowed:
                json.dump(
                    dataclasses.asdict(authorization),
                    sys.stdout,
                    separators=(",", ":"),
                )
                sys.stdout.write("\n")
                return 0
            result = verify_representation(
                representation=declared_representation,
                authorization=authorization,
                observed_media_type=value.get("observed_media_type"),
                content=Path(content_path).read_bytes(),
            )
            json.dump(dataclasses.asdict(result), sys.stdout, separators=(",", ":"))
        elif args.operation == "file-representation":
            content_path = value.get("content_path")
            if not isinstance(content_path, str) or not content_path:
                raise ProtocolError("content_path must be a nonempty string")
            content = Path(content_path).read_bytes()
            representation_value = {
                "url": value.get("url"),
                "media_type": value.get("media_type"),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for dimension in ("width", "height"):
                if dimension in value:
                    representation_value[dimension] = value[dimension]
            json.dump(
                _representation(representation_value),
                sys.stdout,
                separators=(",", ":"),
            )
        sys.stdout.write("\n")
        return 0
    except (json.JSONDecodeError, OSError, ProtocolError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
