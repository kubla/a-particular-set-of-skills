# Request Image Generation acceptance

## Requester-first setup and conservative rerun

**Entry prompts**

1. `Use $request-image-generation to set up Image Upgrade coordination in this confirmed-empty Fulcra owner.`
2. `Use $request-image-generation to verify the existing Image Upgrade setup without replacing anything.`

**Preconditions**

- Claude or another MCP-only host exposes authenticated Fulcra catalog, data-type, file, and write operations.
- The first run uses confirmed-empty state. Separate seeded runs expose one compatible pair and the partial, duplicate, missing, and incompatible cases in the packaged setup fixtures.
- The expected owner and a unique run identifier are known before the first mutation.

**Observable outcome**

- Empty state creates one separate type per role and one configuration with an empty trusted-host list.
- The immediate rerun reports no mutation. One compatible pair is adopted. Ambiguous or broken state stops with observed evidence and no fallback to shell or CLI.

**Mutations, approval gates, cleanup, and evidence**

- Verify the owner before mutations. Record each created identifier and remote path in the cleanup manifest before proceeding. Remove only scenario-created state after convergence is observed, in reverse dependency order.
- Preserve the full MCP observations, exact writes, verification reads, agent report, and final cleanup status. An incomplete cleanup fails the run and retains the manifest.

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

## Referenced-input Request with no Contributions

**Entry prompts**

1. `Use $request-image-generation to request an image based on this HTTPS reference: <authorized reference URL>. Return the exact Request receipt and stop.`
2. `Use $request-image-generation to check Request <exact request_id> from <creation time>.`

**Preconditions**

- The expected owner, unique run identifier, configured types, authenticated Fulcra MCP interface, and an authorized HTTPS reference are known.
- No Contribution exists for the exact Request ID.

**Fulcra interface and host**

- MCP-backed Request Image Generation in the named Claude product and version used for the run.

**Observable outcome**

- The first invocation records one Request whose `input_representations` contains the declared reference and returns its exact receipt without checking for results.
- The later invocation observes zero exact-match Contributions and reports that observation without implying selection, completion, failure, or producer activity.

**Mutations, approval gates, and cleanup**

- Verify the expected owner before mutation. Record the Request ID and remote path in the cleanup manifest as soon as it is created.
- Retrieve the reference only through the per-hop trust policy. Delete the Request after the zero-result check and record the final cleanup status; incomplete cleanup fails the run.

**Required evidence**

- Run identifier, host/runtime, per-interface owner observation, prompts sent, responses received, Request receipt and record observation, zero-result query observation, reference retrieval state, and cleanup manifest.

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

## Exact custom-type write parity diagnostic

Use this live diagnostic when a Request write succeeds through the Fulcra CLI but fails through Fulcra MCP, or after either interface changes. It exercises the public `fulcra record` command and an actual stdio MCP session calling `record_data`; it does not import server resolver internals.

**Entry commands**

```bash
uv run --script tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py
uv run --script tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py --role contribution_data_type
uv run --script tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py --all-annotations
uv run --script tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py --mcp-project /path/to/fulcra-context-mcp
```

**Preconditions**

- The canonical Image Upgrade configuration exists and names two distinct `MomentAnnotation/<UUID>` types.
- The current Fulcra CLI and the published `fulcra-context-mcp@latest` server can authenticate as the same owner.
- The exhaustive mode enumerates every recordable user-defined annotation. It supports Boolean, Duration, Moment, Numeric, and Scale annotation bases and reports only redacted composite addresses.
- Pass `--mcp-project` to launch a local MCP checkout over stdio and validate a candidate server change against the same live control.

**Observable outcome**

- MCP resolves the exact custom type through `get_data_catalog`.
- Each interface accepts the same exact composite type address, one record becomes observable, and cleanup succeeds.
- The script exits nonzero when either interface fails. `mcp_specific_failure: true` means the CLI passed while MCP failed against the same owner and type semantics.
- In exhaustive mode, `mcp_specific_failure_count` counts exact custom types accepted by the CLI but rejected by MCP. `mcp_ambiguous` counts MCP writes that discarded the custom UUID and reduced the address to a non-unique base type.

**Mutations and cleanup**

- Each interface receives a separate UUID-marked test note. The script queries the configured type, deletes every record carrying either marker, verifies absence, and reports `cleanup_complete` without printing owner or custom-type UUIDs.
- Exhaustive mode performs that write, independent observation, deletion, and absence verification serially for every discovered custom annotation.

## Claude-to-Codex release round trip

This is the initial-release authority for both skills. Drive the visible Claude and Codex product interfaces through Computer Use; do not replace either agent with a direct test script.

**Entry prompts**

1. In Claude: `Use $request-image-generation to request a field-guide plate of a blue heron with the small caption "<run_id>". Return the exact Request receipt and stop without checking for a result.`
2. In Codex: `Use $image-upgrader to handle the Image Upgrade Request with ID <exact request_id>. Generate the image, publish and verify a Fetchable Representation, record the Contribution, and return the observed record evidence.`
3. In Claude: `Use $request-image-generation to check Request <exact request_id> from <creation time>. Retrieve and present every valid Contribution with its verification state.`

**Preconditions**

- Build the deterministic requester ZIP and install that exact archive in Claude through its supported custom-skill interface.
- Claude exposes an authenticated Fulcra MCP connection with the required catalog, type, file, record-write, and query operations.
- Codex has the repository Image Upgrader skill, `uv`, the current authenticated Fulcra CLI, image-generation capability, and an authorized HTTPS publisher.
- Both products point to the expected Fulcra owner. A unique run ID and ignored local run directory exist before mutation.

**Fulcra interfaces and hosts**

- Record the Claude product/version and MCP connection used by the requester.
- Record the Codex product/version, resolved `uv` and `fulcra-api` versions, and CLI-backed producer skill version.

**Observable outcome**

- Claude records one text-only Request and returns its exact ID, creation time, and brief summary without checking for Contributions or claiming producer activity.
- The harness independently observes that Request in Fulcra before Codex is prompted.
- Codex observes the exact Request, generates an image, verifies its published bytes, and records one exact-linked Contribution with required provenance.
- The harness independently observes the Contribution and verifies the retrieved SHA-256 digest.
- Claude checks using the exact receipt identity, reports the observed Contribution, retrieves it through the trusted per-hop policy, and visibly renders the image.

**Mutations**

- One Request, one published image, one Contribution, and any canary or setup state created for this run.

**Approval gates**

- Verify the expected owner through each declared Fulcra interface before the first mutation.
- The user has authorized the test Request, image generation, test publication, and canary by starting this scenario. Obtain separate approval for an untrusted redirect hop or for cleanup that would affect pre-existing state.

**Cleanup**

- Add every mutation to the cleanup manifest when it occurs. Delete test-created Contribution, Request, published image, and canary in reverse dependency order.
- Retain pre-existing configuration and types. If this run created setup state needed for later use, mark each target `retained` with the reason; otherwise remove it after dependent records.

**Required evidence**

- Preserve both exact Claude prompts and responses, the Codex prompt and response, screenshots or equivalent visible-state captures, Request receipt, independent Fulcra observations, record identifiers and provenance, artifact URL and media type, declared and retrieved digests, Claude's rendered presentation, cleanup manifest, and final status. Each expected outcome in the receipt must have a passing result and one or more inspectable evidence references.
- Write the ignored receipt as `.acceptance-runs/request-image-generation/<run_id>/round-trip.json` and validate it with `verify_round_trip_receipt.py`.
