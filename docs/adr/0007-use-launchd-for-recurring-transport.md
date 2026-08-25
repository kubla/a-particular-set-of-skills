---
status: accepted
---

# Use launchd for recurring transport

Setup installs a per-user macOS LaunchAgent that runs the deterministic collector every ten minutes. The same collector command is available for manual recovery. Codex scheduled tasks are excluded from the transport loop because moving completed Markdown and duration records requires no reasoning and should consume no model tokens.

`launchd` was chosen over `cron`, a long-running file watcher, Automator Folder Actions, and a native helper app. It is macOS's preferred user-process supervisor, gives the job explicit configuration and logs, requires no continuously running custom process, and is independently installable and removable. Missed intervals are harmless because each Sweep reconciles the source folder against the Projection Map and processes the backlog.

`cron` is the closest lightweight alternative but is deprecated by Apple in favor of `launchd` and has weaker installation and supervision semantics. An FSEvents watcher would reduce latency but still require debouncing, full rescans, and lifecycle supervision. A native Login Item could provide richer status and repair UX but would turn the independently installable skill into a signed macOS application. Codex remains a possible status-review or guided-repair client, not the scheduler of record.

Each Sweep updates passive local Projection Status. The collector uses macOS Notification Center to signal once when it enters a new unresolved condition that requires user action. Continued Sweeps in the same condition, ordinary data gaps, successful operation, and recovery are silent.
