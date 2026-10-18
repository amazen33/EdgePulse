# Proposed ADR -- Migration Studio CDC and tenant-scoped rule migration

> Moved to migration-manager's scope by ADR 0022; kept as its input specification.

Status: proposed. Supplements ADR 0002 and the M9 migration sequence in
`docs/requirements-addendum.md`. No legacy source has been inspected or
authorized for CDC. Full production import and cutover remain in M9.

## Context

Migration Studio currently models source registration and approval but
does not connect to a legacy system. The M9 plan calls for delta
catch-up without naming a capture mechanism. A bulk snapshot alone
cannot preserve changes made while the legacy system remains live.
Rule chains and custom nodes also require tenant ownership, policy and
behavioral parity; copying their configuration without those checks
could execute one tenant's logic against another tenant's data.

## Proposed decision

1. **Migration Studio is the control plane.** It versions source and
   table selections, tenant mappings, transformations, vault secret
   references, capture mode, retention, approval and run state. A
   service-owned connector adapter performs extraction/CDC. The
   browser never holds replication credentials or executes database
   commands. The frozen M1 Python module remains a no-network
   reference; live adapters are later Java work. Its UI exposes
   source/tenant scope, dry-run preview, snapshot and stream position,
   lag and source-health status, quarantined records, evidence manifests,
   pause/resume and approval through authorized backend APIs.
2. **CDC is a capability, not a vendor dependency.** A PostgreSQL
   logical-decoding connector (Debezium is a candidate) may capture
   changes if the inspected legacy source version, permissions,
   publication/slot support, stable row identity, WAL capacity and
   recovery procedure pass a source-specific proof. Other sources use
   their own tested adapters. Never assume that CDC from legacy
   PostgreSQL captures every ThingsBoard CE entity, Mosquitto message,
   rule change or report definition. TB CE configuration needs a
   supported export/API or a separately verified change source.
3. **Snapshot and stream form one ordered migration run.** Record a
   consistent snapshot boundary and source position, load bounded
   snapshot partitions, then consume changes from that position.
   Normalize insert/update/delete semantics explicitly. Apply each
   change idempotently using a source-owned row identity plus source
   transaction position and event order. Commit the target effect and
   applied checkpoint atomically where supported; otherwise prove
   replay safety with an inbox/dedupe table. A missing key, unknown
   tenant, schema drift or ambiguous delete goes to quarantine, never
   an inferred target mutation.
4. **Preserve the stage boundary.** Before M9, only approved limited
   captures may populate isolated shadow data for mapping and parity;
   shadow data cannot drive commands, alarms, billing or tenant-facing
   production reads. The full stream, operational application, writer
   switch and cutover require the M9 gate. A change to that boundary
   requires an explicit revised decision.
5. **Tenant ownership is mandatory for migrated rules.** Each
   rule-chain instance and node has a source tenant ID mapped to exactly
   one target `tenant_id`, plus source ID, version, dependency manifest
   and approval. A reusable platform template may be shared as an
   immutable definition, but every active tenant instance and its
   state are tenant-scoped. Missing or conflicting tenant identity,
   cross-tenant references, unreviewed custom code or an unauthorized
   device scope blocks activation. Rule execution and downstream events
   carry and recheck `tenant_id`; database RLS is the second guard.
6. **Evidence is a release gate.** Each run records source/version,
   approved table and tenant scope, schema and transform hashes,
   snapshot boundary, source positions, connector version, partition
   and batch counts, quarantine reasons, lag, checkpoint continuity,
   rule-graph hashes, golden parity results, approvers and cutover
   decision. Store manifests and hashes in the controlled evidence
   system; keep raw data, secrets and PII out of logs, prompts and Git.
   A capture is successful only when completeness, integrity, semantic
   parity, tenant isolation, lag and recovery meet owner-approved
   thresholds. No threshold is invented by this ADR.
7. **Use the legacy database as an evidence baseline, not a complete
   behavior specification.** After source approval, profile legacy
   PostgreSQL read-only on a controlled snapshot/replica or within a
   DBA-approved live query budget. Version the schema/relationship
   inventory and source-to-target mapping; verify inferred joins with
   source owners. Compare tenant-scoped records, aggregates and latest
   state at the same snapshot/CDC position, using preapproved conversion
   tolerances. Prove rule, alarm, dashboard and report parity separately
   with authorized TB CE exports and fixed-role golden cases. An
   unexplained visible or behavioral difference blocks M9 cutover even
   if database counts match. Studio exposes curated results and evidence
   through backend APIs, never arbitrary source SQL or credentials.
   Legacy SQL outside reports is limited to migration profiling and
   reconciliation; IOT-EE operational workflows and persistence queries
   are designed independently. Legacy report SQL and outputs may serve
   as versioned compatibility references. Any reused or translated
   query runs only in a reporting adapter against a certified target-owned
   read model, with tenant scoping and parity tests; it never creates a
   production dependency on the legacy database.
8. **Make reconciliation filterable without weakening coverage.** The
   Studio accepts tenant ID or a tenant name resolved to one versioned
   tenant ID, mapped source/target device ID, and an explicit half-open
   UTC event-time period. Filters can be combined and must be authorized
   before any source or target query. Record filter, identity-map and
   query versions, snapshot/CDC position and result manifest. An
   ambiguous tenant name or cross-tenant device selection fails closed.
   Drill-down tests support diagnosis, while M9 release still requires
   full approved scope coverage across tenants, devices and periods.

## Required proofs before an operational CDC run

- A source-specific snapshot-plus-stream test demonstrates no missing
  change at the boundary, with duplicate, retry, restart and connector
  failover cases. Source schema changes and replication-slot/WAL growth
  trigger alarms and a documented pause/resnapshot path.
- An isolation test tries a missing, forged and cross-tenant mapping;
  no target tenant row or rule activation changes.
- A delete/correction test proves history, latest state and target
  idempotency semantics, including replay after checkpoint recovery.
- A per-tenant rule test compares golden outcomes and alarm effects
  with the legacy system and rejects cross-tenant rule edges.
- A same-position data and visible-result test compares approved
  legacy and target records, relationships, aggregates, latest device
  values and dashboard/report cases by tenant, role, filter and time
  window; each unexplained difference is a no-go.
- A rehearsal produces a complete evidence manifest, restores the
  target, resumes capture, reaches approved lag, and demonstrates a
  viable rollback or forward-fix path after target writes begin.

## Open inputs

Legacy PostgreSQL and TB CE versions; source ownership and approvals;
table/tenant key inventory; actual data volumes and change rate;
whether logical decoding is permitted; replication-slot/WAL budget;
TB CE configuration export mechanism; rule-node dependencies and
licenses; per-tenant parity tolerances; acceptable lag, RPO/RTO,
retention and rollback window. Until these are supplied, the design is
proposed and CDC readiness is blocked.

## Sources for mechanism, not for this legacy deployment

- [Debezium PostgreSQL connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html): initial snapshot, stream position, restart behavior and slot considerations.
- [PostgreSQL logical decoding concepts](https://www.postgresql.org/docs/current/logicaldecoding-explanation.html): replication-slot retention and source resource impact.
- [ThingsBoard Rule Engine](https://thingsboard.io/docs/user-guide/rule-engine/): tenant rule-chain model. The legacy installation must still be inspected.
