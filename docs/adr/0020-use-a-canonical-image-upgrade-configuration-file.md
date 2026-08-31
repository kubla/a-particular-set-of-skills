---
status: accepted
---

# Use a canonical image-upgrade configuration file

Image Upgrader and Request Image Generation use `Agent Skills/Image Upgrade/config.json` as the owner-scoped source of the image-upgrade protocol version, the owner's request and contribution data-type IDs, and the HTTPS hosts trusted for automatic artifact retrieval. Whichever skill completes setup first creates the types and writes the file; later invocations read it and verify the referenced types. The stable path preserves order-independent installation and avoids treating user-visible type names as identifiers. The file contains no credentials.

Setup makes only unambiguous changes. With no configuration, it adopts exactly one compatible request-and-contribution type pair or creates the pair when neither type exists; partial or duplicate state stops setup with diagnostic evidence. With a configuration, setup verifies the referenced types and stops if either is missing or incompatible. Repair is explicit. Setup never silently replaces a configured type or creates a second blackboard.

Requester-first setup may write an empty trusted-host list. This means durable coordination is ready while artifact delivery still needs producer setup; it is not evidence that a producer can publish. After its publication canary passes, producer setup records the verified host without adding publisher credentials or provider-specific instructions.
