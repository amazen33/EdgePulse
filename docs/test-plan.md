# Stage acceptance and regression gates

Every stage delivers code, tests, docs, deployment artifacts, its complete relevant gate, and the full accumulated regression gate. A failed or unavailable required gate blocks acceptance. PR/CI/human review is mandatory; report actual commands/results and external checks separately.

The approved sequence is [MILESTONES.md](../MILESTONES.md). The table retains historical capability references, not a second roadmap. EdgePulse owns migration readiness MR-1 to MR-14 (ADR 0022); EdgeMig owns M1/M9 orchestration. New application deployment artifacts are a Helm chart and Argo CD Application for Twinfra (ADR 0021). Supply-chain gates follow ADR 0014; implementation is pending IOT-WO-02. No real-environment execution is claimed here.

Evidence and claim rule: every "done" or other completion claim must link
to a merged PR or receipt for that exact scope. Local/CI tests do not prove
milestone acceptance or runtime capability. Tool-agnostic, hybrid-cloud,
cross-vertical and AI capabilities require milestone receipts. AI is F5 work,
not a tested execution path. The rows below specify required tests rather
than completed milestones.

Current platform regression gate: `mvn -B -f pom.xml verify`, including
unit tests and ArchUnit boundary checks. Applicable static infrastructure
and release checks remain required; no check may contact a host or cluster.

The former Python foundation gate and its unit tests, fixture validation,
inert plan checks and required-artifact checks are archived with the frozen
M0–M8 reference at [archive/python-spec-final](https://github.com/amazen33/EdgePulse/tree/archive/python-spec-final/spec).
Its historical `python spec/scripts/check.py` command belongs to that tag;
it is not run by active CI. Relocation history remains merged
[PR #12](https://github.com/amazen33/EdgePulse/pull/12).

| Stage | Required additions to the full gate |
| --- | --- |
| M1 — moved to EdgeMig (ADR 0022) | Historical input specification: source registration/authorization, vault write/reference-only persistence, secret redaction, dry-run non-mutation, approval transitions and evidence; provider integration tests in isolated test environment |
| M2 | Tenant boundary/negative authorization tests; device/asset relations, domain invariants, unit/formula reference cases, schema compatibility |
| M3 | ADR 0020 TB transport/rule engine → outbound Kafka → ingestion adapter → canonical-topic integration; transactional outbox crash/retry; duplicate/out-of-order/replay; tenant isolation; golden rule shadow parity with approved tolerances; quarantine and recovery |
| M4 | APISIX auth/rate/version tests, SSR/BFF end-to-end, WebSocket subscription authorization/reconnect, accessibility, reconciled certified reports and publication approval |
| M5 | Signature/compatibility rejection, provenance, canary/pause/rollback, interrupted downloads and device verification; representative hardware integration |
| M6 | Append-only/WORM retention and privileged deletion tests, hash verification, fault injection, load/soak and backup restore/DR against approved RPO/RTO |
| M7 | Finalized usage only, duplicate safety, effective-dated pricing, period closure/reversals, billing outage isolation |
| M8 (historical spec; Deployment Studio dropped by MILESTONES.md) | Plan policy, least-privilege runner, approval audit, IaC validation/plan, GitOps reconciliation, isolated environment deployment and rollback across approved profiles |
| M9 — moved to EdgeMig (ADR 0022) | Historical input specification: authorized inventory, import, same-position reconciliation, rule/report parity, delta catch-up, approval, rollback rehearsal and cutover; EdgePulse exposes the MR integration surface |
| Graduation (post-M8) | Adapter code: merged [PR #11](https://github.com/amazen33/EdgePulse/pull/11); no live-backend success claimed. Required checks: put/get/list/legal-hold/expire contract conformance against a fake client (mandatory), plus one real-network round trip against a live test bucket, gated on `WORM_S3_BUCKET` and reported as skipped (not passed) when absent |

Future gates must be implemented before claiming those stages complete. M0 tests do not establish production security, rule parity, broker connectivity, WORM retention, or infrastructure readiness. Dependency scanning/SAST, deployment smoke tests, and performance gates must expand with the chosen stack and services.
