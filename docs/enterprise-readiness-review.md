# Enterprise readiness review -- traceability against the 14 product goals

Status: review document, not an ADR. Reviewed 2026-09-26 (updated the same day with the MinIO primary-source
notice and the R1-R6 follow-up roadmap) against `main`
at `3b6a479` plus the uncommitted `docs/reconcile-roadmap-and-direction`
working tree (three proposed ADRs, `cfg.schema.json` aligned to ADR
0016). Where this review and an accepted ADR disagree, the ADR wins; the
disagreement is listed as **conflicting** and needs an owner decision.

## How to read the tables

**Evidence levels** (strongest last). A row's status follows its
strongest evidence:

| Tag | Meaning |
| --- | --- |
| **D** | Documented intent only: an ADR, requirement or plan says it should exist |
| **C** | Code exists in the repository |
| **T** | Automated tests exercise it locally |
| **CI** | Those tests ran green in GitHub Actions |
| **R** | Verified in a real, representative environment |

**Status values:** *implemented/tested* (C+T at least, CI where noted),
*partial* (some of the requirement has C/T, the rest is D only),
*planned* (D only, not blocked), *blocked* (cannot proceed or be
verified without an external input), *conflicting* (two sources in the
repository disagree, or a stated default no longer holds).

**Milestones** use the proposed naming: M0-M9 are product capabilities
(M9 = final legacy import and cutover); **PF** is Platform Foundation
(PF-A/B/C; C0-C7 are PF-C steps).

**Nothing in this repository is verified at level R**, except that Layer
0 host preparation completed once on the owner's Hyper-V host (console
output reported by the owner, not independently checked). No claim of
ThingsBoard EE/PE parity, compliance certification (for example ISO
27001, SOC 2, IEC 62443) or production readiness is made or implied.

## Summary

| # | Goal | Overall status | Strongest evidence |
| --- | --- | --- | --- |
| 1 | Full IoT business platform | Planned | D (spec slices C+T in Python, not the platform) |
| 2 | Enterprise capability toward TB EE workflows | Planned; parity unassessed | D |
| 3 | Technology/tool flexibility | Partial; one ADR-required ban missing | C+T+CI (one service) |
| 4 | Low-friction TB CE upgrades | Planned | D (manifest draft) |
| 5 | Hexagonal architecture and clean code | Implemented/tested for `services/identity` only | C+T+CI |
| 6 | Pluggable infrastructure and tools | Partial; one default conflicting | C+T (bans), D (adapters) |
| 7 | On-prem and cloud deployment | Partial (lab-profile IaC only), cloud planned | C+CI static |
| 8 | Staged private cloud on bare metal | Conflicting (only a Hyper-V lab profile exists; bare-metal Layer 0 planned) | C+CI static, R for host prep only |
| 9 | LGTM as a separately deployable, validated step | Planned (own Layer 3 defined, empty) | D |
| 10 | Java contracts in domain/application; frameworks at edges | Implemented/tested for `services/identity` only | C+T+CI |
| 11 | Multiple AI environments | Planned; not designed | D (single RAG path) |
| 12 | DDD, event-driven, microservices, enterprise controls | Partial | C+T+CI (autonomy, boundaries); D (events) |
| 13 | Legacy and modern device support | Conflicting / planned | D |
| 14 | Enterprise-usable OSS defaults, commercial alternatives named | Conflicting (several defaults not OSI open source) | D |

---

## 1. Full IoT business platform

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Tenant, device, asset/tank hierarchy, telemetry, alarms, commands, reports as platform services | D: ADR 0011 Decision 1 (bounded contexts), `docs/architecture.md`. C+T (Python spec only): `spec/domain_core`, `spec/ingestion`, `spec/reporting`. C+T+CI (Java): `services/identity` walking skeleton (one query use case) | Planned | Any Java business service beyond the identity skeleton; persistence; ingestion | M2-M4 (platform), after PF-C | Per service: create tenant -> device -> tank, ingest synthetic telemetry, read tenant-scoped summary; negative cross-tenant test (addendum list) |
| Operator/device command service (desired vs reported, TTL, acks) | D: addendum "Tenant operators and secure device property updates". C+T (spec): `spec/domain_core` command domain | Planned | Java service, broker delivery, genuine device acknowledgment | M2, M3 | Command accepted -> delivered -> acknowledged; expired/stale/duplicate commands rejected; accepted != applied |
| Reports | D: ADR 0005; C+T (spec): `spec/reporting` read-model | Planned | Java read-model, report definitions from legacy inventory | M4, M9 (parity) | Reconciled report matches approved legacy output within tolerance |

