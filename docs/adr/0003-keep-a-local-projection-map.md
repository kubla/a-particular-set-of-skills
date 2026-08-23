---
status: accepted
---

# Keep a local projection map

The Computer History collector keeps a local Projection Map from each source filename and content hash to the Fulcra file and duration record it created. The map is operational state rather than owner context: it is not embedded in either remote object, and losing it does not make the projection irrecoverable.

This was chosen over a stateless collector because recurring runs and retries must not duplicate data; content hashes are needed to detect edits; remote identifiers are needed to reconcile prior writes; and the design should not depend on undocumented record-upsert behavior. Keeping the relationship local also preserves independent access control for the source file and projection record, while allowing ordinary sweeps to run deterministically without model tokens.

If the map is lost, it can be rebuilt by reconciling source filenames and timestamps, computer source metadata, and existing Fulcra files and records. A corrupt map stops collection and requires diagnosis rather than guessing. Map updates must be atomic so an interrupted Sweep can be retried safely.
