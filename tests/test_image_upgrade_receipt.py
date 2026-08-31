from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = (
    ROOT
    / "tests"
    / "acceptance"
    / "request-image-generation"
    / "scripts"
    / "verify_round_trip_receipt.py"
)
SPEC = importlib.util.spec_from_file_location("verify_image_upgrade_receipt", SCRIPT)
verifier = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = verifier
SPEC.loader.exec_module(verifier)


def valid_receipt():
    digest = "a" * 64
    return {
        "skills": ["request-image-generation", "image-upgrader"],
        "scenario": "claude-codex-image-upgrade-round-trip",
        "run_id": "image-upgrade-20260831T160000Z-example",
        "started_at": "2026-08-31T16:00:00Z",
        "completed_at": "2026-08-31T16:10:00Z",
        "owner_id": "11111111-1111-4111-8111-111111111111",
        "result": "passed",
        "outcomes": {
            name: {"result": "passed", "evidence": [f"evidence/{name}.json"]}
            for name in verifier.OUTCOMES
        },
        "requester": {
            "host": "Claude Desktop",
            "product_version": "2026.08",
            "fulcra_interface": "MCP",
            "owner_id": "11111111-1111-4111-8111-111111111111",
            "owner_observed_before_mutation": True,
            "request_prompt_sent": "Request a test image and stop after the receipt.",
            "request_response_received": "Request receipt returned.",
            "check_prompt_sent": "Check the exact request and render valid results.",
            "check_response_received": "Contribution verified and rendered.",
            "request_id": "22222222-2222-4222-8222-222222222222",
            "created_at": "2026-08-31T16:01:00Z",
            "record_observed": True,
            "request_evidence": ["evidence/claude-request.png"],
            "check_evidence": ["evidence/claude-check.png"],
        },
        "producer": {
            "host": "Codex",
            "product_version": "2026.08",
            "skill_version": "git:abcdef0",
            "uv_version": "0.8.0",
            "fulcra_api_version": "1.2.3",
            "fulcra_interface": "CLI",
            "owner_id": "11111111-1111-4111-8111-111111111111",
            "owner_observed_before_mutation": True,
            "prompt_sent": "Contribute to the exact test request.",
            "response_received": "Contribution recorded.",
            "request_observed": True,
            "contribution_record_id": "33333333-3333-4333-8333-333333333333",
            "contribution_observed": True,
            "evidence": ["evidence/codex-contribution.png"],
            "provenance": [
                "com.fulcradynamics.cli",
                "com.fulcradynamics.agent-skills.image-upgrader",
            ],
        },
        "artifact": {
            "url": "https://assets.example/image.png",
            "media_type": "image/png",
            "declared_sha256": digest,
            "retrieved_sha256": digest,
            "bytes_retrieved": True,
            "digest_verified": True,
            "rendered_in_claude": True,
            "retrieval_evidence": ["evidence/retrieval.json"],
            "render_evidence": ["evidence/claude-render.png"],
        },
        "cleanup": {
            "status": "complete",
            "targets": [
                {
                    "kind": "request",
                    "id": "22222222-2222-4222-8222-222222222222",
                    "path": "Image Upgrade Request/22222222-2222-4222-8222-222222222222",
                    "registered_sequence": 1,
                    "cleanup_sequence": 3,
                    "registered_at": "2026-08-31T16:01:00Z",
                    "cleaned_at": "2026-08-31T16:10:00Z",
                    "result": "deleted",
                },
                {
                    "kind": "artifact",
                    "id": "image-upgrade-20260831T160000Z-example.png",
                    "path": "https://assets.example/image.png",
                    "registered_sequence": 2,
                    "cleanup_sequence": 2,
                    "registered_at": "2026-08-31T16:04:00Z",
                    "cleaned_at": "2026-08-31T16:09:00Z",
                    "result": "deleted",
                },
                {
                    "kind": "contribution",
                    "id": "33333333-3333-4333-8333-333333333333",
                    "path": "Image Upgrade Contribution/33333333-3333-4333-8333-333333333333",
                    "registered_sequence": 3,
                    "cleanup_sequence": 1,
                    "registered_at": "2026-08-31T16:06:00Z",
                    "cleaned_at": "2026-08-31T16:08:00Z",
                    "result": "deleted",
                }
            ],
        },
    }


class ImageUpgradeReceiptTests(unittest.TestCase):
    def test_complete_round_trip_receipt_passes(self):
        self.assertEqual(verifier.verify_receipt(valid_receipt()), [])

    def test_unrendered_or_unclean_result_fails(self):
        receipt = valid_receipt()
        receipt["artifact"]["rendered_in_claude"] = False
        receipt["cleanup"]["status"] = "partial"

        failures = verifier.verify_receipt(receipt)

        self.assertIn("artifact was not rendered in Claude", failures)
        self.assertIn("cleanup is not complete", failures)

    def test_wrong_interface_owner_or_incomplete_cleanup_fails(self):
        receipt = valid_receipt()
        receipt["requester"]["owner_id"] = "44444444-4444-4444-8444-444444444444"
        receipt["cleanup"]["targets"] = receipt["cleanup"]["targets"][2:]

        failures = verifier.verify_receipt(receipt)

        self.assertIn("requester observed the wrong owner", failures)
        self.assertIn("cleanup omits a core round-trip mutation", failures)

    def test_cleanup_identity_sequence_and_evidence_are_exact(self):
        receipt = valid_receipt()
        receipt["outcomes"]["claude_rendered"]["evidence"] = [None]
        receipt["cleanup"]["targets"][0]["id"] = "wrong-request"
        receipt["cleanup"]["targets"][1]["cleanup_sequence"] = 1

        failures = verifier.verify_receipt(receipt)

        self.assertIn(
            "outcome claude_rendered lacks a passing result and evidence", failures
        )
        self.assertIn("cleanup Request identity does not match the receipt", failures)
        self.assertIn("cleanup sequence is not unique and contiguous", failures)


if __name__ == "__main__":
    unittest.main()
