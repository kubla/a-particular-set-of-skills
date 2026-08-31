# Fulcra-backed Agent Skills

This context describes independently installable agent skills that project user-selected context into Fulcra, where the user controls its persistence and access.

## Language

**Context Projection**:
The Fulcra architectural pattern of populating an owner's context lake through user-authorized ingestion from authoritative source systems while preserving provenance and source-system authority. A projection may range from a selective summary to a high-fidelity digital twin; the term describes its relationship to the source, not its degree of detail.

**Context Collector**:
An owner-authorized program, integration, or agent role that implements Context Projection by acquiring selected data from one or more sources and recording it in the owner's context lake with provenance. The role is independent of deployment topology and operational interface.
_Avoid_: Gatherer, File sync

**Collector Manifest**:
A durable owner-controlled declaration of one configured Context Collector's intended behavior. It establishes expectations that agents can compare with observed catalog data; it is not a heartbeat or a claim that collection is currently working.

**Sweep**:
One deterministic, token-free collector run. A per-user macOS LaunchAgent starts a Sweep every ten minutes, while the same command remains available for manual recovery.

**Projection Status**:
The passive, locally recorded operational state of the Computer History projection, including recent Sweep outcomes and unresolved conditions requiring attention. It is queried on demand and reports observable facts; it is not a notification stream, and deeper investigation is diagnosis rather than status.

**Source Artifact**:
An unchanged completed Computer History summary uploaded to Fulcra as a file at `Codex/<computer name>/memories/extensions/skysight/resources/<original filename>`. Its permissions are independent from those of any Projection Record derived from it.

**Projection Record**:
One Fulcra duration annotation representing exactly one completed Computer History summary. It contains the summary's current time range, projected Markdown with the source's terminal Citations section omitted, and provenance metadata, but no direct reference to its Source Artifact.
_Avoid_: Data row

**Projection Map**:
A recoverable local operational map connecting each completed Computer History summary and its content hash to the Source Artifact and Projection Record created from it. It supports reliable projection without exposing that relationship through either independently permissioned Fulcra object.

**Image Upgrade Request**:
A durable typed statement of a desired visual result, its constraints and acceptance criteria, and the source material needed to attempt it. It invites zero, one, or many responses and does not imply exclusive assignment.
_Avoid_: Image job, Upgrade job

**Image Upgrade Contribution**:
A candidate response linked to an Image Upgrade Request. Multiple contributions may coexist for comparison, selection, or further iteration.
_Avoid_: The result, Completed job

**Fetchable Representation**:
A directly retrievable encoding of an artifact, identified by its media type and content digest. It carries content efficiently while the related typed record carries meaning, provenance, and relationships.
_Avoid_: Public URL, The artifact

**Image Upgrader**:
The image-capable Agent Skill that establishes and participates in image-upgrade coordination for products that cannot produce the requested image themselves.

**Image Brief**:
The source material that expresses the desired image and its constraints. It may consist only of text or may include raster images, SVG, HTML, canvas instructions, or other visual drafts.

**Request Image Generation**:
The Agent Skill through which an AI product without image generation expresses an Image Upgrade Request and later discovers candidate contributions.
_Avoid_: Image Upgrade Requester, Image Gen Request

**Companion Skill**:
An independently installed Agent Skill maintained alongside another skill because both participate in the same durable coordination contract. The relationship does not imply nested invocation or shared process lifetime.
_Avoid_: Sub-skill, Child skill

**Image Upgrade Configuration**:
The durable owner-scoped configuration through which Image Upgrader and Request Image Generation find the owner's shared image-upgrade coordination state. It contains no credentials.
