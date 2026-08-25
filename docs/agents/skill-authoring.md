# Skill Authoring

Use these repository conventions whenever you create or change a skill.

## Portable skill boundary

Each directory under `skills/` is an independently distributable [Agent Skill](https://agentskills.io/specification). Keep everything the skill needs at runtime inside its directory; repository-level authoring documents, tests, and sibling skills are unavailable after distribution.

Every `SKILL.md` must declare:

```yaml
compatibility: Requires uv and network access.
```

## Releases

Version each independently distributable skill with Semantic Versioning. Put its version in `SKILL.md` as `metadata.version`, and create an annotated, skill-namespaced Git tag such as `<skill-name>-v1.2.3` for every release. A repository commit may therefore release one skill without incrementing its siblings.

Publish human-facing release notes as a manually curated GitHub Release attached to that tag. Scope the notes to the affected skill rather than treating every repository commit since its previous tag as part of the release. Lead with the outcome, then cover user-visible changes, upgrade action, compatibility or breaking changes, sanitized verification, and a comparison link. Keep `SKILL.md` focused on current behavior and keep raw acceptance receipts local.

Treat runtime/configuration format versions as separate schemas. Do not infer a skill release from an integer such as `"version": 1` in a configuration file or Projection Map.

Perform every Fulcra operation through:

```bash
uvx --from fulcra-api@latest fulcra <command>
```

Use the CLI as the Fulcra boundary for instructions and bundled scripts. Keep authentication guidance to what the skill's workflow specifically requires.

## Context collectors

A **Context Collector** implements the Context Projection pattern. It is an owner-authorized program, integration, or agent role that acquires selected data from one or more sources and records it in the owner's context lake, preserving its provenance.

For an Agent Skill that creates, configures, or operates a collector, use **`<Source> Collector`** as the display name and `<source>-collector` as the skill identifier. A collector skill may perform collection as an agent role or install and manage a separate runtime. The category does not prescribe commands, scheduling, deployment, or interaction models, and not every Fulcra-backed skill is a collector.

### Collector manifests

Each configured collector writes one Markdown manifest through the Fulcra Files interface at `Collector Manifests/<Collector Name>/<Collector Instance>.md`. The manifest declares the collector's intended behavior so agents can compare those expectations with the data visible in the owner's catalog. When the intended behavior changes, maintain the same file by editing the declaration or appending a change note; Fulcra's file snapshots preserve its successive versions.

A Collector Manifest is not a heartbeat, Projection Status, or proof that collection is operating. Do not create Timeline events merely to represent the current declaration. For Computer History Collector, use `Collector Manifests/Computer History Collector/<computer name>.md`; computers with the same user-visible name intentionally maintain the same manifest path.

Use these minimal headings:

1. **Collector** — collector and configured-instance identity.
2. **Sources** — what it acquires and relevant provenance.
3. **Intended outputs** — the Fulcra data types or file namespaces it maintains.
4. **Collection behavior** — cadence, triggers, and circumstances in which gaps are normal.

Save the manifest's Fulcra path in the collector's local configuration and use that saved identity for subsequent changes. Keep this configuration separate from any Projection Map that associates individual source items with their projected Fulcra objects.

When a collector is intentionally uninstalled, update its existing manifest to declare that collection ended. Leave the manifest and previously collected context in Fulcra; removing a collector does not express an intent to delete the owner's context.

## Completion

A skill change is complete when every applicable check passes:

1. Validate each affected directory with `uvx --from skills-ref agentskills validate <skill-directory>`.
2. Run the relevant tests for bundled scripts.
3. Invoke the skill through an agent and exercise its complete workflow against the expected authenticated Fulcra account.

Record the acceptance scenario under `tests/acceptance/<skill-name>/`. The scenario must state its entry prompt, preconditions, observable outcome, mutations, approval gates, cleanup, and required evidence.

## Live-account acceptance

Before a mutating scenario begins, use `user-info` to verify the authenticated Fulcra user ID against the expected author account.

Give test-created artifacts a unique skill-and-run identifier. Record their exact IDs and remote paths in a cleanup manifest as they are created, then clean them up in reverse dependency order. If cleanup is incomplete, fail the run and retain the manifest for recovery.

Obtain explicit approval before a scenario performs an irreversible, account-wide, or externally visible action.

Write raw command output, account-derived data, cleanup manifests, and acceptance receipts under `.acceptance-runs/`; that directory is neither committed nor published. Each local acceptance receipt must record:

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
