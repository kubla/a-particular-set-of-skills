---
status: accepted
---

# Project local edits as revisions

When the content hash of a previously projected Computer History summary changes while the local summary remains present, the collector treats the change as a revision. It uploads the file to the same remote path so Fulcra creates a new file snapshot, then advances the corresponding Timeline record to the revised Markdown instead of leaving overlapping records for the same summary.

This distinguishes affirmative new content from ambiguous local absence. The user receives the current corrected context while Fulcra's file snapshots preserve knowledge that the change occurred and support later comparison or rollback. The Projection Map retains the identifiers and hashes needed to make retries idempotent and to avoid representing a revision as a second memory.
