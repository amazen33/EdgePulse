# Proposed device-event processing topology

Status: architecture proposal, not a deployed pipeline. TBMQ CE remains an
MQTT broker candidate. The selected broker must pass the same device ingress
and external Kafka export contract. This diagram expresses the intended
fan-out and the separate pre-TB CE decision path:

```text
IoT devices -- MQTT/TLS --> TBMQ CE candidate / conforming MQTT broker
                                |  TBMQ-owned Kafka stays internal
                                v
                    TBMQ Integration Executor / export adapter
                                |
                                v
              external IOT-EE Kafka ingress topic
                                |
                  validation + canonicalization
                                |
                   canonical Kafka event topics
                                |
          +---------------------+----------------------+
          |                     |                      |
          v                     v                      v
   Flink CEP (Tier 3)    telemetry delivery      other consumers:
   event-time patterns    gate -> TB CE bridge    search, redacted RAG
   by tenant/device            |
          |                    v
          v               TB CE documented API
   alerts-critical             |
          |                    v
          v              TB CE dashboards,
   Flowable Event Registry   device visibility,
   (Tier 4)                 CE rule processing
          |
   BPMN/CMMN resolution case
          |
   human tasks: notify/approve/dispatch
   service tasks: call authorized core APIs
          |
   core service state + outcome events
          +----> review release / TB CE projections via owned adapters
```

TBMQ's documented Kafka integration uses an **external** Kafka cluster; its
internal Kafka topics are broker implementation state, not IOT-EE's canonical
event API. An ingress adapter validates device/tenant ownership, schema,
event ID, event time and correlation before publishing canonical events.
Broker export and canonicalization need durability, deduplication, DLQ,
replay and outage tests. No atomic delivery claim spans MQTT, external Kafka
and TB CE. TBMQ's availability, CE edition controls and recovery are still
selection gates.

Each Kafka branch has its own versioned contract, consumer group, ACL,
backpressure, retention, replay and tenant authorization. **Flink CEP** is
the Tier 3 candidate for complex temporal patterns across events and
devices. It must partition/state by tenant and the relevant device or group,
define event-time watermarks and late-event handling, and publish a
versioned, deduplicated `AlertRaised` to `alerts-critical` only for the
approved critical class. Simpler threshold checks may stay in a service.
The alert includes tenant, device/group, source event IDs, event time,
pattern version, severity, correlation and idempotency key without secrets
or raw PII. The search branch indexes only approved query fields and redacted/tenant-scoped
documents through a projector; it is a rebuildable read model, not the
telemetry system of record. **OpenSearch** is the open-source search candidate.
Elasticsearch is an optional separately licensed provider: the repository's
8.13.4 managed client version does not make Elasticsearch 8.13.4 an
open-source server distribution. Exact server license and version must be
reviewed before selection.

The **AI/RAG** branch follows accepted ADR 0019: Flink windowing, mandatory
redaction, pgvector and tenant-scoped retrieval. It does not receive secrets,
raw PII or unbounded telemetry, and its output never directly authorizes a
device action. Model providers remain replaceable and profile-bound.

**Flowable** is the Tier 4 workflow candidate. Its Event Registry consumes
the curated `alerts-critical` contract through a service-owned adapter to
start or correlate one BPMN/CMMN resolution case per alert key. It can also
consume `AnomalyReviewRequested`, `WorkOrderRequested` and other approved
domain events. Event Registry supports Kafka channels in OSS, but the exact release,
channel configuration and task UI require conformance tests. BPMN/CMMN
coordinates reviews, approvals, escalations and automation requests. The
alarm/work-order/command services own their state, RBAC/ABAC and APIs; a
workflow task completion alone cannot issue a device command or approve
tenant access. Human tasks cover notify, approve and dispatch; service tasks
call versioned core use cases with scoped identity and stable idempotency
keys. Workflow outputs become versioned decision/command-request events with
evidence. Notifications must have a defined delivery/acknowledgment path;
creating a human task alone does not prove a person was notified.

**TB CE** provides downstream dashboards, device management and visibility,
and continues to run its own CE rule chains. Its documented API is reached
by an external bridge, not directly by Flink or Flowable. Core outcome
events can be projected into CE through an authorized adapter after
contract and parity tests. The telemetry bridge is a separate consumer
behind the anomaly gate. A
policy-approved high-impact class may wait for human release; ordinary
telemetry continues within its SLO. Held/rejected events retain explicit
dispositions and can be reconciled against CE rule, alarm and dashboard
outcomes. A Flowable or AI outage must not silently approve held events.

## Proof before choosing this as a deployment profile

Demonstrate broker-to-external-Kafka export and canonicalization, consumer
isolation, two-tenant denial, duplicate and out-of-order behavior, Flink
replay, search rebuild, RAG redaction, Flowable event correlation and human
task authorization, `alerts-critical` schema/ACL/retention, cross-device
CEP isolation and late-event behavior, alert/approval/automation idempotency,
CE rule parity,
and bounded behavior during broker, Kafka, Flowable and CE outages. Record
the exact editions and versions and measure end-to-end latency and backlog.

## Sources and related decisions

- [TBMQ Kafka integration](https://tbmq.io/docs/integrations/kafka/) distinguishes external and internal Kafka.
- [Flowable OSS Event Registry](https://www.flowable.com/open-source/docs/eventregistry/ch05-Deployment) supports Kafka channel definitions.
- [Apache Flink CEP](https://nightlies.apache.org/flink/flink-docs-stable/api/java/org/apache/flink/cep/CEP.html) provides pattern processing over streams.
- [Elasticsearch version/licensing review](enterprise-readiness-review.md) and [streaming/RAG ADR](adr/0019-streaming-and-rag.md).
- [Broker/DR ADR](adr/XXXX-proposed-mqtt-broker-and-cross-region-recovery.md), [workflow selection ADR](adr/XXXX-proposed-workflow-engine-selection.md), [anomaly-review ADR](adr/XXXX-proposed-pre-tb-ce-anomaly-review.md), and [TB CE bridge ADR](adr/XXXX-proposed-tb-ce-kafka-bridge.md).
