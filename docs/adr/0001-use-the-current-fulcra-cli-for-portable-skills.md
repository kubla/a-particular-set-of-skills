---
status: accepted
---

# Use the current Fulcra CLI for portable skills

Every skill performs Fulcra operations through `uvx --from fulcra-api@latest fulcra`. Each skill declares `uv` and network access as compatibility requirements and remains independently distributable.

This chooses immediate convergence on the current Fulcra CLI over runtime reproducibility. Fulcra and these skills share an owner, the CLI is expected to preserve backward compatibility, and old or environment-dependent clients are a greater concern here than automatic updates. An unversioned `uvx` invocation would create invisible cache-dependent drift; an exact version would require updating every distributed skill; and a bare `fulcra` command would leave installation and version selection outside the skill.

The choice makes the package index part of every invocation, allows a newly published version to enter a workflow immediately, and does not reproduce historical runs. Acceptance receipts therefore record the resolved package version, and every CLI release triggers the maintained-skill acceptance suite described in ADR 0002.

Reconsider this decision if the CLI introduces a breaking behavioral change, a bad release reaches users before acceptance catches it, package-index availability becomes material, acceptance cannot scale with the collection, historical reproducibility becomes necessary, or Fulcra and the skills no longer share an owner.
