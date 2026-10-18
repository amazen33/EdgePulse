# CLAUDE.md

Development contract and architectural conventions for the EdgePulse platform.
All changes require PR, CI, and human review; an agent must not approve its own work.

Prompt frame: state the milestone, bounded context, verified inputs, acceptance criteria, security constraints, intended files, relevant tests, and non-goals. Distinguish assumptions from observations. Inspect before editing and preserve unrelated work.

Secrets and PII: never include raw PII, credentials, keys, production dumps, or vault secret values in prompts, Git, app databases, events, logs, or audit evidence. Use synthetic inputs. Enter source secrets once directly into the scaffold-configured vault; persist only references. Never automatically import secrets from legacy exports. No unrestricted cloud commands or cloud admin credentials in browser flows.

ThingsBoard preservation: preserve ThingsBoard rules through authorized export, inventory, shadow comparison, and approval. Screenshots describe visible UI only, never hidden formulas or rules. Enforce tenant authorization, versioned contracts, idempotent consumers, transactional outbox, and redacted evidence. Never claim atomicity across ThingsBoard and Kafka.

Constitutional engineering rules (see ADR 0011 Decision 4 for the full text): no secrets/PII/payment data/private keys/device credentials in source, Git, events, logs, metrics, prompts, or fixtures; server-issued correlation IDs preserved end-to-end; signed device-verified firmware (WebSockets report progress, not binaries); no destructive/infra/deploy/secret-rotation action or test-gate bypass without explicit human approval; no DR/compliance/migration completion claims from local tests alone; RBAC + ABAC + mTLS/JWT/SSO multi-tenancy.

## Claim wording and evidence
Describe EdgePulse as an IoT platform in foundation development. Every
completion claim, including "done", must link to a merged PR or receipt
and state the scope that evidence proves. A merged code PR does not prove
a runtime integration or milestone acceptance. Do not claim tool-agnostic,
hybrid-cloud, cross-vertical or AI capability until a milestone receipt
proves it. Label architecture descriptions as targets; AI remains the
unimplemented F5 epic. Keep unavailable external verification blocked.

## Roadmap and current scope
The approved delivery sequence is [MILESTONES.md](MILESTONES.md), replacing
the M0–M9, PF-A/B/C, Track and R1–R6 schemes. Its mapping preserves historical
references; do not use those references as a second backlog.

M1 Migration Studio and M9 legacy import/cutover move to **EdgeMig**
(ADR 0022). EdgePulse owns the **migration-readiness epic, MR-1 to MR-14**:
versioned integration contracts, tenant lifecycle, import-safe fence,
reconciliation APIs, run-scoped access, endpoint transitions and evidence.
MS2 defines contracts; MS4–MS6 implement readiness; MS8–MS9 are joint runs.
Readiness precedes customer-facing feature work beyond the core. Discovery,
extraction, transformation and migration orchestration belong to EdgeMig.

MS0 Reset: accepted 2026-10-18 (docs/acceptance/ms0-reset-2026-10-18.md); pre-release v2.0.0-alpha.1. MS1 (IOT-WO-02) and MS2 (IOT-WO-03): not started.
[MILESTONES.md](MILESTONES.md) defines the sequence and required receipts;
runtime integrations remain pending.

