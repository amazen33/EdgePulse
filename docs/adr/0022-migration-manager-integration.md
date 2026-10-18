# ADR 0022: Integration with migration-manager (legacy ThingsBoard migration)

**Status:** Accepted (owner, 2026-10-14).
- On 2026-10-14 the owner decided that migration-manager is developed separately and that IOT-EE must be ready to integrate with it.
- The owner delegated the device-credential question to the architect's recommendation; MR-9 records that recommendation.

The number is confirmed at merge.

**Author:** Claude (architecture). **Implementer:** Codex (IOT-WO-03 builds the contract; IOT-WO-04 runs the spike).

**Moves out of IOT-EE's scope:**
- Migration Studio: milestones M1 and M9, `docs/migration-studio.md`, `docs/legacy-migration-execution-plan.md`, `XXXX-proposed-migration-studio-cdc-and-tenant-rules.md`, and the frozen Python M1 module.
- These become **migration-manager's input requirements**, carried over unchanged as its starting specification.

## Context

- ADR 0020 keeps ThingsBoard CE as the operational core. A legacy ThingsBoard-based product can therefore move into IOT-EE largely in ThingsBoard's own format.
- Discovery, extraction, transformation, reconciliation orchestration and cutover orchestration belong to **migration-manager**, a separate product.
- The legacy system's facts are still unknown: version, telemetry backend, customisations, volumes, protocols and credential types. Migration-manager's discovery will find them.
- IOT-EE must not wait for them. It must expose a **stable, versioned, tested integration surface**, so that whatever discovery finds can be loaded, checked and cut over safely.

## Responsibilities

| Concern | migration-manager | IOT-EE |
| --- | --- | --- |
| Discovering the legacy system: version, schema, counts, protocols, credential types, customisations | Owns it. Produces the **legacy inventory manifest** (MR-1) | Defines the manifest schema. Runs a **readiness check** that lists what IOT-EE cannot accept yet |
| Version translation: legacy TB version to the pinned target | Owns it ("normalise, then move", see the migration modes) | Publishes the pinned target and the import API set it accepts (MR-2) |
| Extraction, transformation, ID mapping, checkpoints, CDC | Owns them | Stores `external_ref` on IOT-EE-owned entities (MR-6) |
| Loading into TB CE | Calls TB CE's documented API with **run-scoped, tenant-scoped API keys** that IOT-EE issues and revokes (MR-12) | Issues and revokes the keys. Provides the import-safe rule chain (MR-3) |
| Loading into IOT-EE services | Calls the IOT-EE migration API | Owns the API, validation and audit |
| Reconciliation | Orchestrates it and keeps the raw results | Exposes reconciliation read APIs for TB data and IOT-EE data (MR-7) |
| Evidence | Keeps the raw evidence in its own store | Takes in run records in the evidence context, append-only (MR-13) |
| Cutover and rollback | Orchestrates them and asks for approval | Executes tenant state transitions and the endpoint switch (MR-2, MR-10). Requires step-up approval |

## Migration modes

- **Mode W, whole instance.** This is the first migration, of the legacy product's own tenants.
  1. migration-manager restores an approved copy of the legacy database in isolation.
  2. It upgrades the copy to the pinned TB CE version with **ThingsBoard's own upgrade procedure**, stepwise if ThingsBoard requires it.
  3. That upgraded database **becomes** IOT-EE's TB database.
  4. IOT-EE then **adopts** it: it syncs TB tenants into IOT-EE tenants and TB users into Keycloak invitations (MR-5), and runs reconciliation.

  Entity IDs, rule chains, dashboards, relations and device credentials keep their TB form. The preconditions are that the legacy product is unforked TB CE, and that its telemetry backend can be upgraded or converted. Discovery confirms both.
- **Mode T, tenant import into a running IOT-EE.** This is for later customers.
  1. migration-manager normalises the legacy copy to the pinned version on an isolated staging TB.
  2. It exports each tenant through that version's documented APIs. CE's entity version-control export is a candidate to evaluate.
  3. It imports into the shared IOT-EE TB through the same APIs, under the import-safe fence (MR-3).

**"Normalise, then move" means IOT-EE only ever accepts data in its own pinned TB version's format.** Legacy version drift is migration-manager's problem, not IOT-EE's.

## Decision: IOT-EE migration-readiness requirements (MR)

The contracts live in IOT-EE under `contracts/migration/v1/`: OpenAPI, JSON Schemas, and envelope fields in proto. They are versioned under ADR 0018's compatibility rules. migration-manager is a consumer, and both sides run the contract tests in CI.

1. **MR-1 Legacy inventory manifest schema** (`legacy-inventory.schema.json`). It records:
   - TB edition, version and build;
   - fork and customisation evidence: custom rule nodes, scripts and widgets, with their licences;
   - telemetry backend (SQL, Timescale, Cassandra or hybrid);
   - for each tenant: counts per data class (the ThingsBoard data-class list in the current migration plan) and telemetry rows per month;
   - device protocols, ports, topic formats and credential types (access token, X.509, MQTT basic);
   - rule-node types in use, with counts;
   - integrations and gateways (Mosquitto layers, IoT Gateway), plus external dependencies.

   IOT-EE's readiness check reads a manifest and reports which items are **supported**, **need work** or **blocked**, each with a reason. A manifest never contains secrets or personal data.
2. **MR-2 Pinned target and tenant lifecycle.**
   - IOT-EE publishes its pinned TB CE version and the import API set it supports. A TB patch bump runs the contract tests first.
   - Each IOT-EE tenant has a lifecycle state: `provisioning → importing → shadow → cutover → active`, plus `rolled_back` and `retired`.
   - Transitions are made only through the API. Each is audited, and moves into `cutover` or `active` need step-up approval from a tier-1 role.
