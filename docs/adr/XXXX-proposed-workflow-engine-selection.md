# ADR XXXX (proposed) -- Human workflow engine selection

> Deferred until after the TB CE core runs on Twinfra.

Status: proposed. No BPM engine is installed or selected for production.
Number at merge. This refines the workflow section of the proposed resilience
ADR; it does not require BPMN for ordinary telemetry or short state machines.

## Provisional decision

Use a service-owned, persisted case/work-order model and a versioned
`WorkflowCoordinator` port. Pilot **Flowable Open Source** as the default
candidate for long-running alarm resolution and human review because its
Apache-2.0 Java engine supports BPMN, CMMN, DMN and human tasks, and its
documented baseline includes Java 17. The service owns tenant authorization,
work-order state, decisions, timers, audit and APIs. Flowable receives scoped
IDs and coordinates only authorized use cases through an adapter. Its tables
and process variables are not the product's canonical device or alarm store.
For event-driven cases, the adapter feeds curated domain events to Flowable's
Event Registry Kafka channel. Do not connect every raw telemetry record to a
process instance. Flowable OSS includes Kafka channel support; its graphical
Flowable Design experience is edition-specific and is not assumed present.
The initial event contract is `alerts-critical`: a Flink CEP-derived alert
starts or correlates one resolution case by stable tenant/alert key. Human
tasks notify, approve and dispatch; service tasks invoke authorized core
APIs with idempotency and record outcomes. TB CE receives relevant approved
outcomes through an owned adapter, while core services remain authoritative.

| Candidate | Verified fit | Gate before choosing it |
| --- | --- | --- |
| Flowable Open Source | Apache-2.0 Java engine; BPMN/CMMN/DMN and human tasks; Java 17 documented | Pin engine and UI editions; test PostgreSQL, tenant isolation, claim/complete authorization, timers, retries, migration, backup/restore, upgrade and 24/7 operations |
| CIB seven CE | Open-source Camunda 7 fork (main source Apache-2.0); existing Camunda 7 model migration is its main advantage | Pin release, verify Java/Spring matrix, third-party licenses, tasklist/admin access, security fixes and process compatibility |
| EximeeBPMS CE | Apache-2.0 Camunda 7 fork with BPMN/DMN; 1.4.0 release is documented | Current 1.4.0 requires JDK 21, above IOT-EE's Java 17 baseline; review version/runtime decision, and note that its older Cockpit Basic/Tasklist are marked obsolete |
| FINOS Fluxnova | Apache-2.0 BPMN engine and human tasklist in source | Pin a stable release and verify Java/Spring compatibility, security maintenance, operational UI and upgrade path |

Do not score a candidate on source license alone. Compare exact artifacts,
edition-gated features, process migration and security patch cadence. If a
small workflow can be safely expressed as a service-owned durable state
machine, do that before operating a general BPM platform. A BPMN engine does
not become the policy decision point or bypass a service's RBAC/ABAC.

## Acceptance scenario

Start an anomaly-review case keyed by tenant, device, event and correlation
IDs. Verify one active case per deduplication key, scoped assignment and
claim, approve/reject/escalate with reasons, deadline and timeout handling,
operator reassignment, immutable decision evidence, outage recovery, and
idempotent return of the decision to the ingestion gate. Repeat against an
alternative adapter to demonstrate replaceability before making any product
claim about a pluggable workflow engine.

## Primary sources

- [Flowable OSS license and Java baseline](https://www.flowable.com/open-source/docs/oss-introduction) and [human tasks](https://www.flowable.com/open-source/docs/cmmn/ch06-cmmn).
- [Flowable OSS Event Registry Kafka channels](https://www.flowable.com/open-source/docs/eventregistry/ch05-Deployment).
- [CIB seven source](https://github.com/cibseven/cibseven) and [edition licenses](https://docs.cibseven.org/manual/2.2/introduction/licenses/).
- [EximeeBPMS 1.4.0 download and runtime requirements](https://eximeebpms.org/download/).
- [FINOS Fluxnova source](https://github.com/finos/fluxnova-bpm-platform).
