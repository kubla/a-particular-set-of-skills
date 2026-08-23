---
name: computer-history-collector
description: Set up and operate the Computer History Collector, which continuously projects completed Codex Computer History Markdown summaries into the owner's Fulcra context lake. Use when a user wants to collect, backfill, check, repair, or stop Computer History collection in Fulcra, or asks about this collector's projection behavior.
compatibility: Requires uv and network access.
---

# Computer History Collector

Use the bundled runtime to configure a token-free macOS LaunchAgent that sweeps about every ten minutes.

## Set up

1. Confirm this is a Mac with Codex Computer History enabled.
2. Locate the completed summaries directory. Prefer `$CODEX_HOME/memories/extensions/skysight/resources`; otherwise use `~/.codex/memories/extensions/skysight/resources` or ask for its location.
3. From this skill directory, run:

   ```bash
   uv run --script scripts/computer_history_collector.py setup --source-folder "<absolute path>"
   ```

4. Help the user complete Fulcra's browser sign-in if prompted.
5. Report the authenticated owner, computer name, initial sweep counts, managed runtime path, and whether scheduling succeeded. Never print or retain an access token.

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