## 2. Enterprise capability extending TB CE toward required TB EE workflows

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| List of the TB EE/PE workflows the business actually needs | D: addendum requires a TB CE inventory before a parity matrix; `docs/tb-ce-inventory.md` notes some features are PE/Cloud-only (integration framework, section 2.2) | **Blocked** | A version-specific matrix: required workflow -> TB CE vX / TB PE vX behaviour -> platform component -> evidence. Needs the legacy TB version (`legacy_version: null` in `tb-extensions/manifest.yaml`) and owner input on required workflows | PF-A follow-up, then M1/M3 | Matrix reviewed and approved by the owner; each row links to a test |
| Platform services for what TB CE lacks (RBAC/ABAC beyond TB tenants, evidence, billing, Deployment/Migration Studio, integration-style connectors) | D: ADR 0011 Decision 2 | Planned | Every service | M1-M8 | Per-capability acceptance tests in `docs/test-plan.md` |
| **No parity claim** | This review | -- | -- | -- | No document may state "EE parity" or "EE-equivalent" without the matrix above |

## 3. Technology/tool flexibility

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Transport swap (REST <-> gRPC) without touching business logic | C+T+CI: `services/identity` `adapter.in.rest` and `adapter.in.grpc` over one `port.in`; `TransportQueryEquivalenceTest`; ArchUnit rules forbid adapter cross-dependencies (`Violating*Adapter*` fixtures) | Implemented/tested (one service, one query) | A command path; a second service | PF-C C6 | Same command via REST and gRPC reaches the same handler; adapters share no code |
| Broker swap (Kafka <-> Redpanda) | D: ADR 0018 Decision 5 (CI conformance on both) | Planned | Messaging adapter and its dual-broker CI run | PF-C C5 | Same suite green on Kafka and Redpanda |
| IAM provider swap | D: ADR 0016 Decisions 3 and 5; ADR 0017 Decision 4 requires an `org.keycloak..` ban. **Not in code:** `services/identity`'s `VENDOR_SDK_DENYLIST` covers `software.amazon.awssdk..`, `io.minio..`, `org.apache.kafka..`, `io.debezium..`, `org.thingsboard..` only | Conflicting (ADR requires a ban the code lacks) | `org.keycloak..` added to the denylist with a planted-violation test; token-verification port and adapter | PF-C C3 | Provider swap in tests is configuration-only |
| Database swap | D: ADR 0017 Decision 5 (PostgreSQL adapter only; Oracle is port-level optionality, not a config switch) | Planned, deliberately limited | -- | PF-C C4 | Not a runtime switch; out of scope until funded |

## 4. Low-friction TB CE version upgrades

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Thin, declared customization set | D: ADR 0011 Decision 8; `tb-extensions/manifest.yaml` (draft, pinned 4.3.1.5 on the 4.3.1.x line; no tooling reads it; no custom rule nodes) | Planned | Tooling that applies the manifest; any custom node | PF-A follow-up, M3 | Upgrade 4.3.1.x patch in a test environment by re-applying the manifest only; rule-chain regression suite passes |
| TB CE runs unmodified, consuming platform Kafka | D: ADR 0019 Decision 4 | **Blocked** | No running TB CE; `docs/track-c-execution-plan.md` 2.3 lists it as unverified | M3 | TB CE 4.3.1.x consumes a platform topic into its rule engine without source changes |
| Legacy TB version known | `legacy_version: null` | **Blocked** | Authorized access to the legacy system | Before M1 inventory | Version recorded with evidence |

## 5. Hexagonal architecture and clean code

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Inward-only dependencies, ports and adapters | C+T+CI: `IdentityHexagonalArchitectureRulesTest` with negative fixtures (`ViolatingDomainDependsOnOuterRing`, `ViolatingPortDependsOnApplication`, `ViolatingApplicationDependsOnAdapter`, ...); CI run #103 on C1 | Implemented/tested (`services/identity`) | Only one service exists; persistence and messaging adapters not yet built, so those rules are vacuously satisfied | PF-C C1 (done), every later service | Each new service ships the same rule set; each rule has a planted-violation test |
| Clean-code controls (static analysis, formatting, coverage thresholds) | None found (no Checkstyle/SpotBugs/PMD/Sonar/JaCoCo gate in `pom.xml`) | Planned, no decision | Tool choice and CI gate | PF-C (add to C2 or its own step) | CI fails on a planted violation |

