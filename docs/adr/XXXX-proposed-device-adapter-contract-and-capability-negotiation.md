# ADR XXXX (proposed) -- Device integration: verified inventory, adapter contract, capability negotiation, device behaviour rules

> Needs revision for ADR 0020: devices connect to TB CE transports.

Status: proposed. Unnumbered draft per `docs/adr/README.md`; the number is
assigned at merge. Encodes direction given by the repository owner on
2026-09-26. Refines Decision 3 of
`XXXX-proposed-ai-and-device-adapter-boundaries.md`, and works with ADR
0003 (canonical units and UTC), ADR 0004 (MQTT topics, outbox, delivery),
ADR 0006 (firmware), ADR 0019 (edge MQTT -> tier-1 buffer -> Kafka; TB CE
downstream) and
`XXXX-proposed-identity-authorization-and-privileged-access.md` (command
authorization and acknowledgement).

**No device adapter exists in Java, and no device class is tested.** The
frozen Python spec models MQTT topics, an outbox, idempotent consumers
and command queues without any real transport. The installed SpectroTANK
fleet is `unverified`: its hardware, firmware, protocols and
authentication are unknown to this repository.

## Context

- The readiness review (goal 13) marks legacy device support
  **conflicting**. ADR 0011 relied on TB CE transports (MQTT/HTTP/CoAP),
  then ADR 0019 moved device ingress in front of TB CE, and no path for
  non-MQTT devices was designed.
- `docs/tb-ce-inventory.md` records the legacy TB CE version as unknown,
  and no document lists the legacy fleet's device models, firmware or
  protocols.
- The owner forbids inferring protocol details or device behaviour from
  screenshots or product marketing.

## Decision

1. **Inventory from verified sources only.** Device classes are recorded
   in `docs/inventory/device-classes.yaml` (schema
   `contracts/device/device-class-profile.schema.json`).
   - Accepted sources: protocol specifications, vendor engineering
     documents, firmware source, authorized and redacted protocol captures
     from the real fleet, lab test reports, and (for synthetic reference
     profiles only) this repository's specs.
   - Not accepted: marketing material, screenshots, the legacy UI, hearsay.

   A class moves through `unverified -> documented -> fixture-tested ->
   device-tested -> supported`:
   - `fixture-tested` and above require passing compatibility tests;
   - `supported` requires at least one transport tested on representative
     hardware;
   - unknown values stay `unknown`, never guessed.
2. **One adapter contract per transport, owned by device connectivity.** The
   device-connectivity service owns a `DeviceTransportAdapter` port family
   in plain Java types:
   - **Inbound:** authenticate a connection by credential reference
     (never by credential material); decode a message into
     `NormalizedTelemetry` or `CommandAcknowledgement`; report connect and
     disconnect.
   - **Outbound:** encode a `DeviceCommand` for delivery.

   `NormalizedTelemetry` carries tenant, device, metric, value in its
   canonical unit, observed time and time quality, received time, message
   id or sequence, adapter id and profile version. `DeviceCommand` carries
   command id, device, property, desired value, expiry and nonce.
   `CommandAcknowledgement` carries command id, nonce, outcome and the
   authenticated device identity. Transport libraries live only in
   `adapter.in.<transport>` / `adapter.out.<transport>` packages.
3. **Capability negotiation.** Each device is registered with a class
   profile and version.
   - The effective capability set is the intersection of what the profile
     declares, what the device reports at connect time (where the class
     supports a capability report), and what the platform implements.
   - A device whose report conflicts with its profile is quarantined for
     review, not silently accepted.
   - Commands, firmware and features outside the effective set are
     refused with a reason.
   - Unknown classes and unknown profile versions are rejected, not
     treated as a default.
4. **Transports.**
   - **MQTT (3.1.1 and 5), the initial transport:** the ADR 0004 topic
     convention, TLS with per-device client certificates, per-device broker
     ACLs (a device may publish and subscribe only to its own tenant/device
     topics), and QoS 1 with platform-side deduplication (proposal).
   - **HTTP (proposal):** devices post telemetry over TLS with a
     per-device credential and poll for commands.
   - **CoAP (RFC 7252, proposal):** DTLS with per-device keys; observe
     only after a fixture shows the target devices implement it.
   - **Legacy protocols:** none is confirmed, so none has an adapter. A
     legacy protocol gets an adapter only after the inventory names it
     from an accepted source and captures or hardware exist to test it.

   HTTP and CoAP adapters are specified here but **unimplemented**.
