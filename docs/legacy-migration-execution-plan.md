# Legacy data migration plan

> Moved to migration-manager's scope by ADR 0022; kept as its input specification.

Status: proposed execution plan. No legacy system has been inspected, no
production data has been exported, and no cutover has been authorized.
This plan makes the existing M1/M3/M9 sequence operational; it does not
move the full production import or cutover earlier than M9.

## Scope and stage boundaries

| Stage | Work allowed | Exit evidence |
| --- | --- | --- |
| Now, before further architecture commitments | Identify source owners, actual versions, topology, data classes, access approval, system of record per entity, and representative data shapes. Use documentation and explicitly approved limited samples only. | Signed inventory and mapping risks; unknowns remain visible. No production import. |
| M1 Migration Studio | Register sources, validate configuration, preview mappings, record approvals and redacted evidence; integrate a real vault only after isolated provider tests. | Source registrations and access scopes reviewed; no live import or cutover capability. |
| M3 and subsequent build stages | Implement tested source adapters, canonical mappings, optional approved limited CDC into an isolated shadow read model, and shadow comparison. Build per-tenant golden rule/report datasets and compatibility tests. | Per-source snapshot/stream and parity tests; shadow data drives no production action; no full production import. |
| M8 | Deploy an isolated target environment and rehearse deployment rollback, backup/restore, CDC monitoring and access control. | Recovery and capture-restart evidence and a ready target; no production cutover. |
| M9, final stage | Perform authorized full export/import, CDC delta catch-up, reconciliation, approval, traffic switch and recovery rehearsal. | Signed per-tenant acceptance record and monitored cutover; legacy remains recoverable for the agreed period. |

## Source inventory to complete before connector design

The legacy shape below comes from supplied requirements, not live
inspection. Record the real version, owner, endpoint, schema, volume,
time span, retention, update rate, export method and authorization for
each source before approving its connector.

| Source | Candidate data | Open verification |
| --- | --- | --- |
| Legacy PostgreSQL | Historical telemetry and any application tables identified by inspection; candidate CDC source for subsequent changes | Schema, primary keys, timestamp semantics, partitions, late corrections, counts, retention, PostgreSQL version, logical-decoding rights and WAL/slot capacity. |
| ThingsBoard CE | Entity/configuration data, attributes, telemetry, rules, alarms, dashboards and operational state listed below | Exact legacy CE version, storage backend, supported export/API paths, custom code dependencies and licenses, and which records are authoritative. |
| Mosquitto layers | Live messages or mirrors for delta capture and shadow comparison | Broker topology, topics, QoS, retained messages, durable history if any, device authentication and replay behavior. Do not assume a broker is a historical database. |
| Reports and external sources | Definitions, schedules, historical exports and reference data | Source of each figure, time zone, formulas, access rights and approved parity tolerance. |

### Read-only PostgreSQL analysis and parity baseline

With source-owner and DBA approval, profile the actual legacy PostgreSQL
schema through least-privilege, read-only access. Prefer a controlled
snapshot or replica; any query against the live primary must have an
approved scope, resource budget and timeout. Inventory tables, columns,
types, primary/foreign keys, indexes, partitions, views, triggers and
relevant functions. Use bounded joins and application/TB CE exports to
investigate relationships that the database does not declare as foreign
keys; have the source owner confirm inferred relationships before they
become migration mappings. This analysis is design and validation work,
not an early production import.

For each approved table and tenant, record stable keys, tenant and
device ownership, row counts by time range, null/duplicate/orphan rates,
relationship cardinality, update/delete and late-correction behavior,
units, timestamp precision/time zone and the rule for selecting a
device's latest value. Build a versioned source-table/column to canonical
entity to target-owner mapping matrix with source-of-truth decisions.
Where PostgreSQL and TB CE disagree, quarantine the mapping until the
owner identifies which system is authoritative for that data class.
Migration Studio should show approved schema and relationship analysis,
mapping versions, baseline query IDs, discrepancies and evidence links
through authorized backend APIs; it must not expose arbitrary SQL
execution or source credentials in the browser.

