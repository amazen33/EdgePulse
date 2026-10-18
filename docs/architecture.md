# Target architecture (decisions recorded; integration not implemented)

Current authority: ADRs 0020–0022 and MILESTONES.md. EdgePulse is an IoT
platform in foundation development. Every flow and integration below is a
target requirement, not an implemented capability. The existing identity
foundation is evidenced by merged [PR #21](https://github.com/amazen33/EdgePulse/pull/21)
and [PR #29](https://github.com/amazen33/EdgePulse/pull/29), within their code/test
scope only. Tool portability, hybrid-cloud, cross-vertical operation and AI
need milestone receipts before any capability claim. AI remains unimplemented
F5 work after MS5. The target places TB CE at the operational core, IOT-EE
services around it and hosting on Twinfra. Legacy version, backend, protocols, credentials and customizations remain unknown until migration-manager produces an authorized inventory (ADR 0022).

## Boundaries and flow

Bounded contexts: identity/tenant; device/connectivity; asset/tank; telemetry ingestion; rules/automation; alarm/command; reporting; audit/evidence; firmware management; usage metering; optional monetization. Each owns its data and contracts; cross-context database writes are prohibited.

Target data path (ADR 0020 Decision 7):

```text
device → TB CE transport → TB rule engine → outbound Kafka node
       → IOT-EE ingestion adapter → canonical topics
       → (Flink → redaction → pgvector → RAG | evidence | billing | …)
```

TB CE owns MQTT/HTTP/CoAP transports, devices/assets/relations,
attributes/telemetry storage, rules, alarms and dashboards. Its stock outbound
Kafka action node publishes to an IOT-EE raw topic. The ingestion adapter
validates, resolves the tenant from TB message metadata (never payload),
deduplicates by TB message ID and timestamp, wraps the canonical v1 envelope
and publishes canonical topics. Redaction precedes every vector write.

TB's cluster queue (`TB_QUEUE_TYPE=kafka`) supplies ingress buffering and is
separate from canonical topics with ACLs. IOT-EE never reads or publishes TB
internal topics and never imports TransportProtos.proto. Edge buffering is
open, subject to ADR 0021's licence gate.

Commands, attributes, provisioning and tenant administration use TB's
documented REST API only through ThingsBoardPort, with API keys in OpenBao;
no direct TB table writes. Consumers require durable tenant-scoped
idempotency. IOT-EE service state changes and their outbox share a local
transaction under ADR 0018. There is no atomic transaction across TB and
Kafka. Retry, reconciliation, DLQ and replay require implementation and tests.

Keep TB unforked and its customization set in tb-extensions/manifest.yaml.
A bounded context leaves it only through a new ADR naming parity tests,
data migration and rollback (0020 Decision 6). Keycloak federation and
TB tenant/customer/user mappings require verification. No running integration
or real-environment test is claimed here.

## Migration-manager integration (ADR 0022)

M1 and M9, discovery, extraction, transformation, CDC and orchestration move
to migration-manager. The retained migration documents are its input
specification. IOT-EE owns MR-1 to MR-14: readiness contracts, tenant
lifecycle, side-effect fence, reconciliation reads, run-scoped access,
endpoint transitions and append-only run records. Mode W upgrades an
approved isolated TB copy using TB procedures; Mode T imports normalized
tenant data through documented APIs. Each credential step needs explicit
owner approval and exposes no values in evidence. The following historical
inventory requirements are inputs to that work.

Support manual/dynamic source registration for Mosquitto live mirrors, PostgreSQL history, ThingsBoard rules/dashboards/devices/assets, and reports. During infrastructure scaffolding configure the vault. Source secrets go directly to that vault once; app DB, Git, events, and audit contain only secret references. Do not automatically import legacy secrets.

Inventory rule chains, custom nodes/scripts, dashboards, devices/assets/relations, formulas, alarms, profiles, integrations, queues, reports, users/roles. Workflow: inventory → dry run → field/formula mapping → preview → shadow comparison → approval → controlled application with immutable evidence. Screenshots may guide visible layout only; they cannot recover rules, formulas, or data.

## Delivery and user experience

APISIX is the north-south L7 gateway on Twinfra, serving REST/gRPC/WebSocket
APIs with authentication, tenancy, rate limits, correlation and versioning.
MQTT terminates at TB CE transport. SSR/BFF serves initial UI. Each browser
uses one tenant-authorized WebSocket connection multiplexing permitted UI
channels; never expose raw Kafka or device streams to browsers. Reauthorize
subscriptions and scope every read model by tenant. Portable packaging
follows ADR 0021 Amendment 1; no alternate-host support is established here.

Visible product requirements: executive fleet status, hierarchy/region/site/tank navigation, map/location, level/temperature/alarm/battery, measurement history, refill/consumption, reports, multiple communication types and tank materials.

Reports are a separate migration lane: retain historical exports as evidence, inventory definitions/metadata, rebuild logic on certified event-backed read models, reconcile old/new results, and require approval before publication or scheduling. First pack: executive fleet status, hierarchy/location, tank health, measurement history, refill/consumption, battery/alarm.

## Firmware, evidence, and monetization

Firmware is a separate bounded context initially integrated with TB OTA: signed artifacts, SBOM/provenance, compatibility policy, rollout rings, canary, pause, and rollback. MQTT/TB notifies devices; HTTPS/object storage delivers binaries; devices verify signatures and compatibility. WebSockets show progress only.

Evidence uses an append-only operational ledger plus WORM objects through an owned S3 port. ADR 0021 selects Twinfra's SeaweedFS path; ADR 0010 Object Lock conformance must pass before any WORM claim. Store manifests, hashes, retention metadata, and verification results. Kafka is the event backbone, not immutable compliance storage. Retention/legal-hold and privileged deletion controls need verification in M6. No raw PII or secrets in logs, events, or audit.

Usage metering finalizes UsageMetered events. Optional, separately deployable monetization consumes them and owns effective-dated plans, entitlements, rating, invoices, credits, immutable closed periods, and reversals. Never bill directly from raw telemetry or let billing availability block telemetry, alarms, or commands.

## Application delivery on Twinfra (ADR 0021)

Deployment Studio is dropped by MILESTONES.md; Twinfra supplies deployment.
Future IOT-EE delivery must provide application images, Helm charts and Argo CD Applications into
IOT-EE namespaces with default-deny ingress. Existing infrastructure packages
are frozen by ADR 0021 (see [freeze notice](../deploy/FROZEN.md)); removal requires a later deletion work order. This document
authorizes no host, cluster, infrastructure, deployment or cutover action.

Packaging follows ADR 0021 Amendment 1: arbitrary UID, non-root, restricted
security context, portable Ingress/Service, configurable storage class and
platform values profiles. OpenShift/OKD is a compatibility target; support
requires an accepted live compatibility receipt. Application charts remain
unimplemented. Twinfra dependencies, gates and real-environment runs remain pending
their work orders. Instrumentation uses Twinfra's observability baseline.
Supply-chain scanning follows ADR 0014; implementation is pending IOT-WO-02.
