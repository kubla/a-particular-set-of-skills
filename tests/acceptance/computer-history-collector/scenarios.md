# Computer History Collector acceptance

Run against an authenticated test account or an explicitly approved owner account. Record only the Fulcra user ID, resolved `fulcra-api` and `uv` versions, unique test names, outcome summaries, and cleanup status in the ignored `.acceptance-runs` directory. Never retain tokens or returned account data.

## Entry prompt

> Use the Computer History Collector skill to set up continuous projection for this fixture Computer History directory, verify its operation and revision behavior, and then uninstall it without deleting owner context.

## Preconditions and approval gates

- macOS, `uv`, network access, and completed `10min` and `6h` fixture Markdown are available.
- Verify `user-info.userid` against the expected owner before any mutation; discard every other returned field.
- When an agent performs that check, require `uvx --from fulcra-api@latest fulcra user-info | jq '{userid}'`; fail the run if raw `user-info` output enters the task transcript.
- Use a unique computer name and run identifier for all test-created paths.
- Setup's data, file, and local scheduler mutations are authorized by the entry prompt. Obtain separate approval if cleanup would affect a pre-existing data type, tag, file, or record.
- Capture pre-existing exact-name data types and tags before setup so cleanup removes only test-created objects.

## Fresh setup and backfill

1. Create a temporary resources directory with one representative `10min` summary and one `6h` summary.
2. Invoke `preview` for each fixture and verify it performs no authentication or Fulcra mutation and matches the later record's projected note, interval, tag names, collector sources, data type, and remote path.
3. Set `COMPUTER_HISTORY_COLLECTOR_HOME` to a temporary Application Support-shaped directory.
4. Invoke `setup --source-folder <directory> --computer-name <unique test name> --no-launchd --minimum-age-seconds 0`.
5. Verify the two duration annotations, projected notes, intervals, computer/application tags, producer sources, two source files, collector manifest, local config, Projection Map, and healthy Projection Status. Each source file must match its local Markdown exactly; each annotation note must equal that Markdown with only its terminal `## Citations` section removed. Verify cadence is represented by the data type rather than duplicated as a tag.
6. Invoke `sweep --no-notify --minimum-age-seconds 0` again and verify no additional annotations or file snapshots.

## Repository source-format audit

1. Run `uv run --script tests/acceptance/computer-history-collector/scripts/audit_source_format.py` against the author's current Computer History resources directory.
2. Verify every current summary has the expected filename and frontmatter fields, one terminal Citations section, and only the citation categories recorded in ADR 0010.
3. Treat an audit failure as a repository-maintenance signal: inspect the new corpus, reconsider ADR 0010 if the citations became useful, and update the collector deliberately. It is not an installed-collector failure or user notification.

## Live release verification

After installing against an explicitly approved owner account, run the read-only verifier and retain its JSON receipt:

```bash
uv run --script tests/acceptance/computer-history-collector/scripts/verify_release_install.py \
  --expected-owner-id "<Fulcra user ID>" \
  --receipt ".acceptance-runs/computer-history-collector/<run>/verification.json"
```

The verifier checks the installed and managed runtimes, local configuration, Projection Map and Status, launchd registration, every stable source-to-record mapping, projected-note hashes, producer sources, exact computer/application tags, absence of cadence tags, representative source files, and the Collector Manifest. It reports only IDs, hashes, counts, paths, and failures; it does not print annotation contents, account details, or credentials.

## Scheduler

1. Rerun convergent setup without `--no-launchd` against the same isolated runtime.
2. Verify `launchctl print gui/<uid>/com.fulcradynamics.computer-history-collector` reports the managed `uv run --script ... sweep` command, a 600-second interval, one RunAtLoad invocation, and exit code 0.
3. Verify Projection Status reflects that unattended invocation and no duplicate artifact was created.

## Revision

1. Change one present Markdown file without renaming it.
2. Sweep again.
3. Verify a new source-file snapshot exists, exactly one current Timeline annotation represents the filename's interval, its note is revised, and the Projection Map points to the revised hash and UUID.

## Absence and failure

1. Remove a local fixture and sweep; verify its remote file and annotation remain.
2. Use expired or absent test credentials for an unattended sweep; verify pending work remains, Projection Status requires action, and no browser flow begins.
3. Repeat the same condition and verify it would not emit another notification.

## First-time installation experience

Run this scenario in a disposable macOS user account or VM with Codex Computer History enabled, `uv` installed, no Fulcra credentials, no prior collector runtime, and no pre-existing collector data types.

1. Install only the `skills/computer-history-collector/` directory through the ordinary Agent Skill installation path.
2. In a new Codex thread, ask: `Set up Computer History collection in my Fulcra account, but preview one real annotation for me before making any changes.`
3. Observe whether the agent finds the source folder, shows an understandable preview, explains the two data types and recurring LaunchAgent, and waits for owner authorization before authentication or writes.
4. Complete Fulcra's device authorization as the human. Verify that no token appears in the conversation or receipt.
5. Confirm setup reports the owner ID, computer name, backfill counts, runtime path, and scheduler result in plain language.
6. Log out and back in, verify a later summary is projected by launchd without Codex running, then run `status` and `diagnose` through a new agent thread.

## Uninstall and cleanup

1. Invoke `uninstall` and verify the manifest records that collection ended while remote context remains, then verify the LaunchAgent, plist, and managed runtime are absent.
2. Use the exact IDs and paths captured in the cleanup manifest to delete test records, files, tags, and temporary data types in reverse dependency order.
3. Preserve the cleanup manifest if any cleanup step fails.

## Required evidence

- Resolved `fulcra-api` and `uv` versions and authenticated owner ID.
- Initial and repeated sweep summaries.
- Read-back evidence for record count, record UUIDs, projected-note hashes, intervals, tags, and sources—not raw note contents.
- Source-file hashes proving that originals, including their Citations sections, remain unchanged.
- File stat evidence for paths and version counts, plus the Collector Manifest headings and ended state.
- Local Projection Map and Projection Status outcome summaries.
- Exact cleanup targets, per-target result, and final cleanup status.