Legacy operational SQL is **not** a specification or runtime dependency
for IOT-EE workflows, services, or their persistence queries. The
profiling queries above run only in the controlled migration/verification
workflow. New services use their own domain contracts and service-owned
data models; no production request depends on a legacy table, view,
stored procedure, or query. The limited exception is **reports**:
inventory and version legacy report SQL, parameters, formulas and
expected outputs as a compatibility reference. An approved report may
be translated or reimplemented against a certified IOT-EE reporting
read model, then compared on the same data, tenant scope and time
window. If a query can be reused safely, it remains confined to the
reporting adapter and target-owned read model. It must not expose
cross-service databases or create a live dependency on legacy
PostgreSQL. Report owners approve semantic and displayed-value parity.

Run versioned, bounded, read-only baseline queries at a recorded
consistent snapshot or source position. Record PostgreSQL and schema
versions, query/configuration hashes, tenant and time scope, snapshot
boundary, counts and aggregate digests in access-controlled evidence.
Do not store raw PII, credentials or production extracts in Git,
prompts, logs or the Studio application database. Compare the target at
the **same logical source position**, including CDC catch-up, so ongoing
writes do not create false mismatches. Compare per-tenant/entity/time
counts and relationships, selected row-level values or digests,
historical aggregates and latest device state. Exact identity and
ownership checks are mandatory; numeric conversion, rounding and time
display tolerances must be documented and approved before the run.

Database equality alone does not prove behavioral or visible parity.
Inventory TB CE rule graphs, custom code, alarms, calculated values,
dashboard/widget definitions and report formulas through authorized
exports or APIs. At a fixed data position and user role, replay approved
synthetic or redacted golden cases in isolated environments and compare
rule outputs, alarm transitions, calculations and safe side effects.
Compare approved legacy and target dashboard/report views by tenant,
role, hierarchy/device filter and time window: displayed values,
labels, units, time zones, ordering, rounding and freshness must agree
within preapproved tolerances. Layout may improve; screenshots alone
cannot prove data or rule equivalence. Product and tenant owners sign
off the parity matrix and every justified exception.

### Migration test filters and coverage

Migration Studio must let an authorized reviewer classify and filter
reconciliation results by **tenant ID**, **tenant name**, **device ID**,
and **time period**, independently or in combination. Tenant ID is the
stable filter key. A tenant-name search first resolves to the source
and target tenant IDs in the versioned identity map; duplicate or
renamed names require explicit selection and cannot silently combine
tenants. Device ID accepts a source or target ID only after resolving
the recorded legacy-to-target device map and verifying it belongs to
the selected tenant. A cross-tenant device filter is denied, not
reported as an empty successful comparison.

Time periods use a specified source event-time field and half-open UTC
interval `[start, end)` on both sides. Show the user's local time zone
only for display; record source zone, precision, inclusive/exclusive
boundary and snapshot/CDC watermark in the test definition. For
classes without event time (for example hierarchy or rule definitions),
use a recorded as-of snapshot rather than pretending they fall in a
telemetry period. Late-arriving or corrected records are reconciled
against the same watermark and reported separately.

Each filter combination produces a repeatable test case with query and
mapping versions, source/target counts and digests, unmatched IDs,
field-level differences, relationship checks, latest-state and
aggregate comparisons where relevant, approved tolerances, exception
status and evidence links. Results are paginated and redacted; access
to a summary never grants access to another tenant's raw rows. Cover
all authorized tenants, devices and periods in the M9 aggregate gate;
a passing selected-device or short-period test cannot certify the
whole migration. Include boundary periods, zero-data devices and
representative high-volume devices in drill-down tests.

Inventory by tenant and data class. Identify the authoritative source
for each device, hierarchy node, telemetry series, alarm, rule state,
user and report. A record with conflicting owners is quarantined until
the ownership decision is made; no cross-context database write is
allowed. Capture source version and export manifest with counts and
checksums in controlled evidence storage, never in Git or prompts.

### ThingsBoard CE layer coverage

The following is an inventory checklist, **not a claim that any class
exists in the legacy deployment**. For each class, record present or
absent, tenant scope, count, supported export method, source version,
target owner, mapping version, parity test and decision to import,
rebuild, archive or exclude. Prefer supported exports/APIs; direct
database reads require a reviewed, read-only extraction plan. Never
write directly to TB CE's internal tables.

