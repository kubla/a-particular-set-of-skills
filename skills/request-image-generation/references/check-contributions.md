# Check for Image Upgrade Contributions through Fulcra MCP

Use this procedure only after obtaining the exact Request receipt.

1. Require the exact canonical lowercase `request_id` and the Request creation time. Stop if either is unavailable.
2. Read and verify owner configuration through Fulcra MCP.
3. Query the configured Contribution type from the Request creation time through the current time.
4. Parse each annotation note as JSON. Accept only `image-upgrade/v1` envelopes containing exactly `protocol`, `request_id`, nonempty `representations`, and optional `summary`. Each representation may contain only `url`, `media_type`, `sha256`, `width`, and `height`.
5. Keep only literal exact `request_id` matches. Preserve Fulcra's recorded order and the record's timestamp and sources. Report malformed or unsupported records separately, without fetching their URLs, then continue.
6. For each representation, authorize the declared HTTPS hostname before the first request. Use redirect-disabled retrieval and authorize every resolved redirect target before contacting it. Trusted hosts are automatic; every other hop requires explicit user approval. If the host cannot expose redirect targets before following them, report that limitation and leave the representation unverified.
7. Accept bytes only after the observed media type and SHA-256 digest match the representation. If the host cannot verify either fact, report that limitation and keep the representation unverified.
8. Return every valid matching Contribution with its summary, representations, timestamp, provenance, and exact observed verification state.

Do not infer a winner, completion, closure, or producer status from the presence or absence of Contributions.
