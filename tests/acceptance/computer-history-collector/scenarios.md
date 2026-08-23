# Computer History Collector acceptance

Run against an authenticated test account or an explicitly approved owner account. Record only the Fulcra user ID, resolved `fulcra-api` and `uv` versions, unique test names, outcome summaries, and cleanup status in the ignored `.acceptance-runs` directory. Never retain tokens or returned account data.

## Entry prompt

> Use the Computer History Collector skill to set up continuous projection for this fixture Computer History directory, verify its operation and revision behavior, and then uninstall it without deleting owner context.

## Preconditions and approval gates

- macOS, `uv`, network access, and completed `10min` and `6h` fixture Markdown are available.
- Verify `user-info.userid` against the expected owner before any mutation; discard every other returned field.
- Use a unique computer name and run identifier for all test-created paths.
- Setup's data, file, and local scheduler mutations are authorized by the entry prompt. Obtain separate approval if cleanup would affect a pre-existing data type, tag, file, or record.
- Capture pre-existing exact-name data types and tags before setup so cleanup removes only test-created objects.

## Fresh setup and backfill

1. Create a temporary resources directory with one representative `10min` summary and one `6h` summary.
2. Set `COMPUTER_HISTORY_COLLECTOR_HOME` to a temporary Application Support-shaped directory.
3. Invoke `setup --source-folder <directory> --computer-name <unique test name> --no-launchd --minimum-age-seconds 0`.
4. Verify the two duration annotations, exact Markdown notes, intervals, cadence/computer/application tags, producer sources, two source files, collector manifest, local config, Projection Map, and healthy Projection Status.
5. Invoke `sweep --no-notify --minimum-age-seconds 0` again and verify no additional annotations or file snapshots.

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

## Uninstall and cleanup

1. Invoke `uninstall` and verify the manifest records that collection ended while remote context remains, then verify the LaunchAgent, plist, and managed runtime are absent.
2. Use the exact IDs and paths captured in the cleanup manifest to delete test records, files, tags, and temporary data types in reverse dependency order.
3. Preserve the cleanup manifest if any cleanup step fails.

## Required evidence

- Resolved `fulcra-api` and `uv` versions and authenticated owner ID.
- Initial and repeated sweep summaries.
- Read-back evidence for record count, record UUIDs, note hashes, intervals, tags, and sources—not raw note contents.
- File stat evidence for paths and version counts, plus the Collector Manifest headings and ended state.
- Local Projection Map and Projection Status outcome summaries.
- Exact cleanup targets, per-target result, and final cleanup status.
