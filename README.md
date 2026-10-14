# IOT-EE

An enterprise, multi-tenant IoT platform for tank monitoring (tenants,
devices, tanks, telemetry, alarms, reports, firmware), built as a
**Java 17 / Spring Boot 3 / Spring Cloud** platform that extends
**ThingsBoard CE** behind a replaceable, upgradeable compatibility boundary. It replaces a
legacy ThingsBoard CE deployment through a controlled migration.

Nothing in this repository has been deployed to, or verified against, a
real environment, a real legacy system, or a real external service.
The status below separates what is implemented and tested locally from
what is planned or blocked. **No ThingsBoard EE/PE feature parity and no
compliance certification is claimed**; parity needs a version-specific
feature matrix with evidence, which does not exist yet. Goal-by-goal
traceability is in
[`docs/enterprise-readiness-review.md`](docs/enterprise-readiness-review.md).

## Product scope

- **ThingsBoard CE is replaceable and upgradeable.** Keep it unforked and isolate version-specific APIs and customizations behind an adapter. Upgrade to a newer CE version by reapplying the thin declared customization set and passing compatibility tests; another conforming platform may replace it after behavioral parity and migration checks. This amends ADR 0011 Decision 2 via the proposed adapter-boundaries ADR; no drop-in equivalence is claimed.
- **Domain:** tenants, devices, assets/tanks and their hierarchy,
  telemetry, alarms and commands, reports.
- **Migration** from the legacy system: Migration Studio (M1) and a
  final, reconciled legacy import and cutover (M9).
- **Reports, firmware, evidence**, and **optional monetization**
  (default off; never blocks telemetry, alarms or commands).
- **Deployment** to private/on-prem and cloud environments: upstream
  Kubernetes on-prem and managed EKS/AKS/GKE, with Deployment Studio (M8)
  producing reviewed, policy-checked plans.

## Platform

