# Naming source-side context utilities

## Recommendation

Use **Context Collector** as the canonical category noun.

> A Context Collector is a source-side application or utility that, with the
> owner's authorization, gathers context from a device or service, may normalize
> or enrich it, and writes it into the owner's context lake.

Keep **Context Projection** as the name of the architectural operation. A Context
Collector performs one or more Context Projections. This separates *what the
software is* from *what transformation it performs*.

For example:

- category: **Context Collector**
- capability/product name: **Computer History Collector**
- package and command name: `computer-history-collector`

This terminology also accommodates a full application such as Context on iOS:
an app can be a Context Collector without being merely a background daemon.

## Why "collector" is the strongest precedent

The most useful established precedent is OpenTelemetry. Its Collector is an
end-to-end, vendor-neutral pipeline that receives, processes, and exports data;
its components explicitly divide those jobs among receivers, processors, and
exporters. OpenTelemetry then uses **agent** and **gateway** to describe ways of
deploying Collector instances, not different fundamental kinds of software.
That distinction maps cleanly to Fulcra: collector is the role; on-device is a
deployment location. See the official OpenTelemetry documentation for
[Collector components](https://opentelemetry.io/docs/collector/components/), the
[agent deployment pattern](https://opentelemetry.io/docs/collector/deploy/agent/),
and the
[agent-to-gateway pattern](https://opentelemetry.io/docs/collector/deploy/other/agent-to-gateway/).

Other systems reinforce the broader family resemblance:

- [Telegraf](https://docs.influxdata.com/telegraf/v1/glossary/) calls its running
  process an agent that gathers through input plugins and sends through output
  plugins.
- [Fluent Bit](https://docs.fluentbit.io/manual/about/what-is-fluent-bit) calls
  itself a telemetry agent at the edge and a collector when aggregating multiple
  sources; its
  [pipeline](https://docs.fluentbit.io/manual/4.2/concepts/data-pipeline) gathers,
  parses, transforms, buffers, routes, and outputs data.
- [Splunk Universal Forwarder](https://docs.splunk.com/Documentation/SplunkCloud/8.2.5/Forwarding/Typesofforwarders)
  and [Elastic Beats](https://www.elastic.co/beats) establish *forwarder* and
  *shipper* for deliberately transport-heavy variants.
- [Kafka Connect](https://kafka.apache.org/25/kafka-connect/connector-development-guide/)
  and [Airbyte](https://github.com/airbytehq/airbyte/blob/master/docs/platform/move-data/sources-destinations-connectors.md)
  use *connector* for an adapter between systems. In both cases it is distinct
  from the source itself and can be orchestrated by a larger runtime.
- [Singer](https://www.singer.io/) calls extraction scripts *taps* and loading
  scripts *targets*, a useful precedent for small composable programs but a
  specialized metaphor rather than a general infrastructure term.

## Decision-oriented comparison

| Candidate | Established role | Fit for coding agents | Fit for operators | Fit for ordinary people | Main problem for Fulcra |
| --- | --- | --- | --- | --- | --- |
| **collector** | Broad pipeline or service that gathers and can process and export | Strong: conventional and compositional | Strong: familiar across telemetry systems | Strong: plain when compounded with “context” | Can imply aggregation, but the definition removes that ambiguity |
| **agent** | A process deployed beside a source or on each host | Weak: now overloaded with AI agency | Very strong: standard endpoint/telemetry topology | Moderate: may imply autonomy or surveillance | Confuses the context-populating utility with AI agents that consume context |
| **forwarder** | Lightweight source-side transport | Strong | Very strong | Strong | Understates parsing, enrichment, revision handling, and projection |
| **exporter** | Output-stage adapter that sends to a backend | Strong | Strong | Moderate | Names only the final pipeline stage, not discovery or transformation |
| **connector** | Adapter/configuration connecting a source or destination to a runtime | Strong | Very strong | Strong | Often denotes a plugin or integration definition, not the installed running utility |
| **shipper** | Lightweight program that moves data from many hosts | Strong | Strong | Moderate | Informal metaphor and too transport-centered |
| **sensor** | Component that observes or measures its environment | Strong | Strong | Very strong | Wrong for historical files, APIs, and already-derived records; implies original measurement |
| **gatherer** | General act of collecting, sometimes used for input-stage behavior | Strong | Moderate | Very strong | Less established as the category name for an operational data pipeline |
| **ingestor** | Component on the receiving/backend side of a data flow | Strong | Strong | Weak | Direction is backwards for software installed at the source |
| **projector** | Component that transforms source facts into a derived representation | Moderate | Moderate | Weak | Accurate architectural vocabulary, but uncommon as a deployable utility and evokes visual projection |
| **source** | The originating system or provenance identity | Weak: highly overloaded | Moderate | Strong | Conflates the origin, its Fulcra provenance record, and the software moving the data |

## Suggested vocabulary boundary

- **Context Collector**: the user-facing and repository-wide category.
- **collector instance**: one installed/running copy, optionally described as
  *on-device*, *service-side*, or *scheduled*.
- **Context Projection**: the mapping from source context to Fulcra records.
- **source**: the originating device, application, service, or source artifact;
  never the collector itself.
- **connector**, **receiver**, **processor**, and **exporter**: implementation
  parts when a collector becomes modular enough to need those distinctions.
- **agent**: reserve for AI agents, or use only as an explicit deployment
  topology term in deeply technical material.

## Naming consequence

If the category is adopted, renaming `computer-history-gatherer` to
`computer-history-collector` before public release would make the first utility
teach the convention. The more explicit `computer-history-context-collector`
is unambiguous but probably redundant inside a Fulcra skills repository; the
canonical documentation can carry the word *Context* while individual names
remain concise.
