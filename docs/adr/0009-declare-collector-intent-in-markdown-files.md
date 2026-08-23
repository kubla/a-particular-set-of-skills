---
status: accepted
---

# Declare collector intent in Markdown files

Each configured Context Collector writes one Markdown Collector Manifest through Fulcra Files at `Collector Manifests/<Collector Name>/<Collector Instance>.md`. It maintains that stable file when its intended behavior changes, either by revising the declaration or appending a change note; Fulcra's file snapshots retain successive versions.

Every manifest declares the collector and configured-instance identity, sources and provenance, intended Fulcra outputs, and collection behavior including circumstances in which gaps are normal. The collector saves its manifest's Fulcra path in local configuration so later setup or behavior changes update the declaration it owns; that identity is not part of the Projection Map for collected source items.

This chooses a durable declaration over setup or status events. Intended behavior is current explanatory context, not an occurrence that belongs on Timeline. A file is naturally readable by people and agents, can be permissioned independently, remains available if collection goes silent, and gives agents stated expectations to compare with observed catalog data without requiring the collector to become a complex self-monitoring system.

Intentional uninstall updates the same manifest to declare that collection ended, then removes the local collector without deleting the manifest or previously collected context. This lets agents distinguish deliberate decommissioning from unexplained silence while preserving the owner's accumulated context.
