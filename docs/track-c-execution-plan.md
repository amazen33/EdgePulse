# Track C (PF-C) execution plan

Status: proposed -- living planning document, not an ADR. Track C is
stage PF-C of Platform Foundation (proposed milestone-naming ADR); it is
not milestone M9, which remains the final legacy import and cutover. It sequences work that
ADRs 0015-0019 already decide; where this plan and an ADR disagree, the
ADR wins. Drafted 2026-09-25 against `main` at `9801589` and the ADR
numbering branch `docs/adr-assign-numbers` (`8d9d202`, not yet merged).

## 1. Scope and inputs

Inputs: the CTO strategic brief for Track C (then labelled "M9 -> Track C"; now PF-C) (hexagonal core,
IAM-agnostic OIDC, event-driven metering, Flink-to-RAG, tiered brokers,
edge-to-cloud deployment), and the ratified Track C ADRs:

| ADR | Decides |
| --- | --- |
| 0015 observability authority | LGTM/OTel is the enterprise plane; `traceparent` + `X-Correlation-ID` carried together, never merged |
| 0016 tenancy and identity | Pooled `tenant_id` + Postgres RLS (`SET LOCAL app.tenant_id`); IAM-agnostic OIDC; service is the trust boundary; 2-tier RBAC |
| 0017 hexagonal conventions | `domain` / `application` / `port.in` / `port.out` / `adapter.*` / `config`; dual REST+gRPC transport; per-adapter vendor bans; Postgres adapter only |
| 0018 events and metering | Transactional outbox + relay; idempotent consumers; `usage-event v1`; broker-swap contract; Kafka + Redpanda CI conformance; `PaymentGateway` port |
| 0019 streaming and RAG | Flink as semantic synthesizer (core/AI cluster, never edge); mandatory redaction; pgvector in production, ChromaDB dev/K3s only; TB CE downstream of Kafka |

## 2. Assessment of the brief

The brief is coherent: one hexagonal mechanism (port + single adapter +
ArchUnit vendor ban) delivers every swap it asks for -- database, broker,
IAM provider, payment provider, transport. One event backbone feeds
metering, Flink/RAG, and TB CE's rule engine; the dual-ID propagation of
ADR 0015 is what makes that backbone traceable end to end.

### 2.1 Brief vs. ratified decisions (the ADRs govern)

| Brief | Ratified | Consequence |
| --- | --- | --- |
| Hot-swap Postgres/Oracle via JPA/Hibernate/jOOQ | Postgres adapter only; Oracle is port-level optionality (ADR 0017 Decision 5) | RLS and pgvector are Postgres-specific; an Oracle adapter is a funded project, not a config switch. "Swap" means build/deploy time, never runtime |
| ChromaDB as the vector store | pgvector in production; ChromaDB dev/K3s only (ADR 0019 Decision 5) | One database engine to operate and secure |
| Kafka/Pulsar | CI conformance on Kafka + Redpanda (ADR 0018 Decision 5) | Pulsar is not Kafka-protocol-native; supporting it needs its own adapter, conformance run, and decision |

### 2.2 Gaps -- no ADR yet

| Requirement from the brief | Current state |
| --- | --- |
| Zero Trust: mTLS between services, OPA policy | Undecided |
| Tiered brokers: edge MQTT buffer -> Kafka | Tier-1 buffer not designed (ADR 0011 Risk 6; ADR 0019 open items) |
| Feature toggles: operation off for tenants, on for Product (system) Operators | Needs its own ADR; must stay out of the billing path (ADR 0011 Decision 6; ADR 0018 "Conflicts") |
| OWASP / secure by design | No baseline ADR; ADR 0014 (supply-chain scanning) is reserved and covers only part |
| Edge-to-cloud deployment (K3s -> RKE2/OKD/optional OpenShift -> EKS/GKE/AKS) | Private-cloud RKE2 lab part drafted (`XXXX-proposed-private-cloud-infrastructure.md`, `deploy/` Layers 0-2). OKD is a proposed open-source alternative; OpenShift Container Platform is an optional commercial/support profile. Neither has an installation profile or conformance result. Cloud and edge profiles also need verification. Restricted SCC/non-root arbitrary-UID behavior must constrain images from the first chart (`XXXX-proposed-kubernetes-options-and-platform-tool-roles.md`). |
| Disposable Migration Studio (SQLGlot/Calcite, rule-node and BIRT mapping) | Explicitly deferred to its own ADR (ADR 0019 open items) |