| Concern | Direction | Governing ADR |
| --- | --- | --- |
| Language/runtime | Java 17, Spring Boot 3.3, Spring Cloud 2023.0, Maven | 0011, 0012 |
| Python | Limited to the RAG subsystem and standalone adapters; the M0-M8 Python code in `spec/` is a frozen reference implementation, not the platform | 0011 Decisions 1, 9 |
| Service structure | Autonomous services sharing contracts only (`.proto`, JSON Schema); hexagonal ports and adapters | 0013, 0017 |
| Frontend | REST over HTTPS through **APISIX** (north-south gateway) and a BFF; one multiplexed WebSocket per browser | proposed communication-direction ADR, 0005 |
| Service to service | **gRPC** (synchronous); **Kafka** (asynchronous events, transactional outbox, idempotent consumers) | proposed communication-direction ADR, 0018 |
| Devices | **MQTT** over authenticated TLS; firmware binaries over HTTPS/object storage. Legacy (non-MQTT) device ingestion is **not designed** since ADR 0019 made TB CE a downstream consumer | 0004, 0006, 0019 |
| Load balancing/network policy | Proposed Cilium pod reachability plus Istio Ambient service policy; no profile selected or installed. Kubernetes Services route in-cluster; Spring Cloud LoadBalancer only where a client must route itself | proposed Cilium/Ambient and communication-direction ADRs |
| Tenancy | Pooled `tenant_id` + PostgreSQL Row-Level Security | 0016 |
| Identity | IAM-agnostic OIDC/JWT (Keycloak as first provider only); each service re-verifies tokens | 0016 |
| Roles | System admin, system operator, tenant admin, tenant operator (ADR 0016's Product and Tenant tiers). Only system admins grant or revoke VM environment-admin channel access | 0016, proposed roles ADR |
| Observability | LGTM + OpenTelemetry; `traceparent` and `X-Correlation-ID` carried separately | 0015 |
| Streaming/RAG | Flink -> redaction -> pgvector, core/AI cluster only. Integration with multiple AI environments/providers is **not designed** (no ADR) | 0019 |
| Open-source defaults | Mostly Apache 2.0; exceptions under review: HashiCorp Vault and EMQX are source-available (BSL), the `minio/minio` repository (the planned on-prem WORM default) was archived on 2026-04-25 and is no longer maintained. Licences and commercial alternatives per component: `docs/enterprise-readiness-review.md`, goal 14 | -- |

"Proposed" ADRs are drafts in `docs/adr/XXXX-proposed-*.md` awaiting
review; they take effect when merged.

## Roadmap and current stage

Milestones M0-M9 are product capabilities
(`docs/requirements-addendum.md`). **M9 is the final full legacy
import, reconciliation and cutover**, after M8. The Java foundation is a
separate stage, **Platform Foundation (PF)**, that the M1-M9
capabilities are built on (proposed milestone-naming ADR).

| Stage | Scope | State |
| --- | --- | --- |
| M0-M8 (spec) | Python reference slices of each capability, in `spec/` | Done as specification and frozen; real backends blocked in every slice |
| PF-A | TB CE investigation (`docs/tb-ce-inventory.md`, `tb-extensions/manifest.yaml`) | Done as a document; the TB CE behaviour it describes is unverified |
| PF-B | Java bootstrap and the ADR 0013 autonomy refactor | Done |
| PF-C | C0 gate, C1 hexagonal skeleton | Done (C1: PR #21) |
| PF-C | C2 observability, C3 identity, C4 persistence and tenancy, C5 events, C6 transport swap, C7 deploy foundation | **C2 next**; C3-C7 not started |
| M1-M8 (platform) | Java implementation of each capability | Not started |
| M9 | Final legacy import, reconciliation, cutover | Not started; needs M8 and real legacy access |

## What is implemented (tested locally and in CI)

- `services/identity` -- a walking skeleton, not a usable identity
  service: hexagonal layout (`domain`, `application`, `port.in`,
  `port.out`, `adapter.in.rest`, `adapter.in.grpc`, `config`), one use
  case (tenant permissions) over REST and gRPC through the same inbound
  port, a local RBAC registry, correlation-ID handling, and `cfg.yaml`
  validation against `contracts/cfg/cfg.schema.json`. The ABAC hook is
  a stub that always permits; it must be replaced before any
  tenant-facing endpoint exists (ADR 0016).
- `contracts/` -- event envelope and identity `.proto` contracts, and the
  draft `cfg.yaml` JSON Schema.
- `architecture/` -- ArchUnit rule factories (test scope) with negative
  fixtures; Maven Enforcer bans shared runtime modules.
- `spec/` -- the frozen Python M0-M8 reference implementation and its
  gate.
- `deploy/` -- IaC in five layers: VMs (OpenTofu), CIS-hardened RKE2
  (Ansible), cluster add-ons (Kustomize) implemented for a single-host
  Hyper-V **lab profile** only; observability (LGTM/OTel) and application
  release (Helm + Argo CD) are planned and **no Helm chart exists**. A
  curated tool catalog and deployment profiles are validated in CI. CI
  checks everything statically only.

## Planned or blocked (not verified)

Each item stays blocked, not passed, until it is verified in a
representative environment:

- **Legacy system:** no legacy access, export, inventory, rule/report
  parity or data import has happened.
- **ThingsBoard CE:** no running TB CE; consuming platform Kafka topics
  and native OTel emission are unverified
  (`docs/track-c-execution-plan.md`, section 2.3).
- **Infrastructure services:** no APISIX, BFF, Kafka, MQTT broker,
  PostgreSQL with RLS, identity provider, Vault, proposed Cilium/Istio Ambient profile and LGTM stack,
  Flink, pgvector, WORM store or payment provider is connected to any
  platform code.
- **Deployment:** Layer 0 host preparation has been run once on the
  owner's Hyper-V host; the VMs, the RKE2 cluster and the add-ons have
  not been created (`deploy/README.md`, "Verification status"). No cloud
  environment exists.
- **Security scanning:** supply-chain scanning (ADR 0014) is reserved,
  not implemented; a green build is not a security clearance. No
  static-analysis or coverage gate exists yet.
- **Bare metal:** the only Layer 0 targets Hyper-V VMs on one Windows
  host; a bare-metal Layer 0 does not exist.
- **LGTM:** no observability stack is deployed or packaged yet (PF-C C2).
- **Added requirements, not yet reconciled by ADR:** rule-based
  authorization with real ABAC (the current ABAC hook always permits),
  refresh-token rotation and OTP, a backend-first Config Studio (scope
  undefined), and a single Terraform/Ansible/Helm responsibility matrix.
  Payment-provider boundaries (ADR 0018) and system-admin-only VM channel
  grants (proposed roles ADR) are decided but not implemented. Proposed
  stages: `docs/enterprise-readiness-review.md`, "Follow-up roadmap".

## Gates

| Gate | Command | Scope |
| --- | --- | --- |
| Java platform | `mvn -B -f pom.xml verify` | `contracts/`, `architecture/`, `services/*` |
| Python spec | `python spec/scripts/check.py` | `spec/` only |
| Infrastructure | `.github/workflows/infra.yml` | `deploy/`: `tofu validate`, Ansible syntax check and inventory validation, PowerShell parse, kustomize + kubeconform, tool catalog/profile validation |

A passing gate is not evidence of production readiness, rule parity,
broker connectivity, retention or deployment success.

## Where to read next

- [`CLAUDE.md`](CLAUDE.md) -- development contract, roadmap, reading order
- [`docs/adr/`](docs/adr/) -- decisions; [`docs/adr/README.md`](docs/adr/README.md) for numbering
- [`docs/enterprise-readiness-review.md`](docs/enterprise-readiness-review.md) -- traceability against the 14 product goals
- [`docs/requirements-addendum.md`](docs/requirements-addendum.md) -- tenant administration, consoles, vault, delivery sequence
- [`docs/track-c-execution-plan.md`](docs/track-c-execution-plan.md) -- PF-C steps
- [`deploy/README.md`](deploy/README.md) -- infrastructure layers
- [`spec/README.md`](spec/README.md) -- the Python reference implementation

All changes go through a PR, CI and human review.
