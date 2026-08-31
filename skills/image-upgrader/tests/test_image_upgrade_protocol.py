from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "image_upgrade_protocol.py"
VALID_ROUND_TRIP = Path(__file__).parents[1] / "references" / "valid-round-trip.json"
SETUP_CASES = Path(__file__).parents[1] / "references" / "setup-cases.json"
SPEC = importlib.util.spec_from_file_location("image_upgrade_protocol", SCRIPT)
protocol = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = protocol
SPEC.loader.exec_module(protocol)


REQUEST_ID = "11111111-1111-4111-8111-111111111111"
REQUEST_TYPE = "MomentAnnotation/33333333-3333-4333-8333-333333333333"
CONTRIBUTION_TYPE = "MomentAnnotation/44444444-4444-4444-8444-444444444444"


class RequestEnvelopeTests(unittest.TestCase):
    def test_valid_text_only_request_is_canonicalized(self):
        envelope = protocol.request_envelope(
            brief="A precise blue heron drawn as a field-guide plate.",
            request_id=REQUEST_ID,
        )

        self.assertEqual(
            envelope,
            {
                "protocol": "image-upgrade/v1",
                "request_id": REQUEST_ID,
                "brief": "A precise blue heron drawn as a field-guide plate.",
            },
        )

    def test_valid_request_note_is_parsed_for_a_producer(self):
        note = json.dumps(
            {
                "protocol": "image-upgrade/v1",
                "request_id": REQUEST_ID,
                "brief": "A precise blue heron drawn as a field-guide plate.",
            }
        )

        envelope = protocol.parse_request_note(note)

        self.assertEqual(envelope["request_id"], REQUEST_ID)
        self.assertEqual(envelope["brief"], "A precise blue heron drawn as a field-guide plate.")

    def test_request_rejects_noncanonical_or_extended_identity(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.validate_request_envelope(
                {
                    "protocol": "image-upgrade/v1",
                    "request_id": "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA",
                    "brief": "A blue heron.",
                }
            )
        with self.assertRaises(protocol.ProtocolError):
            protocol.validate_request_envelope(
                {
                    "protocol": "image-upgrade/v1",
                    "request_id": REQUEST_ID,
                    "brief": "A blue heron.",
                    "status": "pending",
                }
            )

    def test_request_receipt_preserves_exact_identity_time_and_summary(self):
        receipt = protocol.request_receipt(
            request_id=REQUEST_ID,
            created_at="2026-08-31T16:00:00Z",
            brief_summary="A blue-heron field-guide plate.",
        )

        self.assertEqual(
            receipt,
            {
                "request_id": REQUEST_ID,
                "created_at": "2026-08-31T16:00:00Z",
                "brief_summary": "A blue-heron field-guide plate.",
            },
        )


class ConfigurationTests(unittest.TestCase):
    def test_valid_owner_configuration_is_canonicalized(self):
        configuration = protocol.configuration(
            request_data_type=REQUEST_TYPE,
            contribution_data_type=CONTRIBUTION_TYPE,
            trusted_artifact_hosts=[],
        )

        self.assertEqual(
            configuration,
            {
                "protocol": "image-upgrade/v1",
                "request_data_type": REQUEST_TYPE,
                "contribution_data_type": CONTRIBUTION_TYPE,
                "trusted_artifact_hosts": [],
            },
        )

    def test_configuration_requires_separate_types(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.configuration(
                request_data_type=REQUEST_TYPE,
                contribution_data_type=REQUEST_TYPE,
                trusted_artifact_hosts=[],
            )


class SetupReconciliationTests(unittest.TestCase):
    def pair(self):
        return [
            {"id": REQUEST_TYPE, "name": "Image Upgrade Request"},
            {
                "id": CONTRIBUTION_TYPE,
                "name": "Image Upgrade Contribution",
            },
        ]

    def test_empty_owner_state_requires_one_new_pair(self):
        decision = protocol.reconcile_setup(configuration_value=None, catalog=[])

        self.assertEqual(decision.action, "create_pair")
        self.assertIsNone(decision.configuration)
        self.assertEqual(decision.observed["request_type_ids"], [])
        self.assertIn("Create one Request type", decision.change)

    def test_one_compatible_pair_is_adopted(self):
        decision = protocol.reconcile_setup(
            configuration_value=None,
            catalog=self.pair(),
        )

        self.assertEqual(decision.action, "adopt_pair")
        self.assertEqual(
            decision.configuration,
            {
                "protocol": "image-upgrade/v1",
                "request_data_type": REQUEST_TYPE,
                "contribution_data_type": CONTRIBUTION_TYPE,
                "trusted_artifact_hosts": [],
            },
        )

    def test_partial_or_duplicate_state_stops_with_identifiers(self):
        with self.assertRaisesRegex(protocol.ProtocolError, REQUEST_TYPE):
            protocol.reconcile_setup(
                configuration_value=None,
                catalog=self.pair()[:1],
            )
        with self.assertRaisesRegex(protocol.ProtocolError, "duplicate"):
            protocol.reconcile_setup(
                configuration_value=None,
                catalog=[*self.pair(), self.pair()[0]],
            )

    def test_configured_pair_is_verified_without_replacement(self):
        configured = protocol.configuration(
            request_data_type=REQUEST_TYPE,
            contribution_data_type=CONTRIBUTION_TYPE,
            trusted_artifact_hosts=[],
        )

        decision = protocol.reconcile_setup(
            configuration_value=configured,
            catalog=self.pair(),
        )

        self.assertEqual(decision.action, "verified")
        self.assertEqual(decision.configuration, configured)
        self.assertEqual(decision.change, "No setup mutation.")

    def test_missing_or_role_incompatible_configured_type_stops(self):
        configured = protocol.configuration(
            request_data_type=REQUEST_TYPE,
            contribution_data_type=CONTRIBUTION_TYPE,
            trusted_artifact_hosts=[],
        )
        with self.assertRaisesRegex(protocol.ProtocolError, CONTRIBUTION_TYPE):
            protocol.reconcile_setup(
                configuration_value=configured,
                catalog=self.pair()[:1],
            )
        with self.assertRaisesRegex(protocol.ProtocolError, "Image Upgrade Request"):
            protocol.reconcile_setup(
                configuration_value=configured,
                catalog=[
                    {"id": REQUEST_TYPE, "name": "Image Upgrade Contribution"},
                    self.pair()[1],
                ],
            )

    def test_setup_decision_command_reads_observed_state_from_stdin(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "setup-decision"],
            input=json.dumps(
                {
                    "configuration": None,
                    "catalog": self.pair(),
                }
            ),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["action"], "adopt_pair")

    def test_setup_command_requires_confirmed_configuration_and_catalog_reads(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "setup-decision"],
            input="{}",
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("configuration", completed.stderr)
        self.assertIn("catalog", completed.stderr)

    def test_packaged_setup_cases_cover_every_reconciliation_outcome(self):
        cases = json.loads(SETUP_CASES.read_text(encoding="utf-8"))

        for case in cases:
            with self.subTest(case=case["name"]):
                if "expected_action" in case:
                    decision = protocol.reconcile_setup(
                        configuration_value=case["configuration"],
                        catalog=case["catalog"],
                    )
                    self.assertEqual(decision.action, case["expected_action"])
                else:
                    with self.assertRaisesRegex(
                        protocol.ProtocolError, case["expected_error"]
                    ):
                        protocol.reconcile_setup(
                            configuration_value=case["configuration"],
                            catalog=case["catalog"],
                        )

class ContributionEnvelopeTests(unittest.TestCase):
    def test_valid_contribution_is_canonicalized(self):
        envelope = protocol.contribution_envelope(
            request_id=REQUEST_ID,
            representations=[
                {
                    "url": "https://assets.example/image.png",
                    "media_type": "image/png",
                    "sha256": "a" * 64,
                }
            ],
            summary="A field-guide interpretation.",
        )

        self.assertEqual(envelope["protocol"], "image-upgrade/v1")
        self.assertEqual(envelope["request_id"], REQUEST_ID)
        self.assertEqual(envelope["summary"], "A field-guide interpretation.")
        self.assertEqual(envelope["representations"][0]["sha256"], "a" * 64)

    def test_matching_contributions_use_exact_request_id_and_preserve_order(self):
        other_request = "22222222-2222-4222-8222-222222222222"
        first = protocol.contribution_envelope(
            request_id=REQUEST_ID,
            representations=[
                {
                    "url": "https://assets.example/first.png",
                    "media_type": "image/png",
                    "sha256": "a" * 64,
                }
            ],
        )
        unrelated = protocol.contribution_envelope(
            request_id=other_request,
            representations=[
                {
                    "url": "https://assets.example/other.png",
                    "media_type": "image/png",
                    "sha256": "b" * 64,
                }
            ],
        )
        second = protocol.contribution_envelope(
            request_id=REQUEST_ID,
            representations=[
                {
                    "url": "https://assets.example/second.png",
                    "media_type": "image/png",
                    "sha256": "c" * 64,
                }
            ],
        )
        records = [
            {"id": "first", "note": json.dumps(first)},
            {"id": "other", "note": json.dumps(unrelated)},
            {"id": "second", "note": json.dumps(second)},
        ]

        matches, errors = protocol.matching_contributions(records, REQUEST_ID)

        self.assertEqual([record["id"] for record in matches], ["first", "second"])
        self.assertEqual(errors, [])

    def test_contribution_rejects_fields_outside_v1(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.validate_contribution_envelope(
                {
                    "protocol": "image-upgrade/v1",
                    "request_id": REQUEST_ID,
                    "representations": [
                        {
                            "url": "https://assets.example/image.png",
                            "media_type": "image/png",
                            "sha256": "a" * 64,
                        }
                    ],
                    "completed": True,
                }
            )

    def test_contribution_record_command_wraps_compact_note_for_fulcra(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "contribution-record"],
            input=json.dumps(
                {
                    "request_id": REQUEST_ID,
                    "representations": [
                        {
                            "url": "https://assets.example/image.png",
                            "media_type": "image/png",
                            "sha256": "a" * 64,
                        }
                    ],
                }
            ),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        record = json.loads(completed.stdout)
        self.assertEqual(json.loads(record["note"])["request_id"], REQUEST_ID)


class RepresentationVerificationTests(unittest.TestCase):
    def representation(self, content=b"known image bytes"):
        return {
            "url": "https://assets.example/image.png",
            "media_type": "image/png",
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    def authorization(
        self,
        final_url="https://assets.example/image.png",
        trusted_hosts=None,
        approved=False,
    ):
        return protocol.authorize_retrieval(
            candidate_url=final_url,
            trusted_artifact_hosts=(
                ["assets.example"] if trusted_hosts is None else trusted_hosts
            ),
            user_approved=approved,
        )

    def test_trusted_https_representation_with_matching_bytes_is_verified(self):
        content = b"known image bytes"

        result = protocol.verify_representation(
            representation=self.representation(content),
            authorization=self.authorization(),
            observed_media_type="image/png",
            content=content,
        )

        self.assertTrue(result.accepted)
        self.assertEqual(result.status, "verified")
        self.assertEqual(result.final_host, "assets.example")

    def test_untrusted_final_host_requires_approval_even_after_trusted_redirect(self):
        result = self.authorization(
            final_url="https://redirected.example/image.png",
            trusted_hosts=["assets.example"],
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.status, "approval_required")
        self.assertEqual(result.host, "redirected.example")

    def test_explicit_approval_does_not_override_digest_or_media_type(self):
        content = b"different bytes"
        digest_result = protocol.verify_representation(
            representation=self.representation(),
            authorization=self.authorization(
                final_url="https://other.example/image.png",
                trusted_hosts=[],
                approved=True,
            ),
            observed_media_type="image/png",
            content=content,
        )
        media_result = protocol.verify_representation(
            representation=self.representation(),
            authorization=self.authorization(
                final_url="https://other.example/image.png",
                trusted_hosts=[],
                approved=True,
            ),
            observed_media_type="text/html",
            content=b"known image bytes",
        )

        self.assertEqual(digest_result.status, "digest_mismatch")
        self.assertFalse(digest_result.accepted)
        self.assertEqual(media_result.status, "media_type_mismatch")
        self.assertFalse(media_result.accepted)

    def test_explicit_approval_accepts_matching_bytes_from_unlisted_final_host(self):
        result = protocol.verify_representation(
            representation=self.representation(),
            authorization=self.authorization(
                final_url="https://other.example/image.png",
                trusted_hosts=[],
                approved=True,
            ),
            observed_media_type="image/png",
            content=b"known image bytes",
        )

        self.assertTrue(result.accepted)
        self.assertEqual(result.status, "verified")

    def test_verify_command_authorizes_final_host_before_opening_content(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "verify-artifact"],
            input=json.dumps(
                {
                    "representation": self.representation(),
                    "final_url": "https://other.example/image.png",
                    "observed_media_type": "image/png",
                    "content_path": "/path/that/does/not/exist.png",
                    "trusted_artifact_hosts": [],
                }
            ),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status"], "approval_required")

    def test_representation_rejects_fields_outside_v1(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.verify_representation(
                representation={**self.representation(), "filename": "image.png"},
                authorization=self.authorization(),
                observed_media_type="image/png",
                content=b"known image bytes",
            )

    def test_non_boolean_approval_is_rejected(self):
        with self.assertRaises(protocol.ProtocolError):
            self.authorization(
                final_url="https://other.example/image.png",
                trusted_hosts=[],
                approved="false",
            )

    def test_verify_artifact_command_reports_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "image.png"
            artifact.write_bytes(b"different bytes")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "verify-artifact"],
                input=json.dumps(
                    {
                        "representation": self.representation(),
                        "final_url": "https://assets.example/image.png",
                        "observed_media_type": "image/png",
                        "content_path": str(artifact),
                        "trusted_artifact_hosts": ["assets.example"],
                    }
                ),
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["status"], "digest_mismatch")

    def test_file_representation_command_hashes_published_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "image.png"
            artifact.write_bytes(b"known image bytes")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "file-representation"],
                input=json.dumps(
                    {
                        "content_path": str(artifact),
                        "url": "https://assets.example/image.png",
                        "media_type": "image/png",
                    }
                ),
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        representation = json.loads(completed.stdout)
        self.assertEqual(
            representation["sha256"], hashlib.sha256(b"known image bytes").hexdigest()
        )


class RoundTripFixtureTests(unittest.TestCase):
    def test_valid_fixture_crosses_requester_and_producer_contract(self):
        fixture = json.loads(VALID_ROUND_TRIP.read_text(encoding="utf-8"))

        configuration = protocol.configuration(
            request_data_type=fixture["configuration"]["request_data_type"],
            contribution_data_type=fixture["configuration"][
                "contribution_data_type"
            ],
            trusted_artifact_hosts=fixture["configuration"][
                "trusted_artifact_hosts"
            ],
        )
        request = protocol.validate_request_envelope(fixture["request"])
        receipt = protocol.request_receipt(**fixture["request_receipt"])
        contribution = protocol.validate_contribution_envelope(fixture["contribution"])
        record = {
            **fixture["contribution_record"],
            "note": json.dumps(contribution),
        }
        matches, errors = protocol.matching_contributions(
            [record], receipt["request_id"]
        )

        self.assertEqual(configuration, fixture["configuration"])
        self.assertEqual(request["request_id"], receipt["request_id"])
        self.assertEqual(matches[0]["envelope"], contribution)
        self.assertIn(
            "com.fulcradynamics.agent-skills.image-upgrader",
            matches[0]["sources"],
        )
        self.assertEqual(errors, [])


class RequestDiscoveryTests(unittest.TestCase):
    def test_requests_without_contributions_are_prioritized_and_errors_are_isolated(self):
        answered_id = REQUEST_ID
        unanswered_id = "22222222-2222-4222-8222-222222222222"
        requests = [
            {
                "id": "answered",
                "note": json.dumps(
                    protocol.request_envelope(
                        request_id=answered_id,
                        brief="An answered request.",
                    )
                ),
            },
            {
                "id": "unanswered",
                "note": json.dumps(
                    protocol.request_envelope(
                        request_id=unanswered_id,
                        brief="An unanswered request.",
                    )
                ),
            },
        ]
        contribution = protocol.contribution_envelope(
            request_id=answered_id,
            representations=[
                {
                    "url": "https://assets.example/image.png",
                    "media_type": "image/png",
                    "sha256": "a" * 64,
                }
            ],
        )
        contributions = [
            {"id": "malformed", "note": "not json"},
            {"id": "valid", "note": json.dumps(contribution)},
        ]

        prioritized, errors = protocol.prioritize_requests(requests, contributions)

        self.assertEqual(
            [record["id"] for record in prioritized], ["unanswered", "answered"]
        )
        self.assertEqual(prioritized[0]["contribution_count"], 0)
        self.assertEqual(prioritized[1]["contribution_count"], 1)
        self.assertEqual(errors[0]["record_id"], "malformed")


if __name__ == "__main__":
    unittest.main()
