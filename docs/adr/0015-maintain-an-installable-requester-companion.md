---
status: accepted
---

# Maintain an installable requester companion

`request-image-generation` is a static Companion Skill maintained in this repository, not instructions generated afresh for each user. It contains no credentials or embedded user identity; when invoked, it obtains Image Upgrade Configuration from the user's authenticated Fulcra account over MCP. Its first supported installation artifact follows Claude's custom-skill contract: a ZIP containing one top-level `request-image-generation/` directory with `SKILL.md` and any supporting files. Other host-specific delivery formats may be added, but an undocumented `.skill` package is not part of the initial contract.

Request creation and Contribution discovery are separate phases. After recording a Request, the creation path reports its `request_id`, creation time, and brief summary; it does not perform or imply an immediate Contribution check. The user, agent, or host decides when to invoke the later check. That check reports only Contributions it actually observes and never describes a Request as accepted, processing, or complete without evidence.

A Contribution check requires the exact `request_id`. It does not infer identity from recency, brief text, or conversation resemblance. The caller preserves the ID from the Request receipt or its own scheduling state. If the ID is unavailable, the check stops; finding historical Requests is a separate recovery operation rather than part of normal Contribution discovery.
