---
name: computer-history-collector
description: Preview, set up, and operate the Computer History Collector, which continuously projects completed Codex Computer History Markdown summaries into the owner's Fulcra context lake. Use when a user wants to inspect, collect, backfill, check, repair, or stop Computer History collection in Fulcra, or asks about this collector's projection behavior.
compatibility: Requires macOS, uv, and network access.
metadata:
  version: "0.2.0"
---

# Computer History Collector

Use the bundled runtime to configure a token-free macOS LaunchAgent that sweeps about every ten minutes.

## Preview

When the user wants to inspect the projected contents before setup, run this from the skill directory:

```bash
uv run --script scripts/computer_history_collector.py preview "<completed summary.md>"
```

This prints the projected note, interval, tag names, collector sources, data type, and remote file path. The projected note preserves the summary Markdown except for its terminal `Citations` section; the uploaded source file remains unchanged. Preview does not authenticate or write to Fulcra.

When the user asks to review a preview before setup, stop after presenting it and wait for their feedback before authenticating or writing anything.

## Set up

1. Confirm this is a Mac with Codex Computer History enabled.
2. Locate the completed summaries directory. Prefer `$CODEX_HOME/memories/extensions/skysight/resources`; otherwise use `~/.codex/memories/extensions/skysight/resources` or ask for its location.
3. If independently verifying the authenticated owner before setup, expose only the owner ID in the task transcript:

   ```bash
   uvx --from fulcra-api@latest fulcra user-info | jq '{userid}'
   ```

   Never run unfiltered `user-info` in an agent-visible command because its response may contain unrelated private account fields.
4. From this skill directory, run:

   ```bash
   uv run --script scripts/computer_history_collector.py setup --source-folder "<absolute path>"
   ```

5. Help the user complete Fulcra's browser sign-in if prompted.
6. Report the authenticated owner, computer name, initial sweep counts, managed runtime path, and whether scheduling succeeded. Never print or retain an access token.

Setup is convergent. It preserves local configuration, Projection Map, and Projection Status while refreshing the managed runtime.

## Operate

After setup, invoke the managed executable:

```bash
"$HOME/Library/Application Support/Fulcra/computer-history-collector/bin/computer-history-collector" status
"$HOME/Library/Application Support/Fulcra/computer-history-collector/bin/computer-history-collector" sweep
"$HOME/Library/Application Support/Fulcra/computer-history-collector/bin/computer-history-collector" diagnose
```

Use `status` for the passive last-sweep signal. Use `diagnose` only when status indicates a problem or the user asks for investigation.

To stop collection:

```bash
"$HOME/Library/Application Support/Fulcra/computer-history-collector/bin/computer-history-collector" uninstall
```

Uninstall updates the collector's Fulcra manifest, removes only the local runtime and LaunchAgent, and retains all projected context and source-file snapshots.

Read [behavior.md](references/behavior.md) before changing parsing, projection, revision, notification, or deletion behavior.
