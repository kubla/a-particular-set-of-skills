from __future__ import annotations

import importlib.util
import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parents[1] / "scripts" / "computer_history_collector.py"
SPEC = importlib.util.spec_from_file_location("computer_history_collector", SCRIPT)
collector_module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = collector_module
SPEC.loader.exec_module(collector_module)


TEN_MINUTE_NOTE = """---
title: A short work interval
description: Work in Codex and Safari
applications: [com.openai.codex, com.apple.Safari]
---

# Activity

The captured segment ended at `14:39:17Z` after the user finished the task.
"""

TEN_MINUTE = TEN_MINUTE_NOTE + """
## Citations

- /Users/example/Library/Caches/ComputerUse/segments/2026-08-23T14-30-00Z/events.jsonl
- /Users/example/Library/Caches/ComputerUse/segments/2026-08-23T14-30-00Z/metadata.json
"""

SIX_HOUR_NOTE = """---
title: A quiet block
description: No activity was visible
applications: []
---

# Summary

No activity was visible during this block.
"""

SIX_HOUR = SIX_HOUR_NOTE + """
## Citations

- 2026-08-23T12-00-00-AbCd-10min-memory-summary.md
"""

REVISED_TEN_MINUTE_NOTE = TEN_MINUTE_NOTE + "\nA corrected detail.\n"
REVISED_TEN_MINUTE = REVISED_TEN_MINUTE_NOTE + """
## Citations

- /Users/example/Library/Caches/ComputerUse/segments/2026-08-23T14-30-00Z/events.jsonl
"""


class FakeCLI:
    def __init__(self):
        self.uploads: list[tuple[Path, str]] = []
        self.records: list[tuple[str, dict, list[str], list[str]]] = []
        self.deletes: list[tuple[str, str]] = []
        self.events: list[tuple[str, str]] = []

    def authenticated_user_id(self) -> str:
        return "11111111-1111-4111-8111-111111111111"

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        self.uploads.append((local_path, remote_path))
        self.events.append(("upload", remote_path))

    def record(self, data_type: str, record: dict, tags, sources) -> None:
        self.records.append((data_type, record, list(tags), list(sources)))
        self.events.append(("record", record["id"]))

    def delete_record(self, data_type: str, record_id: str) -> None:
        self.deletes.append((data_type, record_id))
        self.events.append(("delete", record_id))


class FailingCLI(FakeCLI):
    def __init__(self, operation: str):
        super().__init__()
        self.operation = operation

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        if self.operation == "upload":
            raise collector_module.CollectorError("synthetic upload failure")
        super().upload_file(local_path, remote_path)

    def record(self, data_type: str, record: dict, tags, sources) -> None:
        if self.operation == "record":
            raise collector_module.CollectorError("synthetic record failure")
        super().record(data_type, record, tags, sources)

    def delete_record(self, data_type: str, record_id: str) -> None:
        if self.operation == "delete":
            raise collector_module.CollectorError("synthetic delete failure")
        super().delete_record(data_type, record_id)


