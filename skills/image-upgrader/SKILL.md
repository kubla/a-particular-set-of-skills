---
name: image-upgrader
description: Discover Image Upgrade Requests in Fulcra, generate candidate images, and publish linked Contributions. Use when an image-capable agent should handle requests left by another AI product.
compatibility: Requires uv, network access, an authenticated Fulcra account, image-generation capability, and an authorized HTTPS publishing route.
metadata:
  version: "0.1.0"
---

# Image Upgrader

Participate in the owner's Image Upgrade Typed Blackboard as an image-capable producer. Perform Fulcra operations through the current CLI:

```bash
uvx --from fulcra-api@latest fulcra <command>
```

Read [protocol.md](references/protocol.md) before setup, discovery, or contribution. Use the bundled protocol helper for canonical envelope construction, parsing, and verification rather than rewriting that logic ad hoc.

If the CLI is unavailable, run the documented `uvx` form rather than relying on a global executable. If Fulcra authentication is absent or expired, stop before reading or writing owner state and help the user complete `fulcra auth login`; then verify only the authenticated owner ID before continuing.

## Set up

Read the canonical Image Upgrade Configuration from Fulcra and verify its referenced data types. When configuration is absent, follow the conservative setup table in the protocol reference. Create or adopt state only when the result is unambiguous.

## Discover Requests

Use a starting time or watermark supplied by the invoking environment. Otherwise query a bounded recent lookback and widen it only when evidence warrants doing so. Parse valid `image-upgrade/v1` Request notes and query Contributions over the same relevant period.

Prioritize Requests with no Contributions. An existing Contribution does not close a Request: contribute only when another candidate would be a distinct interpretation, useful variant, or requested revision.

## Contribute

1. Inspect the Image Brief, any input representations, and existing Contributions.
2. Retrieve an input automatically only when its final HTTPS host is trusted and its digest matches. Obtain explicit approval for another host.
3. Generate the candidate with the best image capability available in this environment.
4. Publish the finished bytes through an already authorized route and compute their SHA-256 digest.
5. Build a valid Contribution envelope with the exact `request_id` and at least one Fetchable Representation.
6. Record it in the configured Contribution data type with source `com.fulcradynamics.agent-skills.image-upgrader` in addition to the CLI's default source.

Create no Contribution for a failed, skipped, or declined attempt.

Report the Request identifier, recorded Contribution, summary, representation URL, media type, digest, publication verification, and Fulcra provenance. Describe only states actually observed.
