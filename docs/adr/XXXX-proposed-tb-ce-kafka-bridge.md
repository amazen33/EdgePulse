# Proposed ADR -- External Kafka-to-ThingsBoard CE bridge

Status: proposed for owner review. If accepted, supersedes only ADR
0019 Decision 4's claim that TB CE itself consumes IOT-EE Kafka topics.
It does not change the tier-1 buffer, Flink/RAG path, or M9 final legacy
cutover boundary. No production Kafka-to-TB CE bridge has been tested.

## Context and evidence

ADR 0019 places TB CE downstream of Kafka for rule execution but leaves
its consumption mechanism blocked. The pinned TB CE 4.3.1.5 spike in
`docs/spikes/tb-ce-kafka-rule-engine-spike.md` verified that external
synthetic telemetry sent through CE's documented device HTTP API reaches
the rule engine, including a two-tenant alarm test. It also observed
that duplicate posts re-execute the rule chain and a CE outage leaves
the HTTP caller responsible for retry. The spike did **not** run a
Kafka-consuming bridge or prove its production delivery semantics.
CE's integration framework for subscribing to an external Kafka topic
is unavailable; `TB_QUEUE_TYPE=kafka` configures CE's internal queue,
not a public subscription to platform events.

## Proposed decision

The target path is device/edge ingestion -> IOT-EE's tier-1 buffer and
canonical Kafka event -> optional policy-driven anomaly-review gate ->
an **external bridge service** -> TB CE's
documented device telemetry/transport API -> CE rule engine. TB CE is
downstream of the bridge, not itself a Kafka consumer. The bridge is an
adapter behind IOT-EE-owned event and ThingsBoard ports, so a new CE
version or replacement rules engine can be tested without changing the
canonical event contract or core application rules.

The bridge must:

- Honor the separate, proposed pre-TB CE anomaly-review gate: only events
  with an authorized release/pass disposition may be posted when a tenant
  policy enables a hold class. Keep rejected/held events in the durable
  ledger and record any resulting CE parity difference. See
  [anomaly-review ADR](XXXX-proposed-pre-tb-ce-anomaly-review.md).
- Consume versioned tenant/device-scoped events, validate source
  identity and authorization, and map each to the intended CE device
  and tenant. Obtain per-device CE credentials by vault reference;
  never place tokens in Kafka messages, logs, evidence or browser state.
- Use CE's documented ingestion API for the pinned version. Do not
  publish to CE's private Kafka topics or import its internal wire
  schema. HTTP device telemetry is the verified first adapter; MQTT
  Gateway ingestion remains unverified and requires its own spike.
- Keep a durable event-ID deduplication and delivery ledger, bounded
  retries with backoff, backlog/lag alarms, dead-letter handling and
  authorized replay. Commit Kafka progress only after recording a
  definite delivery result. Preserve per-device ordering when rule
  behavior requires it. Compare CE rule outcomes with canonical source
  events and reconcile gaps.
- Treat an HTTP timeout or crash after CE accepts a post but before
  the bridge records success as **ambiguous**. A retry may run the CE
  rule chain twice; the bridge cannot make CE's side effects exactly
  once. Rules with commands, notifications or other non-idempotent
  effects need a tested CE-side idempotency mechanism or must remain
  disabled for bridge-driven events until the behavior is resolved.
  Alarm upsert and timeseries overwrite observed in the spike are not
  general message deduplication.
- Keep the CE integration outside business-domain code and preserve
  tenant/device/event/correlation traceability. CE outcomes become
  canonical events through a separately tested outbound adapter; no
  atomic transaction across Kafka and CE is assumed.

## Acceptance before operational use

In an isolated environment with the selected Kafka-compatible broker
and pinned CE version, prove tenant/device mapping, rule outcomes,
event-ID duplicate suppression before the HTTP call, partition and
restart behavior, outage catch-up, replay, lag and dead-letter recovery.
Inject an ambiguous post-result failure and measure duplicate effects
for each enabled rule class. Block activation of non-idempotent rules
that cannot meet approved effect-level parity. Repeat contract and
behavior tests for each CE upgrade or replacement adapter. Record
versions, test cases and evidence; the current spike establishes only
the CE-facing ingress and rule-execution portion of this path.

## Open inputs

Select broker/bridge deployment profile, source topic and ordering key,
delivery retention and lag targets, CE credential lifecycle, rule
classes eligible for replay, ambiguous-result handling, CE outcome
capture path, and per-tenant owner-approved parity thresholds.