class SummaryParsingTests(unittest.TestCase):
    def test_known_helper_bundle_ids_have_human_readable_names(self):
        self.assertEqual(
            collector_module.resolve_application_name("com.apple.dock.helper"),
            "Dock Helper",
        )
        self.assertEqual(
            collector_module.resolve_application_name(
                "com.apple.appkit.xpc.openAndSavePanelService"
            ),
            "Open and Save Panel",
        )

    def test_preserves_source_and_projects_without_citations(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-23T14-30-00-AbCd-10min-memory-summary.md"
            path.write_text(TEN_MINUTE, encoding="utf-8")

            summary = collector_module.parse_summary(path)

        self.assertEqual(summary.content, TEN_MINUTE)
        self.assertEqual(summary.projected_note, TEN_MINUTE_NOTE)
        self.assertEqual(summary.kind, "10min")
        self.assertEqual(
            collector_module.isoformat(summary.start), "2026-08-23T14:30:00Z"
        )
        self.assertEqual(
            collector_module.isoformat(summary.end), "2026-08-23T14:39:17Z"
        )
        self.assertEqual(summary.applications, ("com.openai.codex", "com.apple.Safari"))

    def test_six_hour_no_activity_summary_is_valid_and_uses_nominal_end(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-23T12-00-00-WxYz-6h-memory-summary.md"
            path.write_text(SIX_HOUR, encoding="utf-8")

            summary = collector_module.parse_summary(path)

        self.assertEqual(summary.applications, ())
        self.assertEqual(
            collector_module.isoformat(summary.end), "2026-08-23T18:00:00Z"
        )

    def test_six_hour_child_session_end_does_not_shorten_rollup(self):
        content = (
            SIX_HOUR_NOTE
            + "\nA child segment recorded a session.ended event at `2026-08-23T12:17:04Z`.\n"
            + "\n## Citations\n\n- 2026-08-23T12-00-00-AbCd-10min-memory-summary.md\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-23T12-00-00-WxYz-6h-memory-summary.md"
            path.write_text(content, encoding="utf-8")

            summary = collector_module.parse_summary(path)

        self.assertEqual(
            collector_module.isoformat(summary.end), "2026-08-23T18:00:00Z"
        )

    def test_rejects_unexpected_format(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "not-computer-history.md"
            path.write_text(TEN_MINUTE, encoding="utf-8")
            with self.assertRaises(collector_module.CollectorError):
                collector_module.parse_summary(path)

    def test_projection_does_not_interpret_citation_content(self):
        changed = TEN_MINUTE_NOTE + "\n## Citations\n\n- https://example.com/source\n"
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-23T14-30-00-AbCd-10min-memory-summary.md"
            path.write_text(changed, encoding="utf-8")

            summary = collector_module.parse_summary(path)

        self.assertEqual(summary.projected_note, TEN_MINUTE_NOTE)

    def test_projection_keeps_markdown_when_citations_section_disappears(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-23T14-30-00-AbCd-10min-memory-summary.md"
            path.write_text(TEN_MINUTE_NOTE, encoding="utf-8")

            summary = collector_module.parse_summary(path)

        self.assertEqual(summary.projected_note, TEN_MINUTE_NOTE)

    def test_projection_keeps_nonterminal_citations_section(self):
        changed = (
            TEN_MINUTE_NOTE
            + "\n## Citations\n\n- /tmp/source.jsonl\n"
            + "\n## Later content\n\nThis must not be discarded.\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-23T14-30-00-AbCd-10min-memory-summary.md"
            path.write_text(changed, encoding="utf-8")

            summary = collector_module.parse_summary(path)

        self.assertEqual(summary.projected_note, changed)

    def test_preview_exposes_exact_note_and_human_readable_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "2026-08-23T14-30-00-AbCd-10min-memory-summary.md"
            path.write_text(TEN_MINUTE, encoding="utf-8")
            summary = collector_module.parse_summary(path)

            preview = collector_module.projection_preview(summary, "Feedback Mac")

        self.assertEqual(preview["annotation"]["note"], TEN_MINUTE_NOTE)
        self.assertEqual(
            preview["annotation"]["recorded_at"],
            {
                "start_time": "2026-08-23T14:30:00Z",
                "end_time": "2026-08-23T14:39:17Z",
            },
        )
        self.assertEqual(
            preview["tag_names"],
            ["Feedback Mac", "Codex", "Safari"],
        )
        self.assertEqual(
            preview["collector_sources"],
            [
                "Codex",
                "Codex Computer History",
                "Codex Computer History on Feedback Mac",
            ],
        )
        self.assertNotIn("remote_file", preview["annotation"])


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.state = (
            root / "Application Support" / "Fulcra" / "computer-history-collector"
        )
        self.source = root / "resources"
        self.source.mkdir(parents=True)
        self.cli = FakeCLI()
        self.collector = collector_module.Collector(self.state, self.cli)
        config = {
            "version": 1,
            "computer_name": "Test Mac",
            "source_folder": str(self.source),
            "fulcra_user_id": self.cli.authenticated_user_id(),
            "manifest_path": "Collector Manifests/Computer History Collector/Test Mac.md",
            "data_types": {
                "10min": "DurationAnnotation/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "6h": "DurationAnnotation/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            },
        }
        collector_module.atomic_json(self.collector.config_path, config)

    def tearDown(self):
        self.temporary.cleanup()

    def add_summary(
        self,
        name="2026-08-23T14-30-00-AbCd-10min-memory-summary.md",
        content=TEN_MINUTE,
    ):
        path = self.source / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_first_sweep_projects_file_and_record_with_expected_shape(self):
        path = self.add_summary()

        counts = self.collector.sweep(notify=False, minimum_age_seconds=0)

        self.assertEqual(counts["created"], 1)
        self.assertEqual(len(self.cli.uploads), 1)
        self.assertEqual(self.cli.uploads[0][0], path)
        self.assertEqual(
            self.cli.uploads[0][1],
            "Codex/Test Mac/memories/extensions/skysight/resources/" + path.name,
        )
        data_type, record, tags, sources = self.cli.records[0]
        self.assertEqual(
            data_type, "DurationAnnotation/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        )
        self.assertEqual(record["note"], TEN_MINUTE_NOTE)
        self.assertNotIn("remote_file", record)
        self.assertEqual(record["recorded_at"]["end_time"], "2026-08-23T14:39:17Z")
        self.assertEqual(tags, ["Test Mac", "Codex", "Safari"])
        self.assertEqual(
            sources,
            ["Codex", "Codex Computer History", "Codex Computer History on Test Mac"],
        )
        projection_map = json.loads(self.collector.map_path.read_text())
        self.assertEqual(projection_map["files"][path.name]["record_id"], record["id"])

    def test_second_sweep_is_idempotent(self):
        self.add_summary()
        self.collector.sweep(notify=False, minimum_age_seconds=0)
        self.cli.uploads.clear()
        self.cli.records.clear()

        counts = self.collector.sweep(notify=False, minimum_age_seconds=0)

        self.assertEqual(counts["unchanged"], 1)
        self.assertEqual(self.cli.uploads, [])
        self.assertEqual(self.cli.records, [])

    def test_revision_records_new_content_before_retiring_prior_record(self):
        path = self.add_summary()
        self.collector.sweep(notify=False, minimum_age_seconds=0)
        prior_id = self.cli.records[0][1]["id"]
        self.cli.events.clear()
        path.write_text(REVISED_TEN_MINUTE, encoding="utf-8")

        counts = self.collector.sweep(notify=False, minimum_age_seconds=0)

        revised_id = self.cli.records[-1][1]["id"]
        self.assertEqual(counts["revised"], 1)
        self.assertNotEqual(revised_id, prior_id)
        self.assertEqual(
            [event[0] for event in self.cli.events], ["upload", "record", "delete"]
        )
        self.assertEqual(self.cli.deletes[-1][1], prior_id)
        projection_map = json.loads(self.collector.map_path.read_text())
        self.assertEqual(projection_map["files"][path.name]["record_id"], revised_id)

    def test_local_absence_never_deletes_remote_context(self):
        path = self.add_summary()
        self.collector.sweep(notify=False, minimum_age_seconds=0)
        projection_map_before = self.collector.map_path.read_text()
        path.unlink()
        self.cli.uploads.clear()
        self.cli.records.clear()
        self.cli.deletes.clear()

        self.collector.sweep(notify=False, minimum_age_seconds=0)

        self.assertEqual(self.cli.uploads, [])
        self.assertEqual(self.cli.records, [])
        self.assertEqual(self.cli.deletes, [])
        self.assertEqual(self.collector.map_path.read_text(), projection_map_before)

    def test_record_failure_does_not_advance_projection_map(self):
        self.add_summary()
        failing = FailingCLI("record")
        self.collector.cli = failing

        with self.assertRaises(collector_module.CollectorError):
            self.collector.sweep(notify=False, minimum_age_seconds=0)

        self.assertFalse(self.collector.map_path.exists())
        status = json.loads(self.collector.status_path.read_text())
        self.assertEqual(status["state"], "error")

    def test_interrupted_revision_retries_before_advancing_map(self):
        path = self.add_summary()
        self.collector.sweep(notify=False, minimum_age_seconds=0)
        prior_map = json.loads(self.collector.map_path.read_text())
        failing = FailingCLI("delete")
        self.collector.cli = failing
        path.write_text(REVISED_TEN_MINUTE, encoding="utf-8")

        with self.assertRaises(collector_module.CollectorError):
            self.collector.sweep(notify=False, minimum_age_seconds=0)

        self.assertEqual(json.loads(self.collector.map_path.read_text()), prior_map)
        failing.operation = ""
        counts = self.collector.sweep(notify=False, minimum_age_seconds=0)
        self.assertEqual(counts["revised"], 1)
        self.assertNotEqual(
            json.loads(self.collector.map_path.read_text()),
            prior_map,
        )

    def test_owner_change_stops_before_any_remote_write(self):
        self.add_summary()

        class OtherOwnerCLI(FakeCLI):
            def authenticated_user_id(self) -> str:
                return "22222222-2222-4222-8222-222222222222"

        other_owner = OtherOwnerCLI()
        self.collector.cli = other_owner

        with self.assertRaises(collector_module.CollectorError):
            self.collector.sweep(notify=False, minimum_age_seconds=0)

        self.assertEqual(other_owner.uploads, [])
        self.assertEqual(other_owner.records, [])
        status = json.loads(self.collector.status_path.read_text())
        self.assertEqual(status["state"], "action_required")
        self.assertEqual(status["condition"], "fulcra-owner-changed")


class StatusTests(unittest.TestCase):
    def test_notification_only_when_entering_a_new_action_required_condition(self):
        with tempfile.TemporaryDirectory() as temporary:
            collector = collector_module.Collector(Path(temporary), FakeCLI())
            with mock.patch.object(collector_module.subprocess, "run") as run:
                collector.update_status(
                    "action_required", "Sign in", condition="auth", notify=True
                )
                collector.update_status(
                    "action_required", "Sign in", condition="auth", notify=True
                )
                collector.update_status("ok", "Recovered")
                collector.update_status(
                    "action_required", "Sign in", condition="auth", notify=True
                )

        self.assertEqual(run.call_count, 2)


class ManifestTests(unittest.TestCase):
    def test_manifest_is_declarative_and_uninstall_variant_retains_context(self):
        config = {
            "computer_name": "A/B Mac",
            "source_folder": "/example/resources",
        }
        active = collector_module.manifest_markdown(config)
        ended = collector_module.manifest_markdown(
            config, ended_at="2026-08-23T20:00:00Z"
        )

        for heading in (
            "# Collector",
            "# Sources",
            "# Intended outputs",
            "# Collection behavior",
        ):
            self.assertIn(heading, active)
        self.assertIn("Codex/A%2FB Mac/", active)
        self.assertNotIn("last successful", active.lower())
        self.assertIn("Collection has ended", ended)
        self.assertIn("retained", ended.lower())

    def test_installed_launcher_uses_uv_while_collector_uses_uvx(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "computer-history-collector"
            collector_module.install_runtime(state, SCRIPT, "/opt/example/bin/uv")

            launcher = (state / "bin" / "computer-history-collector").read_text()

        self.assertIn('exec "/opt/example/bin/uv" run --script', launcher)
        self.assertNotIn("uvx run", launcher)

    def test_uv_tool_path_preserves_stable_symlink(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "Cellar" / "uv-0.9.26"
            target.parent.mkdir()
            target.write_text("", encoding="utf-8")
            stable = root / "bin" / "uv"
            stable.parent.mkdir()
            stable.symlink_to(target)
            with mock.patch.object(
                collector_module.shutil, "which", return_value=str(stable)
            ):
                resolved = collector_module.uv_tool_path("uv")

        self.assertEqual(resolved, str(stable))

    def test_launch_agent_runs_managed_script_every_ten_minutes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "runtime"
            (state / "logs").mkdir(parents=True)
            plist_path = root / "LaunchAgents" / "collector.plist"
            completed = subprocess.CompletedProcess([], 0, "", "")
            with (
                mock.patch.object(
                    collector_module, "launch_agent_path", return_value=plist_path
                ),
                mock.patch.object(
                    collector_module.subprocess, "run", return_value=completed
                ) as run,
                mock.patch.dict(
                    collector_module.os.environ,
                    {"COMPUTER_HISTORY_COLLECTOR_HOME": str(state)},
                ),
            ):
                collector_module.install_launch_agent(state, "/opt/example/bin/uv")

            with plist_path.open("rb") as stream:
                payload = plistlib.load(stream)

        self.assertEqual(payload["StartInterval"], 600)
        self.assertTrue(payload["RunAtLoad"])
        self.assertEqual(
            payload["ProgramArguments"][0:3], ["/opt/example/bin/uv", "run", "--script"]
        )
        self.assertEqual(payload["ProgramArguments"][-1], "sweep")
        self.assertEqual(
            payload["EnvironmentVariables"]["COMPUTER_HISTORY_COLLECTOR_HOME"],
            str(state),
        )
        self.assertEqual(run.call_count, 2)

    def test_override_uninstall_target_requires_managed_runtime_shape(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "unrelated"
            state.mkdir()
            config = {"collector": collector_module.COLLECTOR_NAME}
            with (
                mock.patch.dict(
                    collector_module.os.environ,
                    {"COMPUTER_HISTORY_COLLECTOR_HOME": str(state)},
                ),
                self.assertRaises(collector_module.CollectorError),
            ):
                collector_module.validate_removal_target(state, config)


if __name__ == "__main__":
    unittest.main()
