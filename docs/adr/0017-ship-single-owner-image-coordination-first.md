---
status: accepted
---

# Ship single-owner image coordination first

The first version of Image Upgrader and Request Image Generation coordinates within one Fulcra owner's context. Cross-owner coordination is deferred to a future version because it also requires enrollment, sharing, isolation, revocation, and a requester-visible return path. That future design should preserve owner-scoped records—each participant writes to their own context—and investigate Fulcra Groups as the bootstrap and discovery surface without assuming that a Group is a shared writable datastore.
