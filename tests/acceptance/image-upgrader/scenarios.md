# Image Upgrader acceptance

## Producer-first setup and conservative rerun

**Entry prompts**

1. `Use $image-upgrader to set up Image Upgrade coordination in this confirmed-empty Fulcra owner.`
2. `Use $image-upgrader to verify the existing Image Upgrade setup without replacing anything.`

**Preconditions**

- The first run uses an owner or isolated test state with a confirmed-absent canonical configuration and no matching role types.
- Separate seeded runs expose exactly one compatible pair, a partial pair, duplicate role types, a missing configured type, and a configured type with the wrong role name.

**Observable outcome**

- Empty state creates one separate type per role and one configuration with an empty trusted-host list.
- The immediate rerun reports `verified` and makes no setup mutation.
- One compatible pair is adopted. Every partial, duplicate, missing, or incompatible state stops and reports observed identifiers plus required repair.

**Mutations, approval gates, cleanup, and evidence**

- Verify the owner before mutations. Record created types and configuration immediately, then remove only scenario-created state after its convergence check.
- Preserve the full observed input, setup action or error, exact writes, verification read, and cleanup result.

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
