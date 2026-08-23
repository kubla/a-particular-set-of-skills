---
status: accepted
---

# Use a source-native Codex memory namespace

Computer History source files are uploaded to `Codex/<computer name>/memories/extensions/skysight/resources/<original filename>`. The computer dimension is inserted beneath `Codex` because one Fulcra account can receive projections from several machines; identically named computers intentionally share that source identity.

This source-native hierarchy was chosen over `Computer History/<computer>/<cadence>/<filename>`. It preserves the provenance and internal name of the producing Codex subsystem, avoids inventing a parallel cadence taxonomy already encoded in each filename, and leaves `Codex/<computer>/memories/` available for future memory-gathering utilities. Exposing `skysight` is deliberate even though the internal name may change upstream; a future upstream rename should be handled as an explicit namespace evolution rather than silently rewriting historical paths.
