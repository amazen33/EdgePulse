# ADR 0020: ThingsBoard CE is the operational core (Option A)

**Status:** Accepted (owner, 2026-10-14, decision D-1 "Option A"). The number is confirmed at merge, per `docs/adr/README.md`.
**Author:** Claude (architecture). **Implementer:** Codex (IOT-WO-01 applies the document changes).
**Supersedes:** ADR 0019 Decision 4 ("TB CE is downstream of Kafka, not the ingress owner").
**Amends:** ADR 0019 Decision 3 (the data path), and the requirements addendum's "TB CE must be both replaceable … and upgradeable".
**Withdraws (unmerged drafts):** `XXXX-proposed-tb-ce-kafka-bridge.md`, `XXXX-proposed-pre-tb-ce-anomaly-review.md` and `XXXX-proposed-mqtt-broker-and-cross-region-recovery.md`.
**Review:** `E:\vcloud-handoff\reviews\iot-ee-review-2026-10-14.md`, section 3.

## Context

The accepted ADRs disagree about what ThingsBoard CE is for:

- ADR 0011 Decision 2 makes CE the upgradeable core.
- ADR 0019 Decision 4 puts CE behind Kafka.

The spike against a real CE 4.3.1.5 (`docs/spikes/tb-ce-kafka-rule-engine-spike.md`) showed that CE cannot consume an external Kafka topic, because integrations are PE/Cloud-only. CE's device API also gives no deduplication and no buffering. The bridge that would follow from Decision 4 means running two IoT platforms in series, with:

- at-least-once rule side effects;
- two tenant models;
- two identity systems;
- two sources of truth for devices.

The product's goal is an enterprise-grade platform that takes over customers from a legacy ThingsBoard-based product. If the target keeps ThingsBoard CE, legacy data can move in ThingsBoard's own format through ThingsBoard's own upgrade path. If it doesn't, every data class has to be re-modelled.

## Decision

1. **TB CE is the operational core.**
   - TB CE at the pinned patch line in `tb-extensions/manifest.yaml`, currently 4.3.1.x, owns:
     - device transports (MQTT, HTTP and CoAP);
     - devices, assets and relations;
     - attributes and telemetry storage;
     - the rule engine and alarms;
     - dashboards.
   - It is the system of record for those data classes until a later ADR moves one out (Decision 6).
   - It is never forked and never modified in source. Its customisations stay in `tb-extensions/manifest.yaml` (ADR 0011 Decision 8).
2. **IOT-EE services surround the core.** They provide what CE lacks:
   - identity and federation (Keycloak);
   - fine-grained RBAC/ABAC beyond CE's tenant and customer model;
   - evidence;
   - billing;
   - AI;
   - consoles beyond CE's UI;
   - the migration integration surface (ADR 0022).

   They follow ADRs 0013, 0016, 0017 and 0018 unchanged.
3. **Data out of TB uses a supported CE feature.**
   - Tenant rule chains publish to an IOT-EE **raw** Kafka topic through CE's stock outbound Kafka action node.
   - An IOT-EE **ingestion adapter** (an anti-corruption layer) does the rest:
     - validates the message;
     - resolves the tenant from TB's message metadata, never from the payload;
     - deduplicates by TB message ID and timestamp;
     - wraps each event in the canonical envelope (`contracts/events/v1`, ADR 0018);
     - publishes it to the canonical topics.
   - IOT-EE never consumes CE's internal topics (`tb_core`, `tb_rule_engine`, `tb_transport.*`) and never imports `TransportProtos.proto`.
4. **Data into TB uses CE's documented REST API only,** through an IOT-EE `ThingsBoardPort` adapter:
   - commands, attributes, provisioning and tenant administration;
   - authenticated with CE API keys held in OpenBao (ADR 0021);
   - never by writing TB tables;
   - never by publishing to CE's internal topics.

   Atomicity across TB and Kafka is never claimed (`CLAUDE.md`).
5. **Identity.**
   - Keycloak is the identity provider for IOT-EE's consoles. CE login federates to Keycloak through CE's OAuth2 client support (to verify in IOT-WO-04).
   - One TB tenant maps to one IOT-EE `tenant_id`, through a recorded mapping.
   - How TB customers and users map to IOT-EE's tier-2 roles is C3/M2 design work.
6. **The strangler rule.** A bounded context may move out of TB only through a new ADR that names:
   - the context;
   - its parity tests against TB behaviour;
   - its data-migration path, supported by migration-manager (ADR 0022);
   - its rollback.

   The hexagonal ports make this possible. Nothing is strangled in this ADR.
7. **The data path replacing ADR 0019 Decision 3:**
   `device → TB CE transport → TB rule engine → outbound Kafka node → IOT-EE ingestion adapter → canonical topics → (Flink → redaction → pgvector → RAG | evidence | billing | …)`.
   - Redaction before any vector write remains mandatory.
   - Ingress buffering is TB CE's own cluster queue (`TB_QUEUE_TYPE=kafka`). It is separate from IOT-EE's canonical topics, with ACLs, and IOT-EE never reads it.
   - Edge buffering is open. ThingsBoard Edge CE is a candidate, subject to the licence gate (ADR 0021).

## Consequences

**Becomes simpler:**
- There is no separate device broker by default; CE's MQTT transport is the device endpoint.
- There is no bridge and no pre-TB anomaly gate.
- Legacy migration can use ThingsBoard's own export, import and upgrade paths (ADR 0022).

**Stays CE's ceiling:**
- PE/Cloud-only features are not available. The integrations framework is confirmed absent; other PE features need checking against the pinned version.
- Every enterprise feature is built outside TB.

**New work:**
- TB CE high availability on Twinfra: cluster mode and its dependencies, each pinned and licence-checked in the deployment work order.
- A backup, restore and upgrade runbook.
- The ingestion adapter.
- `ThingsBoardPort`.

**Security:**
- CE keeps device credentials in its own database. That database's storage, backups and roles get the same protection as secrets: encryption at rest, a restricted owner role, and no application role with `BYPASSRLS`.
- Verify which credential fields are stored in plain text at the pinned version.

**Legacy devices:** devices on non-TB topics or protocols need a compatibility front-end, chosen from the legacy inventory (ADR 0022) and subject to the licence gate.

## Alternatives rejected

- **Option B, IOT-EE-native with TB retired after cutover.** It needs a full re-model of every TB data class, rule-chain and dashboard rebuilds per tenant, and device re-provisioning, all before any value. It stays reachable later, one context at a time, through Decision 6.
- **Option C, TB CE permanently behind a bridge.** It means permanent dual writes, no exactly-once delivery, and two tenant and identity models.
- **Producing onto CE's internal topics.** That is an undocumented wire format that can change in any patch release.

## Cross-references

ADR 0011 (Decisions 2 and 8), 0013, 0016, 0017, 0018 and 0019; ADR 0021 (Twinfra and the licence gate); ADR 0022 (migration-manager integration); `docs/tb-ce-inventory.md`; the TB CE spike.
