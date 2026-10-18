# IOT-EE milestones (after the 2026-10-14 decisions)

**Status:** Approved (owner, 2026-10-14). The products are named **EdgePulse** (this platform, formerly IOT-EE) and **EdgeMig** (the migration product, ADR 0022's "migration-manager"); see ADR 0023.
**Amendment 1 (2026-10-14):** MS0 now ends with the rename (IOT-WO-05), and MS2's "product names chosen" gate is met.
**Replaces** four overlapping schemes: M0–M9, PF-A/B/C with C0–C7, Tracks A/B/C, and R1–R6. The mapping is at the end.
**Rests on:** ADR 0014, ADR 0020 (TB CE core), ADR 0021 (Twinfra and the licence gate) and ADR 0022 (migration-manager).

**Rules for every milestone**
- Each milestone ends with a **receipt** in `docs/acceptance/`, with the tester sign-off by the owner.
- Evidence levels follow the readiness review: D (design), C (code), T (tests), CI, and R (real environment). A milestone that says **R** needs a run on Twinfra.
- Dates are set at sprint planning, not here.

## Releases (standard `standards/release-streams.md`, owner 2026-10-14)

- Milestones end with EdgePulse **pre-release tags**: MS0–MS6 are `v2.0.0-alpha.N`, MS7 is `v2.0.0-beta.N`, and MS8 is `v2.0.0-rc.N`.
- **v2.0.0 (stable)** ships when the MS8 pilot is accepted.
- MS9 waves are `v2.x` minors.
- The IOT-EE tags `v0.3.0`–`v1.0.0` remain as history.

## Sequence

| MS | Name | Delivers | Work orders | Entry gate | Exit evidence |
| --- | --- | --- | --- | --- | --- |
| **MS0** | Reset | Safety snapshot pushed; PR #29 tested and merged; ADRs 0014 and 0020–0022 in `main`; drafts sorted; own infrastructure frozen; `spec/` archived; this plan in `docs/`; rename to EdgePulse (ADR 0023) | IOT-WO-01, IOT-WO-05 | none | CI green; `main` matches the decisions (C, CI) |
| **MS1** | Gates and runtime | Licence gate, supply-chain gate and quality gate, all blocking; Java 21; supported Spring line | IOT-WO-02 | MS0 | All gates blocking in CI, with planted-violation tests (CI) |
| **MS2** | Migration contract v1 | `contracts/migration/v1`: inventory manifest, readiness report, tenant lifecycle, reconciliation and digest specification, run record, envelope `origin`, import-safe chain, synthetic dataset | IOT-WO-03 | MS0; **product names chosen** (the contract namespaces use them) | Contract `v1.0.0-draft` published; schema, lint and digest test vectors pass (CI) |
| **MS3** | TB CE core on Twinfra (dev) | TB CE 4.3.1.x on `cairo-1` with CNPG PostgreSQL; Keycloak login; API key in OpenBao; upgrade rehearsal from an older TB version; import-path facts; backup and restore; import throughput | IOT-WO-04 | Twinfra WO-31 accepted, WO-08 live, WO-34 merged; MS1 | Receipt with facts b–g (**R**) |
| **MS4** | Identity and tenancy | Token-verification port; TB CE federation to Keycloak; tenant registry on CNPG with RLS; TB tenant ↔ `tenant_id` mapping and **adoption sync**; tenant lifecycle states; run-scoped TB API keys; deny-by-default ABAC; TOTP for administrators | To write (MR-2, MR-5, MR-12; old C3, C4, R1, R2) | MS3 | Cross-tenant negative tests, an IdP swap that is configuration only, and a lifecycle audit trail on Twinfra (**R**) |
| **MS5** | Event path | Kafka as a Twinfra platform service; TB outbound node → raw topic → ingestion adapter → canonical envelope; outbox and idempotent consumers; OpenTelemetry traces in Twinfra's Jaeger | To write; plus a **Twinfra** Kafka work order | MS4; Twinfra Kafka available | Synthetic telemetry reaches the canonical topic with one effect per event; redelivery causes no second effect; the trace is visible end to end (**R**) |
| **MS6** | Migration readiness | Import-safe fence, reconciliation API, purge, external references, credential-import procedure, endpoint switch, evidence intake, test kit (MR-3, MR-6 to MR-11, MR-13, MR-14) | To write | MS5; a migration-manager build that runs the kit | **Joint synthetic rehearsal** with migration-manager in **both modes**, W and T, with rollback rehearsed (**R**) |
| **MS7** | Production readiness | TB CE cluster mode (HA) on multi-node Twinfra; CNPG HA and point-in-time recovery; DR rehearsal; SLOs, RPO and RTO set and measured; 7-day soak; security review; runbooks for TB upgrade and restore | To write | MS6; Twinfra multi-node (ADR-0050, WO-33) | Soak and DR receipts; owner sign-off (**R**) |
| **MS8** | Pilot migration | The first legacy tenant or tenants: the migration-manager discovery manifest, the readiness report, a rehearsal on an approved copy, cutover by endpoint takeover, and an observation period | To write | MS6 and MS7; discovery done; legacy owner's approvals | A signed per-tenant acceptance; legacy still recoverable for the agreed period (**R**) |
| **MS9** | Full migration | The remaining tenants in waves; legacy decommissioning plan | To write | MS8 accepted | Signed per-wave acceptance; final reconciliation (**R**) |

## Feature epics

Feature epics start after MS5, in business-priority order. They never block MS6–MS9.

| Epic | Scope | Old reference |
| --- | --- | --- |
| F1 Consoles | System-admin, tenant-admin and operator consoles; Operators page; scoped commands | M2, M4 |
| F2 Firmware | Entitled, signed firmware rollout | M5 |
| F3 Evidence and WORM | Evidence store on SeaweedFS after an Object Lock conformance run | M6, ADR 0010 |
| F4 Billing | Usage billing, payment port | M7, R3 |
| F5 AI | Flink → redaction → pgvector → RAG on the ADR 0020 data path | ADR 0019 |
| F6 Config Studio | Typed, versioned configuration lifecycle | R4 |
| F7 Device map | Tenant-scoped map and location | Proposed ADR |

## What changed from the old plan

| Old | New |
| --- | --- |
| M0, PF-A, PF-B, C0, C1, C6 | Done; carried as existing code |
| M1 Migration Studio foundation; M9 final import and cutover | **migration-manager** (ADR 0022). IOT-EE's side is MS2 and MS6; the joint runs are MS8 and MS9 |
| C2 observability, Layer 3 LGTM | Instrumentation in MS5 on Twinfra's ADR-0034 stack; no LGTM |
| C3 identity, C4 persistence and RLS, R1, R2 | MS4 |
| C5 event backbone | MS5 |
| C7 deploy foundation; M8 Deployment Studio; R5 tool responsibilities | Helm and Argo CD on Twinfra in MS3. **Deployment Studio is dropped**: Twinfra provides deployment |
| M6 evidence and DR | DR in MS7; evidence store in F3 |
| R6 environment-admin channels | Twinfra's responsibility |
| M2, M4, M5, M7, R3, R4 | F1–F6 |

## Dependencies on Twinfra

| IOT-EE milestone | Needs from Twinfra |
| --- | --- |
| MS3 | WO-31 accepted, WO-08 (OpenBao), WO-34 |
| MS4 | WO-11 (console roles and audit) is recommended |
| MS5 | **Kafka as a platform service** (Twinfra ADR-0014 and ADR-0015, revised) |
| F3 | WO-22 (SeaweedFS) plus an Object Lock run |
| MS7 | ADR-0050 / WO-33 (multi-node) |
