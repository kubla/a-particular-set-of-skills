# Image Upgrader setup through the Fulcra CLI

Use this procedure only for setup or repair.

1. Verify the authenticated owner without exposing the full account response:

   ```bash
   uvx --from fulcra-api@latest fulcra user-info | uv run --script scripts/image_upgrade_protocol.py owner-id
   ```

2. Try to read `Agent Skills/Image Upgrade/config.json`:

   ```bash
   uvx --from fulcra-api@latest fulcra file download "Agent Skills/Image Upgrade/config.json" -
   ```

3. Read the complete recordable catalog. The CLI emits JSONL; convert it to one JSON array without discarding incompatible evidence or configured identifiers:

   ```bash
   uvx --from fulcra-api@latest fulcra catalog --recordable-only | uv run --script scripts/image_upgrade_protocol.py catalog-json
   ```

4. Put the confirmed configuration observation (JSON `null` only after a confirmed not-found result) and complete catalog into one JSON object with keys `configuration` and `catalog`. Ask the bundled helper for the one safe action:

   ```bash
   uv run --script scripts/image_upgrade_protocol.py setup-decision < observed-state.json
   ```

5. For `create_pair`, create both types before writing configuration:

   ```bash
   uvx --from fulcra-api@latest fulcra data-type create MomentAnnotation "Image Upgrade Request" -d "Requests for candidate images from image-capable agents."
   uvx --from fulcra-api@latest fulcra data-type create MomentAnnotation "Image Upgrade Contribution" -d "Candidate images contributed in response to Image Upgrade Requests."
   ```

   Use the exact returned type identifiers. Write the canonical configuration to a temporary file, upload it to the canonical path, and remove the temporary file.

6. For `adopt_pair`, upload the configuration returned by the helper. For `verified`, make no setup mutation.

7. After `create_pair` or `adopt_pair`, read the configuration and complete catalog again, run `setup-decision` on those post-write observations, and require `verified`. Report the exact created or adopted type identifiers, configuration written, and verification result. If creation stops after a partial mutation, report the confirmed identifier and require explicit repair.

Report the initial helper `observed`, `action`, and intended `change`, then the exact mutations actually observed and the post-write verification. For errors, report the observed identifiers and required repair. Any helper error is a stop; repair owner state only after an explicit user decision. The packaged [setup cases](setup-cases.json) are the shared decision interface for both sibling skills.
