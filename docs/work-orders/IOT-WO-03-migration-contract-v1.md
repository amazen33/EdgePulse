# IOT-WO-03: Migration integration contract v1 (contract-first)

**Status:** Approved (ADR 0022 accepted by the owner, 2026-10-14). **Gated:** start only when IOT-WO-01 **and IOT-WO-05 (rename)** have merged. The names are EdgePulse and EdgeMig (ADR 0023). Use `com.edgepulse.platform.contracts.migration.v1` and the media-type prefix `application/vnd.edgepulse.migration.v1+json`. The contract's namespaces, package names and media types use the final names, so the published v1 never needs renaming.
**Author:** Claude · **Implementer:** Codex · **Repository:** IOT-EE · **Branch:** `codex/iot-wo-03-migration-contract`
**Decision:** ADR 0022 (MR-1 to MR-14). **Consumer:** EdgeMig (ADR 0022's migration-manager; private repository `amazen33/edgeMig`).

## Goal

IOT-EE publishes a versioned, tested contract that migration-manager can build against before either side has a running implementation. This work order creates **contracts and their tests only**. The services that implement them come in later work orders.

## Scope (`contracts/migration/v1/`)

1. **`legacy-inventory.schema.json` (MR-1).**
   - Fields: TB edition, version and build; fork and customisation evidence; telemetry backend; per-tenant counts per data class; telemetry rows per month; device protocols, ports, topic formats and credential types; rule-node types with counts; integrations and gateways; external dependencies.
   - **Forbidden by schema:** any field that could carry a secret, a credential value or personal data. This is enforced with `additionalProperties: false` and pattern checks.
2. **`readiness-report.schema.json` (MR-1).** Each manifest item gets `supported`, `needs-work` or `blocked`, with a reason and a reference (an ADR, a rule-node type or a protocol).
3. **`tenant-lifecycle.openapi.yaml` (MR-2, MR-5, MR-11, MR-12).**
   - States and allowed transitions, with step-up for `cutover` and `active`.
   - Create or adopt a tenant; invite users; map roles.
   - Tenant-scoped purge, allowed only in `importing` or `shadow`.
   - Issue and revoke run-scoped TB API keys (returning only a reference).
   - Errors use RFC 9457 problem details.
4. **`reconciliation.openapi.yaml` and `digest-spec.md` (MR-7).**
   - Counts and digests per data class over a half-open UTC window or an as-of snapshot, at a stated watermark.
   - A deterministic digest: canonical JSON, key order, number and timestamp normalisation, and the hash algorithm.
   - Pagination. Cross-tenant selections are refused.
5. **`migration-run-record.schema.json` (MR-13).** Run ID, manifest, mapping and result hashes, approvals and the go/no-go decision. No raw data.
6. **Envelope (MR-4).** Add `origin` (enum: live, migration, replay) and `migration_run_id` to `contracts/events/v1/envelope.proto` as backward-compatible fields. Update `EnvelopeSerializationRoundTripTest`.
7. **Import-safe rule chain (MR-3).** Provide `import-safe-root-rule-chain.json` for the pinned TB CE version: save timeseries and attributes, no other nodes. Its validation against a live TB happens in IOT-WO-04.
8. **Synthetic dataset specification (MR-14).** A deterministic generator specification, plus small checked-in fixtures:
   - two tenants;
   - devices with each credential type, using **fake** values marked as synthetic;
   - telemetry across month boundaries and DST changes;
   - one rule chain with an alarm;
   - one dashboard;
   - historical alarms.

   Fixtures are synthetic only (`CLAUDE.md`).

## Tests

- JSON Schema validation, with valid and invalid fixtures for every schema, including a manifest that tries to carry a credential and is rejected.
- OpenAPI lint, pinned and licence-registered.
- Digest specification test vectors: the same input gives the same digest, and a one-field change gives a different digest.
- The envelope round-trip passes with the new fields and with old messages that lack them.

## Acceptance

- CI is green, including the licence and supply-chain gates from IOT-WO-02.
- `contracts/migration/v1/README.md` explains each artifact and its MR number.
- The PR states the contract version `v1.0.0-draft` and the compatibility rule: additive changes only within v1.

## Amendment 1 (architect, 2026-10-19): start before IOT-WO-02, plus implementation rulings

**Status:** Approved (owner, 2026-10-19, text as written).
**Why:** IOT-WO-01 and IOT-WO-05 have merged, and MS0 is released as `v2.0.0-alpha.3`. MS2's entry gate is MS0 plus the product names; it does **not** require MS1. IOT-WO-02 is waiting for Twinfra WO-34, so the acceptance line "including the licence and supply-chain gates from IOT-WO-02" can't be met yet. This amendment lets the contract land as `v1.0.0-draft` now, and fixes the choices the work order leaves open.

1. **Gates.** The acceptance item for IOT-WO-02's gates is recorded as **pending IOT-WO-02**, not as passed.
   - Every tool or library added here must be MIT/BSD-style or Apache-2.0 (tiers 1 and 2), pinned to an exact version, and at least 14 days old.
   - Each is listed in `contracts/migration/v1/TOOLS.md`: name, version, licence, and checksum or Maven coordinates. IOT-WO-02's register imports that list.
   - When IOT-WO-02 merges, its gates run over these tools, and only then can the contract leave `-draft`.
2. **Where the tests live.** Add a root Maven module, `contract-tests/`, with test sources only and no main code.
   - Nothing may depend on it. Add an Enforcer or ArchUnit rule that fails if any module declares it.
   - Use the managed `com.networknt:json-schema-validator` for the schemas.
   - Use `io.swagger.parser.v3:swagger-parser` (Apache-2.0) for OpenAPI parsing and validation, plus "lint" assertions written as JUnit tests:
     - every 4xx and 5xx response is `application/problem+json` (RFC 9457);
     - success bodies use `application/vnd.edgepulse.migration.v1+json`;
     - every operation has an `operationId` and a tenant path parameter;
     - no request or response schema has a property named like `password`, `secret`, `token`, `apiKey`, `privateKey` or `credentialValue`.
   - Don't add Node or Spectral.
3. **Envelope (MR-4), proto3-safe.**
   - Add `enum Origin { ORIGIN_UNSPECIFIED = 0; ORIGIN_LIVE = 1; ORIGIN_MIGRATION = 2; ORIGIN_REPLAY = 3; }`, a field `Origin origin`, and a field `string migration_run_id`. Use new field numbers and never reuse one.
   - Document that `ORIGIN_UNSPECIFIED`, which is what old messages decode to, is treated as live.
   - `migration_run_id` is set only when `origin` is `ORIGIN_MIGRATION`.
   - The round-trip test covers new messages and bytes encoded before the change.
4. **Digest (MR-7).** `digest-spec.md` fixes:
   - canonical JSON as **RFC 8785 (JCS)**;
   - timestamps as integer epoch milliseconds, UTC;
   - records within a data class sorted by a stated stable key;
   - **SHA-256**, as lowercase hex;
   - a per-class digest over the canonical records, in order.
   - A test-scope reference implementation in `contract-tests/` produces checked-in test vectors: the RFC 8785 appendix examples, plus our own. A tier-1 or tier-2 JCS library may be used at test scope.
5. **Step-up (MR-2).**
   - Moves into `cutover` and `active` return 401 with `WWW-Authenticate: Bearer error="insufficient_user_authentication"` and the required `acr_values` (RFC 9470).
   - Callers use the scope or role `migration.operator` (MR-12).
   - Run-scoped API-key issuance returns only an opaque **reference**; no response field can carry the key.
6. **Synthetic credentials (MR-14).**
   - Every credential-shaped fixture value starts with `SYNTHETIC-` and matches no real format.
   - X.509 credentials appear only as a fake fingerprint string: never a PEM block or a key.
   - A test asserts the prefix on every credential field in the fixtures.
   - `legacy-inventory.schema.json` itself allows credential **types** only, never values.
7. **Import-safe chain (MR-3).**
   - Write the TB rule-chain export format for a named 4.3.1.x patch: record the TB tag and source commit read.
   - It holds exactly the save-timeseries and save-attributes nodes, with their class names checked against that tag, and nothing else.
   - Copy no TB code. A test asserts the node set.
   - Live validation stays IOT-WO-04 fact b.
8. **Scope limits.**
   - The dataset **generator specification** and the small fixtures are in scope.
   - The generator program and the Mode T rehearsal harness (the rest of MR-14) are MS6.
   - Update `compatibility.yaml` to `provides: edgepulse-migration-contract: "v1.0.0-draft"`, and add a CHANGELOG entry under `[Unreleased]`.
