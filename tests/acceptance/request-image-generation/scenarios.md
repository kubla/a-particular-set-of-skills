# Request Image Generation acceptance

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