## 6. Pluggable infrastructure and tools

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Vendor SDKs confined to their adapter package | C+T+CI: per-adapter ArchUnit bans in `services/identity` (`ViolatingVendorSdkUsageClass`, `ViolatingPersistenceProviderUsageClass`, `FakeKafkaProducerClass` fixtures) | Implemented/tested (bans); no real adapter exists | Real adapters behind each port | PF-C C3-C5 | Ban tests plus one real adapter per port |
| No shared runtime libraries | C+CI: Maven Enforcer `bannedDependencies` in `pom.xml` excludes `com.iotee.platform:*` at compile/runtime scope | Implemented/tested | -- | PF-B (done) | Build fails when a service depends on another project module at runtime |
| Named swappable components | D: `CLAUDE.md` "Plug-and-play". Previously listed TB CE as "replaceable" and RabbitMQ as a Kafka replacement, contradicting ADR 0011 Decision 2 and ADR 0018 Decision 5 -- corrected in this change | **Conflicting (corrected)** | -- | -- | -- |
| WORM storage default MinIO | D: ADR 0007, `docs/architecture.md`. The `minio/minio` GitHub repository was archived by its owner on 2026-04-25 and is read-only; its README states "THIS REPOSITORY IS NO LONGER MAINTAINED" and points users to MinIO's AIStor Free and AIStor Enterprise editions. Source remains AGPLv3 ([primary source](https://github.com/minio/minio)). The open-source default the ADRs name therefore receives no further upstream fixes | **Conflicting** | Owner decision on the on-prem WORM default; S3-compatible alternatives need their own Object Lock conformance run | M6 | ADR 0010's WORM conformance suite passes against the chosen on-prem store |

## 7. On-prem and cloud deployment

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| On-prem Kubernetes | C+CI (static only): `deploy/` Layers 0-2 (OpenTofu, Ansible, Kustomize); `infra.yml` runs `tofu validate`, Ansible syntax check, PowerShell parse, kubeconform | Partial | VMs not created, cluster not bootstrapped (`deploy/README.md` real-host table) | PF-C C7, M8 | Layers 0-2 applied on the host; `health.yml` green; smoke LoadBalancer service answers |
| Application deployment (Helm/Argo CD) | D: PF-C C7 | Planned | Chart, Argo CD Application | PF-C C7 | Chart installs on k3d in CI and renders unchanged for EKS/AKS/GKE values |
| Cloud (EKS/AKS/GKE) | D: ADR 0011 Decision 7; ADR 0009 plan/validate-only | Planned | Any cloud Layer 0; cloud account | M8 | Same chart deployed to one managed cluster in an isolated account; rollback rehearsed |

## 8. Staged private-cloud setup on bare metal

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Staged layers, each consuming only the previous layer's outputs | C+CI: `deploy/00-infra`, `deploy/01-k8s-engine`, `deploy/02-cluster-addons`; `ansible_inventory_ini` output matches the committed inventory (checked offline) | Implemented as code; not run past Layer 0 host prep | Layers 0-2 applied | PF-C C7 | One layer at a time, each recorded in `deploy/README.md` |
| **Bare metal** | The only Layer 0 is `private-hyperv`: Hyper-V VMs on one Windows host behind NAT (draft ADR `XXXX-proposed-private-cloud-infrastructure.md`) | **Conflicting** | Decide whether "bare metal" means (a) Linux installed directly on servers (needs a new Layer 0, e.g. PXE/ISO provisioning) or (b) VMs on the owner's own hardware (current design). No bare-metal Layer 0 exists | Owner decision, then PF-C C7 | For (a): a bare-metal Layer 0 emits the same inventory contract and Layer 1 runs unchanged |
| Layer 0 host preparation | R (owner-reported): `prep-hyperv-host.ps1` completed once after PR #28 fixes | Partial | Independent check of the template (size, read-only flag); VM apply | PF-C C7 | `Get-Item` on the template shows read-only and expected size; `tofu apply` creates 3 VMs reachable over SSH |