3. **MR-3 Side-effect fence.** While a tenant is `importing` or `shadow`:
   - its TB root rule chain is IOT-EE's **import-safe chain** (save telemetry and attributes, nothing else). Migrated rule chains are loaded but not activated until `cutover`;
   - device commands, notifications, billing and AI ingestion are suppressed for that tenant;
   - historical alarms are imported as records and never re-raised.
4. **MR-4 Event provenance.** The canonical envelope gains `origin` (`live`, `migration` or `replay`) and `migration_run_id`. Consumers must handle `origin` explicitly; for example, billing never charges for migrated history.
5. **MR-5 Tenant and identity provisioning.**
   - There is an API to create or adopt a tenant (TB tenant, IOT-EE `tenant_id` and Keycloak mapping), and to map TB users and customers to IOT-EE roles.
   - By default users are re-enrolled through **expiring invitations**. Importing password hashes into Keycloak is allowed only if a hash provider passes the licence gate and a security review.
6. **MR-6 Identity of records.**
   - Mode W keeps TB entity UUIDs.
   - Mode T keeps them where the import API accepts them; otherwise migration-manager's ID map is authoritative.
   - IOT-EE-owned entities store an immutable `external_ref` (source system, source ID, run ID).
7. **MR-7 Reconciliation API.**
   - It is read-only and tenant-scoped.
   - It returns counts and digests per data class over a half-open UTC window `[from, to)` or an as-of snapshot, at a stated watermark.
   - It covers TB-held data (through IOT-EE's TB adapter) and IOT-EE service data.
   - The digest algorithm is specified in the contract, so both sides compute it identically.
   - Results are paginated and redacted. Cross-tenant selections are refused, not returned empty.
8. **MR-8 Bulk-load capacity.**
   - IOT-EE states the throughput it supports for historical telemetry import and proves it with synthetic data.
   - In Mode T the import path is TB's documented API under the fence.
   - Direct writes to TB tables are not allowed. A Mode W database copy is not a "write"; it is TB's own upgrade of its own database.
9. **MR-9 Device credentials** (architect recommendation, delegated by the owner).
   - Device credentials **may be migrated** so that field devices need no re-enrolment, but **never automatically** (`CLAUDE.md`). Each run's credential step needs explicit owner approval.
   - In Mode W the credentials stay inside the upgraded TB database. In Mode T they go through TB's device-credentials API.
   - They never pass through logs, events, evidence, manifests or Git.
   - Reconciliation compares **salted fingerprints**, never values.
   - Credentials that are weak or shared get a planned rotation after cutover.
10. **MR-10 Device endpoint compatibility and switch.**
    - IOT-EE's device endpoint accepts the legacy protocols, ports, topic formats and credential types that the manifest lists, or the readiness check marks them blocked.
    - Cutover is an **endpoint takeover** (DNS or address) per tenant or device group, with a tested route back. Devices keep their firmware and credentials.
11. **MR-11 Re-run safety.**
    - In `importing` or `shadow`, a tenant-scoped purge removes everything imported for that tenant, so a failed rehearsal can be re-run.
    - Mode W reverts by restoring the pre-adoption backup.
    - Neither is available once the tenant is `active`.
12. **MR-12 Run-scoped access.**
    - migration-manager authenticates as a Keycloak client with role `migration.operator`, per tenant and time-boxed. Every call is audited.
    - IOT-EE issues TB tenant API keys for the run, stores them in OpenBao, and revokes them when the run ends.
    - migration-manager never receives TB sysadmin credentials or broad OpenBao tokens.
13. **MR-13 Evidence intake.** IOT-EE's evidence context accepts migration run records: run ID, manifest hash, mapping hash, reconciliation-result hashes, approvals and the go/no-go decision. They are append-only and contain no raw data.
14. **MR-14 Contract test kit.**
    - IOT-EE publishes a **synthetic ThingsBoard dataset** at the pinned version: two tenants, devices, telemetry, rule chains, dashboards and alarms.
    - It also publishes a harness that runs a full Mode T rehearsal against a disposable IOT-EE.
    - The same kit is migration-manager's acceptance test.

## Consequences

- IOT-EE's roadmap loses M1 and M9 and gains one epic, **migration readiness (MR-1 to MR-14)**. That epic is ordered before any customer-facing feature work beyond the core (`docs/test-plan.md` M1 and M9 rows move to migration-manager).
- migration-manager needs its own repository, owner and licence-gate registration. We recommend Twinfra's gate applies to it too.
- The first real evidence comes from IOT-WO-04: TB CE on Twinfra, plus an **upgrade rehearsal** from an older synthetic TB version to the pinned version (the Mode W path), plus checks of the MR-3 fence.

## Alternatives rejected

- **Keep Migration Studio inside IOT-EE.** The owner has decided otherwise. It would also tie IOT-EE's release cadence to legacy-specific tooling.
- **Let migration-manager write TB tables or IOT-EE databases directly.** That breaks service ownership (ADR 0013) and CE's supported surface.
- **Re-enrol every device.** That is usually impossible for a deployed field fleet, and it would block cutover.

## Cross-references

ADR 0013, 0016, 0018 and 0020 (TB CE core), ADR 0021 (Twinfra and secrets), `docs/legacy-migration-execution-plan.md` (moved to migration-manager), and the review `E:\vcloud-handoff\reviews\iot-ee-review-2026-10-14.md`, section 6.
