---
status: accepted
---

# Encode image-upgrade records in annotation notes

Image Upgrade Requests and Image Upgrade Contributions use separate user-defined `MomentAnnotation` types. Each record's `note` contains a compact, versioned JSON envelope with a client-generated logical `request_id`; contributions repeat that identifier, and readers correlate them by parsing bounded contribution queries. Image content remains outside the envelope in Fetchable Representations.

The request envelope requires `protocol`, `request_id`, and a natural-language `brief` containing the desired result, constraints, and acceptance criteria. An optional `inputs` array carries Fetchable Representations of source material. The record timestamp and provenance remain in the Fulcra record rather than being duplicated in the envelope; v1 adds no separate status, deadline, acceptance-criteria, or output-specification fields.

The contribution envelope requires `protocol`, `request_id`, and a nonempty `representations` array. Each representation requires `url`, `media_type`, and `sha256`; pixel `width` and `height` are optional. An optional `summary` explains the interpretation or changes. A Contribution always denotes a successfully produced candidate. Failed, skipped, and declined attempts create no Contribution.

Image Upgrader writes `com.fulcradynamics.agent-skills.image-upgrader` as an additional Fulcra record source on every Contribution. This identifies the producing workflow rather than a particular model session or installation. A contributor may add more specific tool or model provenance when it is available and useful.

Readers process only valid envelopes for the exact protocol version they support. They report and skip malformed or unsupported records without fetching their URLs, then continue with valid records.

The envelope contract is designed for CLI/MCP parity, but the live v1 acceptance run on 2026-08-31 found a current MCP implementation blocker. When two user-defined `MomentAnnotation` types exist, `record_data` accepts neither exact composite identifier: the resolver reduces `MomentAnnotation/<UUID>` to the base type, finds both catalog entries, and reports ambiguity. The same exact Request envelope succeeded through `fulcra-api` 0.1.40 on the CLI. This is tracked upstream in [fulcra-context-mcp#20](https://github.com/fulcradynamics/fulcra-context-mcp/issues/20); the cross-interface release gate remains open until a live MCP write succeeds.

Fulcra custom data types specialize fixed base schemas, and the MCP write path also does not return the generated Fulcra record ID. Revisit this ADR when the resolver preserves exact custom-type identity, or when the Fulcra API supports application-defined record fields, durable identity from MCP writes, or server-side correlation that can replace client-side parsing without breaking interface parity.
