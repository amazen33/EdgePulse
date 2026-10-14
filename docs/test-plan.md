# Stage acceptance and regression gates

Every stage delivers code, tests, docs, deployment artifacts, its complete relevant gate, and the full accumulated regression gate. A failed or unavailable required gate blocks acceptance. PR/CI/human review is mandatory; report actual commands/results and external checks separately.

M0: `python spec/scripts/check.py` (formerly `python scripts/check.py`, before the `spec/` relocation) runs all current unit tests, fixture validation, inert plan policy checks, and required-artifact checks. CI runs the same command on Linux and Windows with Python 3.11 and 3.14. It never runs root Multipass scripts, connects to legacy systems, or provisions cloud resources. Deployment artifact is a validated non-executable foundation plan; this stage does not include an application deployment.

| Stage | Required additions to the full gate |
| --- | --- |
| M1 | Source registration/authorization, vault write/reference-only persistence, secret redaction, dry-run non-mutation, approval transitions and evidence; provider integration tests in isolated test environment |
| M2 | Tenant boundary/negative authorization tests; device/asset relations, fixed versus reported device location, coordinate and freshness invariants, unit/formula reference cases, schema compatibility |
| M3 | MQTT/PostgreSQL/Kafka/TB integration; transactional outbox crash/retry; duplicate/out-of-order/replay; tenant isolation; Kafka-to-TB CE bridge conformance against the pinned CE version, including credential mapping, broker outage catch-up, event-ID deduplication, ambiguous HTTP result and effect-level safety for side-effecting rules; approved read-only PostgreSQL schema/relationship profiling and versioned mapping on limited data; approved limited CDC snapshot-plus-stream into isolated shadow data, checkpoint/restart and source-lag tests; tenant-scoped rule-node inventory and same-position golden shadow parity with approved tolerances; quarantine and recovery |
| M4 | APISIX auth/rate/version tests, SSR/BFF end-to-end, WebSocket subscription authorization/reconnect, accessibility, tenant/device-scoped map snapshot and live-delta tests (SSE where selected), location freshness and viewport bounds, cross-tenant/revoked-access rejection, reconciled certified reports and publication approval |
| M5 | Signature/compatibility rejection, provenance, canary/pause/rollback, interrupted downloads and device verification; representative hardware integration |
| M6 | Append-only/WORM retention and privileged deletion tests, hash verification, fault injection, load/soak and backup restore/DR against approved RPO/RTO |
| M7 | Finalized usage only, duplicate safety, effective-dated pricing, period closure/reversals, billing outage isolation |
| M8 | Plan policy, least-privilege runner, approval audit, IaC validation/plan, GitOps reconciliation, isolated environment deployment and rollback across approved profiles; Migration Studio rehearsal monitors CDC lag/source health and proves checkpoint restart plus target restore without production cutover |
| Graduation (post-M8) | Real (test-target) S3 WORM adapter: put/get/list/legal-hold/expire contract conformance against a fake client (mandatory), plus one real-network round trip against a live test bucket, gated on `WORM_S3_BUCKET` and reported as skipped (not passed) when absent |
| M9 | Final legacy import: scoped inventory coverage (including every TB CE data class marked present, imported/rebuilt/archived/excluded with evidence), consistent snapshot/CDC position and gap-free idempotent catch-up, approved PostgreSQL relationship/data-quality baseline and same-position source/target counts, hashes, aggregates, latest state and semantic reconciliation; authorized combinable test filters for tenant ID/resolved name, mapped device ID and half-open UTC period, with ambiguity/cross-tenant rejection and complete approved-scope coverage beyond filtered samples; per-tenant rule-node ownership, rule/alarm parity and dashboard/report visible-value parity by role and filter, with approved tolerances and owner sign-off; verify operational workflows and SQL have no legacy-query/runtime dependency, and adapted report queries use only tenant-scoped target-owned read models; lag and source-health evidence, rollback rehearsal, acceptance and authorized cutover in a representative isolated environment; no automatic secret import (`docs/requirements-addendum.md`; source-by-source plan: `docs/legacy-migration-execution-plan.md`) |
| AI integration (proposed AI ADR; after PF-C C5) | `python tools/policy/check.py` and its tests; per provider/model: adapter contract tests, then an evaluation suite (groundedness and citation accuracy, cross-tenant and redaction leakage, injection resistance, refusal of forbidden actions); fault injection proving AI outages do not affect telemetry, alarms or commands. Every integration stays `unimplemented` until these pass (`docs/ai-device-traceability.md`) |
| Device adapters (proposed device ADR; M3) | `python tools/policy/check.py` and its tests; per transport and device class: authentication and per-device ACLs, capability negotiation, unit/time mapping, offline/late data, dedupe and replay, authenticated acknowledgement, vault credential lifecycle, firmware signature/compatibility. Legacy classes need representative hardware or authorized captures before `supported` |
| PF (Platform Foundation, Java) | `mvn -B -f pom.xml verify`: compile, unit tests, ArchUnit boundary rules with negative fixtures, contract validation; each PF-C step's exit criterion in `docs/track-c-execution-plan.md`. Not a numbered milestone (proposed milestone-naming ADR) |

PF-C C2a validates the Layer 3 installation **before** C2b service
instrumentation: static artifact/version checks, then synthetic OTLP
trace/log/metric ingest and query plus a paired-span Grafana/Tempo
Service Graph edge on the approved lab cluster, storage and access
checks, restart/recovery, alert routing, resource isolation
and an owner-approved soak interval. C2b subsequently proves
application `traceparent` and `X-Correlation-ID` propagation on that
installed stack. The lab Layers 0-2 and Layer 3 are not deployed yet;
neither gate is currently passed. See
`docs/adr/XXXX-proposed-observability-installation-sequence.md`.

For each implemented remote dependency, stage tests must exercise its documented deadline, retry budget and owner, circuit breaker/bulkhead where applicable, bounded backlog, failure isolation, ambiguous-write reconciliation and recovery alert. M6 adds combined load, sustained-fault and DR proof; it does not defer all resilience implementation until M6. See `docs/adr/XXXX-proposed-resilience-and-workflow-patterns.md`.

Future gates must be implemented before claiming those stages complete. M0 tests do not establish production security, rule parity, broker connectivity, WORM retention, or infrastructure readiness. Dependency scanning/SAST, deployment smoke tests, and performance gates must expand with the chosen stack and services.
