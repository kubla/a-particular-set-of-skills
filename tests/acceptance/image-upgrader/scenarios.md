# Image Upgrader acceptance

The initial release also requires the complete Claude-to-Codex scenario in the Request Image Generation acceptance suite. Image Upgrader is the producer in that Computer Use-driven round trip; its CLI observations, publication evidence, Contribution provenance, and cleanup targets enter the shared receipt.

## Producer-first setup and conservative rerun

**Entry prompts**

1. `Use $image-upgrader to set up Image Upgrade coordination in this confirmed-empty Fulcra owner.`
2. `Use $image-upgrader to verify the existing Image Upgrade setup without replacing anything.`

**Preconditions**

- The first run uses an owner or isolated test state with a confirmed-absent canonical configuration and no matching role types.
- Separate seeded runs expose exactly one compatible pair, a partial pair, duplicate role types, a missing configured type, and a configured type with the wrong role name.
- The expected owner and a unique run identifier are known before the first mutation.

**Observable outcome**

- Empty state creates one separate type per role and one configuration with an empty trusted-host list.
- The immediate rerun reports `verified` and makes no setup mutation.
- One compatible pair is adopted. Every partial, duplicate, missing, or incompatible state stops and reports observed identifiers plus required repair.

**Mutations, approval gates, cleanup, and evidence**

- Verify the owner before mutations. Record each created type and configuration identifier plus remote path in the cleanup manifest immediately, then remove only scenario-created state after its convergence check and in reverse dependency order.
- Preserve the full observed input, setup action or error, exact writes, verification read, and final cleanup status. An incomplete cleanup fails the run and retains the manifest.

## Discover and contribute to one text-only Request

**Entry prompt**

`Use $image-upgrader to discover the Image Upgrade Request with ID <exact request_id>, generate a candidate, publish it through the authorized HTTPS route, and record a Contribution.`

**Preconditions**

- The skill is installed in an image-capable agent host with `uv`, network access, an authenticated Fulcra CLI, and an authorized HTTPS publishing route.
- The expected Fulcra owner ID, unique run identifier, canonical configuration, and text-only Request are known.

**Observable outcome**

- The agent observes the exact Request, generates and publishes one image, records one valid Contribution with the stable Image Upgrader source, and reports the representation and recorded provenance.

**Mutations**

- The agent publishes one artifact and records one Contribution. Setup may create the canonical types and configuration only when the owner has no image-upgrade state.

**Approval gates**

- Verify the authenticated owner before the first mutation.
- Use only a publisher already authorized in the producer environment.

**Cleanup**

- Record the published artifact, Contribution, and any setup state in the cleanup manifest as each is created.
- Delete the Contribution and artifact in reverse dependency order. Remove setup state only when the scenario created it and no retained state refers to it.

**Required evidence**

- Host, resolved `fulcra-api` and `uv` versions, owner ID, prompt sent, Request observed, generation result, published bytes and digest, Contribution observed, provenance, and cleanup status.

## Open Contributions and publisher canary

**Entry prompt**

`Use $image-upgrader to inspect the seeded Requests and Contributions, verify this authorized publishing route with a canary, and add a useful candidate where appropriate.`

**Preconditions**

- Seed two valid Requests in recorded order, with the first already holding one valid Contribution; insert one malformed Contribution before that valid record.
- Use the expected owner, a unique run identifier, an image-capable Codex host, the current Fulcra CLI, and an authorized test publisher whose canary may be deleted.

**Fulcra interface and host**

- CLI-backed Image Upgrader in Codex with the resolved `uv` and `fulcra-api` versions recorded.

**Observable outcome**

- The agent reports the malformed record, prioritizes the unanswered Request, and still sees the later valid Contribution. It may add a candidate to the answered Request only after explaining the distinct value.
- The canary's final HTTPS host, media type, and digest verify before the host enters owner configuration. A redirected untrusted host requires approval; wrong media type or digest remains unaccepted even after approval.

**Mutations**

- Seeded Requests and Contributions, one canary, one configuration revision, published candidates, and their Contribution records.

**Approval gates**

- Verify the expected owner before mutation. Obtain user approval before making a canary externally retrievable and before following any untrusted final host.

**Cleanup**

- Record every seeded record, canary, configuration revision, published candidate, and Contribution in the cleanup manifest when created. Remove them in reverse dependency order, including seeded records.

**Required evidence**

- Run identifier, host/runtime, owner ID, exact prompts and responses, discovery observations, retrieval headers, final URLs, approval events, computed digests, Fulcra record IDs and provenance, rendered state, and final cleanup status.