## 9. LGTM as a separately deployable and validated step

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| LGTM is the enterprise trace/log plane | D: ADR 0015 | Planned | Everything below | PF-C C2 | -- |
| Installed as its own deploy step, not inside Layer 1 | D: Layer 1 README excludes add-ons; no LGTM layer or manifest exists in `deploy/` | Planned | A separate `deploy/` layer or add-on with its own validation | PF-C C2 (dev K3s profile), C7 | LGTM installs and uninstalls independently of the apps; its own smoke test passes |
| Dual-ID propagation | D: ADR 0015; C+T: correlation-ID handling in `services/identity` (`CorrelationIdContextTest`); no OTel yet | Partial | OTel instrumentation, trace export | PF-C C2 | One request's logs and spans carry `traceparent` and `X-Correlation-ID` in separate slots (C2 exit criterion) |

## 10. Java contracts in domain/application; frameworks at adapters and composition roots

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| No Spring/servlet/JAX-RS/persistence-provider imports in `domain`, `rbac`, `port`, `application` | C+T+CI: `IdentityFrameworkFreedomArchitectureRulesTest` with `Violating*FrameworkUsageClass` fixtures | Implemented/tested (`services/identity`) | Other services | PF-C, every service | Planted framework import in `domain` fails the build |
| Spring wiring only in `config` | C+T+CI: hexagonal rules; `IdentityServiceConfig`, `GrpcServerLifecycle` in `config` | Implemented/tested | -- | PF-C C1 (done) | As above |
| `io.grpc` only in `adapter.in.grpc`, Spring Web only in `adapter.in.rest` | C+T+CI: `ViolatingGrpcUseOutsideGrpcAdapter` and related fixtures | Implemented/tested | -- | PF-C C1 (done) | As above |
| `jakarta.persistence` annotations allowed in domain | D: `CLAUDE.md` permits them | Note | Allowing JPA annotations in domain is a deliberate relaxation of goal 10; confirm it is intended | Owner decision | -- |

## 11. Integration with multiple AI environments

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| RAG over redacted, windowed telemetry | D: ADR 0019 (Flink -> redaction -> pgvector -> RAG agent, core/AI cluster only); Flink versions managed in `pom.xml` | Planned | Flink job, redaction stage, vector store, agent | After PF-C C5 | Redaction test: no PII/secret reaches embeddings |
| **Multiple** AI environments (for example on-prem model runtime and several cloud model providers) behind one port | None. No ADR names a model-provider port, provider list, data-residency rule or evaluation approach | **Planned, undesigned** | An ADR: model-provider port, allowed providers per deployment profile, tenant data boundaries, audit | New ADR, then after C5 | Same RAG request served by two providers selected by configuration; tenant data never crosses a disallowed boundary |

## 12. DDD, event-driven design, microservices, enterprise engineering controls

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| Bounded contexts, each owning its data | D: `docs/architecture.md`, ADR 0011 Decision 1; C+T: sibling-context isolation rule in `IdentityArchitectureRulesTest` | Partial | Second context to isolate from | M2+ | Cross-context database access fails a rule |
| Microservice autonomy | C+T+CI: ADR 0013 refactor, Enforcer ban, `FakeRetiredCommonRbacClass` fixture | Implemented/tested | -- | PF-B (done) | -- |
| Event-driven: outbox, idempotent consumers, versioned envelope | C+T+CI: `contracts/events/v1/envelope.proto`, `EnvelopeSerializationRoundTripTest`. D: ADR 0018 | Partial | Outbox, relay, consumers | PF-C C5 | Redelivery produces no second effect |
| PR + CI + human review, no self-approval | D: `CLAUDE.md`; practice: PRs #20-#28 merged by the owner | Implemented (process) | Branch protection settings not verified from here | -- | Branch protection requires review and green checks |
| Supply-chain scanning, SBOM, signing | D: ADR 0014 reserved, not drafted | Planned | Everything | Post-PF | CI fails on a planted vulnerable dependency |
| Zero-trust mTLS, policy engine | D: `docs/track-c-execution-plan.md` 2.2 "Undecided" | Planned, undesigned | ADR | New ADR | -- |

## 13. Legacy and modern device support

