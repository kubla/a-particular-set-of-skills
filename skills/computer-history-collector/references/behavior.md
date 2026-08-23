# Collector behavior

## Boundary

The collector reads only completed derived Markdown whose filename matches Codex Computer History's `10min` or `6h` resource convention. It never reads raw event streams. A file younger than 30 seconds or changing while read is deferred to a later sweep.

Every completed summary is projected, including summaries that describe no activity. A missing local file never implies remote deletion.

## Owner context

Each summary produces two independently permissionable artifacts:

- A source-file upload at `Codex/<computer name>/memories/extensions/skysight/resources/<filename>`.
- One duration annotation in either `Computer History (10-minute)` or `Computer History (6-hour)`.

There are exactly two account-wide data types. Multiple computers contribute to them and are distinguished by the exact macOS computer-name tag and producer source. Identically named computers intentionally coalesce.

The annotation note is the unchanged Markdown. Tags contain the summary cadence, computer name, and human-readable name of every application in frontmatter. Its start is the UTC timestamp in the filename. A plausible explicit end stated in the derived Markdown wins; otherwise the end is ten minutes or six hours after the start.

The annotation does not contain a deterministic link to the uploaded source file.

## Revisions and local state

`projection-map.json` maps filename and content hash to remote file path and record UUID. Unchanged content is skipped. Changed content creates a Fulcra file snapshot, records a new deterministic annotation UUID, and retires the prior annotation. The new record is written before the old one is deleted so an interrupted revision does not leave the Timeline blank.

The Projection Map and `status.json` are local operational state, not owner context. Losing the map must not cause remote deletion.

## Collector manifest

The collector owns `Collector Manifests/Computer History Collector/<computer name>.md` in Fulcra Files and remembers that path in local configuration. It states sources, intended outputs, and collection behavior. It is declarative, not a heartbeat. Setup updates it only when its content changes; uninstall writes an ended state.

## Scheduling and signals

Setup copies the runtime beneath `~/Library/Application Support/Fulcra/computer-history-collector/` and installs a per-user LaunchAgent with a 600-second interval. Scheduled sweeps use `uvx --from fulcra-api@latest fulcra`; they do not invoke an AI product and never begin an interactive sign-in.

Projection Status is passive. A built-in macOS notification appears once when the collector enters a new unresolved condition requiring user action. Repeats, transient errors, normal gaps, successes, and recovery are silent.
