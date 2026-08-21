# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`
- **Read an issue**: `gh issue view <number> --comments`
- **List issues**: `gh issue list` with appropriate label and state filters.
- **Comment**: `gh issue comment <number> --body "..."`
- **Apply or remove labels**: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repository from its GitHub remote. This configuration becomes operational once that remote exists.

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Skill terminology

When a skill says “publish to the issue tracker,” create a GitHub issue.

When a skill says “fetch the relevant ticket,” read the GitHub issue and its comments.

## Wayfinding

The `wayfinder` skill uses one issue as a map and linked issues as child tickets. Prefer GitHub sub-issues and native dependencies where available; otherwise use task lists and explicit `Blocked by: #<number>` references.

Claim work by assigning the issue to yourself. Resolve it by recording the result, closing the issue, and updating the map.