| Requirement | Repository evidence | Status | Missing proof | Milestone | Acceptance test |
| --- | --- | --- | --- | --- | --- |
| MQTT devices (modern) | D: ADR 0004 (topics), ADR 0019 (edge MQTT -> tier-1 buffer -> Kafka); C+T (spec): `spec/ingestion` | Planned | Broker, ingestion service, tier-1 buffer design | M3 | Synthetic device publishes over mTLS; event reaches Kafka once, tenant-scoped |
| Legacy devices (non-MQTT protocols, existing fleet) | D: ADR 0011 Decision 2 relied on TB CE transports (MQTT/HTTP/CoAP); ADR 0019 Decision 4 superseded TB CE as ingress owner, and no replacement path for HTTP/CoAP or other protocols is designed. Addendum: unknown protocols may need reviewed adapters | **Conflicting** | Inventory of the legacy fleet's protocols and firmware; an ingestion ADR covering non-MQTT devices (protocol adapters or TB CE transports feeding the buffer) | Before M3 | Representative legacy device (or a recorded capture) ingests through the chosen path with parity to the legacy system |
| Device credentials and ACLs | D: addendum (mTLS where supported, per-device broker ACLs) | Planned | Broker and credential service | M3 | Device A cannot publish/subscribe to device B's topics |

## 14. Enterprise-usable open-source defaults with commercial alternatives identified

Licences below are as reported by each project's own site or public
notices at review time; **re-verify at every version pin**, since
several changed recently.

