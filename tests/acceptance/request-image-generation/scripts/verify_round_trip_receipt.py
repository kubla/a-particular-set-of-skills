#!/usr/bin/env python3
"""Verify the evidence receipt for the Claude-to-Codex round trip."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCENARIO = "claude-codex-image-upgrade-round-trip"
PROVENANCE = "com.fulcradynamics.agent-skills.image-upgrader"
SKILLS = ["request-image-generation", "image-upgrader"]
OUTCOMES = {
    "requester_recorded",
    "request_independently_observed",
    "producer_contributed",
    "contribution_independently_observed",
    "artifact_digest_verified",
    "claude_rendered",
    "cleanup_completed",
}


def verify_receipt(receipt: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    def is_evidence(value: Any) -> bool:
        return (
            isinstance(value, list)
            and bool(value)
            and all(isinstance(item, str) and bool(item.strip()) for item in value)
        )

    require(receipt.get("skills") == SKILLS, "skill identifiers are incorrect")
    require(receipt.get("scenario") == SCENARIO, "scenario identifier is incorrect")
    for field in ("run_id", "started_at", "completed_at", "owner_id"):
        require(bool(receipt.get(field)), f"{field} is missing")
    require(receipt.get("result") == "passed", "round-trip result did not pass")

    outcomes = receipt.get("outcomes")
    require(isinstance(outcomes, Mapping), "expected-outcome evidence is missing")
    if isinstance(outcomes, Mapping):
        for name in OUTCOMES:
            outcome = outcomes.get(name)
            require(
                isinstance(outcome, Mapping)
                and outcome.get("result") == "passed"
                and is_evidence(outcome.get("evidence")),
                f"outcome {name} lacks a passing result and evidence",
            )

    requester = receipt.get("requester")
    require(isinstance(requester, Mapping), "requester evidence is missing")
    if isinstance(requester, Mapping):
        require(requester.get("fulcra_interface") == "MCP", "requester did not use MCP")
        for field in (
            "host",
            "product_version",
            "owner_id",
            "request_prompt_sent",
            "request_response_received",
            "check_prompt_sent",
            "check_response_received",
            "request_id",
            "created_at",
        ):
            require(bool(requester.get(field)), f"requester {field} is missing")
        for field in ("request_evidence", "check_evidence"):
            require(is_evidence(requester.get(field)), f"requester {field} is missing")
        require(
            requester.get("owner_id") == receipt.get("owner_id"),
            "requester observed the wrong owner",
        )
        require(
            requester.get("owner_observed_before_mutation") is True,
            "requester owner was not observed before mutation",
        )
        require(requester.get("record_observed") is True, "Request was not observed")

    producer = receipt.get("producer")
    require(isinstance(producer, Mapping), "producer evidence is missing")
    if isinstance(producer, Mapping):
        require(producer.get("fulcra_interface") == "CLI", "producer did not use CLI")
        for field in (
            "host",
            "product_version",
            "skill_version",
            "uv_version",
            "fulcra_api_version",
            "owner_id",
            "prompt_sent",
            "response_received",
            "contribution_record_id",
        ):
            require(bool(producer.get(field)), f"producer {field} is missing")
        require(is_evidence(producer.get("evidence")), "producer evidence is missing")
        require(
            producer.get("owner_id") == receipt.get("owner_id"),
            "producer observed the wrong owner",
        )
        require(
            producer.get("owner_observed_before_mutation") is True,
            "producer owner was not observed before mutation",
        )
        require(producer.get("request_observed") is True, "producer did not observe Request")
        require(
            producer.get("contribution_observed") is True,
            "Contribution was not observed",
        )
        provenance = producer.get("provenance", [])
        require(
            isinstance(provenance, list) and PROVENANCE in provenance,
            "Image Upgrader provenance is missing",
        )

    artifact = receipt.get("artifact")
    require(isinstance(artifact, Mapping), "artifact evidence is missing")
    if isinstance(artifact, Mapping):
        for field in (
            "url",
            "media_type",
            "declared_sha256",
            "retrieved_sha256",
        ):
            require(bool(artifact.get(field)), f"artifact {field} is missing")
        for field in ("retrieval_evidence", "render_evidence"):
            require(is_evidence(artifact.get(field)), f"artifact {field} is missing")
        require(artifact.get("bytes_retrieved") is True, "artifact bytes were not retrieved")
        require(artifact.get("digest_verified") is True, "artifact digest was not verified")
        require(
            artifact.get("declared_sha256") == artifact.get("retrieved_sha256"),
            "artifact digests differ",
        )
        require(
            artifact.get("rendered_in_claude") is True,
            "artifact was not rendered in Claude",
        )

    cleanup = receipt.get("cleanup")
    require(isinstance(cleanup, Mapping), "cleanup evidence is missing")
    if isinstance(cleanup, Mapping):
        require(cleanup.get("status") == "complete", "cleanup is not complete")
        targets = cleanup.get("targets")
        require(isinstance(targets, list) and bool(targets), "cleanup targets are missing")
        if isinstance(targets, list):
            kinds: set[str] = set()
            ordered_targets: list[Mapping[str, Any]] = []
            for target in targets:
                complete = (
                    isinstance(target, Mapping)
                    and bool(target.get("kind"))
                    and bool(target.get("id"))
                    and bool(target.get("path"))
                    and isinstance(target.get("registered_sequence"), int)
                    and isinstance(target.get("cleanup_sequence"), int)
                    and bool(target.get("registered_at"))
                    and bool(target.get("cleaned_at"))
                    and target.get("result") in {"deleted", "retained"}
                )
                require(complete, "cleanup target is incomplete")
                if isinstance(target, Mapping):
                    kinds.add(str(target.get("kind")))
                    ordered_targets.append(target)
                    if target.get("result") == "retained":
                        require(bool(target.get("reason")), "retained target lacks a reason")
            require(
                {"request", "artifact", "contribution"}.issubset(kinds),
                "cleanup omits a core round-trip mutation",
            )
            targets_by_kind = {
                str(target.get("kind")): target for target in ordered_targets
            }
            request_target = targets_by_kind.get("request", {})
            contribution_target = targets_by_kind.get("contribution", {})
            artifact_target = targets_by_kind.get("artifact", {})
            require(
                request_target.get("id")
                == (requester.get("request_id") if isinstance(requester, Mapping) else None),
                "cleanup Request identity does not match the receipt",
            )
            require(
                contribution_target.get("id")
                == (
                    producer.get("contribution_record_id")
                    if isinstance(producer, Mapping)
                    else None
                ),
                "cleanup Contribution identity does not match the receipt",
            )
            require(
                artifact_target.get("path")
                == (artifact.get("url") if isinstance(artifact, Mapping) else None),
                "cleanup artifact path does not match the receipt",
            )
            if all(
                isinstance(target.get("registered_sequence"), int)
                and isinstance(target.get("cleanup_sequence"), int)
                for target in ordered_targets
            ):
                expected_sequence = list(range(1, len(ordered_targets) + 1))
                registered_sequences = sorted(
                    target["registered_sequence"] for target in ordered_targets
                )
                cleanup_sequences = sorted(
                    target["cleanup_sequence"] for target in ordered_targets
                )
                require(
                    registered_sequences == expected_sequence,
                    "registration sequence is not unique and contiguous",
                )
                require(
                    cleanup_sequences == expected_sequence,
                    "cleanup sequence is not unique and contiguous",
                )
                cleanup_order = sorted(
                    ordered_targets, key=lambda target: target["cleanup_sequence"]
                )
                registration_order = [
                    target["registered_sequence"] for target in cleanup_order
                ]
                require(
                    registration_order == sorted(registration_order, reverse=True),
                    "cleanup did not run in reverse registration order",
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    failures = verify_receipt(receipt)
    print(json.dumps({"valid": not failures, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
