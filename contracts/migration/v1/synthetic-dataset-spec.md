# Deterministic synthetic dataset specification (MR-14)

Version: **v1.0.0-draft**. Namespace:
`com.edgepulse.platform.contracts.migration.v1`. Target TB CE **4.3.1.5**.
This is a generator **specification** and a small seed descriptor, not a
generator program, a ready-to-import TB export or a Mode T rehearsal harness.
The generator and harness remain MS6 under IOT-WO-03 Amendment 1 item 8.

## Fixed seed and expansion rules

- Seed identifier: `SYNTHETIC-MR14-v1`. No randomness, current time, locale,
  machine identity or source-system access may influence output.
- Emit tenants `SYNTHETIC-tenant-a` and `SYNTHETIC-tenant-b` in that order.
  Each has devices `SYNTHETIC-a-device-0` through `-2`, or the corresponding
  `b` names. Derive every TB UUID with UUIDv5, URL namespace
  `6ba7b811-9dad-11d1-80b4-00c04fd430c8`, and the UTF-8 name
  `urn:edgepulse:migration:v1:SYNTHETIC-MR14-v1:` followed by the logical ID.
  UUIDv5 uses SHA-1 of the namespace bytes plus that name, with the standard
  version/variant bits; this is an entity-ID mapping, not a security digest.
  Preserve this fixed mapping in reconciliation; never use server-assigned
  random IDs or another tenant's mapping.
- Credential types by device index are access-token, x509 and mqtt-basic.
  Every credential-shaped seed value starts with `SYNTHETIC-` and is deliberately
  outside real credential formats. X.509 has only a fake fingerprint string;
  there is no certificate, PEM or key. These stand-ins must not be sent to a
  real credential endpoint. Future disposable-environment provisioning uses
  the scaffold-configured vault and separately authorized synthetic credentials;
  values never enter manifests, evidence or Git.
- Emit the six telemetry samples in the descriptor for device 0 of each tenant,
  with stable record IDs and the given temperature integers. Timestamps bracket
  the Europe/Berlin spring and autumn DST transitions and the March/April UTC
  month boundary. Their ordering and integer UTC milliseconds are normative.
  The paired UTC times are 2026-03-29 00:59:59.999 / 01:00:00,
  2026-03-31 23:59:59.999 / 2026-04-01 00:00:00, and
  2026-10-25 00:59:59.999 / 01:00:00. Local offsets are for test display only.
- Emit one client attribute for device 0, one disabled migrated rule chain
  containing the stock alarm-node behavior, one temperature dashboard, and
  one inert CLEARED_ACK historical alarm per tenant. Historical alarms are
  records and are never re-raised. No migrated chain is activated before cutover.
  The safe root chain is the separate MR-3 artifact; it has no alarm node.
- The small descriptor names the stock `TbCreateAlarmNode` type but includes no
  TB code, embedded script, widget code or live deployment instruction. A future
  authorized harness renders these seed intentions through the pinned version's
  documented APIs and tests its exports. It must not write TB tables.
- The two tenants' definitions are structurally identical except for their
  explicit logical IDs. Repeat runs at the same seed produce identical descriptor
  bytes, counts, source keys and digest projections. The future generator uses
  the existing run/tenant idempotency contract and exposes no cross-tenant data.

Example mapping: `SYNTHETIC-tenant-a` becomes `113b6b45-ea3f-5d53-859e-ff6d849fa319`.

## Checked-in artifacts and checks

`fixtures/dataset.json` contains only the small explicit seed descriptor. The
inventory fixture uses three devices, six historical samples, one latest series,
one client attribute, one rule chain/alarm rule, one dashboard and one historical
alarm per tenant. Monthly telemetry counts are March=3, April=1, October=2.
It does not stand for discovered legacy facts or supported import throughput.

Schema examples are separate conformance examples: credential and personal-field
injections are rejected by the closed inventory schema. The readiness sample
classifies every manifest leaf with synthetic statuses/reasons, not a real
implementation's support assessment. Digest projections are separate, redacted
records with the normative stable keys in `digest-spec.md`.

`SyntheticAndFenceTest` checks both tenants, every credential type/value prefix,
both DST boundaries, the UTC month edge, disabled migrated alarm chains and inert
alarm history. It also checks the distinct import-safe chain's exact two-node set
and suppression settings. This is C/CI evidence only; no TB instance is run.
