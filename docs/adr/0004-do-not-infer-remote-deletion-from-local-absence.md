---
status: accepted
---

# Do not infer remote deletion from local absence

The collector never deletes a Fulcra Source Artifact or Projection Record merely because its local Computer History Memory disappears. Removing a local copy does not communicate the user's intent for an independently retained object in their context lake, and treating absence as a deletion command could destroy context the user expected Fulcra to preserve.

This chooses durable remote retention over automatic mirroring. The Projection Map may record that a source is no longer present, but remote deletion requires a separate explicit Fulcra operation rather than inference from filesystem state.