### 2.3 Blocked external verifications (blocked, not passed)

- Direct TB CE v4.3.1.5 subscription to platform-owned Kafka topics is
  unavailable in CE; the synthetic REST-to-rule-engine path was verified
  in `docs/spikes/tb-ce-kafka-rule-engine-spike.md`. The proposed
  external Kafka-to-CE bridge (`docs/adr/XXXX-proposed-tb-ce-kafka-bridge.md`)
  has not been implemented or tested end to end. Migration Studio's
  rule-node mapping target still needs source-specific verification.
- TB CE v4.3.1.5 native OTel trace emission: unverified (ADR 0015 open
  questions).

## 3. Entry conditions and progress (updated 2026-09-25)

C0 gate, as it stood when this plan was drafted, and what closed it:

| Condition | Status |
| --- | --- |
| ADRs 0015-0019 numbered and accepted | Done: PR #19 (numbers, `331bf89`) and PR #20 (accepted, `bd8c98e`) |
| `main` green in CI after PRs #16-#18 | Done: PRs #20, #21 and #23 each passed CI on top of it |
| `CLAUDE.md` intact | Done: the truncated working copy was discarded; the committed file is authoritative |

Progress against section 4:

| Step | Status |
| --- | --- |
| C0 | Done |
| C1 | Done: PR #21 (`8d95e3c`), CI run #103 green on `878f568` |
| C2 | Next |
| C3-C7 | Not started |

Outside the C-step sequence:
- Private-cloud IaC (`deploy/`) merged in PR #23 (`21c325f`), then re-laid
  out in layers: Layer 0 `deploy/00-infra/private-hyperv` (single Hyper-V
  host, NAT switch, 1 control plane + 2 workers) replaces
  `deploy/provisioning`; Layer 1 `deploy/01-k8s-engine/rke2-ansible`
  (CIS-profile RKE2, restricted PSS, secrets encryption; engine only)
  replaces `deploy/configuration`, and kube-vip moves to Layer 2 as a
  services-only DaemonSet. Layer 0 host preparation has run once on the
  owner's host (PR #28); VMs, cluster and add-ons are not created yet.
  The ADR is still in draft
  (`XXXX-proposed-private-cloud-infrastructure.md`). It covers the
  private-cloud part of section 2.2's edge-to-cloud gap.
- Flink and Elasticsearch version management merged in PR #24 (`f04851c`).
- Roadmap and direction reconciliation (this branch): three proposed ADRs
  -- milestone naming (PF vs M9), platform communication direction, roles
  and privileged environment access -- and `cfg.schema.json` aligned to
  ADR 0016.

## 4. Execution steps

Step labels follow the ADRs' own references (ADR 0017 "C1 work", ADR 0016
"C3 design", ADR 0018 "C4 design"). Each step is its own PR with its own
green CI run.

