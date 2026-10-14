# CLAUDE.md

Development contract and architectural conventions for the IOT-EE platform.
All changes require PR, CI, and human review; an agent must not approve its own work.

Prompt frame: state the milestone, bounded context, verified inputs, acceptance criteria, security constraints, intended files, relevant tests, and non-goals. Distinguish assumptions from observations. Inspect before editing and preserve unrelated work.

Secrets and PII: never include raw PII, credentials, keys, production dumps, or vault secret values in prompts, Git, app databases, events, logs, or audit evidence. Use synthetic inputs. Enter source secrets once directly into the scaffold-configured vault; persist only references. Never automatically import secrets from legacy exports. No unrestricted cloud commands or cloud admin credentials in browser flows.

ThingsBoard preservation: preserve ThingsBoard rules through authorized export, inventory, shadow comparison, and approval. Screenshots describe visible UI only, never hidden formulas or rules. Enforce tenant authorization, versioned contracts, idempotent consumers, transactional outbox, and redacted evidence. Never claim atomicity across ThingsBoard and Kafka.

Constitutional engineering rules (see ADR 0011 Decision 4 for the full text): no secrets/PII/payment data/private keys/device credentials in source, Git, events, logs, metrics, prompts, or fixtures; server-issued correlation IDs preserved end-to-end; signed device-verified firmware (WebSockets report progress, not binaries); no destructive/infra/deploy/secret-rotation action or test-gate bypass without explicit human approval; no DR/compliance/migration completion claims from local tests alone; RBAC + ABAC + mTLS/JWT/SSO multi-tenancy.

