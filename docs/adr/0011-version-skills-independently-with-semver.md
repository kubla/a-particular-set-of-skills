---
status: accepted
---

# Version skills independently with SemVer

Skills in this repository are independently distributable, so each skill uses Semantic Versioning in `SKILL.md` metadata and an annotated, skill-namespaced release tag such as `<skill-name>-v1.2.3`. This chooses per-skill releases over a repository-wide version because unrelated skills can evolve on different schedules; integer versions inside runtime configuration and projection maps remain format-schema versions rather than release identifiers.
