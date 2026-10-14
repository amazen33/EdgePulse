# ADR XXXX (proposed) -- MQTT broker selection and cross-region recovery

Status: proposed; no broker selected or installed. Number at merge. This
proposal refines ADR 0011's broker and MirrorMaker direction without changing
the Kafka-to-TB CE bridge proposal. TBMQ CE and Absmach FluxMQ are candidates.

## Decision proposed

1. Keep the IOT-EE device ingress contract, authentication/ACL mapping and
   canonical Kafka events independent of the MQTT broker. Evaluate pinned
   editions and releases of TBMQ CE and `absmach/fluxmq` with the same
   MQTT 3.1.1/5, QoS, persistent session, retained message, will, TLS/mTLS,
   client/topic ACL, tenant isolation, Kafka export, operational and upgrade
   tests. Include load, long-duration soak, outage, replay and restore tests.
   Neither repository's feature list alone establishes production readiness.
   For TBMQ v2.1+, its documented Kafka Integration exports through the
   Integration Executor to an **external Kafka cluster**, distinct from
   TBMQ's internal Kafka state. Validate and canonicalize those exported
   messages before any IOT-EE downstream consumer; do not subscribe to
   TBMQ private topics as the product API.
2. Treat FluxMQ as an exploratory candidate. Its published source is
   Apache-2.0 and documents MQTT and clustering, but its queue append Raft
   layer is marked work in progress. Identify the exact release, support
   model, admin authorization, audit capabilities, persistence semantics,
   and geographic failure behavior before any default decision. FluxMQ is
   an MQTT/other-protocol ingress candidate; it does not satisfy Kafka
   protocol, MirrorMaker or canonical event requirements by its name.
3. Treat TBMQ CE as a candidate with edition gaps. The vendor's comparison
   lists MQTT client ACLs in CE, while advanced admin RBAC and audit logs
   are PE-only. Broker admin least privilege and audit evidence therefore
   need tested compensating controls or an approved edition decision.
   Confirm all claims again for the version and build actually pinned.
4. Use MirrorMaker 2 first for approved **IOT-EE canonical Kafka topics**
   between regional Kafka clusters, preferably with one active writer per
   device/tenant partition during failover. Define topic allowlists, ACLs,
   encryption, retention, checkpoint/offset translation, replication-lag
   alarms, promotion and failback procedures. It is asynchronous: set RPO
   from measured lag and test results, not from a zero-loss assertion.
5. Do not mirror TBMQ's internal topics as a claimed full broker DR design.
   TBMQ also stores persistent DEVICE inboxes in Redis/Valkey and metadata
   and some MQTT session state in PostgreSQL. MirrorMaker alone cannot
   recover those or guarantee consistent MQTT session and QoS state. A
   regional TBMQ standby requires a tested, edition/version-supported
   recovery method for the complete state set, credentials and certificates,
   device endpoint redirection, duplicate handling, and failback. Require
   vendor support or explicit lab proof before including TBMQ internal topics
   in a replication plan. Keep canonical events authoritative for IOT-EE.
6. Keep TB CE downstream of the external Kafka-to-CE bridge. Replication of
   canonical events does not automatically replicate TB CE rules, alarms,
   credentials or tenant state. Reconcile bridge delivery and CE outcomes
   after any region switch. Never claim exactly-once CE side effects.

## Selection and DR evidence

Record the version/build, license, deployment profile, test topology,
synthetic test IDs, results, timestamps and reviewer. Prove broker auth and
authorization denials; administration least privilege and audit capture;
MQTT QoS/session behavior under node and region loss; Kafka export; tenant
separation; throughput and soak; patch/rollback; backup and restore. Set
business-approved RTO/RPO through the impact assessment, then test regional
loss, MirrorMaker lag/checkpoints, controlled promotion, device reconnect,
duplicate/reordered events, recovery and failback. A successful component
test is not a business-continuity or certification claim.

## Primary references

- [TBMQ architecture and state stores](https://tbmq.io/docs/architecture/),
  [external Kafka integration](https://tbmq.io/docs/integrations/kafka/),
  and [TBMQ edition comparison](https://tbmq.io/).
- [Absmach FluxMQ source, license and feature status](https://github.com/absmach/fluxmq).
- [Apache Kafka cross-cluster replication](https://kafka.apache.org/35/operations/geo-replication-cross-cluster-data-mirroring/).
