# Discover Requests and record Contributions

Use this procedure when handling Image Upgrade Requests.

## Discover

1. Read and verify the owner configuration. Choose the host-supplied starting time or watermark; otherwise use a bounded recent lookback and report it.
2. Query the configured Request and Contribution types with `fulcra get-records`. Convert either JSONL or an array response into an array:

   ```bash
   uvx --from fulcra-api@latest fulcra get-records "<request type>" "<time range>" | uv run --script scripts/image_upgrade_protocol.py jsonl-array
   uvx --from fulcra-api@latest fulcra get-records "<contribution type>" "<time range>" | uv run --script scripts/image_upgrade_protocol.py jsonl-array
   ```

3. Put both observed arrays into a JSON object under `requests` and `contributions`, then run:

   ```bash
   uv run --script scripts/image_upgrade_protocol.py prioritize-requests < discovery.json
   ```

The result lists valid unanswered Requests first and retains answered Requests in their original relative order. Review existing Contributions before deciding whether another candidate would add value. Report parse errors without fetching any URL they mention.

## Verify inputs and publication

Validate the representation fields before network access. Put the declared URL, configured trusted hosts, and any explicit approval for that host into `authorize-url`; make no request unless it returns `allowed: true`. Use a redirect-disabled client. For every redirect, put the resolved `Location` target through `authorize-url` before contacting it. Download the final response body only after that hop is authorized.

After download, preserve the response media type and local byte path. Run `verify-artifact` with the authorized final URL and approval state. Use bytes only when the result is `accepted: true`. If the client cannot expose each redirect before following it, do not use that client for automatic retrieval.

Before adding a publisher host to owner configuration, perform a canary:

1. Publish known bytes through the authorized route.
2. Build their representation with `file-representation`.
3. Resolve and authorize the final URL, retrieve the published bytes, and run `verify-artifact` against the observed final URL and media type.
4. Add the verified final hostname to configuration only after the result is `verified`.
5. Remove the canary when practical and report its cleanup state.

Publisher credentials and provider instructions remain outside the skill and owner configuration.

## Record a Contribution

After successful generation and publication:

1. Run `file-representation` on the exact published bytes, URL, media type, and any known dimensions.
2. Put the exact Request identifier, representation, and optional summary into a JSON object. Produce the Fulcra record payload:

   ```bash
   uv run --script scripts/image_upgrade_protocol.py contribution-record < contribution-input.json > contribution-record.json
   ```

3. Record it through the configured Contribution type:

   ```bash
   uvx --from fulcra-api@latest fulcra record "<contribution type>" -f contribution-record.json --source com.fulcradynamics.agent-skills.image-upgrader
   ```

4. Preserve the CLI response, then query the relevant interval and verify the exact Contribution envelope and provenance before reporting it observed.
5. Remove temporary local JSON files. Create no Contribution when generation, publication, or verification did not produce an available candidate.