### Language and implementation status
The current build remains Java 17 + Spring Boot / Spring Cloud. ADR 0021
selects Java 21 and a supported Spring line; the build upgrade is pending
IOT-WO-02. Python remains limited to RAG and standalone adapters
(ADR 0011 Decision 1). The frozen M0–M8 Python reference implementation
is archived at [archive/python-spec-final](https://github.com/amazen33/EdgePulse/tree/archive/python-spec-final/spec); its former relocation
is recorded in merged [PR #12](https://github.com/amazen33/EdgePulse/pull/12).
The archived specification has no active CI gate; local Java gates do not
prove real-backend integration.

Merged [PR #14](https://github.com/amazen33/EdgePulse/pull/14) supplies the
Java bootstrap and boundary gates;
[PR #21](https://github.com/amazen33/EdgePulse/pull/21) supplies the hexagonal
identity query over REST and gRPC; and
[PR #29](https://github.com/amazen33/EdgePulse/pull/29) adds caller authorization.
These are foundation code/test outcomes, not platform completion. TB CE core integration, Twinfra application packaging
and migration readiness remain work for later orders, with external
verification blocked pending those orders and their required access.

ADR 0013 established microservice autonomy: services share only contracts
(.proto, OpenAPI, JSON Schema) and test-scope build artifacts (ArchUnit rules).
No shared runtime JARs. Per-service RBAC, correlation and Spring wiring are
duplicated by design; repeated code is a boundary signal, never grounds to
reopen a shared JAR. Retained application drafts remain proposals subject
to the dispositions in docs/adr/README.md and accepted ADRs 0020–0022.

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
adapters/<provider>/        real-backend implementations behind contracts (future Java work; none exist yet)
  └─ (e.g. worm_s3)         patterns archived at archive/python-spec-final:spec/; isolated, optional deps
deploy/                     frozen infrastructure sources (ADR 0021; deploy/FROZEN.md); future application delivery is Helm + Argo CD on Twinfra
archive/python-spec-final   tag containing spec/ (M0–M8 Python reference; absent from the active checkout)
docs/                       ADRs, architecture guides, inventories
  └─ adr/                   numbered ADRs (0001–present) + README.md convention
.github/workflows/          CI: Java platform gate + applicable static infrastructure and release checks
```

docs/, AGENTS.md, CLAUDE.md, README.md, MILESTONES.md, .github/workflows/ stay at the repository root — they describe the project as a whole, not any single language tree.

## Gates

The Java and naming gates run in CI on every change. The existing infrastructure gate runs on deploy/ changes and is retained unchanged. Each gate must pass for changes touching its scope. The archived Python specification has no active CI job.

| Gate | Command | Scope |
| --- | --- | --- |
| Java platform gate | `mvn -B -f pom.xml verify` | contracts/, architecture/, services/*, adapters/*. Compile + unit tests + ArchUnit boundary rules. |
| Naming gate | `bash .github/scripts/naming_gate.sh` | Tracked paths and contents; only approved history/frozen files, exact generated path references, archive tags and the former-name line exception are allowed. |
| Infrastructure gate | `.github/workflows/infra.yml` | Existing deploy/ package checks; static CI checks only, no host or cluster access. |

After every stage run its complete relevant gate and the full regression gate. A stage requires code, tests, docs, deployment artifacts, and passing gates; document unavailable external verification as blocked, not passed.

## Architectural principles
### Microservice autonomy (ADR 0013)
Zero shared runtime — services do not share executable Java libraries containing business logic, domain classes, repositories, Spring components, or helper implementations.

Contracts over libraries — communication relies on versioned schemas (Protobuf / OpenAPI / JSON Schema) rather than shared code dependencies. Each service generates its own Protobuf classes from .proto contracts as part of its own build.

Standard format libraries allowed — Jackson, protobuf-java, CloudEvents SDK, etc. are ordinary per-service third-party dependencies. Do not hand-roll a serializer to "purify" a service.

### Hexagonal architecture
Pure domain core — business rules live in a framework-free layer. No org.springframework.., jakarta.servlet.., jakarta.ws.rs.. imports in domain/, rbac/, port/, or application/. Ports and adapters per ADR 0017: dependencies point inward only, each driving adapter depends only on port/in, io.grpc.. only in adapter/in/grpc, org.springframework.web.. only in adapter/in/rest (identity enforcement: merged [PR #21](https://github.com/amazen33/EdgePulse/pull/21); see services/identity IdentityHexagonalArchitectureRulesTest).

Database independence — the domain knows nothing about PostgreSQL, JPA, or SQL. Persistence via repository interfaces (ports); implemented by infrastructure adapters. jakarta.persistence.. annotations permitted; org.hibernate.., org.eclipse.persistence.., and org.jooq.. are denied by the ArchUnit rule added in merged [PR #17](https://github.com/amazen33/EdgePulse/pull/17) (no persistence code exists yet, so the rule is not exercised against real persistence code).

Protocol independence — REST, gRPC, and Kafka are driving/driven adapters. Incoming requests translate to plain Java commands before hitting the domain; domain events translate to Kafka messages at the outer edge.

### TB CE core and owned integration boundaries (ADRs 0020–0022)
The following paragraphs are target requirements, not working integration
claims. No portability, AI or real-environment capability is established.

TB CE is the operational core and system of record for MQTT/HTTP/CoAP
transports, devices/assets/relations, attributes/telemetry, rules, alarms
and dashboards. Keep it unforked and track its thin customization set in
tb-extensions/manifest.yaml. EdgePulse services surround it with identity,
fine-grained authorization, evidence, billing, AI, consoles and migration
integration. A bounded context leaves TB only through a new ADR naming
parity tests, data migration and rollback (0020 Decision 6).

TB's stock outbound Kafka node publishes to a raw topic. An ingestion
adapter validates, resolves tenants from TB metadata, deduplicates by TB
message ID and timestamp, and publishes canonical events. Commands,
attributes, provisioning and administration use TB's documented REST API
behind ThingsBoardPort. Never write TB tables or read/publish internal TB
queue topics. No atomicity across TB and Kafka is claimed.

Other infrastructure/provider integrations stay behind owned ports or
versioned contracts. A replacement needs behavioral and operational
conformance; alternatives are not presumed equivalent. Broker conformance
targets Apache Kafka only (ADR 0021). The target uses Twinfra for hosting,
networking, PostgreSQL, OpenBao and observability. Future application delivery
must provide images, Helm charts and Argo CD Applications; these remain
unimplemented. Packaging follows ADR 0021 Amendment 1's
OpenShift compatibility rules; no support claim precedes an accepted live
receipt. WORM still needs Object Lock conformance.

Foundation enforcement: Maven Enforcer bannedDependencies + ArchUnit autonomy rules (merged [PR #14](https://github.com/amazen33/EdgePulse/pull/14), with follow-ups in [PR #17](https://github.com/amazen33/EdgePulse/pull/17)). Test-scope shared artifacts (ArchUnit rules, checkstyle configs, .proto, JSON Schema) are permitted; runtime shared artifacts with business logic are prohibited.

### Communication direction (application proposal)
REST over HTTPS through APISIX/BFF; one tenant-authorized multiplexed
WebSocket per browser; gRPC between deployed services; in-process ports in
a modular monolith; Kafka for asynchronous events. Devices connect to TB CE
transports (ADR 0020). The retained application proposal is
docs/adr/XXXX-proposed-platform-communication-direction.md; historical
platform references do not override ADR 0021. Workload security follows
Twinfra's baseline and requires explicit deployment-order verification.

### Tenancy and roles
Pooled tenant_id + PostgreSQL RLS (ADR 0016); contracts/cfg/cfg.schema.json
accepts tenant_mode: pooled-rls only. Keep system admin, system operator,
tenant admin and tenant operator distinct. TB tenant to tenant_id mapping
and TB customer/user mapping require MS4 design. Tenant operators are not
automatically TB customer users. Environment-admin channels belong to
Twinfra (MILESTONES.md); the privileged-environment-access draft is deferred.

## ADR conventions
ADRs live in docs/adr/ and are numbered sequentially. The number is assigned at merge, not at branch creation.

Drafts use docs/adr/XXXX-proposed-<slug>.md

At merge, the file is renamed to docs/adr/<NNNN>-<slug>.md with the next free number

Superseding an ADR: write a new ADR that references and supersedes the old one; do not edit the old one

See docs/adr/README.md for the current convention and next free number

## Stage-completion checklist
A stage is not complete without all of:

□ Code implementing the stage's scope
□ Tests — unit + boundary (ArchUnit for Java; additional gates for the implemented scope)
□ Documentation — architecture notes, ADR if the stage introduces a new decision
□ Helm chart and Argo CD Application for Twinfra where the stage touches deployment (ADR 0021, including Amendment 1)
□ Stage gate passes (mvn verify and any additional gate required by the implemented scope)
□ Full regression gates pass (Java platform, naming and applicable static infrastructure/release checks)
□ Blocked items recorded explicitly — external verification not available is documented as blocked, not passed
Supply-chain security scanning follows accepted ADR 0014: pinned Syft
SBOMs, Grype image/SBOM scanning and OSV-Scanner for lockfiles and the Maven
graph, with KEV blocking, cool-off and evidenced exceptions. ADR 0021 adds
Twinfra's licence gate. Implementation of these CI gates is pending
IOT-WO-02. Signing/provenance follows Twinfra's later adoption and is
outside ADR 0014. Green current CI does not prove these gates exist.

M0–M8 legacy constraints (still binding)
The original M0 constraint remains in force as a standing rule:

The Python reference at archive/python-spec-final:spec/ remains subject to its original constraint: it must not provision infrastructure, import legacy data, or execute unrestricted cloud commands. It is historical input, not an active platform gate.

Migration Studio M1/M9 requirements are EdgeMig inputs under ADR 0022. EdgePulse implements migration readiness only; real legacy access and owner approval remain required. ADR 0022 MR-9 requires explicit owner approval for each device-credential step, with no values in logs, events, evidence or Git.

Legacy ThingsBoard CE exports are handled through authorized export, inventory, shadow comparison, and approval — never recreated from memory or screenshots.

Reading order for a new session
1. AGENTS.md and CLAUDE.md -- the same contract (only the titles differ).
2. README.md and MILESTONES.md -- status and approved sequence.
3. docs/adr/README.md, then ADRs 0014 and 0020–0023 -- current decisions and dispositions. ADR 0023 records names; implementation is IOT-WO-05.
4. docs/requirements-addendum.md -- historical body with its amending header.
5. ADRs 0011–0013 and 0015–0019 -- read through the supersession map; accepted text stays unchanged.
6. docs/architecture.md, docs/test-plan.md and the relevant task ADR.
7. docs/enterprise-readiness-review.md and docs/reviews/iot-ee-review-2026-10-14.md -- dated reviews, not current runtime evidence.
8. docs/work-orders/IOT-WO-01-snapshot-and-decisions.md -- historical work-order scope; only explicitly assigned parts authorize work.

Do not start writing code until you have read the relevant ADR for the work you are about to do.
