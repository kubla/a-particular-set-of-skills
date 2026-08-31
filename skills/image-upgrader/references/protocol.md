# Image Upgrade protocol v1

This reference defines the complete coordination contract used by Image Upgrader and Request Image Generation.

## Owner configuration

The canonical Fulcra file is `Agent Skills/Image Upgrade/config.json`:

```json
{
  "protocol": "image-upgrade/v1",
  "request_data_type": "MomentAnnotation/<uuid>",
  "contribution_data_type": "MomentAnnotation/<uuid>",
  "trusted_artifact_hosts": []
}
```

The referenced user-defined types are based on `MomentAnnotation` and are named `Image Upgrade Request` and `Image Upgrade Contribution`. The file contains no credentials, publisher choice, or owner identity.

When the file is absent:

| Observed compatible types | Action |
| --- | --- |
| Neither type exists | Create one Request type and one Contribution type, then write the configuration. |
| Exactly one compatible pair exists | Adopt the pair and write the configuration. |
| Only one side exists, or either side has duplicates | Stop with the observed type identifiers and require explicit repair. |

When the file exists, its identifiers are authoritative. Verify both referenced types. Stop if either is missing, not based on `MomentAnnotation`, or named for the other role. Never silently replace configured state or create a second blackboard.

## Request envelope

The Request record's `note` is compact JSON. Required fields:

```json
{
  "protocol": "image-upgrade/v1",
  "request_id": "<uuid>",
  "brief": "Natural-language desired result, constraints, and acceptance criteria."
}
```

An optional `inputs` array contains Fetchable Representations. Generate `request_id` before recording the Request and encode it in canonical lowercase UUID form. Readers reject alternate spellings rather than normalizing them. Fulcra supplies the record timestamp and provenance; do not duplicate them in the envelope.

## Contribution envelope

The Contribution record's `note` is compact JSON:

```json
{
  "protocol": "image-upgrade/v1",
  "request_id": "<the exact Request uuid>",
  "representations": [
    {
      "url": "https://assets.example/image.png",
      "media_type": "image/png",
      "sha256": "<64 lowercase hexadecimal characters>"
    }
  ]
}
```

`representations` must be nonempty. Each representation may also contain positive integer `width` and `height`. An optional nonempty `summary` describes the interpretation or changes.

A Contribution denotes a successfully produced candidate. Failed, skipped, or declined attempts create no Contribution. Existing Contributions do not close the Request, and several candidates may coexist.

See [valid-round-trip.json](valid-round-trip.json) for a synthetic configuration, Request, receipt, Contribution, and Contribution record that cross the complete contract. Its identifiers and host are examples, never owner configuration.

## Fetchable Representations

A representation URL must be absolute HTTPS. Automatic retrieval requires the final host after redirects to appear in `trusted_artifact_hosts`. Any other host requires explicit user approval. Retrieved bytes are accepted only when their SHA-256 digest equals the lowercase declared digest.

Typed Fulcra records are authoritative for meaning, provenance, timestamps, and relationships. The HTTPS resource carries the large artifact bytes.

## Discovery and reporting

Request discovery is bounded by a host-supplied starting time or watermark when available, otherwise a documented recent lookback. Contribution discovery for one Request starts at that Request's creation time and filters parsed notes by exact `request_id`.

Process valid records in Fulcra's recorded order. Report malformed or unsupported notes without fetching their URLs, then continue. Reports distinguish what was recorded, observed, retrieved, digest-verified, and rendered.

The protocol has no claims, leases, queue ordering, processed ledger, completion state, selected winner, or exactly-once guarantee. Scheduling and recurrence belong to the invoking environment.