| Component (default) | Licence reported | Enterprise concern | Commercial or alternative option | Status |
| --- | --- | --- | --- | --- |
| ThingsBoard CE | Apache 2.0 | PE/Cloud-only features (integrations) | ThingsBoard PE (commercial) | OK as default; PE is the commercial alternative |
| Kafka / Flink / APISIX / Keycloak / Istio / RKE2 / PostgreSQL + pgvector | Apache 2.0 / Apache 2.0 / Apache 2.0 / Apache 2.0 / Apache 2.0 / Apache 2.0 / PostgreSQL | -- | Confluent, managed Kafka/Flink, cloud IdPs, managed PostgreSQL | OK |
| OpenTofu | MPL 2.0 | -- | Terraform (BSL, HashiCorp) | OK (repo uses OpenTofu) |
| **HashiCorp Vault** (addendum: initial secrets backend) | Business Source License since 2023 (not OSI open source) | Licence terms restrict some commercial offerings | OpenBao (MPL 2.0 fork); Vault Enterprise; cloud KMS/secret managers | **Conflicting** with goal 14: needs an owner decision on the default |
| **Redpanda** (ADR 0018 CI conformance target) | Community edition under BSL | Source-available, not OSI open source | Redpanda Enterprise | OK as a *test* target; must not become the default without a licence review |
| **EMQX** (ADR 0011 broker option) | BSL 1.1 from 5.9 (May 2025) | Not OSI open source from 5.9 | EMQX Enterprise | Should be listed as source-available, not open source |
| Mosquitto (ADR 0011 broker option) | EPL 2.0 / EDL | Clustering limits for HA | HiveMQ (commercial; CE is open source), EMQX | OK as default for lab |
| **MinIO** (WORM default on-prem) | AGPLv3 source; repository archived 2026-04-25, "no longer maintained" | No upstream security fixes for the open-source repository | MinIO AIStor Free / AIStor Enterprise (MinIO's named successors; licence terms to review); other S3-compatible stores with Object Lock | **Conflicting** (see goal 6) |
| Grafana / Loki / Tempo / Mimir (LGTM) | AGPLv3 for current releases (**no version pinned yet**; verify the licence of the exact versions when Layer 3 pins them) | AGPL obligations if modified and offered as a service | Grafana Enterprise / Grafana Cloud | OK; record the AGPL obligation |
| Elasticsearch **client libraries** managed in `pom.xml` (no Elasticsearch server is pinned or deployed) | `co.elastic.clients:elasticsearch-java`, `org.elasticsearch.client:elasticsearch-rest-client` and `-sniffer` **8.13.4** (Spring Boot 3.3.4 BOM): **Apache-2.0**. `flink-connector-elasticsearch7` 3.1.0 pulls `elasticsearch-rest-high-level-client` and the `org.elasticsearch:elasticsearch` server jar at **7.10.2**: Apache-2.0 (the last Apache-2.0 line; 7.11+ is SSPL/ELv2). `flink-connector-elasticsearch8` 3.1.0 declares `elasticsearch-java` 8.12.1 (Apache-2.0), overridden to 8.13.4 by the BOM. See note below | The earlier "triple licence including AGPLv3" statement was wrong for these versions: the AGPL option exists only for the Elasticsearch **server** from 8.16.0; 8.13.x server is SSPL-1.0 / Elastic License 2.0, neither OSI open source. Any future server choice needs its own review. Also: the BOM forces the 8.13.4 low-level REST client under the ES7 connector's 7.10.2 high-level client (mixed majors) -- a compatibility risk to test in the first job module | Elastic commercial subscriptions / Elastic Cloud; OpenSearch (Apache-2.0) | Clients: licence checked (Apache-2.0). No accepted ADR uses Elasticsearch; server licence depends on the version chosen |
| Stripe (payment adapter) | Commercial SaaS | Behind `PaymentGateway` port, monetization default-off | Other payment providers behind the same port | OK (commercial, optional) |

Missing proof for goal 14: a maintained `docs/` table of every default
with its pinned version, licence and commercial alternative, re-checked
at each pin; and a CI licence scan (part of the ADR 0014 scope).

---

## Deployment update (2026-09-26, after this review)

The deployment plan was corrected in the same working tree
(`docs/adr/XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md`).
Effect on the rows above:

- **Goals 7-9:** `deploy/` now has five separately validated layers:
  0 provisioning (OpenTofu default; Terraform optional compatibility, BSL),
  1 OS hardening + Kubernetes (Ansible), 2 add-ons
  (`deploy/02-cluster-addons`, formerly `deploy/k8s`), 3 observability
  (`deploy/03-observability`, planned, empty) and 4 application release
  (`deploy/04-apps`, Helm + Argo CD, planned). **No Helm chart exists.**
  The Hyper-V target is labelled the `lab-hyperv-single-host` profile;
  cloud profiles are `planned`. Nothing was applied.
- **Layer 1 inventory:** the real inventory is git-ignored; only an example
  with RFC 5737 addresses is committed. `validate-inventory.yml` runs
  before any host is contacted, with five negative fixtures in CI. No
  `-e` extra vars for privileged switches (heal uses tags plus typed
  confirmation; the Pod Security exemption list is guarded).
- **Goals 6 and 14:** a curated tool catalog (`deploy/catalog/tools.yaml`)
  records licence class, role, pinned versions, capabilities, commercial
  alternatives and four checks per tool; deployment profiles
  (`deploy/profiles/`) select only catalog tools and carry vault and
  storage profiles; `deploy/catalog/validate.py` and 27 unit tests enforce
  the rules in CI. OpenBao is the **proposed** secrets default; HashiCorp
  Vault is optional compatibility (BSL) with explicit editions; Spring
  Vault is a client only. MinIO is `rejected` in the catalog. **No tool is
  approved yet**, so no profile can be validated or approved.
- **R5 (tool responsibilities):** answered by the layer table: OpenTofu
  owns Layer 0, Ansible Layer 1, Kustomize Layer 2 (Helm vs Kustomize for
  add-ons still open), Helm + Argo CD Layer 4.

## Follow-up roadmap: requirements added after the 14-goal review

These six requirements were stated by the owner after the goal review.
Some already appear in the repository; none is fully reconciled into
the roadmap by an accepted ADR. **Stage assignments below are proposals
for owner confirmation**, following the addendum's delivery sequence
(M2 identity/permissions, M4 consoles and integration, M7 monetization,
M8 deployment) and the PF-C step that each depends on. Nothing here is
implemented beyond what the "Already in the repository" column says.

| # | Requirement | Already in the repository | Reconciled status | Proposed stage | Acceptance test | Open inputs |
| --- | --- | --- | --- | --- | --- | --- |
| R1 | **Rule-based authorization plus ABAC**: role/permission rules evaluated together with attributes (tenant, resource ownership, hierarchy scope, environment) | D: ADR 0011 Decision 5 (RBAC + ABAC), ADR 0016 Decision 6 (2-tier RBAC, ABAC tenant scope), addendum (effective permissions, no self-escalation). C+T: `services/identity` `RbacRegistry`, `AbacContext` **stub that always permits** | Partial: RBAC registry exists; ABAC is a stub; no decision on how rules are expressed or evaluated (in-code policy vs a policy engine such as OPA -- `docs/track-c-execution-plan.md` 2.2 lists OPA as undecided) | PF-C C3 (replace the stub, tenant ABAC), M2 (full rule set, hierarchy scope), M4 (Operators page shows effective permissions) | Deny-by-default; cross-tenant, unassigned-device and excess-delegation requests rejected; the stub cannot reach a tenant-facing endpoint (ArchUnit or test) | Policy language/engine; who authors rules (system admin only, or tenant admin within scope) |
| R2 | **SSO/JWT with refresh-token rotation and OTP** | D: addendum (OIDC authorization code + PKCE, HttpOnly BFF cookies, CSRF, short token lifetimes, MFA for administrators, step-up for sensitive operations, separate admin/operator audiences); ADR 0016 (IAM-agnostic OIDC, services re-verify JWTs). **Refresh-token rotation and OTP are not mentioned anywhere** | Partial (SSO/JWT/MFA intent); **new** (rotation, OTP) | PF-C C3 (JWT verification port), M4 (BFF sessions, refresh rotation with reuse detection, OTP/MFA enrolment and step-up) | Rotated refresh token invalidates its predecessor; reuse of an old refresh token revokes the session family; admin login without a second factor rejected; operator token rejected by admin APIs | OTP form (TOTP app, SMS, email) and which roles require it; whether rotation is the IdP's job or the BFF's |
| R3 | **Payment-provider boundaries** | D: ADR 0018 Decision 6 (`PaymentGateway` port; Stripe first); ADR 0017 Decision 4 requires a `com.stripe..` ban, **which is not yet in `services/identity`'s denylist**; ADR 0011 Decision 6 and ADR 0008 (monetization optional, default-off, consumes finalized usage only, never blocks telemetry/alarms/commands). No port or adapter code yet | Planned; boundary rules decided; required ArchUnit ban missing | Add `com.stripe..` to the denylist now (PF-C C1 follow-up); port and adapter in M7 (after PF-C C5 usage events) | No non-adapter class imports a payment SDK (ArchUnit); billing outage leaves telemetry/alarm/command paths unaffected; no card data stored or logged (tokens only) | Which providers after Stripe; PCI scope boundary (hosted payment pages vs direct card handling) |
| R4 | **Backend-first Config Studio** | **Not found in the repository.** Related: addendum "Version, validate, preview, approve, and roll back configurations" (Migration Studio, M1); `contracts/cfg/cfg.schema.json` (per-service `cfg.yaml`); ADR 0011 Decision 8 (`cfg.yaml`-driven tool swaps) | **New, undefined** | Needs its own ADR first; proposed after PF-C C3 (it needs identity and audit), backend APIs before any UI | Config change goes draft -> validate -> preview -> approve -> apply -> rollback, all through APIs with audit, no UI required; invalid config rejected by schema | Scope: platform/tool configuration, tenant configuration, device/profile configuration, or all; relation to Migration Studio's configuration lifecycle and Deployment Studio |
| R5 | **Terraform/Ansible/Helm responsibilities** | D+C: ADR 0011 Decision 3 (Ansible + Terraform/OpenTofu + Helm + Argo CD); draft `XXXX-proposed-private-cloud-infrastructure.md` and `deploy/`: OpenTofu = Layer 0 VMs, Ansible = Layer 1 OS + RKE2 only, **Kustomize** (not Helm) = Layer 2 add-ons; PF-C C7 plans Helm + Argo CD for applications; ADR 0009 (Deployment Studio plan/validate-only) | Partial; responsibilities split across documents, and Layer 2 uses Kustomize while ADR 0011 names Helm | PF-C C7 (write the responsibility matrix into the private-cloud ADR before it merges), M8 (Deployment Studio drives the same tools) | Each tool owns one layer; no layer's tool changes another layer's resources; `deploy/` CI checks each layer separately (exists for Layers 0-2) | Whether Layer 2 add-ons stay Kustomize or move to Helm; whether Argo CD also owns add-ons |
| R6 | **System-admin-only grants for VM environment-admin channels** | D: proposed `XXXX-proposed-roles-and-privileged-environment-access.md` Decision 2; ADR 0011 Decisions 4-5 (bastion channel) | Decided in a proposed ADR; not implemented | M2 (grant model and audit), M8 (Deployment Studio / environment channels) | Tenant admin, system operator and self-grants rejected; revoked grant ends access; every grant and revocation audited | Default expiry; whether revocation terminates open sessions |

## Corrections made in this change

- `CLAUDE.md` "Plug-and-play infrastructure": TB CE described as
  "replaceable" (contradicts ADR 0011 Decision 2: upgradeable, not
  replaceable); RabbitMQ named as a Kafka replacement (contradicts ADR
  0018 Decision 5: Kafka-protocol brokers only, conformance on Kafka and
  Redpanda); every component described as already "an interchangeable
  plugin behind an abstract contract" although only the vendor bans and
  one service exist; CDC/Debezium named with no ADR. Rewritten as design
  intent with its enforcement status.
- `README.md`: added explicit "no TB EE/PE parity and no compliance
  certification is claimed"; stated that legacy (non-MQTT) device
  support and multiple AI environments are undesigned; marked licence
  concerns on Vault, EMQX and MinIO defaults; pointed to this review.

## Unresolved inputs (owner decisions or external access needed)

1. The TB EE/PE workflows the business requires, and the legacy TB
   version (goal 2, goal 4).
2. "Bare metal": servers without a hypervisor, or VMs on owned hardware
   (goal 8).
3. On-prem WORM default now that the `minio/minio` repository is archived
   and no longer maintained (since 2026-04-25) (goals 6, 14).
4. Secrets default: HashiCorp Vault (BSL) or OpenBao (MPL) (goal 14).
5. Which AI environments/providers, and data-residency rules per
   deployment profile (goal 11).
6. Legacy device protocols and the ingestion path for non-MQTT devices
   (goal 13).
7. Clean-code gate tooling (goal 5) and whether `jakarta.persistence`
   annotations in domain code are intended (goal 10).
8. Whether branch protection enforces review and green checks (goal 12);
   not visible from the authoring environment.
9. The inputs listed per row in "Follow-up roadmap" (R1-R6), including
   R4 Config Studio's scope.

## Code gap found during this review (not fixed here)

`services/identity`'s `VENDOR_SDK_DENYLIST`
(`IdentityFrameworkFreedomArchitectureRulesTest`) omits `org.keycloak..`
and `com.stripe..`, which ADR 0017 Decision 4 requires. Adding both, each
with a planted-violation fixture, is a small PF-C C1 follow-up; it is
left out of this docs change to keep scope narrow.

## Sources (licence and status notices, checked 2026-09-26)

- Elasticsearch versions and licences (read from the upstream repositories at the exact tags, 2026-09-27):
  Spring Boot `v3.3.4` `spring-boot-dependencies/build.gradle` (`library("Elasticsearch Client", "8.13.4")`: elasticsearch-rest-client, elasticsearch-rest-client-sniffer, elasticsearch-java);
  `elastic/elasticsearch-java` `v8.13.4` (`LICENSE.txt` and published POM: Apache-2.0);
  `elastic/elasticsearch` `v8.13.4` `client/rest/build.gradle` and `client/sniffer/build.gradle` (Apache-2.0) and `LICENSE.txt` (server default SSPL-1.0 / ELv2);
  `v8.15.0` `LICENSE.txt` (SSPL-1.0 / ELv2) versus `v8.16.0` `LICENSE.txt` (AGPL-3.0-only / SSPL-1.0 / ELv2);
  `v7.10.2` `LICENSE.txt` (default Apache-2.0) versus `v7.11.0` (SSPL-1.0 / ELv2);
  `apache/flink-connector-elasticsearch` `v3.1.0` module POMs (`elasticsearch.version` 7.10.2 for elasticsearch7/base, 8.12.1 for elasticsearch8).
  Caveat: the 3.1.0-1.20 artifact is assumed to be built from the `v3.1.0` source tag; Maven Central POMs were not reachable from the review environment.

- EMQX adopts BSL from 5.9: https://www.emqx.com/en/news/emqx-adopts-business-source-license and https://github.com/emqx/emqx/discussions/15163
- MinIO repository notice (primary source; archived 2026-04-25, "THIS REPOSITORY IS NO LONGER MAINTAINED"): https://github.com/minio/minio
- HashiCorp Vault licence change (BSL, 2023) and OpenBao: not re-fetched in this review; verify at pin time.
