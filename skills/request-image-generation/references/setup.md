# Request Image Generation setup through Fulcra MCP

Use this procedure only for setup or repair. Perform every operation through the authenticated Fulcra MCP connection exposed by the host.

1. Read `Agent Skills/Image Upgrade/config.json` with the Fulcra file operations. Treat a confirmed not-found result as absent configuration.
2. Read the complete data catalog. Preserve entries with the expected role names, every configured identifier, and any incompatible entry relevant to those roles.
3. Use the packaged [setup cases](setup-cases.json) as the setup reconciliation interface. Match the structure of the observed state, substituting the actual identifiers; do not invent a separate state machine. The cases yield these actions:
   - no configuration and no matching types: create both types;
   - no configuration and exactly one matching type for each role: adopt them;
   - partial or duplicate matching state: stop with the observed identifiers;
   - configuration present: verify its exact identifiers and role names, then make no setup mutation.
4. Create types through the MCP data-type operation using `MomentAnnotation` as the base, the exact role name, and the descriptions from this reference.
5. Write the canonical JSON configuration through the MCP file operation only after both type identifiers are known. Start with an empty trusted-host list.
6. Read the file and complete catalog again. Report the observed state, exact mutation made, and verified result. Report setup ready only when the stored identifiers resolve to one Request type and one separate Contribution type. A verified rerun reports that it made no setup mutation.

Descriptions:

- Image Upgrade Request: `Requests for candidate images from image-capable agents.`
- Image Upgrade Contribution: `Candidate images contributed in response to Image Upgrade Requests.`

If any required MCP operation is absent, authentication fails, a write result is uncertain, or verification disagrees with the intended state, stop. Report the last confirmed observation and do not attempt a second setup path through shell or CLI.
