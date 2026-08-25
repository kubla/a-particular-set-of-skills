# A Particular Set of Skills

Models and agents can be replaced. What they learn about their user should survive the replacement.

This is a collection of independently installable [Agent Skills](https://agentskills.io/) built on [Fulcra](https://fulcradynamics.com/). Each skill gives an agent a focused workflow over the owner's context lake. Everything required at runtime lives inside the skill directory.

Skills access Fulcra exclusively through the current CLI:

```bash
uvx --from fulcra-api@latest fulcra <command>
```

## Available skills

| Skill | What it does | Compatibility |
| --- | --- | --- |
| [Computer History Collector](skills/computer-history-collector/) | Copies completed Codex Computer History summaries into Fulcra so agents the owner authorizes can read the same work history. | macOS, Codex Computer History, `uv`, and network access |

## Repository layout

```text
.
├── skills/
│   └── <skill-name>/
│       ├── README.md      # human-facing purpose and installation
│       ├── SKILL.md
│       ├── scripts/       # optional
│       ├── references/    # optional
│       └── assets/        # optional
├── tests/
│   └── acceptance/
│       └── <skill-name>/  # repository-only live-account tests
├── docs/                  # authoring conventions and ADRs
├── AGENTS.md
└── README.md
```

## Using the skills

Each skill follows the [Agent Skills specification](https://agentskills.io/specification) and can be installed independently by a compatible agent client. Each skill directory documents its own purpose and installation.

## Developing a skill

1. Clone this repository to adopt its shared authoring conventions.
2. Create the skill under `skills/<skill-name>/`.
3. Keep everything required at runtime inside that skill directory.
4. Validate and test the skill according to [`docs/agents/skill-authoring.md`](docs/agents/skill-authoring.md), including acceptance against a live Fulcra account.
5. Keep private acceptance artifacts under the ignored `.acceptance-runs/` directory.
6. Distribute the individual skill directory without the repository-level development infrastructure.

Repository-wide references:

- [`AGENTS.md`](AGENTS.md) contains the repository-wide agent instructions.
- [`docs/agents/skill-authoring.md`](docs/agents/skill-authoring.md) defines the portable skill boundary and completion criteria.
- [`tests/acceptance/`](tests/acceptance/) contains repository-only live-account acceptance scenarios.
- [`docs/adr/`](docs/adr/) records consequential authoring and release decisions.

This is a public repository. Raw Fulcra account data, acceptance output, cleanup manifests, credentials, and local environment files remain local and are never committed.

## License

Licensed under the [Apache License 2.0](LICENSE).
