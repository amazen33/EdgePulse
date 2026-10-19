# MS2 Migration contract v1 acceptance receipt — 2026-10-19

## Scope and authorization

- **Milestone:** MS2, migration contract v1 ([MILESTONES.md](../../MILESTONES.md)). Work order: [IOT-WO-03](../work-orders/IOT-WO-03-migration-contract-v1.md) with Amendment 1 (approved by the owner, 2026-10-19).
- **Entry gate:** MS0 (accepted 2026-10-18; pre-release `v2.0.0-alpha.3`) and the product names (ADR 0023). MS1 is **not** part of MS2's entry gate.
- **Exit evidence required by the plan:** contract `v1.0.0-draft` published; schema, lint and digest test vectors pass in CI. Evidence levels **C and CI** only.
- **Environment:** GitHub-hosted CI and local Maven only. No cluster, ThingsBoard instance, EdgeMig repository or legacy system was used. Nothing is deployed.
- **Tested head:** `main` at `548cac0` (PR #44, which includes PR #43's `88f0da7`).
- **Tester:** Ahmed Mazen (@amazen33), enterprise and cloud tester; QoS tester.
- **QoS targets agreed before testing:** not applicable (no runtime). The targets are the MS2 deliverables below.

## Deliverables (all in [PR #43](https://github.com/amazen33/EdgePulse/pull/43), merged as `88f0da7` on 2026-10-19)

| # | Deliverable (MILESTONES MS2) | MR | Evidence | Result |
| --- | --- | --- | --- | --- |
| 1 | Inventory manifest | MR-1 | `legacy-inventory.schema.json`: every object is closed (15 of 15 with `additionalProperties: false`); credential **types** only. Invalid fixtures that add `credentialValue` or `email` are rejected in tests | Done |
| 2 | Readiness report | MR-1 | `readiness-report.schema.json`: `supported`, `needs-work` or `blocked`, each with a reason and reference; valid and invalid fixtures | Done |
| 3 | Tenant lifecycle | MR-2, MR-5, MR-11, MR-12 | `tenant-lifecycle.openapi.yaml`: lifecycle states and transitions; step-up for `cutover` and `active` (RFC 9470 `insufficient_user_authentication` with `acr_values`); `migration.operator`; tenant-scoped purge; run-scoped key issuance that returns only an opaque reference; RFC 9457 errors | Done |
| 4 | Reconciliation and digest specification | MR-7 | `reconciliation.openapi.yaml` (half-open UTC window or as-of snapshot, watermark, cross-tenant selection 403) and `digest-spec.md` (RFC 8785 JCS, epoch milliseconds, records sorted by `record_id`, SHA-256 in lowercase hex); test vectors include the RFC 8785 examples | Done |
| 5 | Run record | MR-13 | `migration-run-record.schema.json`: hashes, approvals and the go/no-go decision; no raw data; valid and invalid fixtures | Done |
| 6 | Envelope `origin` | MR-4 | `envelope.proto`: `Origin` enum with `ORIGIN_UNSPECIFIED = 0` (treated as live), new fields 12 and 13; the round-trip test decodes bytes encoded before the change | Done |
| 7 | Import-safe chain | MR-3 | `import-safe-root-rule-chain.json` for TB CE 4.3.1.6 (source commit recorded): only the timeseries and attributes save nodes, with WebSocket and calculated-field processing set to `SKIP`; node-set test | Done (static). Live validation is IOT-WO-04 fact b |
| 8 | Synthetic dataset | MR-14 | `synthetic-dataset-spec.md` and fixtures: two tenants; every credential-shaped value starts with `SYNTHETIC-`; no PEM blocks or keys; prefix test | Done (specification and fixtures). The generator and Mode T harness are MS6 |
| 9 | Contract `v1.0.0-draft` published | — | `contracts/migration/v1/` on `main`; `compatibility.yaml` provides `edgepulse-migration-contract: "v1.0.0-draft"`; rule: additive changes only within v1 | Done |

## CI evidence

| Check | Revision | Result |
| --- | --- | --- |
| Java platform and naming gates: `edgepulse-contract-tests` 61 tests and identity 211 tests, BUILD SUCCESS | `548cac0` | Success ([run 39278215540](https://github.com/amazen33/EdgePulse/actions/runs/39278215540)) |
| Java platform and naming gates | `88f0da7` (PR #43 merge) | Success ([run 39255545133](https://github.com/amazen33/EdgePulse/actions/runs/39255545133)) |
| `release-checks` | `548cac0` | Success ([run 39278215523](https://github.com/amazen33/EdgePulse/actions/runs/39278215523)) |

The contract tests cover schema validation (valid and invalid fixtures for every schema), OpenAPI parsing and lint rules, the digest test vectors, the `SYNTHETIC-` prefix and the chain's node set. The module is test-only, and an Enforcer rule bans any dependency on it.

## Not claimed

- **No runtime evidence:** no TB instance validated the chain, and no service implements these contracts.
- **EdgeMig hasn't consumed the contract yet.** MS6's joint rehearsal is the first consumer evidence.
- **The contract is a draft:** `v1.0.0-draft` stays a draft until the IOT-WO-02 gates pass over it (IOT-WO-03 Amendment 1, item 1).

## Pending gates, deviations and owner actions

- **Pending IOT-WO-02:** the licence and supply-chain gates over the contract tooling (`contracts/migration/v1/TOOLS.md`). They are recorded as **pending**, not passed (Amendment 1). JUnit (EPL-2.0, existing, test scope) needs a ruling in IOT-WO-02's register.
- **Open design item for MS6:** reconciliation compares credentials by salted fingerprints, but the contract doesn't yet say who generates the salt or how both sides share it without exchanging a secret. Defining it later is an additive change, which v1 allows.
- **Out-of-scope change accepted:** PR #43 also pinned the existing `ci.yml` actions by SHA, which is in line with ADR 0014.
- **Order note:** MS2 completes before MS1. MILESTONES permits this, because MS2's entry gate doesn't include MS1.
- **Release, after signing:**
  1. Copilot opens the `release: 2.0.0-alpha.4` PR, which moves `[Unreleased]` into `[2.0.0-alpha.4]` and adds this receipt.
  2. The owner merges it.
  3. The owner fetches and checks that `origin/main` names that PR, runs the `v2.0.0-alpha.4` dry run and waits for `✓`, then tags `origin/main`.
- **Restoration:** none needed; no environment was changed.

## Tester sign-off
Tester: Ahmed Mazen (@amazen33), enterprise and cloud tester; QoS tester
Result: Accepted
Date (UTC): 2026-10-19
QoS targets checked: the nine MS2 deliverables in this receipt (MR-1, MR-2, MR-3, MR-4, MR-5, MR-7, MR-11, MR-12, MR-13 and MR-14 artifacts in `contracts/migration/v1/` and the envelope) and the CI evidence on `548cac0` (61 contract tests and 211 identity tests). Evidence levels C and CI only; no runtime targets apply.
Notes: Accepted with the IOT-WO-02 gates pending, the salt design item open for MS6, and the chain's live validation left to IOT-WO-04. Signed by the owner in chat ("I accept MS2"); recorded by the architect at the owner's instruction.
