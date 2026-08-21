# Acceptance Tests

This tree contains repository-only end-to-end acceptance scenarios and test support. Nothing here is a runtime dependency of a distributed skill.

Give each maintained skill its own directory:

```text
tests/acceptance/<skill-name>/
├── scenarios.md
└── scripts/
```

`scenarios.md` defines each entry prompt, preconditions, observable outcome, mutations, approval gates, cleanup, and required evidence. Add `scripts/` only when repeatable setup, verification, or cleanup benefits from executable support.

Run the installed skill through an agent against the expected authenticated Fulcra account. Store raw results and cleanup manifests under `.acceptance-runs/<skill-name>/<run-id>/`, outside this tree. Follow `docs/agents/skill-authoring.md` for completion criteria and live-account handling.
