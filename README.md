# EdgePulse (formerly IOT-EE)

EdgePulse is an IoT platform in foundation development. Its partly implemented
Java foundation is evidenced by merged [PR #14](https://github.com/amazen33/EdgePulse/pull/14),
[PR #21](https://github.com/amazen33/EdgePulse/pull/21) and
[PR #29](https://github.com/amazen33/EdgePulse/pull/29). The accepted target
uses ThingsBoard CE as its operational core with autonomous Java services
around it, under [ADR 0020](docs/adr/0020-tb-ce-operational-core.md),
[Twinfra hosting and licence gate](docs/adr/0021-twinfra-platform-and-licence-gate.md)
and [migration-manager integration](docs/adr/0022-migration-manager-integration.md).
The approved roadmap is [MILESTONES.md](MILESTONES.md).

MS0 Reset: accepted 2026-10-18 ([receipt](docs/acceptance/ms0-reset-2026-10-18.md)); pre-release v2.0.0-alpha.3 (tags v2.0.0-alpha.1 and v2.0.0-alpha.2 were never released). MS2 migration contract v1.0.0-draft: accepted 2026-10-19 ([receipt](docs/acceptance/ms2-migration-contract-v1-2026-10-19.md)); pre-release v2.0.0-alpha.4. MS1 (IOT-WO-02): in progress; licence and supply-chain code/CI foundations are merged ([#46](https://github.com/amazen33/EdgePulse/pull/46), [#48](https://github.com/amazen33/EdgePulse/pull/48)). Part C runtime work precedes Part D quality work under Amendment 5; MS1 acceptance remains pending.
[MILESTONES.md](MILESTONES.md) defines the sequence and required receipts;
runtime integrations remain pending.

Tool-agnostic, hybrid-cloud, cross-vertical and AI capabilities remain
unproven. Each needs a milestone receipt before it can be claimed. AI is
deferred epic F5 after MS5; no AI execution path is implemented. Merged PRs
below evidence only their stated foundation artifacts and tests.

## Status

| Area | Foundation artifacts / evidence | Next work / evidence required |
| --- | --- | --- |
| Java foundation | Maven reactor, correlation, configuration schema and boundary rules ([#14](https://github.com/amazen33/EdgePulse/pull/14), [#17](https://github.com/amazen33/EdgePulse/pull/17)); REST/gRPC query ([#21](https://github.com/amazen33/EdgePulse/pull/21)); caller authorization ([#29](https://github.com/amazen33/EdgePulse/pull/29)) — all merged | Identity federation, persistence, messaging and operational integrations remain unimplemented |
| Python reference | Python reference archived at [archive/python-spec-final](https://github.com/amazen33/EdgePulse/tree/archive/python-spec-final/spec); relocation history in merged [#12](https://github.com/amazen33/EdgePulse/pull/12) | Removed from active checkout and CI; no platform milestone completion inferred |
| Decision records | ADRs 0014 and 0020–0023, the draft dispositions and approved milestone plan define the target | Later work orders implement the decisions |
| TB CE core | Inventory and plan-only customization manifest from merged [#13](https://github.com/amazen33/EdgePulse/pull/13); dated spike retained as historical input | MS3 deployment/upgrade rehearsal and MS5 event path await implementation and acceptance receipts |
| Migration | M1/M9 moved to EdgeMig; execution plan retained as its input specification | EdgePulse readiness MR-1 to MR-14: MS2 contracts, then MS4–MS6 implementation |
| Deployment | Own-infrastructure history is preserved in [archive/iot-ee-own-infra](https://github.com/amazen33/EdgePulse/tree/archive/iot-ee-own-infra/deploy/); active application sources are under [charts/](charts/) and the isolated [kind harness](dev/kind/) | Runtime integration and Argo CD application delivery require their work orders and acceptance receipts |
| Gates and runtime | Java [#14](https://github.com/amazen33/EdgePulse/pull/14), release [#36](https://github.com/amazen33/EdgePulse/pull/36), licence [#46](https://github.com/amazen33/EdgePulse/pull/46) and supply-chain [#48](https://github.com/amazen33/EdgePulse/pull/48) code/CI foundations are merged | IOT-WO-02 Part C runtime baseline, then Part D quality gate; MS1 receipt remains pending |

The snapshot is preserved at `archive/reconcile-snapshot-2026-09-26`;
it is not a merge source wholesale. The dated
[enterprise readiness review](docs/enterprise-readiness-review.md) and
[2026-10-14 review](docs/reviews/iot-ee-review-2026-10-14.md) record their own
evidence limits. They do not establish current runtime readiness.

## Platform

The integration rows below are accepted design targets, not working platform
capabilities. Existing foundation evidence is limited to the linked PRs above;
an ADR alone does not prove implementation, portability or runtime acceptance.

| Concern | Accepted direction / implementation limit | Authority |
| --- | --- | --- |
| Runtime | Java 21 build/CI baseline; Spring Boot 3.3.4 / Spring Cloud 2023.0.3 unchanged. Supported Spring upgrade remains IOT-WO-02 Part C; [pin and checks](docs/runtime/java21-baseline.md) | 0011, 0012, 0021 |
| Structure | Autonomous services, versioned contracts, hexagonal ports/adapters; no shared runtime libraries | 0013, 0017 |
| TB CE and devices | TB CE owns MQTT/HTTP/CoAP transports, devices/assets/relations, telemetry/attributes, rules, alarms and dashboards; unforked | 0020 |
| Events | TB outbound Kafka node → raw topic → ingestion adapter → canonical topics; Apache Kafka only; outbox/idempotent consumers for EdgePulse service publishing | 0018 as amended by 0021, 0020 |
| TB administration | Documented REST API through ThingsBoardPort; API keys in OpenBao; no TB table writes or internal-topic access | 0020, 0021 |
| Frontend/service calls | HTTPS REST through APISIX/BFF, one scoped WebSocket; gRPC synchronous, Kafka asynchronous; communication draft remains proposed | 0005, 0017, application proposal |
| Identity/tenancy | Keycloak consoles, CE federation to verify, TB tenant mapping, service JWT verification, pooled tenant_id + PostgreSQL RLS | 0016, 0020, 0022 |
| Hosting/secrets | Target: Twinfra provides platform, PostgreSQL and OpenBao; future EdgePulse application artifacts are images, Helm charts and Argo CD Applications | 0021 |
| Observability | Twinfra baseline: Prometheus, OpenTelemetry, Jaeger and Perses; separate traceparent and server-issued correlation IDs | 0015 as amended by 0021 |
| AI/RAG (F5, unimplemented) | Design only: canonical topics → Flink → mandatory redaction → pgvector → tenant-scoped RAG; no AI capability claimed | 0019 as amended by 0020, 0021 |
| Evidence | Owned S3 port to Twinfra SeaweedFS; Object Lock conformance before WORM claims | 0010, 0021 |
| Supply chain/licences | Pinned Syft, Grype, OSV-Scanner and Twinfra licence rules; implementation in IOT-WO-02 | 0014, 0021 |
| Packaging | Helm/Argo CD for Twinfra, portable OpenShift/OKD-compatible packaging; accepted live compatibility receipt before support claims | 0021 Amendment 1 |

M1 discovery/import tooling and M9 cutover orchestration are EdgeMig's
scope. EdgePulse's migration-readiness epic exposes versioned, tenant-authorized
contracts and APIs as future work. Legacy facts and approvals remain external inputs.
Feature epics follow MS5 in the approved plan; Deployment Studio is dropped
because Twinfra supplies deployment.

## Security

See [SECURITY.md](SECURITY.md) for supported versions and private vulnerability reporting.

## Gates

```sh
mvn -B -f pom.xml verify
bash .github/scripts/naming_gate.sh
```

The Java gate compiles and runs unit/boundary tests on pushes and PRs.
The naming gate checks tracked paths and contents, with approved historical
and frozen-file exceptions and exact historical path/tag references. Its CI
self-test proves that an exempt reference cannot hide a separate retired name.
The Python reference and its former gate are available only in tag
archive/python-spec-final. Own-infrastructure sources and their former static
gate are preserved in [archive/iot-ee-own-infra](https://github.com/amazen33/EdgePulse/tree/archive/iot-ee-own-infra).
The current licence gate is documented in [security/README.md](security/README.md). Passing these
gates does not establish deployment, security clearance, legacy parity,
WORM conformance, recovery or production readiness. Root Multipass scripts
are outside the supported test path and must not be executed by CI.

Read [architecture](docs/architecture.md), [test plan](docs/test-plan.md),
[requirements amendments](docs/requirements-addendum.md),
[ADR index/dispositions](docs/adr/README.md) and the
[work order](docs/work-orders/IOT-WO-01-snapshot-and-decisions.md).
[AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) carry the same development
contract. All changes require a PR, CI and human review.

Current contributor roles and approval boundaries are in [development team](docs/development-team.md). OpenCode is excluded from the EdgePulse team.