| Step | Scope | Exit criterion |
| --- | --- | --- |
| **C0 Gate** | Restore `CLAUDE.md` (HEAD or the complete revised version); merge ADR numbering and fix H1/status lines; fresh green CI on `main`; open proposed ADR stubs for every gap in 2.2 | `main` green on GitHub-hosted CI after PR #18; ADRs 0015-0019 accepted; gap ADRs exist as proposals |
| **C1 Hexagonal skeleton** (ADR 0017) | Refactor `services/identity` into `domain` / `application` / `port.in` / `port.out` / `adapter.in.rest` / `config`; constructor injection; Spring wiring in `config` only; per-adapter vendor bans for `org.apache.kafka..`, persistence providers, `org.keycloak..`, `com.stripe..`, `io.grpc..`, `org.springframework.web..` via `ArchRules.noClassesOutsideSubpackageDependOnPackages` | ArchUnit proves inward-only dependencies; every ban has a negative fixture test and a vacuity tripwire |
| **C2a Observability and topology installation** (ADR 0015; proposed installation-sequence ADR) | After approved lab Layers 0-2 are running, install the independently versioned Layer 3 LGTM/Collector artifacts and Grafana/Tempo Service Graph configuration. Before application instrumentation, validate synthetic OTLP trace/log/metric ingest and query, a paired-span topology edge, storage/retention, access, restart, recovery, resource limits, alerting and owner-approved soak. Cilium/Hubble flow topology is validated separately with the cluster networking layer. Static artifact/CI work can begin while the lab infrastructure is prepared; live installation waits for Layers 0-2. | Layer 3 static checks pass; target-cluster installation, synthetic no-application stability and service-graph evidence are recorded. No app-code change or 24/7 production claim is part of C2a. |
| **C2b Service instrumentation** (ADR 0015; proposed end-to-end traceability ADR) | After C2a passes, instrument existing identity REST/gRPC paths with OTel; define the correlation baggage key in `contracts/`; propagate server-issued `X-Correlation-ID` through span, MDC and supported transport headers. Define Kafka event-context mappings with synthetic envelopes for C5 and opaque actor/device audit mappings for C3. | REST/gRPC integration tests on the installed Layer 3 prove correlation/trace propagation, spoofed correlation rejection, log/span/baggage redaction and bounded-cardinality metrics. Authenticated actor and Kafka end-to-end proof follows C3/C5. |
| **C3 IAM-agnostic identity** (ADR 0016) | `port.out` for token verification and claim mapping to a framework-free `Principal`; adapter on Spring Security OAuth2 resource server with standard JWT (no Keycloak SDK); claim names are configuration; 2-tier role set; Keycloak only in per-service Testcontainers ITs; design Tier 1's audited cross-tenant path | Swapping the OIDC provider in tests is configuration-only; a request carrying only APISIX identity headers is rejected |
| **C4 Persistence and tenancy** (ADRs 0016, 0017) | First `adapter.out.persistence` (PostgreSQL + Flyway); `SET LOCAL app.tenant_id` per transaction; `ENABLE` + `FORCE ROW LEVEL SECURITY` on tenant-owned tables | Testcontainers test shows RLS blocks a cross-tenant read with the application-level check deliberately bypassed |
| **C5 Event backbone** (ADR 0018) | Outbox table + relay; per-consumer dedupe tables; `usage-event v1` (Protobuf, envelope `idempotency_key`) in `contracts/`; `adapter.out.messaging`; CI conformance on Kafka and Redpanda; implement and test C2's deferred correlation/actor/device/event propagation across the real event path | Same suite green on both brokers; redelivery produces no second effect; full authenticated actor/device/event/causation trace after C3 and C5, including negative tenant and sensitive-data cases |
| **C6 Transport-swap proof** (ADR 0017 Decision 3) | `adapter.in.grpc` over the same `port.in` as REST; stubs generated per service from `contracts/`. May run in parallel from C1 | The same command reaches the same handler over REST and gRPC; the two adapters share no code |
| **C7 Deploy foundation** | `deploy/` Helm chart for `services/identity`, K3s values and Argo CD Application consuming the already validated Layer 3 observability endpoint; OpenShift-restricted-SCC-compatible `securityContext`; no cloud-vendor data services | Application chart installs on k3d in CI and exports a trace to Layer 3; the same chart renders unchanged with EKS/GKE/AKS values files |

### 4.1 Ordering rationale

- C1 first: every later step adds an adapter, and adapters need the port
  layout to exist.
- C2a precedes C2b: the observability stack is installed and stable
  before service code is instrumented. Approved lab Layers 0-2 are
  prerequisites for live C2a validation.
- C2b and C3 before C4: tenant scoping (RLS) needs a trusted `Principal`,
  and the trace plane should observe persistence from its first query.
- C5 after C4: the outbox must share a transaction with the state change.
- C2b establishes synchronous trace propagation on the installed stack;
  C3 adds authenticated actor identity, C5 adds real Kafka propagation,
  and C7 installs the application chart. No C2a/C2b acceptance
  criterion depends on a later step's implementation.

## 5. Next milestone (after C5 and the gap ADRs)

- Billing domain consuming `usage-event v1`; `PaymentGateway` port with a
  Stripe adapter (`com.stripe..` banned elsewhere).
- Flink job -> redaction -> pgvector -> RAG agent, core/AI cluster only.
- Tier-1 edge MQTT buffer (after its ADR).
- mTLS/OPA (after the Zero Trust ADR).
- Migration Studio pipeline (after its own ADR; authorized export,
  inventory, shadow comparison, and approval per `CLAUDE.md`).

## 6. Assumptions vs. observations

- **Observed** (read from the repository on 2026-09-25): ADR contents,
  branch and commit state, `services/identity/README.md` CI record,
  `CLAUDE.md` working-tree truncation.
- **Assumed / not verified here**: GitHub Actions run history (not
  reachable from the authoring environment); TB CE capabilities listed in
  2.3; step sizes and parallelism, which are planning estimates.
