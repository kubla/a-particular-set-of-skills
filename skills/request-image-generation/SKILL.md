---
name: request-image-generation
description: Request an image from an image-capable agent through Fulcra, or check a previous request for candidate images. Use when the current AI product cannot generate the needed image itself.
compatibility: Requires an authenticated Fulcra MCP connection with read and write access.
metadata:
  version: "0.1.0"
---

# Request Image Generation

Use the owner's Fulcra context as a Typed Blackboard shared with an image-capable producer. Use only Fulcra MCP operations exposed by the host. Assume no shell, filesystem, Python, `uv`, or Fulcra CLI.

Read [protocol.md](references/protocol.md) before setup, creating a Request, or checking for Contributions.

If the Fulcra MCP operations are unavailable or unauthenticated, stop before reading or writing owner state. Ask the user to connect or reauthenticate Fulcra in the host product, then retry through MCP. Do not substitute shell or CLI instructions.

## Set up

Read [setup.md](references/setup.md). Read the canonical Image Upgrade Configuration through Fulcra MCP and verify its referenced data types. When configuration is absent, create or adopt state only when the observed owner state is unambiguous.

If setup creates the configuration before a producer is ready, write an empty `trusted_artifact_hosts` list. Report that coordination is ready and artifact delivery still needs producer setup.

## Create a Request

1. Turn the user's desired image, constraints, and acceptance criteria into one nonempty Image Brief. Text alone is valid.
2. Generate a UUID for `request_id` before writing anything.
3. Include only source representations the user supplied or authorized. Each must satisfy the protocol contract.
4. Record the compact Request envelope as the `note` of the configured Request data type. Preserve the write time for later Contribution discovery.
5. Return a receipt containing the exact `request_id`, creation time, and a brief summary.

End after the receipt. Creation does not check for Contributions and does not imply that a producer has accepted or seen the Request.

## Check for Contributions

Require the exact `request_id` from the Request receipt or caller-maintained state. If it is unavailable, stop and offer historical Request recovery as a separate operation.

Query the configured Contribution data type from the Request's creation time. Parse only `image-upgrade/v1` notes and keep exact `request_id` matches in recorded order. Report malformed or unsupported records separately and continue with valid records.

For each match, report its summary, Fetchable Representations, Fulcra timestamp, provenance, and observed verification state. Automatically retrieve a representation only when its final HTTPS host appears in `trusted_artifact_hosts`; otherwise obtain explicit user approval. Accept retrieved bytes only after their SHA-256 digest matches.

Return every valid match. Do not select a winner or describe the Request as accepted, processing, completed, or closed without separate evidence.