5. **Credentials through the vault; per-device authorization.**
   - Device credentials (client certificates, tokens, PSKs) are issued,
     rotated and revoked through the vault broker. Adapters receive
     references or short-lived material, never long-lived secrets in
     configuration, events or logs.
   - Every message is authorized for its device and tenant.
   - New device classes may not use shared fleet secrets. A legacy class
     that already does keeps them only under a recorded, time-limited
     exception with a migration plan.
6. **Commands and acknowledgements.** Commands are authorized and
   server-mediated as in the identity ADR (Decision 7). An acknowledgement
   counts only if it arrives over the device's authenticated channel and
   echoes the command id and nonce before expiry. Duplicate or late
   acknowledgements are recorded but change nothing. For a class without
   authenticated acknowledgement, a delivered command's status is
   `sent-unconfirmed`, never `applied`.
7. **Time and units.** Storage and domain logic use UTC and canonical
   metric units (ADR 0003).
   - The adapter converts device units through versioned mapping tables
     named in the class profile.
   - A device timestamp is used only when the class declares a network-
     synchronized clock and the timestamp lies within a skew bound of the
     receive time (proposal: 5 minutes). Otherwise the receive time is used
     and the record is flagged with its time quality.
   - Out-of-order data is accepted and ordered by observed time.
8. **Offline buffering, retry and replay prevention.**
   - Devices that buffer offline declare it in their profile. The platform
     accepts late data within a bounded window (proposal: 7 days) and
     quarantines older data for review.
   - Telemetry is deduplicated on `(tenant, device, message id or
     sequence)` idempotently; a class that offers neither cannot reach
     `fixture-tested`.
   - Devices retry with exponential backoff and jitter.
   - Commands are retried until their TTL, then expire and are never
     delivered after expiry. Command ids and nonces are single-use; a
     replayed command or acknowledgement is rejected.
9. **Firmware verification.**
   - Over-the-air updates are offered only to classes that verify
     artifact signatures on the device before applying them (ADR 0006
     signed artifacts), and whose compatibility keys (for example hardware
     revision and bootloader version) are declared and checked before
     dispatch.
   - Success is the device reporting the new version after reboot over its
     authenticated channel.
   - Rollback is claimed only where the class supports it.
   - A class without on-device verification is not eligible for OTA.
10. **No support claims ahead of evidence.** No document says the platform
    "supports legacy devices" until a legacy class is `supported`, meaning
    representative compatibility tests pass on real hardware or on
    authorized captures replayed through the real adapter.
    `tools/policy/check.py` fails CI on such a claim.

## Consequences

- The inventory, its schema and `tools/policy/check.py` are the first
  executable part. The checker enforces:
  - that marketing, screenshots and hearsay are rejected;
  - that status is gated on sources and compatibility tests;
  - that tested classes declare acknowledgement, time, units and replay
    keys;
  - that OTA requires on-device verification;
  - that new classes use no shared fleet secrets;
  - that credentials are vault references only;
  - that no legacy-support claim appears in the docs.
- Everything else is **unimplemented**, with acceptance tests listed in
  `docs/ai-device-traceability.md`: the adapter ports, MQTT/HTTP/CoAP
  adapters, the tier-1 buffer, the vault credential broker,
  acknowledgement handling and the firmware delivery path.
- Legacy support stays blocked on owner-provided inputs: the device model
  list, firmware versions, the legacy TB CE device profiles and transport
  configuration through the authorized export process, and redacted
  captures.

## Alternatives rejected

- **Declaring HTTP/CoAP/legacy support because TB CE has those
  transports.** Rejected: ADR 0019 moved ingress in front of TB CE, and a
  transport existing is not compatibility with a given fleet.
- **A default "generic device" profile for unknown devices.** Rejected:
  it hides incompatibility until data is wrong.
- **Using the device timestamp unconditionally.** Rejected: unsynchronized
  device clocks corrupt ordering and reports.

## Open questions for the owner

- The legacy fleet inventory: models, hardware revisions, firmware
  versions, protocols, bearers, authentication, and who can provide
  captures and test hardware.
- Whether HTTP or CoAP devices exist in the fleet, or are only future
  options.
- The late-data window, the clock-skew bound and the offline queue limits.
- Whether any legacy devices use shared credentials and, if so, the
  migration deadline.
