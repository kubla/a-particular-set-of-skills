from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "image_upgrade_protocol.py"
VALID_ROUND_TRIP = Path(__file__).parents[1] / "references" / "valid-round-trip.json"
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


if __name__ == "__main__":
    unittest.main()
