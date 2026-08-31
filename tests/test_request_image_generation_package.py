from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = (
    ROOT
    / "tests"
    / "acceptance"
    / "request-image-generation"
    / "scripts"
    / "package_skill.py"
)
SPEC = importlib.util.spec_from_file_location("package_request_image_generation", SCRIPT)
packager = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = packager
SPEC.loader.exec_module(packager)


class RequestImageGenerationPackageTests(unittest.TestCase):
    def test_package_is_deterministic_and_has_one_skill_root(self):
        skill = ROOT / "skills" / "request-image-generation"
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"

            first_receipt = packager.build_package(skill, first)
            second_receipt = packager.build_package(skill, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_receipt["sha256"], second_receipt["sha256"])
            with zipfile.ZipFile(first) as archive:
                members = archive.namelist()
                contents = b"\n".join(archive.read(name) for name in members).lower()

        self.assertEqual(
            members,
            [
                "request-image-generation/SKILL.md",
                "request-image-generation/agents/openai.yaml",
                "request-image-generation/references/check-contributions.md",
                "request-image-generation/references/protocol.md",
                "request-image-generation/references/setup-cases.json",
                "request-image-generation/references/setup.md",
                "request-image-generation/references/valid-round-trip.json",
            ],
        )
        self.assertEqual({name.split("/", 1)[0] for name in members}, {"request-image-generation"})
        self.assertNotIn("request-image-generation/config.json", members)
        for marker in (
            b"access_token",
            b"refresh_token",
            b"api_key",
            b"client_secret",
            b"authorization: bearer",
        ):
            self.assertNotIn(marker, contents)


if __name__ == "__main__":
    unittest.main()
