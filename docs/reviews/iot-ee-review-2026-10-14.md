# IOT-EE review: stability, architecture, code and stories (2026-10-14)

**Author:** Claude (head of architecture). **Status:** discussion draft for the owner. Nothing in IOT-EE was changed.
**Goal it is measured against:** an enterprise-grade IoT platform that can take over customers and data from the legacy ThingsBoard-based product (SpectroTANK).
**Sources read:** `D:\project\IOT-EE` at `7dde126` plus its uncommitted working tree: README, `docs/enterprise-readiness-review.md`, `requirements-addendum.md`, `legacy-migration-execution-plan.md`, `migration-studio.md`, `tb-ce-inventory.md`, the TB CE spike, ADRs 0011, 0016 and 0019, the proposed TB CE bridge ADR, `track-c-execution-plan.md`, `test-plan.md`, `tb-extensions/manifest.yaml`, `services/identity`, `pom.xml`, and PR #29.

## Decisions taken (owner, 2026-10-14)

- **D-1: Option A** (IOT-EE ADR 0020).
- **D-2: Twinfra's licence gate applies** (ADR 0021 and ADR 0014).
- **Legacy facts come from migration-manager,** developed separately. IOT-EE prepares its integration (ADR 0022, Proposed).
- **The remaining questions** (device credentials, WIP push, ordering after WO-08) were delegated to the architect's recommendations.

