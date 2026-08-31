# Building with Fulcra

This repository uses Fulcra as an owner-controlled context backend. Context may outlive any particular application, agent, model, or provider; agents are clients of that context, not its owners.

Every skill in this repository is built on Fulcra, conforms to the [Agent Skills specification](https://agentskills.io/specification), and is independently distributable.

Each skill declares its required Fulcra interface in its `compatibility` field. Use only the interface the skill declares; repository membership does not imply shell or CLI access.

- CLI-backed skills use the current Fulcra CLI:

```bash
uvx --from fulcra-api@latest fulcra <command>
```

- MCP-backed skills use the authenticated Fulcra MCP connection exposed by the host product.

Follow `docs/agents/skill-authoring.md` for access declarations and acceptance requirements.

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

Use Matt Pocock style triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.
