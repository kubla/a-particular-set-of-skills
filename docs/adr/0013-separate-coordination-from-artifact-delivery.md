---
status: accepted
---

# Separate typed coordination from artifact delivery

Fulcra records are authoritative for the meaning, provenance, and relationships of Image Upgrade Requests and Contributions, while output content is exposed through one or more Fetchable Representations. Direct HTTPS retrieval is the compatibility baseline for large images and remotely consumed skill instructions, but the contract does not depend on GitHub or require every representation to be public; media type and content digest identify the retrieved content across public, authenticated, short-lived, Fulcra, or future delivery routes.

Image Upgrade Configuration lists the HTTPS hosts its owner trusts for automatic artifact retrieval. Agents automatically fetch Request inputs and Contribution outputs only from those hosts and accept the bytes only when their SHA-256 digest matches the representation. Fetching from another host requires explicit user approval. GitHub may be configured for v1 acceptance, but it is not a protocol default.

The shared configuration does not describe how to publish. Image Upgrader uses an authorized publisher available in its own environment, where publishing credentials remain. Producer setup proves the route with a canary: publish known bytes, retrieve the result through HTTPS, verify the final host and SHA-256 digest, and remove the canary when practical. Request Image Generation needs only the resulting trust policy.