Work orders IOT-WO-01 to IOT-WO-04 are in `E:\vcloud-handoff\iot-ee\work-orders\`.

## 1. Verdict

IOT-EE is **not ready to deploy**, and "stability" is not yet a runtime question: nothing has ever run. The instability is in the **design and the repository**:

- **No settled target architecture.** Three accepted or required statements contradict each other on what ThingsBoard CE is for (section 3.1).
- **Design far ahead of code.** There are about 5,700 lines of ADRs plus 22 proposed ADRs (2,660 lines), against one service with 58 main Java files serving one query.
- **The work at risk is unpushed.** 83 uncommitted changes, 18 days old.
- **The biggest unknown has not moved since September.** That is the legacy system itself: its version, storage, customisations, volumes and device credentials. It decides both the architecture and the cost of migration.

The quality of what *does* exist is good. The hexagonal rules, the ArchUnit planted-violation tests, the readiness review's evidence levels (D/C/T/CI/R) and the migration governance (snapshot and CDC positions, per-tenant reconciliation, no secrets in evidence) are enterprise-grade thinking. The problem is direction and order, not craftsmanship.

## 2. Stability and repository hygiene

| # | Finding | Risk | Recommendation |
| --- | --- | --- | --- |
| S1 | The branch `docs/reconcile-roadmap-and-direction` holds **83 uncommitted changes** (28 modified, 7 deleted, 48 untracked): 22 proposed ADRs, deploy layers 02–04, catalog, profiles, `tools/`, contracts for AI, device and deploy. The last commit was 2026-09-26. | **Loss.** It exists only on drive D. | Push a WIP snapshot branch now, without merging, then split it into reviewable PRs or drop parts after the decisions below. |
| S2 | PR #29 (caller authorization on REST and gRPC) has been open since 2026-09-26 with green CI. It sits on a "docs" branch that carries code commits. | Review debt; mixed scope. | Merge or close it on its own; keep docs and code PRs apart. |
| S3 | The working tree deletes `deploy/k8s/kube-vip/**` and `group_vars/all.yml`. | Silent infrastructure changes. | Resolved by S5 or D-2. |
| S4 | Nothing is verified at level R except one host-preparation run. | No runtime evidence. | The first R evidence should be the migration rehearsal (section 6, gate 3). |
| S5 | IOT-EE has its own Layers 0–4: OpenTofu Hyper-V VMs, RKE2 through Ansible, kube-vip, LGTM, Vault or OpenBao, Mosquitto or EMQX, MinIO. | It duplicates Twinfra; see section 3.3. | Under the owner directive "IOT-EE on Twinfra", freeze `deploy/00–02` behind a tag and stop extending them. |

## 3. Architecture

### 3.1 The central contradiction: what is ThingsBoard CE for?

| Source | What it says |
| --- | --- |
| ADR 0011 Decision 2 (accepted) | TB CE is the "upgradeable compatibility core": device transports, rule engine and dashboards. It is upgradeable, **not replaceable**. |
| ADR 0019 Decision 4 (accepted) | TB CE sits **downstream of Kafka** and is **not** the ingress owner. |
| TB CE spike (real 4.3.1.5) | CE **cannot consume** an external Kafka topic, because integrations are PE/Cloud-only. Telemetry can reach the rule engine only through CE's device API. CE has no deduplication and no buffering. |
| Proposed bridge ADR | device → IOT-EE buffer → Kafka → anomaly gate → **bridge** → CE HTTP API → CE rule engine. Exactly-once is impossible, so non-idempotent rules stay disabled. |
| Requirements addendum | TB CE must be **both replaceable** through an adapter **and upgradeable**. |

Taken together, the current design runs **two IoT platforms in series**:

- IOT-EE ingestion, then a lossy bridge, then TB CE with its own PostgreSQL, telemetry tables, rule engine and dashboards;
- with **two tenant models** (TB tenants and customers, and IOT-EE `tenant_id` with RLS);
- with **two identity systems** (TB users and JWT, and Keycloak);
- with **two sources of truth for devices**.

The bridge makes rule side effects at-least-once at best, and the product keeps every TB CE limit. This is the most important thing to fix, because the choice also decides how expensive migration is.

### 3.2 Two coherent target shapes (owner decision D-1)

**Option A: TB CE as the operational core, enterprise services around it, strangled later per bounded context.**

- TB CE 4.3.1.x owns the device transports (MQTT, HTTP and CoAP), the rule engine and the dashboards, as ADR 0011 Decision 2 originally said.
- IOT-EE services take events **out** of TB through CE's supported **outbound** Kafka rule node. The spike confirmed CE has Kafka, MQTT and RabbitMQ outbound action nodes.
- Those services add: Keycloak federation, fine-grained RBAC/ABAC, evidence and WORM storage, billing, AI on Flink, Migration Studio, and later Deployment and Config Studio.
- **Effect on migration:** if the legacy system is unmodified TB CE on PostgreSQL, the core migration becomes **"restore a copy, upgrade it with ThingsBoard's own upgrade procedure, reconcile"**.
  - Rule chains, dashboards, device credentials, relations and attributes then carry over in TB's own format.
  - Users and devices do **not** need re-enrolling.
  - Migration Studio shrinks to inventory, reconciliation, evidence, identity federation and cutover.
- **Ceiling:** the product inherits CE's limits: no integrations framework, CE's tenant and customer model, and CE's scaling profile. Every enterprise feature must be built outside TB without touching its database.

**Option B: IOT-EE-native platform; TB CE only as a temporary shadow runtime until M9.**

- IOT-EE owns devices, telemetry, alarms, rules, dashboards and identity.
- Legacy rule chains run in TB CE only for shadow parity until each tenant's rules are rebuilt. TB is retired after cutover.
- **Effect on migration:** the full Migration Studio, as already designed, becomes mandatory:
  - mapping every TB data class;
  - a node-type compatibility matrix for rule chains, which ADR 0011 Risk 3 says does not exist;
  - rebuilding dashboards per tenant;
  - re-provisioning device credentials;
  - CDC on TB's database.
- **Cost:** large. Today one service exists.

**Option C, the current hybrid (TB CE permanently downstream through a bridge), should be rejected.** It brings permanent dual writes, no exactly-once delivery, and two tenant and identity models.

**Recommendation: A now, with B's door kept open.**

- Keep the hexagonal ports, so a bounded context such as alarms or reporting can later be strangled out of TB.
- Concretely:
  - withdraw ADR 0019 Decision 4 and the bridge proposal;
  - restore TB CE as the ingress owner;
  - publish IOT-EE's canonical events from TB's outbound Kafka node into an IOT-EE ingestion adapter that deduplicates by event ID (ADR 0018).
- **Precondition:** gate 2 (legacy discovery) must confirm the legacy system is TB CE on PostgreSQL without a fork. If it is a fork, or uses Cassandra for telemetry, revisit.

### 3.3 Alignment with Twinfra and the licence policy

The owner directive puts IOT-EE on Twinfra. IOT-EE's own choices then collide with Twinfra's accepted platform and its Apache-2.0/MIT licence gate:

| IOT-EE choice | Issue | Twinfra equivalent or replacement |
| --- | --- | --- |
| OpenTofu (MPL), Ansible (GPL), RKE2, kube-vip, Hyper-V VMs | Duplicate platform; OpenTofu is rejected in our licence policy and Ansible is a known GPL conflict | kubeadm + Cilium on cairo-1 (ADR-0048) |
| LGTM (Grafana, Loki, Tempo, Mimir; AGPL) | Rejected in our policy | Twinfra observability (WO-07, Perses, pending) |
| HashiCorp Vault (BSL) or OpenBao | Vault is rejected; OpenBao is already Twinfra's | OpenBao (WO-08) |
| MinIO (archived; rejected in IOT-EE's own catalog) | No maintained default for WORM storage | SeaweedFS (WO-22; Object Lock conformance still unproven) |
| EMQX (BSL), Mosquitto (EPL-2.0) | BSL is rejected; EPL is outside Apache/MIT | Under Option A, **TB CE's own MQTT transport** (Apache-2.0) removes the separate broker |
| Trivy (named in the requirements addendum) | Twinfra dropped it after CVE-2026-33634 | Grype, Syft and OSV-Scanner (ADR-0049, WO-32) |
| Redpanda (BSL, conformance target) | Test-only, but still BSL | Kafka only; Strimzi (Apache-2.0) needs a licence-gate entry |
| PostgreSQL 16 + pgvector, Keycloak, APISIX, Argo CD | Already on Twinfra | Reuse: CNPG PG18 + pgvector, Keycloak, APISIX, Argo CD |

Adopting Twinfra removes about half of the 22 proposed ADRs: private cloud, Kubernetes options, deployment layers and catalog, Cilium, observability sequence, MQTT broker. IOT-EE's work narrows to **application-level** decisions. Owner decision D-2: does Twinfra's licence gate apply to IOT-EE as a product?

### 3.4 Enterprise non-functional gaps (missing in every option)

- **No targets yet:** no SLOs, RPO/RTO, capacity numbers (devices, messages per second, retention) or support model. "Enterprise grade" cannot be accepted without them.
- **No TB CE HA design.** That needs cluster mode with Kafka and the cache, plus backup and restore and the TB upgrade runbook.
- **Supply chain:** ADR 0014 is reserved but not drafted. Reuse Twinfra's ADR-0049 gate.
- **Runtime versions:**
  - Java 17 with Spring Boot 3.3 and Spring Cloud 2023.0. That Spring line is past open-source support; verify the dates.
  - TB CE 4.3.1.5 itself runs **Java 21 with Spring Boot 3.5** (seen in the spike).
  - Move to Java 21 and a supported Spring Boot line before more services are written.

## 4. Code

| # | Finding | Assessment |
| --- | --- | --- |
| C1 | `services/identity`: 58 main and 54 test Java files. Hexagonal structure, ArchUnit with planted violations, REST and gRPC over one port. | Good template. Only one query use case; no persistence, messaging, OTel or Helm chart. |
| C2 | The always-permit ABAC stub is **no longer wired** into endpoints (PR #29, `IdentityServiceConfig`). The `org.keycloak` and `com.stripe` bans now have fixtures. | The earlier gaps are fixed on the branch, but unmerged. |
| C3 | No static-analysis or coverage gate (Checkstyle, SpotBugs, JaCoCo). | Add one with the Java 21 upgrade. |
| C4 | `spec/`: a frozen 8,283-line Python reference, including M1 Migration Studio, which forbids network access by design. | Archive it behind a tag and move it out of the main tree. Otherwise it is a second source of truth. |
| C5 | `tb-extensions/manifest.yaml` is a plan that no tool reads, with `legacy_version: null`. | Fine for now. Under Option A it becomes the upgrade contract and needs tooling. |

## 5. Stories and milestones

1. **Four overlapping naming schemes** (M0–M9, PF-A/B/C with C0–C7 and C2a/C2b, Tracks A/B/C, R1–R6). Progress is hard to read. Use **one backlog**: epics with stories and acceptance criteria, like Twinfra's work orders.
2. **Migration is last (M9, after M8 Deployment Studio).** But migrating legacy customers is the product's reason to exist, and legacy discovery decides the architecture. Move **legacy discovery and one migration rehearsal to the front**, keeping production cutover last.
3. **Scope creep before a first telemetry path exists:**
   - AI across several environments;
   - document collaboration (Nextcloud and others);
   - payments;
   - device map;
   - Flowable workflows;
   - the anomaly review gate;
   - Config Studio and Deployment Studio;
   - firmware.

   Enterprise grade means reliability, security, operability and supportability, not breadth. Defer everything not needed for "migrate a tenant and run it reliably".
4. **No story has a named business owner, size or customer outcome.** The readiness review traces goals to evidence well; the backlog needs the same per story.

## 6. Migration capability: specific gaps

The governance in `legacy-migration-execution-plan.md` is strong. What is missing is ThingsBoard-specific and operational:

| # | Gap | Why it matters | Proposal |
| --- | --- | --- | --- |
| G1 | **Legacy facts unknown:** version, telemetry backend (PostgreSQL, Timescale or Cassandra), customisations or fork, tenant, device and row counts, device protocols and credential types. | Every design choice depends on them. | Gate 2: a discovery checklist answered by the legacy owner, plus an approved anonymised schema and database copy. |
| G2 | **No TB data model in the plan.** Telemetry `ts_kv` and its partitions with the key dictionary, `ts_kv_latest`, `attribute_kv`, `relation`, `device_credentials`, `rule_chain`/`rule_node`, `dashboard`, `alarm`, `audit_log`, OTA packages. Table names vary by version. | Extraction sizing and reconciliation queries need them. | Map them against the **legacy** version once known. |
| G3 | **Device credentials: "never import secrets" plus "rotate or re-enrol".** | Re-enrolling a field fleet of tank sensors is usually impossible. That blocks cutover. | Allow an **audited, owner-approved import of device credentials into OpenBao** (or keep them in TB under Option A), plus an **endpoint takeover** (DNS or IP) so devices reconnect without a firmware change. |
| G4 | **No device-traffic cutover design.** "Switch ingress in controlled steps" is not a design. | Devices talk to the legacy Mosquitto and TB endpoints. | Per-tenant routing: an MQTT bridge or mirror from legacy to new for shadowing, then switch the endpoint per tenant, with a tested rollback route. |
| G5 | **Users have no password-hash import, so everyone re-enrols.** | User experience and support load at cutover. | Decide between invitation-based re-enrolment and importing the bcrypt hashes into Keycloak (needs a hash provider; licence-check it). |
| G6 | **Bulk load "through owning services".** | Billions of telemetry rows through APIs can take weeks. | Set a throughput target; bulk `COPY` into a staging schema, then service-owned import, with partitioned checkpoints. |
| G7 | **Rule chains and dashboards.** | Under Option B these are a rebuild per tenant, and the compatibility matrix doesn't exist. | Under Option A they carry over through TB's upgrade; parity tests still apply. |

### Proposed gates before any IOT-EE deployment

0. **Hygiene:** push a WIP snapshot (S1); merge or close PR #29; archive `spec/`; freeze IOT-EE's own infrastructure layers.
1. **Decisions:** the owner chooses D-1 (Option A or B) and D-2 (licence policy). I write the ADR.
2. **Legacy discovery** (G1), with the owner or the legacy owner supplying access.
3. **Migration rehearsal on Twinfra:**
   - restore the approved copy into an isolated CNPG namespace;
   - under Option A, upgrade it to TB CE 4.3.1.x with ThingsBoard's own upgrade path;
   - measure the time;
   - reconcile counts and checksums.

   This is IOT-EE's first level-R evidence.
4. **First deployment:** TB CE 4.3.1.x and `services/identity` on Twinfra, after WO-08 (OpenBao) and with the WO-32 gate, as a single tenant.

## 7. Questions for the owner

1. **D-1:** Option A (TB CE core plus enterprise services, strangle later) or Option B (IOT-EE-native, TB retired after M9)?
2. **D-2:** Does Twinfra's Apache-2.0/MIT licence gate apply to IOT-EE?
3. **Legacy access:** who can provide the legacy TB version, a schema or anonymised database copy, device counts, protocols and credential types?
4. **Device credentials:** may they be migrated through an audited import, so the field fleet needs no re-enrolment?
5. **The 83 uncommitted changes:** may Codex push them as a WIP snapshot branch now, unmerged?
6. **Order (still open):** IOT-EE after WO-08 (recommended), or before?
