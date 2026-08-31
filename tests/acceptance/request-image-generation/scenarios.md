# Request Image Generation acceptance

## Requester-first setup and conservative rerun

**Entry prompts**

1. `Use $request-image-generation to set up Image Upgrade coordination in this confirmed-empty Fulcra owner.`
2. `Use $request-image-generation to verify the existing Image Upgrade setup without replacing anything.`

**Preconditions**

- Claude or another MCP-only host exposes authenticated Fulcra catalog, data-type, file, and write operations.
- The first run uses confirmed-empty state. Separate seeded runs expose one compatible pair and the partial, duplicate, missing, and incompatible cases in the packaged setup fixtures.

**Observable outcome**

- Empty state creates one separate type per role and one configuration with an empty trusted-host list.
- The immediate rerun reports no mutation. One compatible pair is adopted. Ambiguous or broken state stops with observed evidence and no fallback to shell or CLI.

**Mutations, approval gates, cleanup, and evidence**

- Verify the owner before mutations. Record each created identifier before proceeding. Remove only scenario-created state after convergence is observed.
- Preserve the full MCP observations, exact writes, verification reads, agent report, and cleanup result.

## Text-only Request and later Contribution check

**Entry prompts**

1. `Use $request-image-generation to request a precise blue heron drawn as a field-guide plate. Return the request receipt and stop.`
2. After a producer records a Contribution: `Use $request-image-generation to check request <exact request_id> for Contributions.`

**Preconditions**

- The skill is installed in a host that exposes authenticated Fulcra MCP read, write, data-type, record-query, and file operations.
- The expected Fulcra owner ID and a unique run identifier are known.
- The Contribution fixture points to authorized HTTPS bytes whose digest is known independently.

**Observable outcome**

- The first invocation records one valid text-only Request and returns its exact identifier, creation time, and brief summary without checking for Contributions.
- The later invocation returns every valid exact-match Contribution in recorded order without implying selection or closure.

**Mutations**

- Setup may create two user-defined data types and the canonical configuration file.
- The first invocation records one Request. A cooperating producer records at least one Contribution.

**Approval gates**

- Verify the authenticated owner before the first mutation.
- Obtain explicit approval before retrieving a representation from an untrusted final host.

**Cleanup**

- Record every created type, file, Request, and Contribution in the run cleanup manifest.
- Delete test records and files in reverse dependency order. Archive test-created types only when the scenario created them and no retained state refers to them.

**Required evidence**

- Host and Fulcra MCP interface, owner ID, prompts sent, responses received, exact Request receipt, observed Fulcra records, representation verification, and cleanup status.

## Multiple Contributions and conservative retrieval

**Entry prompt**

`Use $request-image-generation to check request <exact request_id> and report every candidate image with its verification state.`

**Preconditions**

- Seed a malformed Contribution followed by two valid exact matches and one valid Contribution for another Request.
- Use the expected owner, a unique run identifier, and Claude with authenticated Fulcra MCP plus a host retrieval facility capable of exposing final URL, media type, and bytes.

**Fulcra interface and host**

- MCP-backed Request Image Generation in the named Claude product and version used for the run.

**Observable outcome**

- The agent reports the malformed record, ignores the unrelated record, and returns both exact matches in recorded order with timestamp and provenance.
- A trusted final host with matching media type and digest is verified. An untrusted final host requires approval. Digest or media-type mismatch remains unaccepted.

**Mutations**

- Scenario setup records the seeded Contributions; the check itself creates no mutation.

**Approval gates**

- Verify the expected owner before seeding. Obtain user approval before downloading from an untrusted final host.

**Cleanup**

- Record seeded records in the cleanup manifest as created and remove them in reverse order after the check.

**Required evidence**

- Run identifier, host/runtime, owner ID, prompt and response, complete query observation, parse results, approval event if any, retrieval metadata, computed digest, rendered or unrendered presentation state, and cleanup status.
