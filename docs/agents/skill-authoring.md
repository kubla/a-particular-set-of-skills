# Skill Authoring

Use these repository conventions whenever you create or change a skill.

## Portable skill boundary

Each directory under `skills/` is an independently distributable [Agent Skill](https://agentskills.io/specification). Keep everything the skill needs at runtime inside its directory; repository-level authoring documents, tests, and sibling skills are unavailable after distribution.

Every `SKILL.md` must declare:

```yaml
compatibility: Requires uv and network access.
```

Perform every Fulcra operation through:

```bash
uvx --from fulcra-api@latest fulcra <command>
```

Use the CLI as the Fulcra boundary for instructions and bundled scripts. Keep authentication guidance to what the skill's workflow specifically requires.

## Completion

A skill change is complete when every applicable check passes:

1. Validate each affected directory with `skills-ref validate <skill-directory>`.
2. Run the relevant tests for bundled scripts.
3. Invoke the skill through an agent and exercise its complete workflow against the expected authenticated Fulcra account.

Record the acceptance scenario under `tests/acceptance/<skill-name>/`. The scenario must state its entry prompt, preconditions, observable outcome, mutations, approval gates, cleanup, and required evidence.

## Live-account acceptance

Before a mutating scenario begins, use `user-info` to verify the authenticated Fulcra user ID against the expected author account.

Give test-created artifacts a unique skill-and-run identifier. Record their exact IDs and remote paths in a cleanup manifest as they are created, then clean them up in reverse dependency order. If cleanup is incomplete, fail the run and retain the manifest for recovery.

Obtain explicit approval before a scenario performs an irreversible, account-wide, or externally visible action.

Write raw command output, account-derived data, and cleanup manifests under `.acceptance-runs/`; that directory is not committed. A sanitized acceptance receipt must record:

- skill and scenario;
- timestamp;
- resolved `fulcra-api` version;
- `uv` version;
- authenticated Fulcra user ID;
- result and evidence for each expected outcome; and
- cleanup status.

Until the Fulcra CLI exposes its package version directly, resolve it with:

```bash
uvx --from fulcra-api@latest python -c \
  'from importlib.metadata import version; print(version("fulcra-api"))'
```

See `tests/acceptance/README.md` for the repository-only acceptance layout.

## Fulcra releases

Treat every Fulcra CLI release as an acceptance event for all maintained skills. Run the full live-account suite against the release candidate before publication and against `fulcra-api@latest` after publication. See `docs/adr/0002-test-all-skills-for-every-fulcra-cli-release.md`.
