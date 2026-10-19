# Migration contract v1 (MR-1 to MR-14)

Contract version: **v1.0.0-draft**. Namespace:
`com.edgepulse.platform.contracts.migration.v1`. Success media type:
`application/vnd.edgepulse.migration.v1+json`. Errors:
`application/problem+json` ([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html)).

**Additive changes only within v1.** Existing names, field types, meanings,
requiredness and digest framing must not change incompatibly. Optional additions
require updated schemas and both sides' contract tests; strict readers use the
agreed schema revision, and writers must not send a new optional field before
that revision is negotiated. Breaking changes require a new major directory.
No generated runtime library is shared. These files define an integration
surface; they do not implement an API or prove a migration or deployment.

Authority: [ADR 0022](../../../docs/adr/0022-migration-manager-integration.md),
[ADR 0020](../../../docs/adr/0020-tb-ce-operational-core.md), and the approved
[IOT-WO-03 with Amendment 1](../../../docs/work-orders/IOT-WO-03-migration-contract-v1.md).
The consumer is EdgeMig; no consumer repository was read or modified.

## Artifact map

| Artifact | Requirement and boundary |
| --- | --- |
| `legacy-inventory.schema.json` | MR-1: closed inventory metadata; versions/build, fork/customization hashes and licences, backend, per-tenant data-class counts/monthly rows, protocols/ports/topics, credential **types**, rule-node types, integrations/gateways/dependencies. MR-9: no credential values or personal fields. |
| `readiness-report.schema.json` | MR-1: supported / needs-work / blocked, a reason and reference for every manifest leaf (including empty containers). Completeness, unique pointers and the manifest JCS hash are checked in the fixture pair. The statuses in the sample are synthetic illustrations, not actual support claims. |
| `tenant-lifecycle.openapi.yaml` | MR-2, MR-5, MR-6, MR-11, MR-12: pinned target, create/adopt, immutable external references, expiring invitations, tenant role mapping, audited transitions, purge and time-boxed run-access references. RFC 9470 step-up before cutover/active. |
| `reconciliation.openapi.yaml` | MR-7: tenant-scoped, read-only counts/digests for TB-adapter and service data, a half-open UTC window or snapshot, fixed watermark and bounded cursor pages. MR-9: credential comparisons use salted fingerprints only. |
| `digest-spec.md` | MR-7: exact RFC 8785 canonical bytes, stable record ordering, epoch-millisecond timestamps, array framing and SHA-256. |
| `migration-run-record.schema.json` | MR-13: append-only run metadata; manifest/mapping/result hashes, opaque tier-1 approvals, go/no-go. No raw source records. |
| `import-safe-root-rule-chain.json` | MR-3: authored two-save-node configuration for TB CE 4.3.1.5. The source identifiers and safety settings are described below. Live validation is pending IOT-WO-04. |
| `synthetic-dataset-spec.md`, `fixtures/dataset.json` | MR-14: deterministic seed specification and small fixtures. Six devices across two tenants; fake examples for each credential type, UTC month/DST edges, disabled alarm chains, dashboards and historical alarms. No generator program or rehearsal harness. |
| `data-classes.json` | MR-1 / MR-7: count/reconciliation vocabulary expanded from the existing migration-plan inventory rows; no raw data. |
| `fixtures/*.valid.json`, `fixtures/*.invalid*.json` | MR-1 / MR-13 / MR-14: positive and negative schema examples, including rejected synthetic credential and personal-field injections. |
| `fixtures/jcs-vectors.json`, `fixtures/digest-vectors.json` | MR-7: all Appendix B numeric samples, Appendix E strings, UTF-16 ordering and independent small SHA-256 expectations. |
| `TOOLS.md` | MR-14 / MR-7: exact test dependency and CI-action inventory for the later licence register. |
| `../../../contract-tests/` | MR-14: test sources and the test-scope digest reference only. The parent Enforcer bans dependencies on its artifact in **every** scope. |
| `../../events/v1/envelope.proto` and identity round-trip tests | MR-4: additive Origin enum plus fields 12/13; fixed pre-change wire bytes still decode. |

The two OpenAPI `.yaml` files use JSON syntax, which is valid YAML 1.2 and is
parsed and validated by the pinned Swagger Parser. References are local only;
no network schema resolution is required during tests.

## Security and lifecycle semantics

All operations require an authorized `migration.operator` grant bound to the
tenant path and run/time box. A grant for an existing or pre-authorized
provisioning tenant ID cannot be used to create or inspect another tenant.
The server derives authorization context; caller IDs and approval references
are selectors, never proof. A cross-tenant reference is refused with 403, not
silently filtered into an empty success. Idempotent operations with the same
run/source identity return the existing result; conflicting immutable identity
or expected-state changes return 409. Every call is audited with a server-issued
correlation ID. Error text uses owned, redacted messages, never reflected input.

