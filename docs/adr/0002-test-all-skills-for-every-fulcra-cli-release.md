---
status: accepted
---

# Test all skills for every Fulcra CLI release

Every Fulcra CLI release is an acceptance event for every maintained skill in this repository. Run the repository's complete end-to-end suite against the release candidate before publication, then run it against the published `fulcra-api@latest` package using the author's real Fulcra account.

This obligation follows from ADR 0001: publishing the CLI implicitly updates every distributed skill even when no skill file changes. Release acceptance must therefore cover the skills as downstream consumers, verify real agent behavior rather than only CLI availability, preserve local receipts, and surface incomplete cleanup.

Reconsider this decision if the skill collection and Fulcra release process no longer share an owner, the suite becomes too large for release-time execution, or skills adopt an explicit compatibility policy that decouples them from the current CLI.
