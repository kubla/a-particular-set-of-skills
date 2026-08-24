---
status: accepted
---

# Omit source citations from Computer History records

The Computer History Collector uploads every completed Markdown summary unchanged as its Source Artifact, but removes the terminal `## Citations` section from the Markdown stored in its Projection Record. The record is a useful Timeline projection rather than a byte-for-byte file duplicate, while the independently permissionable Source Artifact retains the complete original and makes this transformation reversible.

At the time of this decision, Citations entries are only machine-local paths or Computer History summary filenames. They point mainly into Codex application caches and source summaries, with occasional paths to user documents; none is a portable or permission-bearing reference from the Fulcra record. Keeping them in every annotation adds implementation detail without making the cited material available, while the record's Fulcra sources, computer tag, application tags, and preserved body carry useful provenance.

Citation content is not an input to the installed collector and never interrupts collection. The runtime removes a terminal Citations section when present and otherwise leaves the Markdown intact; it does not classify references or predict future formats. Repository authors run the corpus audit under `tests/acceptance/computer-history-collector/` to detect changes to the source shape or citation categories during development and release acceptance. Reconsider this decision if that audit finds portable links, Fulcra object references, embedded evidence, or other citation content that could materially improve a Projection Record.