| TB CE data class to verify | Planned treatment and main check |
| --- | --- |
| Tenants, customers, users, groups/roles and assignments | Map tenant and organization identity to the new identity context; compare memberships and effective permissions. Re-enroll or federate users; do not import password hashes, sessions, API keys or tokens. |
| Devices, assets, entity relations, locations, customer assignments and profiles | Import through the owning device/asset services with a stable legacy-to-target ID map; validate hierarchy, ownership, profile behavior and cross-tenant isolation. |
| Server, shared and client attributes; desired and reported device state | Classify mutable configuration versus observations; map allowed properties and compare effective latest state. Never import credential-valued attributes as ordinary data. |
| Historical time-series and latest telemetry | Determine whether TB CE or the separate legacy PostgreSQL history is authoritative for each series and time range. Reconcile duplicates, late corrections, units and timestamps; preserve latest-value semantics. Identify TB CE's actual time-series backend before sizing extraction. |
| Rule chains, node configurations, scripts/custom nodes, calculated fields and alarm rules | Inventory and map each chain/node to its owning source tenant and target `tenant_id`; preserve versioned source artifacts as controlled evidence, review code/dependencies/licenses, and rebuild or adapt behavior behind the target boundary. Require per-tenant golden input/output and alarm parity before enabling. |
| Alarm records, acknowledgement/clear history and active alarms | Preserve historical decisions and current active state separately; reconcile lifecycle timestamps, actors, severity and device scope. Do not replay old alarms as new operational alerts. |
| Dashboards, widgets, maps, views, notifications and report definitions/exports | Inventory definitions, report SQL/parameters and dependencies. Rebuild or safely translate report queries only against certified target-owned reporting read models; compare approved visible results and archive historical exports where required. Do not infer logic from screenshots or carry legacy SQL into operational services. |
| Integrations, transport configuration, queues and scheduled/notification jobs | Record topology and behavior for replacement or reconfiguration. Treat credentials as new vault-backed provisioning; do not copy secrets or blindly start jobs that could duplicate commands/messages. |
| OTA package metadata/artifacts and rollout state, if present | Map only verified packages and provenance into the firmware context; require signatures, device compatibility and rollout-state reconciliation. Do not assume a legacy artifact meets new on-device verification rules. |
| Audit/debug events, logs, transient queues, caches and sessions | Set an explicit archive or exclusion decision and retention rule. Operational caches/sessions are normally recreated; historical evidence is preserved in an authorized evidence store, not replayed as live events. |

The actual legacy CE version may differ from the target CE v4.3.1.5 in
`docs/tb-ce-inventory.md`. Export formats, data classes and upgrade
compatibility must be checked against the **legacy** version before a
connector or migration transform is approved.

## Mapping and validation contract

- Version every mapping configuration. Resolve arbitrary approved
  hierarchy depths from configuration; preserve parent-child relations
  and stable tenant-scoped IDs through an explicit legacy-to-target ID
  map. Reject cycles, orphans, duplicate keys and cross-tenant links
  unless an approved rule resolves them.
- Map timestamps to UTC while retaining source time, zone/offset and
  precision as evidence where needed. Define units, conversion rules,
  missing-value handling and tolerance per telemetry key. Preserve
  the source value for reconciliation; do not silently coerce invalid
  readings.
- Give every imported record a deterministic source identity based on
  the source's stable key and version/revision. A retry must be
  idempotent, while two legitimate measurements must remain distinct.
  Quarantine records without a defensible identity instead of deduping
  by payload hash alone. Keep `event_id`, `causation_id`, tenant and
  correlation mapping compatible with ADRs 0012, 0015 and 0018.
- Treat rule chains, custom scripts and report formulas as reviewed
  executable logic, not ordinary data. Inventory dependencies and
  licenses, construct golden input/output sets, and obtain approval
  before enabling equivalent target behavior. Every active migrated
  chain/node, its state, device scope and emitted event must carry the
  mapped `tenant_id`. A shared template is an immutable definition;
  execution is a separately authorized tenant instance. Reject
  missing/ambiguous tenant mappings and cross-tenant graph edges. A
  screenshot is not evidence of rule semantics.
- Do not copy password hashes, device credentials, tokens or vault
  values. Plan user federation/invitation and device credential
  rotation or re-enrollment separately. Source access is read-only
  until the authorized M9 cutover procedure says otherwise.

Each adapter exposes validation, a dry-run preview, bounded extraction,
checkpoint/resume and a reconciliation manifest through Migration
Studio-owned ports. Connector implementation must not make another
bounded context's database its target; the owning service accepts
validated commands or imports through its own contract.
The frozen Python M1 module deliberately forbids network I/O; live
connectors belong in the later Java service adapters with their own
authorization and integration tests, not in that reference module.

