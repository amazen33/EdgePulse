# IOT-EE

An enterprise, multi-tenant IoT platform with ThingsBoard CE as its
operational core and autonomous Java services around it. The accepted
direction is [ADR 0020](docs/adr/0020-tb-ce-operational-core.md),
[Twinfra hosting and licence gate](docs/adr/0021-twinfra-platform-and-licence-gate.md)
and [migration-manager integration](docs/adr/0022-migration-manager-integration.md).
The approved roadmap is [MILESTONES.md](MILESTONES.md).

This change implements **IOT-WO-01 Part B: decision records**. Part C
(infrastructure freeze and Python archival) and IOT-WO-05 (renaming under
ADR 0023) remain separate. MS0 is not complete from Part B alone. No
deployment, real-environment test, migration completion, feature parity or
compliance claim is made by this change.

## Status

| Area | Implemented or retained | Next work / evidence required |
| --- | --- | --- |
| Java foundation | Maven reactor, autonomous identity skeleton, tenant-permissions query through REST/gRPC, correlation handling, configuration schema and ArchUnit boundaries | Identity federation, persistence, messaging and operational integrations remain unimplemented |
| Python reference | Frozen M0–M8 contract-gated slices in spec/; real-backend items remain individually blocked | Part C archives/removes it; unchanged in Part B |
| Decision records | ADRs 0014 and 0020–0023, draft dispositions and approved milestone plan | Human review and merge; later work orders implement decisions |
| TB CE core | Declared customization/upgrade manifest and dated spike report as historical input | MS3 deployment/upgrade rehearsal, MS5 event path; no run performed by Part B |
| Migration | M1/M9 moved to migration-manager; execution plan retained as its input specification | IOT-EE readiness MR-1 to MR-14: MS2 contracts, then MS4–MS6 implementation |
| Deployment | Existing standalone infrastructure packages and CI retained unchanged | Images, Helm charts and Argo CD Applications for Twinfra; no chart promoted by Part B |
| Gates and runtime | Existing Java/Python gates retained | MS1 / IOT-WO-02 implements accepted licence/supply-chain gates and runtime upgrade |

The snapshot is preserved at `archive/reconcile-snapshot-2026-09-26`;
it is not a merge source wholesale. The dated
[enterprise readiness review](docs/enterprise-readiness-review.md) and
[2026-10-14 review](docs/reviews/iot-ee-review-2026-10-14.md) record their own
evidence limits. They do not establish current runtime readiness.

## Platform

| Concern | Accepted direction / implementation limit | Authority |
| --- | --- | --- |
| Runtime | Current Java 17, Spring Boot 3.3 / Spring Cloud 2023.0; Java 21 and supported Spring line in later IOT-WO-02 | 0011, 0012, 0021 |
| Structure | Autonomous services, versioned contracts, hexagonal ports/adapters; no shared runtime libraries | 0013, 0017 |
| TB CE and devices | TB CE owns MQTT/HTTP/CoAP transports, devices/assets/relations, telemetry/attributes, rules, alarms and dashboards; unforked | 0020 |
| Events | TB outbound Kafka node → raw topic → ingestion adapter → canonical topics; Apache Kafka only; outbox/idempotent consumers for IOT-EE service publishing | 0018 as amended by 0021, 0020 |
| TB administration | Documented REST API through ThingsBoardPort; API keys in OpenBao; no TB table writes or internal-topic access | 0020, 0021 |
| Frontend/service calls | HTTPS REST through APISIX/BFF, one scoped WebSocket; gRPC synchronous, Kafka asynchronous; communication draft remains proposed | 0005, 0017, application proposal |
| Identity/tenancy | Keycloak consoles, CE federation to verify, TB tenant mapping, service JWT verification, pooled tenant_id + PostgreSQL RLS | 0016, 0020, 0022 |
| Hosting/secrets | Twinfra supplies platform, PostgreSQL and OpenBao; IOT-EE ships application artifacts only | 0021 |
| Observability | Twinfra baseline: Prometheus, OpenTelemetry, Jaeger and Perses; separate traceparent and server-issued correlation IDs | 0015 as amended by 0021 |
| AI/RAG | Canonical topics → Flink → mandatory redaction → pgvector → tenant-scoped RAG; deferred proposals and unimplemented provider candidates | 0019 as amended by 0020, 0021 |
| Evidence | Owned S3 port to Twinfra SeaweedFS; Object Lock conformance before WORM claims | 0010, 0021 |
| Supply chain/licences | Pinned Syft, Grype, OSV-Scanner and Twinfra licence rules; implementation in IOT-WO-02 | 0014, 0021 |
| Packaging | Helm/Argo CD for Twinfra, portable OpenShift/OKD-compatible packaging; accepted live compatibility receipt before support claims | 0021 Amendment 1 |

M1 discovery/import tooling and M9 cutover orchestration are migration-manager's
scope. IOT-EE's migration-readiness epic exposes versioned, tenant-authorized
contracts and APIs. Legacy facts and approvals remain external inputs.
Feature epics follow MS5 in the approved plan; Deployment Studio is dropped
because Twinfra supplies deployment.

## Gates

```sh
mvn -B -f pom.xml verify
python spec/scripts/check.py
```

The Java gate compiles and runs unit/boundary tests; the Python gate checks
the retained frozen specification. CI runs both on pushes and PRs. Existing
infrastructure CI runs on its path scope and is unchanged. Passing these
gates does not establish deployment, security clearance, legacy parity,
WORM conformance, recovery or production readiness. Root Multipass scripts
are outside the supported test path and must not be executed by CI.

Read [architecture](docs/architecture.md), [test plan](docs/test-plan.md),
[requirements amendments](docs/requirements-addendum.md),
[ADR index/dispositions](docs/adr/README.md) and the
[work order](docs/work-orders/IOT-WO-01-snapshot-and-decisions.md).
[AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) carry the same development
contract. All changes require a PR, CI and human review.
