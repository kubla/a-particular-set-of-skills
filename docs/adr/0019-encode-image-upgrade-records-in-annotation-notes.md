---
status: accepted
---

# Encode image-upgrade records in annotation notes

Image Upgrade Requests and Image Upgrade Contributions use separate user-defined `MomentAnnotation` types. Each record's `note` contains a compact, versioned JSON envelope with a client-generated logical `request_id`; contributions repeat that identifier, and readers correlate them by parsing bounded contribution queries. Image content remains outside the envelope in Fetchable Representations.

The request envelope requires `protocol`, `request_id`, and a natural-language `brief` containing the desired result, constraints, and acceptance criteria. An optional `inputs` array carries Fetchable Representations of source material. The record timestamp and provenance remain in the Fulcra record rather than being duplicated in the envelope; v1 adds no separate status, deadline, acceptance-criteria, or output-specification fields.

The contribution envelope requires `protocol`, `request_id`, and a nonempty `representations` array. Each representation requires `url`, `media_type`, and `sha256`; pixel `width` and `height` are optional. An optional `summary` explains the interpretation or changes. A Contribution always denotes a successfully produced candidate. Failed, skipped, and declined attempts create no Contribution.

Image Upgrader writes `com.fulcradynamics.agent-skills.image-upgrader` as an additional Fulcra record source on every Contribution. This identifies the producing workflow rather than a particular model session or installation. A contributor may add more specific tool or model provenance when it is available and useful.

Readers process only valid envelopes for the exact protocol version they support. They report and skip malformed or unsupported records without fetching their URLs, then continue with valid records.

The first live v1 acceptance run on 2026-08-31 exposed an MCP parity bug: `record_data` reduced an exact `MomentAnnotation/<UUID>` address to its base type and reported ambiguity when the owner had two custom Moment annotations. [fulcra-context-mcp#21](https://github.com/fulcradynamics/fulcra-context-mcp/pull/21) fixed the exact-type lookup. On 2026-09-01, Claude wrote a Request through the deployed public MCP service, Codex recorded a linked Contribution through `fulcra-api` 0.1.40, and Claude retrieved, digest-verified, and rendered the result. That run closed the cross-interface release gate recorded in [issue #20](https://github.com/fulcradynamics/fulcra-context-mcp/issues/20).

Fulcra custom data types specialize fixed base schemas, and the MCP write path does not return the generated Fulcra record ID. Revisit this ADR when the Fulcra API supports application-defined record fields, durable identity from MCP writes, or server-side correlation that can replace client-side parsing without breaking interface parity.