The OpenAPI state-transition table is normative. Entering `cutover` or `active`
also requires a verified tier-1 approval and step-up. An insufficient
authentication returns 401 with
`WWW-Authenticate: Bearer error="insufficient_user_authentication"` and the
required `acr_values`, per [RFC 9470](https://www.rfc-editor.org/rfc/rfc9470.html).
Machine client-credentials authentication cannot itself satisfy a human step-up.
The OAuth declaration also provides the authorization-code flow for the authorized
tier-1 actor; its authentication context and the stored approval must be verified
and bound to the same tenant/run grant.
The example ACR is an EdgePulse contract identifier, not proof of an existing
identity-provider configuration. Concrete role/ACR mapping is later identity work.

Mode W adopts an approved, isolated database copy upgraded using TB's own
procedure, preserving TB UUIDs. Mode T imports through documented APIs under
the fence, preserving UUIDs where supported; otherwise the consumer's ID map
is authoritative. `external_ref` is immutable for EdgePulse-owned entities.
Expiring invitations are the default; password-hash import is excluded until
its provider passes licence and security review. There is no personal address
or credential field in invitation or role-mapping requests.

Purge is Mode T, tenant/run-scoped and only in `importing` or `shadow`. Mode W
retry uses an authorized pre-adoption backup restore. Neither purge nor restore
is allowed after `active`. No destructive implementation is supplied here.
Run access is a TB tenant API-key reference only; values stay in OpenBao and
never enter this contract, events or evidence. An approved credential-migration
step is a separate, explicit owner decision for each run. No sysadmin credential
or broad vault token is handed to the consumer. Ending or expiring a run revokes
all its run-scoped access. The contract does not implement vault retrieval.

MR-13 records are appended, never updated or deleted. A repeated record ID with
identical content is idempotent; different content must conflict. Previous-record
hashes chain the run's records; approvals reference external owner-authorized
evidence. A schema-valid record does not establish approval authenticity, WORM
conformance or a go decision; those need the implementing evidence context.

## MR-3 import-safe chain provenance and limits

Source read: **ThingsBoard CE tag `v4.3.1.5`, commit
`2cd31ac359214f94b945546830da503ddf80070f`**. The export shape, node class names
and configuration versions were read from these upstream paths at that commit:

- [Tenant root export](https://github.com/thingsboard/thingsboard/blob/2cd31ac359214f94b945546830da503ddf80070f/application/src/main/data/json/tenant/rule_chains/root_rule_chain.json)
- [TbMsgTimeseriesNode](https://github.com/thingsboard/thingsboard/blob/2cd31ac359214f94b945546830da503ddf80070f/rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/telemetry/TbMsgTimeseriesNode.java) and `TbMsgTimeseriesNodeConfiguration.java`
- [TbMsgAttributesNode](https://github.com/thingsboard/thingsboard/blob/2cd31ac359214f94b945546830da503ddf80070f/rule-engine/rule-engine-components/src/main/java/org/thingsboard/rule/engine/telemetry/TbMsgAttributesNode.java) and `TbMsgAttributesNodeConfiguration.java`
- `telemetry/settings/TimeseriesProcessingSettings.java`,
  `telemetry/settings/AttributesProcessingSettings.java`, and
  `telemetry/strategy/ProcessingStrategy.java`, relative to the same rule-engine package.

No TB source code or scripts were copied. The authored JSON contains exactly
`org.thingsboard.rule.engine.telemetry.TbMsgTimeseriesNode` (configuration v1)
and `org.thingsboard.rule.engine.telemetry.TbMsgAttributesNode` (v3).
The timeseries node is first. Its Failure edge reaches the attributes node:
the reviewed source rejects non-telemetry messages before saving, so an
attribute message can reach the second node without adding a type-switch node.
The second node rejects non-attribute messages. A telemetry save failure is
therefore not converted into an attribute write. Success paths end without
forwarding to another chain; there is no log, alarm, RPC, notification or Kafka node.
Live error handling and import behavior still require the IOT-WO-04 rehearsal.

Advanced processing saves timeseries/latest values or attributes only;
WebSocket and calculated-field processing are SKIP. Attribute/device update
notifications are disabled; original metadata timestamps are retained.
Attribute scope uses the TB metadata scope if supplied, with CLIENT_SCOPE as
the configured default. Historical alarms are inert records, not re-raised.
This chain alone cannot prove the complete MR-3 fence: external device commands,
notifications, billing and AI ingestion must also be suppressed by future
tenant-lifecycle and integration implementations while importing/shadow.

## Tests and outstanding requirements

Run `mvn -B -f pom.xml verify` from the repository root. It validates schemas,
OpenAPI parsing/lint, vectors, fixture safety, source-confirmed node set and
the module boundary. Identity retains 211 tests; its existing three envelope
methods also check new provenance, invalid combinations and old wire bytes.
Those assertions are a test-scope conformance reference, not a deployed consumer.

**Licence and supply-chain gates: pending IOT-WO-02.** Metadata inventory and
green existing CI do not mean those gates passed. Only after they run can this
contract leave `-draft`. This work provides static contracts/test evidence only.

MR-8 throughput remains unproven; the target API says so. MR-10 endpoint
compatibility/switch implementation and MR-9 credential handling need later
approved work. MR-14's dataset generator program and full Mode T rehearsal
harness are MS6. TB import/export compatibility, the fence, identity federation,
capacity and the Mode W upgrade path require live receipts from IOT-WO-04 or
later work. Nothing here provisions, migrates, cuts over or deploys an environment.
