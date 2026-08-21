# Building with Fulcra

This repository uses Fulcra as an owner-controlled context backend. Context may outlive any particular application, agent, model, or provider; agents are clients of that context, not its owners.

When working with Fulcra:

- Use it for durable, owner-scoped context while keeping application-specific operational state in the application.
- Preserve user consent, ownership, provenance, and the distinction between source observations and agent-derived conclusions.
- Expect available data and historical coverage to vary by account.
- Choose the interface that fits the task: Python or REST for application code, CLI for shell workflows, or MCP for compatible agent environments.

Consult live documentation when implementation details matter:

- [Fulcra for Agents](https://github.com/kubla/fulcra-for-agents/blob/main/fulcra-for-agents.md) for the architectural model.
- [Agent onboarding](https://docs.fulcradynamics.com/agent-get-started.txt) for connection and authentication.
- [Fulcra documentation](https://docs.fulcradynamics.com/) for current concepts, interfaces, and API details.

## Agent skills

### Issue tracker

Issues and specs live as GitHub issues. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default Matt Pocock triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md`.