## Roadmap
Milestones M0-M9 are product capability milestones (docs/requirements-addendum.md). M9 is the final full legacy import, reconciliation, approval and cutover, after M8. The Java foundation is a separate stage, Platform Foundation (PF), not a numbered milestone (proposed ADR docs/adr/XXXX-proposed-milestone-naming-and-roadmap.md; it supersedes ADR 0012's "M9" label only).

| Stage | Capability | Spec (Python, frozen) | Platform (Java) |
| --- | --- | --- | --- |
| M0 | Foundation | Done | -- |
| M1 | Migration Studio foundation: vault abstraction, configuration lifecycle | Done | Not started |
| M2 | Domain core: tenant identities, permissions, entitlements, operator/device command domain | Done | Not started |
| M3 | MQTT/PostgreSQL ingestion, Kafka, TB shadow parity, authenticated device delivery | Done | Not started |
| M4 | APISIX/BFF, separated console logins, Operators page, REST/gRPC/WebSocket integration, reports | Done | Not started |
| M5 | Entitled firmware management | Done | Not started |
| M6 | Immutable evidence, secret rotation/revocation, resilience/DR | Done | Not started |
| M7 | Optional monetization | Done | Not started |
| M8 | Deployment Studio / multi-environment | Done | Not started |
| M9 | Final full legacy import, reconciliation, approval, cutover | -- | Not started; needs M8 and real legacy access |

"Done" for a spec slice means its contract-gated Python slice passes spec/scripts/check.py; every slice's real-backend items are blocked. A milestone is complete on the platform only when its Java implementation meets the stage-completion checklist below.

### Platform Foundation (PF)
- PF-A (formerly "M9 Track A"): TB CE investigation -- done, a document (docs/tb-ce-inventory.md, tb-extensions/manifest.yaml). The TB CE behaviour it describes is unverified.
- PF-B (formerly "M9 Track B"): Java bootstrap (ADR 0012) and the ADR 0013 autonomy refactor -- done.
- PF-C (formerly "M9 -> Track C"): steps C0-C7 in docs/track-c-execution-plan.md, governed by ADRs 0015-0019. C0 and C1 done; C2 (observability) next; C3-C7 not started.

Older documents use "M9" for PF and "M10+" for post-foundation Java work. Read those as PF and "Java implementation of M1-M8", respectively; "M9" meaning final migration/cutover (ADR 0002, docs/migration-studio.md) is unchanged.

### Language scope
ADR 0011 pivoted the platform to Java 17 + Spring Boot / Spring Cloud, integrating ThingsBoard CE behind a replaceable adapter and tested upgrade boundary (proposed partial supersession of ADR 0011 Decision 2). The M0-M8 Python code is a frozen specification/reference implementation in spec/ (ADR 0011 Decision 9, ADR 0012 Decision 7). Python is written only for the RAG subsystem and standalone adapters (ADR 0011 Decision 1).

ADR 0013 established microservice autonomy: services share only contracts (.proto, OpenAPI, JSON Schema) and test-scope build artifacts (ArchUnit rules). No shared runtime JARs. Per-service RBAC, correlation, and Spring wiring, duplicated by design -- no duplication ceiling; repeated code is a boundary signal, never grounds to reopen a shared JAR.

Post-PF work is scoped milestone by milestone; each milestone's Java implementation needs its own ADR where it introduces a decision.

Requirements added after the 14-goal review (docs/enterprise-readiness-review.md, "Follow-up roadmap", R1-R6) with proposed stages awaiting owner confirmation: R1 rule-based authorization + ABAC (C3, M2, M4); R2 SSO/JWT with proposed refresh-token rotation and MFA defaults (C3, M4); R3 replaceable payment platform and service-owned APIs (M7; proposed service API/payment ADR); R4 backend-first Config Studio (proposed ADR scopes platform/service and tenant configuration, backend before UI); R5 OpenTofu/Ansible/Helm responsibility matrix (C7, M8; Kustomize currently owns Layer 2); R6 system-admin-only VM environment-admin channel grants (M2, M8; proposed roles ADR). Decisions remain proposals until their ADRs are accepted.

## Repository layout

```
contracts/                  language-neutral contracts (.proto, OpenAPI, JSON Schema)
architecture/               ArchUnit rule factories, test scope only (build-time shared artifact)
services/<name>/            autonomous Java services
  └─ domain/, rbac/          framework-free business rules (no Spring, no JPA, no HTTP, no gRPC)
  └─ port/in/, port/out/     inbound use-case / outbound dependency interfaces (ADR 0017)
  └─ application/            implements port/in; reaches adapters only through port/out
  └─ adapter/in/rest/        Spring MVC driving adapter over port/in
  └─ adapter/in/grpc/        gRPC driving adapter over the SAME port/in
  └─ adapter/out/<concern>/  driven adapters implementing port/out (vendor SDKs live only here)
  └─ config/                 composition root (Spring wiring only)
  └─ correlation/            framework-free correlation-ID context
adapters/<provider>/        real-backend implementations behind contracts (M10+; none exist in Java yet)
  └─ (e.g. worm_s3)         built from spec/ patterns; isolated, optional deps
deploy/                     IaC in five separately validated layers: 00-infra/private-hyperv (L0: VMs, OpenTofu; lab profile only), 01-k8s-engine/rke2-ansible (L1: Ansible, CIS-hardened RKE2), 02-cluster-addons (L2), 03-observability (L3: LGTM/OTel, planned), 04-apps (L4: Helm + Argo CD, planned, no charts exist); catalog/ (curated tool catalog + validator), profiles/ (lab + planned cloud profiles); see deploy/README.md
spec/                       frozen M0–M8 Python reference implementation (not the platform)
docs/                       ADRs, architecture guides, inventories
  └─ adr/                   numbered ADRs (0001–present) + README.md convention
.github/workflows/          CI: python spec gate + java platform gate
```

docs/, CLAUDE.md, README.md, .github/workflows/ stay at the repository root — they describe the project as a whole, not any single language tree.

## Gates

Both gates run in CI on every change. Both must pass for changes touching their scope.

| Gate | Command | Scope |
| --- | --- | --- |
| Python spec gate | `python spec/scripts/check.py` | The frozen M0–M8 reference implementation only. Mechanical isolation checks + full regression suite. |
| Java platform gate | `mvn -f pom.xml verify` | contracts/, architecture/, services/*, adapters/*. Compile + unit tests + ArchUnit boundary rules. |

After every stage run its complete relevant gate and the full regression gate. A stage requires code, tests, docs, deployment artifacts, and passing gates; document unavailable external verification as blocked, not passed.

## Architectural principles
### Microservice autonomy (ADR 0013)
Zero shared runtime — services do not share executable Java libraries containing business logic, domain classes, repositories, Spring components, or helper implementations.

Contracts over libraries — communication relies on versioned schemas (Protobuf / OpenAPI / JSON Schema) rather than shared code dependencies. Each service generates its own Protobuf classes from .proto contracts as part of its own build.

Standard format libraries allowed — Jackson, protobuf-java, CloudEvents SDK, etc. are ordinary per-service third-party dependencies. Do not hand-roll a serializer to "purify" a service.

### Hexagonal architecture
Pure domain core — business rules live in a framework-free layer. No org.springframework.., jakarta.servlet.., jakarta.ws.rs.. imports in domain/, rbac/, port/, or application/. Ports and adapters per ADR 0017: dependencies point inward only, each driving adapter depends only on port/in, io.grpc.. only in adapter/in/grpc, org.springframework.web.. only in adapter/in/rest (ArchUnit-enforced per service; see services/identity IdentityHexagonalArchitectureRulesTest).

Database independence — the domain knows nothing about PostgreSQL, JPA, or SQL. Persistence via repository interfaces (ports); implemented by infrastructure adapters. jakarta.persistence.. annotations permitted; org.hibernate.., org.eclipse.persistence.., and org.jooq.. are denied by ArchUnit rule (no persistence code exists yet, so this rule is currently vacuously satisfied, not exercised against real persistence code).

Protocol independence — REST, gRPC, and Kafka are driving/driven adapters. Incoming requests translate to plain Java commands before hitting the domain; domain events translate to Kafka messages at the outer edge.

### Plug-and-play infrastructure
Mandatory architecture constraint: every selected infrastructure component, framework/provider, and integration platform sits behind an owned port or versioned contract so it can be replaced without changing domain/application rules. A replacement is supported only after the same behavioral and operational conformance checks pass; alternatives are not presumed drop-in. This includes ThingsBoard CE: it must be replaceable through a conforming adapter and upgradeable across tested versions (proposed partial supersession of ADR 0011 Decision 2). Implementation status: vendor-SDK bans are enforced in services/identity and REST <-> gRPC query equivalence is demonstrated there; no infrastructure or platform replacement has yet been demonstrated. APISIX may use a conforming NGINX/Envoy adapter; Kafka-protocol brokers need conformance tests (ADR 0018); OpenTofu is the default with Terraform an optional BSL compatibility choice; Spring Boot needs upgrade tests; WORM storage and payments use their own ports. CDC tooling has no ADR yet.

Enforcement: Maven Enforcer bannedDependencies + ArchUnit autonomy rules, both in the build. Test-scope shared artifacts (ArchUnit rules, checkstyle configs, .proto, JSON Schema) are permitted; runtime shared artifacts with business logic are prohibited.

### Communication direction (proposed ADR docs/adr/XXXX-proposed-platform-communication-direction.md)
REST over HTTPS for the frontend, through APISIX (the selected north-south gateway) and a BFF; one tenant-authorized, multiplexed WebSocket per browser. gRPC for synchronous calls between separately deployed services; in-process port calls inside the modular-monolith profile. Kafka for asynchronous domain events. MQTT for devices. Spring Cloud LoadBalancer only where a service client must route among instances itself (never on the external edge, not a default dependency); otherwise Kubernetes Services route in-cluster traffic. The proposed layered profile uses Cilium for pod reachability and Istio Ambient for workload mTLS and service policy, pending conformance and selection. TBMQ CE and Absmach FluxMQ remain MQTT broker candidates; MirrorMaker is proposed first for canonical Kafka topics.

### Tenancy and roles
Pooled tenant_id + PostgreSQL RLS (ADR 0016); contracts/cfg/cfg.schema.json accepts tenant_mode: pooled-rls only. Four roles in two tiers, kept distinct: system admin (ADR 0016 PRODUCT_ADMIN), system operator (Product Operator), tenant admin, tenant operator. Only system admins grant or revoke tenant-operator or system-operator access to VM environment-admin channels (bastion/environment admin access); tenant admins and operators cannot (proposed ADR docs/adr/XXXX-proposed-roles-and-privileged-environment-access.md). Tenant operators are not ThingsBoard customer users.

## ADR conventions
ADRs live in docs/adr/ and are numbered sequentially. The number is assigned at merge, not at branch creation.

Drafts use docs/adr/XXXX-proposed-<slug>.md

At merge, the file is renamed to docs/adr/<NNNN>-<slug>.md with the next free number

Superseding an ADR: write a new ADR that references and supersedes the old one; do not edit the old one

See docs/adr/README.md for the current convention and next free number

## Stage-completion checklist
A stage is not complete without all of:

□ Code implementing the stage's scope
□ Tests — unit + boundary (ArchUnit for Java, check.py for Python)
□ Documentation — architecture notes, ADR if the stage introduces a new decision
□ Deployment artifacts where the stage touches infrastructure (OpenTofu default; Terraform-compatible optional, Ansible, Helm/Argo CD per layer plan)
□ Stage gate passes (mvn verify and/or python spec/scripts/check.py as applicable)
□ Full regression gate passes (both gates green)
□ Blocked items recorded explicitly — external verification not available is documented as blocked, not passed
Supply-chain security scanning (planned — ADR 0014, post-v1.0.0)
Trivy scans for CVEs in dependencies, container images, IaC misconfigurations, and secrets. SBOM generation and image signing (cosign/Sigstore) are part of the same ADR. Until ADR 0014 is ratified, scanning is not part of the CI gate — do not assume a green build means a clean bill of health.

M0–M8 legacy constraints (still binding)
The original M0 constraint remains in force as a standing rule:

The Python spec tree (spec/) must not provision infrastructure, import legacy data, or execute unrestricted cloud commands.

Migration Studio's data import is a separate concern governed by its own ADR (see docs/adr/0002), and is still pending real legacy system access.

Legacy ThingsBoard CE exports are handled through authorized export, inventory, shadow comparison, and approval — never recreated from memory or screenshots.

Reading order for a new session
If you are a new agent starting work on this repository, read in this order:

1. CLAUDE.md (this file) -- conventions, roadmap, current stage
2. README.md -- what is implemented versus planned or blocked
   docs/enterprise-readiness-review.md -- goal-by-goal traceability, evidence levels, unresolved inputs
3. docs/requirements-addendum.md -- product requirements and the M0-M9 delivery sequence
4. docs/adr/0011-platform-architecture-and-language-stack.md -- the platform pivot (read with its supersession pointers)
5. docs/adr/XXXX-proposed-milestone-naming-and-roadmap.md -- M9 versus Platform Foundation (read before ADR 0012)
6. docs/adr/0012-m9-foundation-scope.md -- PF-A/PF-B scope and technical choices
7. docs/adr/0013-microservice-autonomy.md -- the autonomy rule
8. docs/adr/0015 to 0019 -- PF-C decisions (observability, tenancy and identity, hexagonal conventions, events and metering, streaming and RAG)
9. docs/adr/XXXX-proposed-platform-communication-direction.md, docs/adr/XXXX-proposed-roles-and-privileged-environment-access.md, docs/adr/XXXX-proposed-service-api-and-payment-provider-boundaries.md, docs/adr/XXXX-proposed-config-studio.md, docs/adr/XXXX-proposed-ai-and-device-adapter-boundaries.md, and docs/adr/XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md
10. docs/track-c-execution-plan.md -- PF-C steps and progress
11. docs/adr/README.md -- ADR numbering convention
12. The milestone ADR relevant to your task: 0002 (M1), 0003 (M2), 0004 (M3), 0005 (M4), 0006 (M5), 0007 (M6), 0008 (M7), 0009 (M8); deploy/README.md, docs/adr/XXXX-proposed-deployment-layers-tool-catalog-and-profiles.md and docs/adr/XXXX-proposed-private-cloud-infrastructure.md for infrastructure

When a proposed ADR merges and is numbered, replace its XXXX path here.

Do not start writing code until you have read the relevant ADR for the work you are about to do.