## CDC capture through Migration Studio

Migration Studio owns the **control workflow**: register an approved
source and table scope, configure the vault reference, version tenant
and field mappings, validate, preview, approve, start/pause/resume a
run, and inspect evidence. A separately deployed connector adapter
owns the **data workflow**. PostgreSQL logical decoding with a tool
such as Debezium is a candidate, not a mandated implementation or an
assumed capability of the uninspected legacy system. TB CE rule and
configuration changes and Mosquitto messages need separate verified
capture paths; database CDC alone does not cover them.

| Capture step | Required evidence and failure rule |
| --- | --- |
| Authorize and inspect | Source/version, source owner, approved tables/tenants and export rights, stable row keys, source-of-truth decision, data classification, schema hash, least-privilege access and WAL/slot resource budget. Unknown or conflicting tenant ownership blocks the table. |
| Prove snapshot plus stream | In an isolated test, capture a consistent snapshot boundary and source position, then read changes from that position. Record both; prove a write committed across the boundary is present exactly once in target effect after dedupe. |
| Transform and route | Version and hash mapping code/configuration. Resolve the source tenant to one target `tenant_id` before any target write. Validate device IDs, units, timestamps, insert/update/delete semantics and authorized target owner. A replay or late older version cannot overwrite newer latest state. Quarantine missing keys, schema drift and ambiguous deletes. |
| Checkpoint and recover | Persist applied source position with target effect or prove replay-safe inbox semantics. Record batch IDs, accepted/duplicate/quarantined counts and last contiguous position. Restart, replay and reconnect tests must show no gap or duplicate effect. |
| Monitor source impact | Alert on connector lag, replication-slot/WAL growth, unavailable source positions, schema changes and capture errors. Pause before source health is endangered; resnapshot only through an approved recovery run. |
| Reconcile and release | Compare snapshot and delta counts/checksums plus tenant/device latest state and rule/report semantics. Record lag and high-watermark at approval. Unexplained discrepancy, cross-tenant write, source position gap or unapproved lag blocks cutover. |

Before M9, an explicitly approved limited capture may feed **isolated
shadow data only**. It cannot drive device commands, alarms, billing or
tenant-facing production reads. At M9, the authorized run performs the
full snapshot and continuous catch-up, then changes the authoritative
writer only after the evidence and human go/no-go gate. If logical CDC
is unavailable, choose and test another incremental mechanism after
source inspection; do not silently substitute timestamp polling.

### Tenant rule migration steps

1. Export the rule-chain graph, node configuration and custom code for
   each source tenant through an approved path. Record source IDs,
   tenant ID, version/hash, referenced devices/assets, dependencies,
   licenses and owner.
2. Map source tenant and entity IDs to target `tenant_id` and IDs.
   Quarantine orphan nodes, missing owners, cross-tenant edges and
   external calls lacking an approved adapter or secret reference.
3. Rebuild or adapt each node behind the target rule boundary. Review
   executable code and permissions; keep it disabled until sandbox
   tests compare golden inputs, outputs, alarms and side effects per
   tenant with approved tolerances.
4. Preview the graph and parity report for that tenant, obtain its
   authorized approval, then activate in a controlled ring at M9.
   Compare live outcomes and retain the prior graph/version for a
   tested rollback or forward fix. A platform template does not grant
   access to another tenant's data.

### Evidence package for each migration run

Migration Studio must produce a reviewable manifest with links to
access-controlled evidence, without embedding raw exports or secrets:

| Evidence item | Demonstrates |
| --- | --- |
| Source authorization and inventory | Which owner approved which version, tables, tenants, TB CE objects and time range. |
| Snapshot and CDC continuity report | Snapshot boundary, source position, every applied checkpoint, restart/failover results, gap count, duplicate-effect count, lag and source WAL/slot health. |
| Mapping and exception report | Transform/configuration hash, legacy-to-target IDs, per-tenant accepted/quarantined counts and resolution of every blocking exception. |
| PostgreSQL analysis and data parity baseline | Approved read-only query catalog and hashes, schema/relationship mapping matrix, source snapshot position, target checkpoint, tenant-scoped counts/digests, latest-state and aggregate comparisons, tolerances and discrepancies. |
| Filtered migration test matrix | Tenant ID and resolved tenant name, mapped device ID and half-open UTC period/as-of snapshot; combined-filter counts, differences, coverage and authorization results. |
| Rule and report parity package | Per-tenant rule graph/node hashes, golden input/output, alarm effects, report figures, tolerances and approver. |
| Visible-result parity package | Same-position legacy/target dashboard and report cases by tenant, role, filter and time window; compared values, units, time zones, rounding and freshness, with owner sign-off. |
| Reconciliation and recovery record | Per-source/tenant/entity/time counts and checksums, latest state, backup restore, rollback or forward-fix rehearsal, and final go/no-go signatures. |

