---
status: accepted
---

# Install companion skills independently

Image Upgrader and Request Image Generation are independently distributable sibling skills under `skills/`, not a parent skill and nested sub-skill. Either may be installed first: requester-side setup can guide the user toward establishing a producer when none is visible, while producer-side setup can provide the requester installation path. Their coordination contract, not installation order or filesystem nesting, establishes their relationship.
