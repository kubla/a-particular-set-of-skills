# Building with Fulcra

This repository uses Fulcra as an owner-controlled context backend. Context may outlive any particular application, agent, model, or provider; agents are clients of that context, not its owners.

Every skill in this repository is built on Fulcra and conforms to the [Agent Skills specification](https://agentskills.io/specification). Access Fulcra only through the current CLI:

```bash
uvx --from fulcra-api@latest fulcra <command>
```

Each skill must be independently distributable and declare `Requires uv and network access.` in its `compatibility` field.

Consult live documentation when implementation details matter:

- [Fulcra for Agents](https://github.com/kubla/fulcra-for-agents/blob/main/fulcra-for-agents.md) for the architectural model.
- [Agent onboarding](https://docs.fulcradynamics.com/agent-get-started.txt) for connection and authentication.
- [Fulcra documentation](https://docs.fulcradynamics.com/) for current concepts, interfaces, and API details.

## Agent skills

### Authoring and acceptance

When creating or changing a skill, follow `docs/agents/skill-authoring.md`. A skill change is complete only after structural validation, relevant script tests, and live-account acceptance pass.

### Issue tracker

Issues and specs live as GitHub issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default Matt Pocock triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.
