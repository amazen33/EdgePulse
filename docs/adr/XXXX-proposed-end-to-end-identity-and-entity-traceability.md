# Proposed ADR -- end-to-end identity and entity traceability

Status: proposed; requires owner review. This proposal supplements ADRs
0012, 0015, 0016, 0017 and 0018. It does not change their accepted
decisions.

## Context

ADR 0015 requires `traceparent` and `X-Correlation-ID` to travel together
across HTTP/gRPC, logs, spans and Kafka. ADR 0018 requires an event
identity, causation, tenant scope and idempotency across asynchronous
processing. Neither ADR defines a common, privacy-safe way to follow a
user-initiated action and the affected device through every service.

This is needed for incident response, support, authorization review and
auditable 24/7 operations. Trace context alone describes technical
lineage; it does not answer who initiated the action, which business
event it represents, or which device was affected.

## Proposed decision

1. **Keep technical and business IDs distinct.** Preserve W3C
   `traceparent` and server-issued `X-Correlation-ID` under ADRs 0012 and
   0015. Do not overload either with an event, user, tenant or device ID.
2. **Define a per-operation trace context.** Where applicable, carry the
   following typed fields through authenticated service calls, event
   envelopes and audit records:
   - `tenant_id`: the tenant scope, validated at each service boundary;
   - `event_id`: the canonical envelope `id` for an event, retained as
     the deduplication and support lookup key;
   - `causation_id`: the prior command/event that caused this event;
   - `actor_ref`: a platform-issued opaque subject reference for a
     human/service actor; never copy an external IdP claim, email,
     username, access token or session identifier into this field;
   - `device_id`: the opaque tenant-scoped device UUID, only on
     device-related operations and events.
   Preserve the originating actor and causation when work crosses
   asynchronous boundaries. System-generated work identifies its
   service principal and records the initiating actor reference when
   there is one.
3. **Make audit records the accountability source.** Security-relevant
   actions (authorization decisions, grants/revocations, device
   property changes, firmware actions and environment access) record
   actor reference, tenant, target device when applicable, action,
   decision/outcome, event/correlation IDs, timestamp and policy
   version. Audit reads require explicit authorization and are
   tenant-scoped; retention and legal hold are configured per deployment.
   Audit records are append-only at the application boundary. Do not
   store credentials, tokens, property secrets or full payloads in the
   audit record.
4. **Apply data minimization by carrier.** `actor_ref`, `tenant_id`,
   `device_id` and `event_id` are not OTel baggage. Baggage remains
   limited to the correlation ID per ADR 0015. Do not use any of these
   IDs as metric labels. Spans and operational logs may include only
   opaque platform IDs when the service's data-classification policy
   permits it; security audit records remain the authoritative lookup
   path. Never log raw external identity claims, secrets, credentials or
   device property values classified as sensitive. Cross-tenant support
   views must be separately authorized and audited.
5. **Use explicit adapter mappings.** Each service owns its own
   framework-free trace-context type and maps it at REST, gRPC, Kafka,
   device-protocol and persistence adapters. Internal service calls
   authenticate independently; incoming identity/trace headers are
   validated at trust boundaries. Never treat caller-provided actor,
   tenant or device IDs as proof of authorization. Authorization is
   evaluated against the authenticated principal and resource ownership.
6. **Test the whole chain.** The observability acceptance suite creates
   a tenant-scoped user action on a device, emits an event, processes it
   in another service, and verifies that the audit lookup can connect
   actor, device, event, causation, `X-Correlation-ID` and
   `traceparent`. It also proves that cross-tenant spoofing is rejected,
   third-party egress strips internal context, credentials and sensitive
   payloads never appear in telemetry, and no identifier is a metric
   label. Test synchronous REST/gRPC and asynchronous Kafka paths.

## Consequences

- Every service template must define context mapping and audit behavior
  before it is considered production-ready; missing identifiers are
  explicit for system-originated work and operations with no device.
- Support can search using an event, correlation or opaque device
  reference without treating traces as the durable audit ledger.
- This ADR defines the contract only. Identity mapping, audit storage,
  retention periods, support break-glass access and service-specific
  data classifications remain implementation/configuration decisions.
- Existing requirements prohibit raw PII and secrets in events and
  telemetry. `actor_ref` and all other IDs must be reviewed against the
  platform's data-classification and privacy requirements before the
  proposal is accepted.

## Acceptance criteria

- Contract schemas define the trace-context fields and compatibility
  rules; event `id` remains canonical and is consistently called
  `event_id` in observability/support interfaces.
- A cross-service integration test proves end-to-end context across
  REST/gRPC and Kafka, including asynchronous actor and causation
  preservation.
- Tests reject forged tenant/device context and prove authorization is
  checked at every boundary.
- Automated leak checks confirm no tokens, credentials, raw IdP claims
  or prohibited payload data reach logs, spans, baggage, metrics or
  fixtures.
- Audit access is tenant-scoped, separately permissioned, and itself
  audited; retention and deletion behavior is documented per profile.

## Open decisions before acceptance

- Who issues `actor_ref`, its stability and rotation lifecycle, and how
  authorized auditors resolve it to a person or service principal.
- Which exact actions require durable audit records and which audit
  store/immutability controls are supported on-prem and in cloud.
- Retention, legal hold, redaction and break-glass policy by deployment
  jurisdiction and service tier.
- Which opaque IDs may appear in access-controlled spans/logs after the
  data-classification review.
