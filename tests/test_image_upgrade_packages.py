from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class ImageUpgradePackageTests(unittest.TestCase):
    def test_sibling_skills_ship_the_same_protocol_contract(self):
        producer = (
            ROOT / "skills" / "image-upgrader" / "references" / "protocol.md"
        ).read_bytes()
        requester = (
            ROOT
            / "skills"
            / "request-image-generation"
            / "references"
            / "protocol.md"
        ).read_bytes()

        self.assertEqual(requester, producer)

    def test_sibling_skills_ship_the_same_valid_round_trip_fixture(self):
        producer = (
            ROOT
            / "skills"
            / "image-upgrader"
            / "references"
            / "valid-round-trip.json"
        ).read_bytes()
        requester = (
            ROOT
            / "skills"
            / "request-image-generation"
            / "references"
            / "valid-round-trip.json"
        ).read_bytes()

        self.assertEqual(requester, producer)


if __name__ == "__main__":
    unittest.main()
