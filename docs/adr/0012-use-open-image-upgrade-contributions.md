---
status: accepted
---

# Use open contributions rather than exclusive image-upgrade jobs

An Image Upgrade Request is an invitation for zero, one, or many Image Upgrade Contributions, not a claimable job. This preserves the plurality and address decoupling of Type-Addressed Work and is especially useful for image generation, where several interpretations may be valuable. Selection and closure are separate decisions; any deployment that requires claims, leases, or exactly-once fulfillment must add a workflow mechanism outside the core protocol.

When invoked, Image Upgrader inspects existing Contributions and prioritizes Requests with none. An existing Contribution does not close its Request: the agent may add a distinct interpretation, useful variant, or requested revision. V1 keeps no processed ledger, claim, or completion status; the agent decides whether another candidate would help from the Request and its current Contributions.

Image Upgrader owns no scheduler or polling cursor. Each invocation performs one bounded discovery run using a starting time or watermark supplied by the host when available, otherwise a documented recent lookback that the agent may widen when evidence warrants it. Request Image Generation queries for Contributions from its Request's creation time. Recurrence and wakeups remain concerns of the invoking environment.

Given an exact `request_id`, Contribution discovery returns every valid matching Contribution in recorded order with its summary, representations, timestamp, and provenance. It reports malformed or unverifiable records separately. Discovery does not select a winner or imply closure; comparison and recommendation are later agent or user judgments.