Success requires all applicable items to pass the owner-approved
thresholds. An unexplained data, rule, or visible-result difference
blocks cutover, even when row counts match. Missing source position,
unexplained data gap, wrong-tenant write or rule activation, unaudited
exception, source-health risk, or
unrehearsed recovery is a no-go even if aggregate row counts match.

## M9 rehearsal and cutover sequence

1. Approve scope, owners, maintenance window, source snapshots,
   retention, access roles, rollback deadline and explicit go/no-go
   thresholds. Define who can stop the run. Record the authoritative
   writer for each entity before and after the switch.
2. Take verified, restorable source and target backups. Freeze and
   version mapping/configuration. Capture source counts, ranges,
   checksums and high-watermarks; record an immutable run ID.
3. Run a full rehearsal in an isolated environment using an authorized
   representative export. Exercise interrupted extraction, retries,
   duplicates, malformed rows, cross-tenant data and recovery from a
   checkpoint. Prove the target can be restored from the rehearsal.
4. In the approved M9 run, bulk-load by bounded partitions through
   owning services. Record each partition's source range, transform
   version, accepted/quarantined counts and destination checksum.
   Repeat the same partition without creating duplicates.
5. Start the approved CDC/incremental capture at the proven snapshot
   boundary and apply changes in source order to the proper tenant.
   Keep source high-watermarks, target checkpoints, connector lag and
   quarantine counts; prove no gap or unbounded lag before switching
   writes. A PostgreSQL CDC connector is selected only after the
   source-specific proof above; TB CE configuration requires its own
   export/change-capture procedure.
6. Reconcile counts and hashes by source, tenant, entity and time
   range at the same recorded source position; reconcile relationships,
   latest device state, alarm/rule outcomes and approved report figures
   against golden data. Compare approved user-visible dashboard and
   report cases by role and tenant. Record per-tenant rule-graph
   inventory and golden parity.
   Every mismatch is fixed, explicitly waived with evidence, or
   blocks cutover under agreed thresholds.
7. Obtain human approval, switch ingress/API traffic in controlled
   steps, and monitor telemetry freshness, command acknowledgments,
   alarms, error rates and support tickets. Keep the legacy environment
   readable/recoverable for the agreed observation period.
8. Rehearse and document rollback before the switch. After the target
   accepts new writes, rollback must account for those writes; simply
   restoring an old snapshot would lose them. Define reverse
   reconciliation or a forward-fix path and test the chosen method.
   Close the run only after business acceptance and evidence review.

## Decision gates and current blockers

The following inputs are required before a real M9 runbook can be
approved: the actual legacy TB CE version and installed customizations;
source owners and read-only access; inventory and export rights;
tenant/device counts and data volumes; source schemas and stable keys;
per-tenant rule-node ownership and required rule/report parity;
unit/time definitions; retention and privacy requirements; source
change rate, CDC eligibility, WAL/slot budget and allowable delta lag;
service SLOs, RPO/RTO and acceptable cutover/rollback windows; and
approvers for each data class. Record owner, due date and evidence for
each input in the migration project register.

The acceptance gate is the M9 row of `docs/test-plan.md`: scoped
inventory coverage, counts/checksums and semantic reconciliation,
delta catch-up, rule/report parity, rollback rehearsal, human approval
and verified behavior in a representative isolated environment. A
synthetic unit test or dry-run preview alone cannot satisfy this gate.

Related decisions: `docs/requirements-addendum.md` (migration sequence),
`docs/adr/XXXX-proposed-migration-studio-cdc-and-tenant-rules.md`
(CDC and tenant rule proposal),
`docs/adr/0002-migration-studio-foundation.md` (M1 boundary),
`docs/adr/0004-m3-ingestion-outbox-delivery.md` (M3 shadow parity), and
`docs/adr/XXXX-proposed-milestone-naming-and-roadmap.md` (M9 final).
