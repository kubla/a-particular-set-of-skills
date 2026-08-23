---
status: accepted
---

# Install the runtime under Application Support

Setup installs one managed collector tree at `~/Library/Application Support/Fulcra/computer-history-collector/`, with its executable at `bin/computer-history-collector`. The Agent Skill and per-user LaunchAgent invoke that executable by absolute path. V1 does not install a command link elsewhere or modify the user's `PATH`; the LaunchAgent property list under `~/Library/LaunchAgents/` is the separate registration artifact required by macOS.

This was chosen over running in place from the skill directory because users and agents may move, replace, or remove an installed skill without intending to break an already configured projection. It was also chosen over adding a `~/.local/bin/` link because agents and `launchd` can use the stable absolute path, while a second entry point would add collision, stale-link, shell-configuration, and uninstall cases. The Fulcra-owned tree gives setup, status, repair, upgrade, and uninstall one explicit collector lifecycle boundary.

`setup` is repeatable: rerunning it converges the managed runtime and LaunchAgent to the collector bundled with the current Agent Skill while preserving source configuration, the Projection Map, and Projection Status. A Sweep never updates collector code; adopting a new collector version requires an explicit `setup` run through the skill.

Setup writes or updates the configured collector's manifest, then runs the first complete Sweep, including historical backfill. It reports setup complete only after reporting the Sweep's results, so installation verifies source discovery, authentication, parsing, and Fulcra writes rather than deferring the first proof to a later unattended run.
